from datetime import datetime, timedelta
import uuid
from google.cloud import storage
from flask import Blueprint, request, jsonify, abort


BUCKET_NAME = "trio-oref-logs-gcs"

sign_url_api = Blueprint('sign_url_api', __name__)

@sign_url_api.route('/v1/signed-url', methods=['POST'])
def get_signed_url():
    # Get request data
    data = request.get_json()
    if not data:
        abort(400, "Missing request body")
        
    # Extract required fields
    project = data.get('project')
    device_id = data.get('deviceId')
    app_version = data.get('appVersion')
    function = data.get('function')
    created_at = data.get('createdAt')
    
    # Validate required fields
    if not all([project, device_id, app_version, function, created_at]):
        abort(400, "Missing required fields")
        
    # Validate function name
    valid_functions = {"determineBasal", "autosense", "makeProfile", "meal", "iob"}
    if function not in valid_functions:
        abort(400, "Invalid function name")

    # Validate project
    valid_projects = {"trio-oref-validation"}
    if project not in valid_projects:
        abort(400, "Invalid project")
        
    # Convert timestamp to UTC date for path
    date = datetime.utcfromtimestamp(created_at).strftime("%Y-%m-%d")
    
    # Generate batch ID
    batch_id = str(uuid.uuid4())
    
    # Construct GCS path with project as a component
    path = f"{project}/algorithm-comparisons/{date}/{app_version}/{function}/{device_id}/{batch_id}.json"
    
    # Generate signed URL
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(path)
    
    expires_at = datetime.now() + timedelta(minutes=15)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type="application/json",
    )
    
    return jsonify({
        "url": url,
        "expiresAt": expires_at.timestamp()
    })
