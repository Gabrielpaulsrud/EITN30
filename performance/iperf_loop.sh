#!/bin/bash

SERVER_IP="11.11.11.1"

for (( b=10; b<=150; b+=10 ))
do
    bitrate="${b}K"
    output_file="${b}_10s"
    echo "Running iperf3 test with bitrate $bitrate..."
    iperf3 -c $SERVER_IP -u -b $bitrate -l 32 -t 10 > "$output_file"
    sleep 3
done
