"""Configuration loader for Email-to-Podcast application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
	"""Application configuration from environment variables."""
    
	# Email settings
	EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
	EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
	EMAIL_SUBJECT_FILTER = os.getenv('EMAIL_SUBJECT_FILTER', 'Daily Digest')
	EMAIL_FOLDER = os.getenv('EMAIL_FOLDER', 'inbox')
	EMAIL_SEARCH_BY = os.getenv('EMAIL_SEARCH_BY', 'subject')
	IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    
	# Google Cloud TTS (Vertex AI Voice) settings
	GOOGLE_TTS_VOICE_NAME = os.getenv('GOOGLE_TTS_VOICE_NAME', 'en-US-Neural2-D')
	GOOGLE_TTS_LANGUAGE_CODE = os.getenv('GOOGLE_TTS_LANGUAGE_CODE', 'en-US')
	GOOGLE_TTS_SPEAKING_RATE = float(os.getenv('GOOGLE_TTS_SPEAKING_RATE', '1.0'))
	GOOGLE_TTS_PITCH = float(os.getenv('GOOGLE_TTS_PITCH', '0.0'))
    
	# Intro music settings (optional)
	INTRO_MUSIC_FILE = os.getenv('INTRO_MUSIC_FILE')  # Path to intro music file
	INTRO_MUSIC_LEAD_IN = int(os.getenv('INTRO_MUSIC_LEAD_IN', '2'))  # Seconds of music-only intro
	INTRO_MUSIC_VOLUME = float(os.getenv('INTRO_MUSIC_VOLUME', '0.5'))  # 0.0 to 1.0
    
	# Audio ducking settings
	ENABLE_DUCKING = os.getenv('ENABLE_DUCKING', 'true').lower() == 'true'
	DUCKED_VOLUME = float(os.getenv('DUCKED_VOLUME', '0.25'))  # Volume when voice is playing (0.0 to 1.0)
    
	# Outro music settings (optional)
	OUTRO_MUSIC_FILE = os.getenv('OUTRO_MUSIC_FILE')  # Path to outro music file
	OUTRO_MUSIC_DURATION = int(os.getenv('OUTRO_MUSIC_DURATION', '5'))  # Seconds
	OUTRO_MUSIC_VOLUME = float(os.getenv('OUTRO_MUSIC_VOLUME', '0.7'))  # 0.0 to 1.0
    
	# Section chime settings (optional)
	SECTION_CHIME_FILE = os.getenv('SECTION_CHIME_FILE')  # Path to chime sound file
	SECTION_CHIME_VOLUME = float(os.getenv('SECTION_CHIME_VOLUME', '0.6'))  # 0.0 to 1.0
    
	# Google Cloud Storage settings
	GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
	GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
	GCS_CREDENTIALS_FILE = os.getenv('GCS_CREDENTIALS_FILE')
    
	# Podcast metadata
	PODCAST_TITLE = os.getenv('PODCAST_TITLE', 'My Daily Digest Podcast')
	PODCAST_DESCRIPTION = os.getenv('PODCAST_DESCRIPTION', 'Daily digest converted to audio')
	PODCAST_AUTHOR = os.getenv('PODCAST_AUTHOR', 'Your Name')
	PODCAST_OWNER = os.getenv('PODCAST_OWNER', PODCAST_AUTHOR)  # Defaults to Author if not set
	PODCAST_EMAIL = os.getenv('PODCAST_EMAIL')
	PODCAST_IMAGE_URL = os.getenv('PODCAST_IMAGE_URL')
    
	# RSS Feed
	RSS_FEED_URL = os.getenv('RSS_FEED_URL')

	# Pipeline behavior
	# When true, re-generate and re-upload audio even if an episode with the same
	# timestamped filename already exists (overwrites the remote object).
	FORCE_REGENERATE = os.getenv('FORCE_REGENERATE', 'false').lower() == 'true'
    
	@classmethod
	def validate(cls):
		"""Validate required configuration values are set."""
		required = [
			'EMAIL_USERNAME',
			'EMAIL_PASSWORD',
			'GCP_PROJECT_ID',
			'GCS_BUCKET_NAME',
			'GCS_CREDENTIALS_FILE',
		]
        
		missing = [key for key in required if not getattr(cls, key)]
        
		if missing:
			raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
		return True
