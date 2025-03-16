#!/bin/bash

# Check if an argument was provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <function> YYYY-MM-DD"
    echo "Example: $0 iob 2025-03-15"
    exit 1
fi

# Store the command line argument
function=$1
input_date=$2

# Use the provided value in the path
for json in downloaded_files/trio-oref-validation/algorithm-comparisons/*/0.3.0/"${function}"/*/*.json; do
    path_date=$(echo $json | awk -F'/' '{print $4}')
    if [[ "$path_date" > "$input_date" ]] || [[ "$path_date" = "$input_date" ]]; then
	python scripts/list_errors.py $function < $json
    fi
done
