import os
import fcntl
import struct
import board
from digitalio import DigitalInOut
import spidev
from circuitpython_nrf24l01.rf24 import RF24
import threading
import time
import subprocess
import socket

MAX_PAYLOAD = 32
HEADER_SIZE = 4
CHUNK_SIZE = MAX_PAYLOAD - HEADER_SIZE

def get_ip_address(ifname):
    """Get the IPv4 address assigned to a network interface."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode())
        )[20:24])
    except OSError:
        return None

def create_tun(base_station: bool):
    dnsmasq_proc = None
    TUNSETIFF = 0x400454ca
    IFF_TUN   = 0x0001
    IFF_NO_PI = 0x1000

    # 1. Open the tun device file
    tun = os.open('/dev/net/tun', os.O_RDWR)

    # 2. Create myG tun interface
    ifr = struct.pack('16sH', b'myG', IFF_TUN | IFF_NO_PI)

    fcntl.ioctl(tun, TUNSETIFF, ifr)

    # 3. Bring the interface up
    os.system("ip link set dev myG up")

    # Todo fix this comment, also can os.system("ip link set dev myG up") be moved out of the if statement
    # 3. If base station, assign yourself a static IP and star DHCP server
    #    If mobile device, get IP from DHCP server
    if base_station:
        # Assign static IP to base station side
        os.system(f"ip addr add 11.11.11.1/24 dev myG")
        print(f"TUN interface created and ready (myG @ 11.11.11.1)")
        
        # Start dnsmasq DHCP server
        dnsmasq_proc = subprocess.Popen([
            "dnsmasq",
            "--interface=myG",
            "--bind-interfaces",
            "--dhcp-range=10.0.0.10,10.0.0.100,12h"
        ])
        print("Started DHCP server with dnsmasq")
    else:
        # Run DHCP client to get dynamic IP from base station
        subprocess.Popen(["dhclient", "myG"])
        #print("Requesting IP from DHCP server...", end="", flush=True)
        threading.Thread(target=wait_for_dhcp, daemon=True).start()
        # Wait until an IP is assigned
        # ip = None
        # for _ in range(30):  # wait up to ~3 seconds
        #     ip = get_ip_address("myG")
        #     if ip:
        #         break
        #     print(".", end="", flush=True)
        #     time.sleep(0.1)

        # if ip:
        #     print(f"\nTUN interface created and ready (myG @ {ip})")
        # else:
        #     print("\nFailed to obtain IP address via DHCP")

    return tun, dnsmasq_proc

def setup_nRF24L01(radio_number):
    # Sender module setup
    SPI_BUS = spidev.SpiDev()
    CSN_SEND = 0  # SPI CE0
    CE_SEND = DigitalInOut(board.D17)
    nrf_send = RF24(SPI_BUS, CSN_SEND, CE_SEND)
    nrf_send.pa_level = -12

    # Receiver module setup
    SPI_BUS2 = spidev.SpiDev()
    CSN_RECV = 10  # SPI CE1
    CE_RECV = DigitalInOut(board.D27)
    nrf_recv = RF24(SPI_BUS2, CSN_RECV, CE_RECV)
    nrf_recv.pa_level = -12


    addresses = [b"1Node", b"2Node"]
    # Radio number is either 0 or 1, used to initalize the different radios with different addresses
    # addresses needs to be in a buffer protocol object (bytearray)
    my_addres = addresses[radio_number]
    other_addres = addresses[1-radio_number]

    nrf_send.channel = 76 + radio_number   # depending on destination
    nrf_send.open_tx_pipe(other_addres)
    nrf_send.listen = False

    nrf_recv.channel = 77 - radio_number   # opposite of sender
    nrf_recv.open_rx_pipe(1, my_addres)
    nrf_recv.listen = True
    return nrf_send, nrf_recv

def receive_loop(nrf_recv, tun):
    message_parts = {}
    expected_chunks = None
    packet_id = None
    while True:
        if nrf_recv.any():
            packet = nrf_recv.read()
            pid, total, seq, _ = packet[:4]
            print(f"Received message {pid}, {total}, {seq}")
            data = packet[4:]

            # First packet: set expectations
            if packet_id is None:
                packet_id = pid
                expected_chunks = total

            # Ignore other packet_ids
            if pid != packet_id:
                continue

            message_parts[seq] = data
            if len(message_parts) == expected_chunks:
                full_bytes = b''.join(message_parts[i] for i in sorted(message_parts))

                print(f"Construced message of {expected_chunks} chunks:")
                os.write(tun, full_bytes)
                message_parts = {}
                expected_chunks = None
                packet_id = None


def wait_for_dhcp():
    print("Requesting IP from DHCP server...", end="", flush=True)
    ip = None
    for _ in range(50):  # ~5 seconds
        ip = get_ip_address("myG")
        if ip:
            break
        print(".", end="", flush=True)
        time.sleep(0.1)
    if ip:
        print(f"\nTUN interface created and ready (myG @ {ip})")
    else:
        print("\n❌ Failed to obtain IP address via DHCP")

def main(radio_number):
    if radio_number == 0:
        base_station = True
    else:
        base_station = False
    nrf_send, nrf_recv = setup_nRF24L01(radio_number)
    tun, dnsmasq_proc = create_tun(base_station)
    
    recv_thread = threading.Thread(target=receive_loop, args=(nrf_recv, tun,), daemon=True)
    recv_thread.start()

    packet_id = 0
    try:
        while True:
            data_bytes = os.read(tun, 2048)
            total_chunks = (len(data_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
            packet_id+=1   # Just an example, increment for each message

            print(f"\nReceived on TUN, writing to nrf")
            for seq in range(total_chunks):
                start = seq * CHUNK_SIZE
                end = start + CHUNK_SIZE
                chunk = data_bytes[start:end]
                header = bytes([packet_id, total_chunks, seq, 0])  # last byte = flags or reserved
                packet = header + chunk
                nrf_send.send(packet)
    except KeyboardInterrupt:
        print("Exiting tunnel...")
        os.close(tun)
        if base_station:
            dnsmasq_proc.terminate()
            dnsmasq_proc.wait()
            subprocess.run(["pkill", "dnsmasq"])
            print("dnsmasq terminated")
    # try:
    #     while True:
    #         packet = os.read(tun, 2048)
    #         if len(packet) > 32:
    #             print("⚠️ Packet too large for nRF24L01, dropping")
    #             continue
    #         print(f"\nReceived on TUN, writing to nrf")
    #         nrf_send.send(packet)
    # except KeyboardInterrupt:
    #     print("Exiting tunnel...")
    #     os.close(tun)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ["0", "1"]:
        print("Usage: python symmetrical_msg.py [0|1]")
        sys.exit(1)

    radio_number = int(sys.argv[1])
    main(radio_number)