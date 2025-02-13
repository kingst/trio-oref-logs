import json
import os
from datetime import datetime
from google.cloud import storage
from pathlib import Path


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-auth.json'

class LocalDownloader:
    def __init__(self, bucket_name: str = "trio-oref-logs-gcs"):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.tracking_file = 'downloaded_files/incremental_download.json'
        self.output_dir = Path('downloaded_files')
        self.output_dir.mkdir(exist_ok=True)
        self.load_tracking_data()

    def load_tracking_data(self):
        """Load or initialize the tracking data."""
        if os.path.exists(self.tracking_file):
            with open(self.tracking_file, 'r') as f:
                self.processed_files = json.load(f)
        else:
            self.processed_files = {}

    def save_tracking_data(self):
        """Save the tracking data."""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.processed_files, f, indent=4)

    def should_process_file(self, blob) -> bool:
        """Check if we should process this file based on its last update time."""
        if blob.name not in self.processed_files:
            return True
        return blob.updated.isoformat() > self.processed_files[blob.name]

    def download_incrementally(self, prefix: str = "trio-oref-validation/algorithm-comparisons/"):
        """Download only new or updated files."""
        print(f"Starting incremental download from bucket: {self.bucket_name}")
        print(f"Using prefix: {prefix}")
        
        # List all blobs in the bucket with the given prefix
        blobs = list(self.bucket.list_blobs(prefix=prefix))
        print(f"Found {len(blobs)} total files")
        
        # Filter for files that need processing
        blobs_to_process = [blob for blob in blobs if self.should_process_file(blob)]
        print(f"Found {len(blobs_to_process)} files that need processing")
        
        processed_count = 0
        for blob in blobs_to_process:
            try:
                # Create directory structure matching the GCS path
                local_path = self.output_dir / blob.name
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download the file
                blob.download_to_filename(local_path)
                
                # Update tracking data
                self.processed_files[blob.name] = blob.updated.isoformat()
                self.save_tracking_data()
                
                processed_count += 1
                print(f"Downloaded: {blob.name}")
                
            except Exception as e:
                print(f"Error processing {blob.name}: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        print(f"\nIncremental download complete. Downloaded {processed_count} files.")


def main():
    downloader = LocalDownloader()
    downloader.download_incrementally()


if __name__ == "__main__":
    main()
