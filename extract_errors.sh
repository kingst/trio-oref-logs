#!/bin/bash

# Check if date argument is provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 function YYYY-MM-DD"
    exit 1
fi

function=$1
input_date=$2

files=(downloaded_files/trio-oref-validation/algorithm-comparisons/${input_date}/0.5.0/${function}/*/*.json)

if [ -e "${files[0]}" ]; then
    for iob_json in "${files[@]}"; do
        python scripts/extract_error_results.py "$iob_json"
    done
fi
