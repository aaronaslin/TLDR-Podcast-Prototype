#!/usr/bin/env python3
"""
Utility script to upload podcast artwork to Google Cloud Storage.
"""
import sys
import os
from src.config import Config
from src.gcs_upload import upload_to_gcs

def upload_artwork(image_path):
    """
    Uploads the podcast cover art to GCS and prints the URL.
    
    Args:
        image_path (str): Path to the local image file.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    print(f"Uploading {image_path} to GCS bucket {Config.GCS_BUCKET_NAME}...")
    
    # Extract filename from path
    filename = os.path.basename(image_path)
    
    # Upload to GCS
    # We upload to the root of the bucket or a specific 'images' folder if you prefer
    # Based on feed.xml, it seems it expects it at the root or matching the PODCAST_IMAGE_URL path
    # If PODCAST_IMAGE_URL is set, we can try to match that path, but for now let's just upload to root
    # or use the filename provided.
    
    url = upload_to_gcs(image_path, filename, content_type='image/png')
    
    if url:
        print("\nSUCCESS! Image uploaded.")
        print(f"Public URL: {url}")
        print("\nMake sure this URL matches the PODCAST_IMAGE_URL in your .env file!")
    else:
        print("\nFailed to upload image.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_artwork.py <path_to_image_file>")
        print("Example: python upload_artwork.py my_cover_art.png")
        sys.exit(1)
        
    upload_artwork(sys.argv[1])
