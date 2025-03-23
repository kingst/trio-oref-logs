#!/usr/bin/env python3
from flask import Flask, jsonify, send_from_directory, Response
import os
import mimetypes

app = Flask(__name__)

# Configuration
TEST_FILES_DIR = "./errors"
PORT = 8123

@app.route('/list')
def list_files():
    """Return a JSON array of available files with their metadata"""
    try:
        files = []
        for filename in os.listdir(TEST_FILES_DIR):
            filepath = os.path.join(TEST_FILES_DIR, filename)
            if os.path.isfile(filepath):
                files.append(f"/files/{filename}")
        return jsonify(files)  # This returns a JSON array directly
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    """Serve a specific file by name"""
    try:
        return send_from_directory(TEST_FILES_DIR, filename)
    except Exception as e:
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500

@app.route('/')
def index():
    """Serve a simple help page"""
    return """
    <html>
    <head><title>Flask Test File Server</title></head>
    <body>
        <h1>Test File Server</h1>
        <p>Available endpoints:</p>
        <ul>
            <li><a href="/list">/list</a> - Get JSON array of available files</li>
            <li>/files/FILENAME - Download a specific file</li>
        </ul>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Create test files directory if it doesn't exist
    os.makedirs(TEST_FILES_DIR, exist_ok=True)
    
    print(f"Starting Flask test file server on port {PORT}...")
    print(f"Test files directory: {os.path.abspath(TEST_FILES_DIR)}")
    print(f"Server URL: http://localhost:{PORT}")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
