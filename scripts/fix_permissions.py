from google.cloud import storage
from src.config import Config

def make_blob_public(bucket_name, blob_name):
    """Makes a blob public."""
    print(f"Attempting to make {blob_name} in {bucket_name} public...")
    try:
        storage_client = storage.Client.from_service_account_json(
            Config.GCS_CREDENTIALS_FILE,
            project=Config.GCP_PROJECT_ID
        )
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Check if exists
        if not blob.exists():
            print(f"Error: Blob {blob_name} does not exist.")
            return

        blob.make_public()
        print(f"Success! {blob.public_url} is now public.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    make_blob_public(Config.GCS_BUCKET_NAME, "TLDR_AI_Podcast_Image.png")