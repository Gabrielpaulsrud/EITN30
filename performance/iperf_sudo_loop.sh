#!/bin/bash

SERVER_IP="11.11.11.1"
CSV_FILE="iperf_results.csv"

# Write CSV header
echo "Sender_Bitrate_Kbps,Receiver_Bitrate_Kbps,Receiver_Jitter_ms" > "$CSV_FILE"

for (( b=10; b<=150; b+=10 ))
do
    bitrate="${b}K"
    echo "Running iperf3 test with bitrate $bitrate..."
    
    # Run iperf3 in namespace with sudo and capture output
    OUTPUT=$(sudo ip netns exec ns-client iperf3 -c $SERVER_IP -u -b $bitrate -l 32 -t 10)

    # Extract sender line
    SENDER_LINE=$(echo "$OUTPUT" | grep sender | tail -n 1)

    # Extract receiver line
    RECEIVER_LINE=$(echo "$OUTPUT" | grep receiver | tail -n 1)

    # Parse sender bitrate (6th column)
    SENDER_BITRATE=$(echo $SENDER_LINE | awk '{print $6}')

    # Parse receiver bitrate and jitter (6th and 7th column)
    RECEIVER_BITRATE=$(echo $RECEIVER_LINE | awk '{print $6}')
    RECEIVER_JITTER=$(echo $RECEIVER_LINE | awk '{print $7}')

    # Save to CSV
    echo "$SENDER_BITRATE,$RECEIVER_BITRATE,$RECEIVER_JITTER" >> "$CSV_FILE"

    # Sleep between tests
    sleep 3
done

echo "All tests complete. Results saved to $CSV_FILE."