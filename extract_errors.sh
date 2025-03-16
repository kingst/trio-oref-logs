#!/bin/bash

# Check if date argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 YYYY-MM-DD"
    exit 1
fi

input_date=$1

for iob_json in downloaded_files/trio-oref-validation/algorithm-comparisons/*/0.3.0/iob/*/*.json; do
    # Extract date from the file path (first wildcard)
    path_date=$(echo $iob_json | awk -F'/' '{print $4}')
    
    # Bash string comparison - the >= operator doesn't exist in bash for strings
    # Instead we check if path_date is either greater or equal to input_date
    if [[ "$path_date" > "$input_date" ]] || [[ "$path_date" = "$input_date" ]]; then
        python scripts/extract_iob_error_results.py $iob_json
    fi
done
