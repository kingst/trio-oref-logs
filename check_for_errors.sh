#!/bin/bash

# Check if an argument was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <function>"
    echo "Example: $0 iob"
    exit 1
fi

# Store the command line argument
function="$1"

# Use the provided value in the path
for json in downloaded_files/trio-oref-validation/algorithm-comparisons/*/0.3.0/"${function}"/*/*.json; do
    python scripts/list_errors.py $function < $json
done
