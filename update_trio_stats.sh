#!/bin/bash
python scripts/local-downloader.py
rm downloaded_files/tmp.db
python scripts/db-creator.py downloaded_files/tmp.db downloaded_files
python scripts/stats.py downloaded_files/tmp.db
