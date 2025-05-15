#!/bin/bash

OUTPUT_CSV="iperf_summary.csv"

# Write CSV header
echo "Bitrate_Kbps,Role,Interval,Transfer,Bitrate,Jitter,Loss/Total,Loss_Percent,Source_File" > "$OUTPUT_CSV"

# Regex pattern explained below
pattern='^\[ *[0-9]+\] +([0-9.]+-[0-9.]+) +sec +([0-9.]+ [KMG]Bytes) +([0-9.]+ [KMG]bits/sec) +([0-9.]+ ms) +([0-9]+/[0-9]+) +\(([0-9.]+)%\) +(sender|receiver)$'

# Process each file
for (( b=10; b<=150; b+=10 ))
do
    file="${b}_10s"
    if [[ -f "$file" ]]; then
        grep -E "Kbits/sec|Mbits/sec|Gbits/sec" "$file" | tail -n 2 | while read -r line; do
            if [[ $line =~ $pattern ]]; then
                interval="${BASH_REMATCH[1]}"
                transfer="${BASH_REMATCH[2]}"
                bitrate="${BASH_REMATCH[3]}"
                jitter="${BASH_REMATCH[4]}"
                loss_total="${BASH_REMATCH[5]}"
                loss_percent="${BASH_REMATCH[6]}"
                role="${BASH_REMATCH[7]}"
                
                echo "$b,$role,$interval,$transfer,$bitrate,$jitter,$loss_total,$loss_percent,$file" >> "$OUTPUT_CSV"
            fi
        done
    fi
done

