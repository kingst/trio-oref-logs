from datetime import datetime
import json
import sys

iob_results = json.loads(sys.stdin.read())

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} index < log_file.json > inputs.json")

print_index = int(sys.argv[1])
    
for index, iob_result in enumerate(iob_results):
    if index == print_index:
        inputs = iob_result["iobInput"]
        print(json.dumps(inputs, indent=4, sort_keys=True))
        
