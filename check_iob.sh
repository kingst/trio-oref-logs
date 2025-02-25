#!/bin/bash

for iob_json in "$@"; do
    echo $iob_json
    python scripts/list_iob.py < $iob_json
done
