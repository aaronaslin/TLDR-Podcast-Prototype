"""
Google Cloud Storage upload module for hosting audio files and RSS feed.
"""
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from src.config import Config


def upload_to_gcs(local_file_path, gcs_key, content_type='audio/mpeg', make_public=True):
    """
    Upload a file to Google Cloud Storage bucket.
    
    Args:
        local_file_path (str): Local path to the file to upload
        gcs_key (str): GCS object key (path in bucket)
        content_type (str): MIME type of the file
        
    Returns:
        str: Public URL of the uploaded file or None on failure
    """
    try:
        # Initialize GCS client
        storage_client = storage.Client.from_service_account_json(
            Config.GCS_CREDENTIALS_FILE,
            project=Config.GCP_PROJECT_ID
        )
        
        # Get bucket
        bucket = storage_client.bucket(Config.GCS_BUCKET_NAME)
        
        # Create blob (file object)
        blob = bucket.blob(gcs_key)
        
        # Upload file (5 min timeout for large audio files on slow connections)
        blob.upload_from_filename(
            local_file_path,
            content_type=content_type,
            timeout=300
        )
        
        # Make publicly accessible.
        # Note: with Uniform Bucket-Level Access (UBLA) enabled, object ACLs are disabled and
        # blob.make_public() will fail even though the upload succeeded. In that case, rely on
        # bucket-level IAM to provide public access.
        if make_public:
            try:
                blob.make_public()
            except GoogleCloudError as e:
                message = str(e)
                if "uniform bucket-level access" in message.lower() or "legacy acl" in message.lower():
                    print("Warning: bucket has Uniform Bucket-Level Access enabled; skipping object ACL publicization.")
                else:
                    raise
        
        # Generate public URL
        url = f"https://storage.googleapis.com/{Config.GCS_BUCKET_NAME}/{gcs_key}"
        return url
        
    except GoogleCloudError as e:
        print(f"Error uploading to GCS: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


# TODO: Add error handling and retry logic
# TODO: Add progress callback for large files
# TODO: Add support for resumable uploads
