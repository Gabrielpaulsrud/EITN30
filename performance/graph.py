import matplotlib.pyplot as plt
import csv

# Lists to store data
sender_bitrates = []
receiver_bitrates = []
receiver_jitters = []

# Open and read the CSV
with open('iperf_results.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip the header

    for row in reader:
        sender_bitrates.append(float(row[0]))
        receiver_bitrates.append(float(row[1]))
        receiver_jitters.append(float(row[2]))

# Plot: Sender vs Receiver bitrate
plt.figure(figsize=(8,6))
plt.scatter(sender_bitrates, receiver_bitrates, color='b', s=80)
plt.xlabel('Sender Bitrate (Kbps)')
plt.ylabel('Receiver Bitrate (Kbps)')
plt.title('Sender vs Receiver Bitrate')
plt.grid(True)
plt.show()

# Plot: Sender vs Receiver jitter
plt.figure(figsize=(8,6))
plt.scatter(sender_bitrates, receiver_jitters, color='r', s=80)
plt.xlabel('Sender Bitrate (Kbps)')
plt.ylabel('Receiver Jitter (ms)')
plt.title('Sender Bitrate vs Receiver Jitter')
plt.grid(True)
plt.show()