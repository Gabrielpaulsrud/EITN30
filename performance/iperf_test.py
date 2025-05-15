import subprocess
import csv
import matplotlib.pyplot as plt

# Settings
server_ip = "11.11.11.1"
bitrates = range(10, 160, 10)  # from 10 to 150 step 10

# Lists to store the results
sender_bitrates = []
receiver_bitrates = []
receiver_jitters = []

# Optional: save raw iperf outputs
save_raw_outputs = False

for b in bitrates:
    bitrate_str = f"{b}K"
    print(f"Running iperf3 test with bitrate {bitrate_str}...")

    # Run iperf3 and capture output
    result = subprocess.run(
        ["iperf3", "-c", server_ip, "-u", "-b", bitrate_str, "-l", "32", "-t", "10"],
        capture_output=True,
        text=True
    )

    output = result.stdout

    if save_raw_outputs:
        with open(f"{b}_10s", "w") as f:
            f.write(output)

    # Parse output
    sender_bitrate = None
    receiver_bitrate = None
    receiver_jitter = None

    for line in output.splitlines():
        if 'sender' in line:
            parts = line.split()
            sender_bitrate = float(parts[6])
        if 'receiver' in line:
            parts = line.split()
            receiver_bitrate = float(parts[6])
            receiver_jitter = float(parts[7])

    # Store results
    if sender_bitrate is not None and receiver_bitrate is not None and receiver_jitter is not None:
        sender_bitrates.append(sender_bitrate)
        receiver_bitrates.append(receiver_bitrate)
        receiver_jitters.append(receiver_jitter)

    # Optional sleep between tests
    import time
    time.sleep(3)

# Save results to CSV
with open('iperf_results.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Sender_Bitrate_Kbps', 'Receiver_Bitrate_Kbps', 'Receiver_Jitter_ms'])
    for s, r, j in zip(sender_bitrates, receiver_bitrates, receiver_jitters):
        writer.writerow([s, r, j])

print("Results saved to iperf_results.csv")

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