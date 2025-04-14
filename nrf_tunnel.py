import os
import fcntl
import struct
import board
from digitalio import DigitalInOut
import spidev
from circuitpython_nrf24l01.rf24 import RF24
import threading
import time

MAX_PAYLOAD = 32
HEADER_SIZE = 4
CHUNK_SIZE = MAX_PAYLOAD - HEADER_SIZE

def create_tun(radio_number):
    adress = radio_number+1
    TUNSETIFF = 0x400454ca
    IFF_TUN   = 0x0001
    IFF_NO_PI = 0x1000

    # 1. Open the tun device file
    tun = os.open('/dev/net/tun', os.O_RDWR)


    # 2. Create tun0
    ifr = struct.pack('16sH', b'tun0', IFF_TUN | IFF_NO_PI)
    # tun_name = f"tun{adress}"
    # ifr = struct.pack('16sH', tun_name.encode(), IFF_TUN | IFF_NO_PI)

    fcntl.ioctl(tun, TUNSETIFF, ifr)

    # 3. Assign IP and bring it up
    # os.system(f"ip addr add 11.11.11.{adress}/24 dev {tun_name}")
    # os.system(f"ip link set dev {tun_name} up")
    os.system(f"ip addr add 11.11.11.{adress}/24 dev tun0")
    os.system("ip link set dev tun0 up")

    print(f"TUN interface created and ready (tun0 @ 11.11.11.{adress})")
    return tun

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
                # full_msg = full_bytes.decode('utf-8')
                print(f"Construced message of {expected_chunks} chunks:")
                os.write(tun, full_bytes)
                message_parts = {}
                expected_chunks = None
                packet_id = None


def main(radio_number):
    nrf_send, nrf_recv = setup_nRF24L01(radio_number)
    tun = create_tun(radio_number)
    
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
            nrf_send.send(packet)
    except KeyboardInterrupt:
        print("Exiting tunnel...")
        os.close(tun)
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