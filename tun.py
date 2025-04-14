import os
import fcntl
import struct

TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

# 1. Open the tun device file
tun = os.open('/dev/net/tun', os.O_RDWR)

# 2. Create tun0
ifr = struct.pack('16sH', b'tun0', IFF_TUN | IFF_NO_PI)
fcntl.ioctl(tun, TUNSETIFF, ifr)

# 3. Assign IP and bring it up (these are terminal commands!)
os.system("ip addr add 11.11.11.2/24 dev tun0")
os.system("ip link set dev tun0 up")

print("TUN interface created and ready (tun0 @ 11.11.11.2)")

# 4. Loop to read + echo packets
try:
    while True:
        packet = os.read(tun, 2048)
        print(f"[📥] Received {len(packet)} bytes")
        os.write(tun, packet)
        print("[📤] Echoed back")
except KeyboardInterrupt:
    print("\nExiting.")
    os.close(tun)