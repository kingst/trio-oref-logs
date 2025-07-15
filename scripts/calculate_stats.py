#!/usr/bin/env python

import datetime
import json
import os
from collections import Counter, defaultdict

# Configuration
# Path to the directory containing the daily log folders
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'downloaded_files', 'trio-oref-validation', 'algorithm-comparisons')
DAYS_TO_PROCESS = 7

def process_record(record, stats, day_str, function_name, device_id, app_version):
    """Processes a single record and updates statistics."""
    if not isinstance(record, dict):
        print(f"Warning: Skipping malformed record, expected a dictionary but got {type(record)}")
        return

    # Filter out simulator data
    if record.get('isSimulator', False):
        return

    stats['total_comparisons'] += 1
    result_type = record.get('resultType')

    # Collect timing data
    js_duration = record.get('jsDuration')
    swift_duration = record.get('swiftDuration')
    if js_duration is not None and swift_duration is not None:
        stats['timing_data'][function_name]['js_durations'].append(js_duration)
        stats['timing_data'][function_name]['swift_durations'].append(swift_duration)

    if result_type != 'matching':
        stats['total_errors'] += 1
        stats['errors_by_day'][day_str] += 1
        stats['errors_by_function'][function_name] += 1
        stats['errors_by_device'][device_id] += 1
        stats['errors_by_oref_version'][app_version] += 1
        stats['errors_by_swift_version'][app_version] += 1

def calculate_stats():
    """Calculates and prints statistics from downloaded logs."""
    stats = {
        'total_comparisons': 0,
        'total_errors': 0,
        'errors_by_day': Counter(),
        'errors_by_function': Counter(),
        'errors_by_oref_version': Counter(),
        'errors_by_device': Counter(),
        'errors_by_swift_version': Counter(),
        'timing_data': defaultdict(lambda: defaultdict(list)) # Store durations for timing analysis
    }

    today = datetime.date.today()
    for i in range(DAYS_TO_PROCESS):
        date = today - datetime.timedelta(days=i)
        day_str = date.strftime('%Y-%m-%d')
        day_path = os.path.join(DOWNLOAD_DIR, day_str)

        if not os.path.exists(day_path):
            continue

        for root, _, files in os.walk(day_path):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    
                    # Extract metadata from path
                    try:
                        # Path is .../{date}/{app_version}/{function}/{device_id}/{file}.json
                        path_parts = root.split(os.sep)
                        device_id = path_parts[-1]
                        function_name = path_parts[-2]
                        app_version = path_parts[-3]
                    except IndexError:
                        print(f"Warning: Could not extract metadata from path: {filepath}")
                        continue # Skip if path is malformed

                    with open(filepath, 'r') as f:
                        try:
                            content = json.load(f)
                            records = content if isinstance(content, list) else [content]
                            
                            for record in records:
                                process_record(record, stats, day_str, function_name, device_id, app_version)

                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON from {filepath}")
    
    return stats

def print_stats(stats):
    """Prints a formatted report of the statistics."""
    print("\n--- Statistics Report ---")
    print(f"Total Comparisons (excluding simulators): {stats['total_comparisons']}")
    print(f"Total Errors (excluding simulators): {stats['total_errors']}")
    
    print("\nErrors by Day:")
    for day, count in sorted(stats['errors_by_day'].items()):
        print(f"  {day}: {count}")

    print("\nErrors by Function:")
    for function, count in stats['errors_by_function'].most_common():
        print(f"  {function}: {count}")

    print("\nErrors by oref_version:")
    for version, count in stats['errors_by_oref_version'].most_common():
        print(f"  {version}: {count}")

    print("\nErrors by Swift Version:")
    for version, count in stats['errors_by_swift_version'].most_common():
        print(f"  {version}: {count}")

    print("\nErrors by Device:")
    for device, count in stats['errors_by_device'].most_common():
        print(f"  {device}: {count}")

    print("\n--- Timing Statistics by Function ---")
    for function, durations in stats['timing_data'].items():
        js_durations = durations['js_durations']
        swift_durations = durations['swift_durations']

        if js_durations and swift_durations:
            avg_js = sum(js_durations) / len(js_durations)
            avg_swift = sum(swift_durations) / len(swift_durations)
            avg_diff = avg_swift - avg_js

            print(f"\n{function}:")
            print(f"  Avg JS Duration: {avg_js:.4f}")
            print(f"  Avg Swift Duration: {avg_swift:.4f}")
            print(f"  Avg Difference (Swift - JS): {avg_diff:.4f}")
            print(f"  {'(Swift slower)' if avg_diff > 0 else '(Same)' if avg_diff == 0 else '(Swift faster)'}")

    print("------------------------\n")

def main():
    """Main function to run the script."""
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"Error: Download directory not found at {DOWNLOAD_DIR}")
        print("Please run the download script first.")
        return

    stats = calculate_stats()
    print_stats(stats)

if __name__ == "__main__":
    main()
