import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys


class DatabaseCreator:
    def __init__(self, db_name: str):
        self.db_path = db_name
        self.setup_database()

    def setup_database(self):
        """Create SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main comparison table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparisons (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP,
                    function TEXT,
                    result_type TEXT,
                    js_duration REAL,
                    swift_duration REAL,
                    app_version TEXT,
                    device_id TEXT,
                    batch_id TEXT
                )
            """)

            # Value differences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS differences (
                    comparison_id TEXT,
                    key TEXT,
                    js_value TEXT,
                    swift_value TEXT,
                    js_key_missing BOOLEAN,
                    native_key_missing BOOLEAN,
                    FOREIGN KEY(comparison_id) REFERENCES comparisons(id),
                    PRIMARY KEY(comparison_id, key)
                )
            """)

            # Exceptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exceptions (
                    comparison_id TEXT,
                    exception_type TEXT,  -- 'js', 'swift', or 'comparison'
                    message TEXT,
                    stack_trace TEXT,
                    error_type TEXT,
                    FOREIGN KEY(comparison_id) REFERENCES comparisons(id),
                    PRIMARY KEY(comparison_id, exception_type)
                )
            """)

    def process_file(self, file_path: Path):
        """Process a single JSON file."""
        try:
            with open(file_path, 'r') as f:
                comparisons = json.load(f)

            # Extract metadata from path
            parts = file_path.parts
            # Find the indices of our metadata in the path
            app_version_idx = next(i for i, part in enumerate(parts) if part.count('.') >= 2)  # Looks for semver
            device_id_idx = app_version_idx + 2  # device id is two parts after app version
            batch_id = file_path.stem  # filename without extension

            app_version = parts[app_version_idx]
            device_id = parts[device_id_idx]

            with sqlite3.connect(self.db_path) as conn:
                for comparison in comparisons:
                    if self.is_new_format(comparison):
                        # Add metadata
                        comparison['app_version'] = app_version
                        comparison['device_id'] = device_id
                        comparison['batch_id'] = batch_id
                        self.save_comparison(conn, comparison)

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def is_new_format(self, comparison):
        """Check if comparison uses the new format."""
        required_fields = {'id', 'createdAt', 'function', 'resultType'}
        return all(field in comparison for field in required_fields)

    def save_comparison(self, conn, comparison):
        """Save a single comparison and its related data."""
        cursor = conn.cursor()
        
        # Insert main comparison record
        cursor.execute("""
            INSERT OR REPLACE INTO comparisons (
                id, created_at, function, result_type,
                js_duration, swift_duration, app_version, device_id, batch_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comparison['id'],
            datetime.fromtimestamp(comparison['createdAt']),
            comparison['function'],
            comparison['resultType'],
            comparison.get('jsDuration'),
            comparison.get('swiftDuration'),
            comparison['app_version'],
            comparison['device_id'],
            comparison['batch_id']
        ))
        
        # Insert differences if present
        if comparison.get('differences'):
            for key, diff in comparison['differences'].items():
                cursor.execute("""
                    INSERT OR REPLACE INTO differences (
                        comparison_id, key, js_value, swift_value,
                        js_key_missing, native_key_missing
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    comparison['id'],
                    key,
                    json.dumps(diff['js']),
                    json.dumps(diff['swift']),
                    diff.get('jsKeyMissing', False),
                    diff.get('nativeKeyMissing', False)
                ))

        # Insert exceptions if present
        if comparison.get('jsException'):
            self.save_exception(cursor, comparison['id'], 'js', comparison['jsException'])
        if comparison.get('swiftException'):
            self.save_exception(cursor, comparison['id'], 'swift', comparison['swiftException'])
        if comparison.get('comparisonError'):
            self.save_exception(cursor, comparison['id'], 'comparison', comparison['comparisonError'])

    def save_exception(self, cursor, comparison_id, exception_type, exception):
        """Save an exception record."""
        cursor.execute("""
            INSERT OR REPLACE INTO exceptions (
                comparison_id, exception_type, message, stack_trace, error_type
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            comparison_id,
            exception_type,
            exception['message'],
            exception.get('stackTrace'),
            exception.get('errorType')
        ))

    def process_all_files(self, directory: str):
        """Process all JSON files in the given directory."""
        base_dir = Path(directory)
        if not base_dir.exists():
            print(f"Directory not found: {directory}")
            return

        print(f"Processing files from: {directory}")
        json_files = list(base_dir.rglob("*.json"))
        print(f"Found {len(json_files)} JSON files")

        for file_path in json_files:
            try:
                print(f"Processing: {file_path}")
                self.process_file(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                import traceback
                print(traceback.format_exc())


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <database_name> <files_directory>")
        print("Example: python script.py comparisons.db downloaded_files")
        sys.exit(1)

    database_name = sys.argv[1]
    if not database_name.endswith('.db'):
        database_name += '.db'

    files_directory = sys.argv[2]

    processor = DatabaseCreator(database_name)
    processor.process_all_files(files_directory)


if __name__ == "__main__":
    main()
