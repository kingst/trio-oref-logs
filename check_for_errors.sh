#!/bin/bash

# Check if an argument was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 YYYY-MM-DD"
    echo "Example: $0 2025-03-15"
    exit 1
fi

# Store the command line argument
input_date=$1

for func in autosens determineBasal iob profile meal; do
    # Use the provided value in the path
    echo "Checking ${func}"
    count=0
    shopt -s nullglob
    for json in downloaded_files/trio-oref-validation/algorithm-comparisons/${input_date}/0.5.0/"${func}"/*/*.json; do
        count=$((count + $(python3 scripts/list_errors.py $func < "$json" | wc -l)))
    done
    echo "Found ${count} errors for ${func}"
done
