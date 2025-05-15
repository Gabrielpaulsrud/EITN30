import matplotlib.pyplot as plt
import glob
import os

# Lists to collect data
sender_bitrates = []
receiver_bitrates = []
receiver_jitters = []

# Find all files ending with _10s
files = glob.glob("*_10s")

for filename in files:
    with open(filename, 'r') as file:
        lines = file.readlines()
        sender_bitrate = None
        receiver_bitrate = None
        receiver_jitter = None
        
        for line in lines:
            if 'sender' in line:
                parts = line.split()
                sender_bitrate = float(parts[6])
            if 'receiver' in line:
                parts = line.split()
                receiver_bitrate = float(parts[6])
                receiver_jitter = float(parts[8])

        # Only add if all values were found
        if sender_bitrate is not None and receiver_bitrate is not None and receiver_jitter is not None:
            sender_bitrates.append(sender_bitrate)
            receiver_bitrates.append(receiver_bitrate)
            receiver_jitters.append(receiver_jitter)

# Now make the plots
# 1st plot: Sender vs Receiver bitrate
plt.figure(figsize=(8,6))
plt.scatter(sender_bitrates, receiver_bitrates, color='b', s=80)
# plt.plot(sender_bitrates, receiver_bitrates, linestyle='--', alpha=0.5)
plt.xlabel('Sender Bitrate (Kbps)')
plt.ylabel('Receiver Bitrate (Kbps)')
plt.title('Sender vs Receiver Bitrate')
plt.grid(True)
plt.show()

# 2nd plot: Sender vs Receiver jitter
plt.figure(figsize=(8,6))
plt.scatter(sender_bitrates, receiver_jitters, color='r', s=80)
# plt.plot(sender_bitrates, receiver_jitters, linestyle='--', alpha=0.5)
plt.xlabel('Sender Bitrate (Kbps)')
plt.ylabel('Receiver Jitter (ms)')
plt.title('Sender Bitrate vs Receiver Jitter')
plt.grid(True)
plt.show()