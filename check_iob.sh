#!/bin/bash

for iob_json in downloaded_files/trio-oref-validation/algorithm-comparisons/*/0.3.0/iob/*/*.json; do
    #echo $iob_json
    python scripts/list_iob.py < $iob_json
done
