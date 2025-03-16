from datetime import datetime
import json
import sys

iob_results = json.loads(sys.stdin.read())

for index, iob_result in enumerate(iob_results):
    result = iob_result["resultType"]
    created_at = iob_result["createdAt"]
    time = datetime.fromtimestamp(created_at)
    if result != "matching":
        print(f"iob[{created_at}]: {result} @ {time.strftime('%A, %B %d, %Y at %I:%M %p')}")

