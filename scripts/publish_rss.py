import os
import glob
from datetime import datetime, timezone

from src.config import Config
from src.config.settings import Settings
from src.rss_feed import create_or_update_rss_feed
from src.gcs_upload import upload_to_gcs

def publish_rss():
    print("Generating RSS feed from existing audio files...")
    
    settings = Settings.load()

    # Find all mp3s in output
    mp3_files = glob.glob(os.path.join(settings.output_dir, "digest_*.mp3"))
    episodes = []
    
    for mp3_path in mp3_files:
        filename = os.path.basename(mp3_path)
        # format: digest_YYYYMMDD_HHMMSS.mp3
        try:
            date_str = filename.split('_')[1]
            time_str = filename.split('_')[2].split('.')[0]
            dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            # Make it timezone aware (UTC)
            dt = dt.replace(tzinfo=timezone.utc)
            
            # Formulate URL
            audio_url = f"https://storage.googleapis.com/{Config.GCS_BUCKET_NAME}/episodes/{filename}"
            
            # Get file size
            file_size = os.path.getsize(mp3_path)
            
            episodes.append({
                'title': f"Daily Digest - {dt.strftime('%B %d, %Y')}",
                'audio_url': audio_url,
                'description': f"TLDR AI Digest for {dt.strftime('%B %d, %Y')}.",
                'pub_date': dt,
                'file_size': file_size,
                'link': Config.RSS_FEED_URL
            })
            print(f"Added episode: {filename}")
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            
    # Sort episodes by date (newest first)
    episodes.sort(key=lambda x: x['pub_date'], reverse=True)
    
    # Generate Feed
    create_or_update_rss_feed(episodes, settings.feed_file)
    print(f"RSS feed file generated at {settings.feed_file}")
    
    # Upload Feed
    print("Uploading feed.xml to GCS...")
    feed_url = upload_to_gcs(settings.feed_file, 'feed.xml', content_type='application/rss+xml')
    print(f"Success! Feed is live at: {feed_url}")

if __name__ == "__main__":
    publish_rss()