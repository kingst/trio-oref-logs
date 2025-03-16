from datetime import datetime
import json
import os
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} logfile.json")
    sys.exit(1)

iob_results = json.loads(open(sys.argv[1]).read())
logfile = os.path.splitext(os.path.basename(sys.argv[1]))[0]
for index, iob_result in enumerate(iob_results):
    result = iob_result["resultType"]
    if result != "matching":
        filename = f"{logfile}.{index}.json"
        open(f'errors/{filename}', 'w').write((json.dumps(iob_result, indent=4, sort_keys=True)))
        
