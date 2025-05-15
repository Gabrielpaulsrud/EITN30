#!/bin/bash

# File to save the metrics
OUTPUT_FILE="performance_metrics.csv"

# Write the header to the CSV file
echo "Size,DNS Lookup,Connect,Start Transfer,Total,Size Downloaded" > $OUTPUT_FILE

# Range of sizes to test
START_SIZE=100
END_SIZE=1000
STEP_SIZE=100

# Function to make the request and save the metrics
measure_performance() {
    SIZE=$1
    METRICS=$(curl -o /dev/null -s -w \
        "%{time_namelookup},%{time_connect},%{time_starttransfer},%{time_total},%{size_download}\n" \
        http://localhost:8080/$SIZE)
    
    # Append the size and metrics to the CSV file
    echo "$SIZE,$METRICS" >> $OUTPUT_FILE
}

# Sweep over the range of sizes
for (( SIZE=$START_SIZE; SIZE<=$END_SIZE; SIZE+=$STEP_SIZE )); do
    measure_performance $SIZE
done

echo "Performance metrics saved to $OUTPUT_FILE"
