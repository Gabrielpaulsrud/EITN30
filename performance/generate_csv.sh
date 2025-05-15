#!/bin/bash

OUTPUT_CSV="iperf_summary.csv"

# Write CSV header
echo "Bitrate_Kbps,Role,Interval,Transfer,Bitrate,Jitter,Loss/Total,Loss_Percent,Source_File" > $OUTPUT_CSV

# Loop through all test result files
for (( b=0; b<=100; b+=10 ))
do
    file="${b}_10s"

    # Make sure the file exists
    if [[ -f "$file" ]]; then
        # Get the last two lines (sender and receiver)
        grep -E "Kbits/sec|Mbits/sec" "$file" | tail -n 2 | while read -r line; do
            # Extract values using awk
            role=$(echo "$line" | awk '{print $NF}')
            interval=$(echo "$line" | awk '{print $2}')
            transfer=$(echo "$line" | awk '{print $4 " " $5}')
            bitrate=$(echo "$line" | awk '{print $6 " " $7}')
            jitter=$(echo "$line" | awk '{print $8 " " $9}')
            loss_total=$(echo "$line" | awk '{print $10}')
            loss_percent=$(echo "$line" | awk '{print $11}' | tr -d '()%')

            # Write row to CSV, include filename as Source_File
            echo "$b,$role,$interval,$transfer,$bitrate,$jitter,$loss_total,$loss_percent,$file" >> $OUTPUT_CSV
        done
    fi
done
