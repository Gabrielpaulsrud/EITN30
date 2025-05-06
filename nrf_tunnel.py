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
import sys

MAX_PAYLOAD = 32
HEADER_SIZE = 4
CHUNK_SIZE = MAX_PAYLOAD - HEADER_SIZE

# Message flag definitions
FLAG_NORMAL = 0      # Regular IP packet
FLAG_IP_REQUEST = 1  # Mobile → Base: asks for IP
FLAG_IP_ASSIGN  = 2  # Base → Mobile: assigns IP
FLAG_DEBUG      = 3  # Optional: debug or test messages

class TunnelNode:
    def __init__(self, radio_number: int):
        self.radio_number = radio_number
        self.base_station = (radio_number == 0)
        self.next_packet_id = 1
        self.next_ip_addr = 2
        self.send_lock = threading.Lock()
        self.ip_assigned_event = threading.Event()
        self.assigned_ip = None  # optional, for debugging or future use

        self.nrf_send, self.nrf_recv = self.setup_nRF24L01()
        self.tun = self.create_tun()

    def setup_nRF24L01(self):
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
        my_addres = addresses[self.radio_number]
        other_addres = addresses[1-self.radio_number]

        nrf_send.channel = 76 + self.radio_number   # depending on destination
        nrf_send.open_tx_pipe(other_addres)
        nrf_send.listen = False

        nrf_recv.channel = 77 - self.radio_number   # opposite of sender
        nrf_recv.open_rx_pipe(1, my_addres)
        nrf_recv.listen = True
        return nrf_send, nrf_recv

    def create_tun(self):
        TUNSETIFF = 0x400454ca
        IFF_TUN   = 0x0001
        IFF_NO_PI = 0x1000 # Don't include packet info in TUN interface

        # 1. Open the tun device file
        tun = os.open('/dev/net/tun', os.O_RDWR)

        # 2. Create myG tun interface
        ifr = struct.pack('16sH', b'myG', IFF_TUN | IFF_NO_PI)

        fcntl.ioctl(tun, TUNSETIFF, ifr) # Creates the TUN interface

        # 3. Bring the interface up
        os.system("ip link set dev myG up")

        # 3. If base station, assign yourself a static IP 
        #    If mobile device, get IP from base station
        if self.base_station:
            # Assign static IP to base station side
            os.system(f"ip addr add 11.11.11.1/24 dev myG")
            print(f"TUN interface created and ready (myG @ 11.11.11.1)")
            
        if not self.base_station:
            print("📡 Requesting IP address from base station...")
            # self.send_message(b"IP_REQUEST", flag=FLAG_IP_REQUEST)
            # self.request_ip_from_base()
            threading.Thread(target=self.request_ip_from_base, daemon=True).start()

        return tun

    def request_ip_from_base(self):
        max_attempts = 10
        for attempt in range(max_attempts):
            print(f"📡 Sending IP request... attempt {attempt+1}")
            self.send_message(b"IP_REQUEST", flag=FLAG_IP_REQUEST)
            if self.ip_assigned_event.wait(timeout=1.0):  # wait 1 second
                print(f"✅ IP successfully assigned: {self.assigned_ip}")
                return
            print("⏳ No response, retrying...")
        
        print("❌ Failed to obtain IP after multiple attempts.")

    def receive_loop(self):
        message_parts = {}
        expected_chunks = None
        packet_id = None
        while True:
            if self.nrf_recv.any():
                packet = self.nrf_recv.read()
                pid, total, seq, flag = packet[:4]
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
                    if (flag == FLAG_NORMAL):
                        os.write(self.tun, full_bytes)

                    if (flag == FLAG_IP_ASSIGN):
                        if not self.base_station:
                            ip_str = data.decode()
                            print(f"🎯 Received IP assignment: {ip_str}")
                            os.system(f"ip addr add {ip_str}/24 dev myG")
                            self.assigned_ip = ip_str
                            self.ip_assigned_event.set()
                        else:
                            print("WARNING: Got IP assignment but this is the base station, discarding")


                    if (flag == FLAG_IP_REQUEST):
                        if self.base_station:
                            ip_str = f"11.11.11.{self.next_ip_addr}"
                            self.next_ip_addr += 1
                            print(f"🛠 Assigning IP {ip_str} to requester")
                            self.send_message(ip_str.encode(), flag=FLAG_IP_ASSIGN)
                        else:
                            print("WARNING: Got IP request but not base station")

                    # Reseet to prepare for next message
                    message_parts = {}
                    expected_chunks = None
                    packet_id = None

    def send_message(self, message: bytes, flag: int):
        with self.send_lock:
            packet_id = self.next_packet_id
            self.next_packet_id = (self.next_packet_id + 1) % 256  # Wrap at 255 to fit in 1 byte

            total_chunks = (len(message) + CHUNK_SIZE - 1) // CHUNK_SIZE
            for seq in range(total_chunks):
                start = seq * CHUNK_SIZE
                end = start + CHUNK_SIZE
                chunk = message[start:end]
                header = bytes([packet_id, total_chunks, seq, flag])
                packet = header + chunk
                self.nrf_send.send(packet)
    
    def run(self):
        threading.Thread(target=self.receive_loop, daemon=True).start()
        try:
            while True:
                data_bytes = os.read(self.tun, 2048)
                print(f"\nReceived on TUN, writing to nrf")
                self.send_message(data_bytes, FLAG_NORMAL)
        except KeyboardInterrupt:
            print("Exiting tunnel...")
            os.close(self.tun)

if __name__ == "__main__":
    
    if len(sys.argv) != 2 or sys.argv[1] not in ["0", "1"]:
        print("Usage: python symmetrical_msg.py [0|1]")
        sys.exit(1)

    radio_number = int(sys.argv[1])
    node = TunnelNode(radio_number)
    node.run()