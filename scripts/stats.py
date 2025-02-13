import sqlite3
import sys
from typing import Dict, List, Tuple


def get_overall_stats(cursor) -> Tuple[int, int, int, int]:
    """Get overall statistics."""
    cursor.execute("""
        SELECT 
            COUNT(*) as total_comparisons,
            COUNT(DISTINCT device_id) as unique_devices,
            COUNT(DISTINCT app_version) as unique_versions,
            COUNT(DISTINCT function) as unique_functions
        FROM comparisons
    """)
    return cursor.fetchone()


def get_result_distribution(cursor) -> List[Tuple[str, int, float]]:
    """Get distribution of result types."""
    cursor.execute("""
        SELECT 
            result_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM comparisons), 1) as percentage
        FROM comparisons 
        GROUP BY result_type
        ORDER BY count DESC
    """)
    return cursor.fetchall()


def get_function_stats(cursor) -> List[Tuple[str, int, int, int, int]]:
    """Get statistics broken down by function."""
    cursor.execute("""
        SELECT 
            function,
            COUNT(*) as total,
            SUM(CASE WHEN result_type = 'matching' THEN 1 ELSE 0 END) as matching_count,
            SUM(CASE WHEN result_type = 'valueDifference' THEN 1 ELSE 0 END) as diff_count,
            COUNT(DISTINCT device_id) as device_count
        FROM comparisons
        GROUP BY function
        ORDER BY total DESC
    """)
    return cursor.fetchall()


def get_duration_stats(cursor) -> List[Tuple[str, float, float, float]]:
    """Get duration statistics."""
    cursor.execute("""
        SELECT 
            function,
            ROUND(AVG(js_duration), 4) as avg_js,
            ROUND(AVG(swift_duration), 4) as avg_swift,
            ROUND(AVG(swift_duration - js_duration), 4) as avg_diff
        FROM comparisons
        WHERE js_duration IS NOT NULL 
        AND swift_duration IS NOT NULL
        GROUP BY function
        ORDER BY avg_diff DESC
    """)
    return cursor.fetchall()


def get_common_differences(cursor) -> List[Tuple[str, int, int]]:
    """Get most common value differences."""
    cursor.execute("""
        SELECT 
            key,
            COUNT(*) as occurrences,
            COUNT(DISTINCT comparison_id) as comp_count
        FROM differences
        GROUP BY key
        ORDER BY occurrences DESC
        LIMIT 10
    """)
    return cursor.fetchall()


def print_stats(db_path: str):
    """Print all statistics in a formatted way."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Overall Statistics
        total, devices, versions, functions = get_overall_stats(cursor)
        print("\n=== Overall Statistics ===")
        print(f"Total Comparisons: {total:,}")
        print(f"Unique Devices: {devices}")
        print(f"App Versions: {versions}")
        print(f"Functions: {functions}")
        
        # Result Type Distribution
        print("\n=== Result Type Distribution ===")
        for result_type, count, percentage in get_result_distribution(cursor):
            print(f"{result_type}: {count:,} ({percentage}%)")
        
        # Function Statistics
        print("\n=== Function Statistics ===")
        for func, total, matching, diff, devices in get_function_stats(cursor):
            print(f"\n{func}:")
            print(f"  Total: {total:,}")
            print(f"  Matching: {matching:,}")
            print(f"  Differences: {diff:,}")
            print(f"  Devices: {devices}")
        
        # Duration Statistics
        print("\n=== Duration Statistics ===")
        for func, js_dur, swift_dur, diff in get_duration_stats(cursor):
            print(f"\n{func}:")
            print(f"  Avg JS Duration: {js_dur:.4f}")
            print(f"  Avg Swift Duration: {swift_dur:.4f}")
            print(f"  Avg Difference: {diff:.4f}")
            print(f"  {'(Swift slower)' if diff > 0 else '(Swift faster)' if diff < 0 else '(Same)'}")
        
        # Most Common Differences
        print("\n=== Most Common Value Differences ===")
        for key, occurrences, comp_count in get_common_differences(cursor):
            print(f"{key}: {occurrences:,} occurrences in {comp_count:,} comparisons")


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <database_path>")
        print("Example: python script.py comparisons.db")
        sys.exit(1)

    db_path = sys.argv[1]
    print_stats(db_path)


if __name__ == "__main__":
    main()
