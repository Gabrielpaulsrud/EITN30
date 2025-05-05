import os
import fcntl
import struct
import socket

TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

# 1. Open the tun device file
tun = os.open('/dev/net/tun', os.O_RDWR)

# 2. Create myG tun interface
ifr = struct.pack('16sH', b'myG', IFF_TUN | IFF_NO_PI)
fcntl.ioctl(tun, TUNSETIFF, ifr)

# 3. Assign IP and bring it up
os.system("ip addr add 11.11.11.2/24 dev myG")
os.system("ip link set dev myG up")

print("TUN interface created and ready (myG @ 11.11.11.2)")
print("Waiting for packets...")

def is_icmp_echo_request(packet):
    if len(packet) < 20:
        return False
    ip_header = packet[:20]
    iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
    protocol = iph[6]
    if protocol != 1:  # Not ICMP
        return False
    # IP header length in 32-bit words
    ihl = iph[0] & 0x0F
    ip_header_len = ihl * 4
    if len(packet) < ip_header_len + 1:
        return False
    icmp_type = packet[ip_header_len]
    return icmp_type == 8  # ICMP Echo Request

try:
    while True:
        packet = os.read(tun, 2048)
        if is_icmp_echo_request(packet):
            print("🚀 ICMP Echo Request (ping) received!")
        else:
            print(f"[📥] Received {len(packet)} bytes (non-ping)")
        os.write(tun, packet)
except KeyboardInterrupt:
    print("\n[✋] Exiting.")
    os.close(tun)