# Email to Podcast

Automatically convert email digests into podcast episodes using Python, Google Cloud TTS, and Google Cloud Storage.

## Architecture

1. **Ingest**: IMAP fetch
2. **Process**: HTML parsing + clean text
3. **Synthesize**: Google Cloud TTS
4. **Host**: Upload MP3 to GCS
5. **Publish**: Generate RSS feed
6. **Listen**: Subscribe in any podcast app

## Project Structure

```
.
├── src/
│   ├── config/
│   │   ├── __init__.py      # Env config
│   │   └── settings.py      # Typed settings
│   ├── core/
│   │   ├── models.py        # Episode/Digest models
│   │   └── pipeline.py      # Orchestration
│   ├── services/
│   │   ├── ingest_service.py
│   │   ├── tts_service.py
│   │   ├── rss_service.py
│   │   └── storage_service.py
│   ├── email_ingest.py      # IMAP fetch
│   ├── text_processor.py    # Text parsing/cleanup
│   ├── tts.py               # Google Cloud TTS
│   ├── gcs_upload.py        # GCS uploader
│   └── rss_feed.py          # RSS generator
├── data/
│   ├── output/              # MP3/feed/processed text
│   ├── episodes.json        # Episode store
│   └── feedback/            # Feedback files
├── assets/
│   └── audio/               # Music/chimes
├── credentials/             # GCS credentials
├── docs/                    # Docs
├── scripts/                 # Utilities
├── tests/                   # Unit tests
├── main.py                  # Entrypoint
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

### 1. Install System Dependencies

**ffmpeg** is required for audio processing:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

### 2. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- **Email**: Gmail address and app-specific password
- **Google Cloud TTS (Vertex AI voices)**: Voice name and language code (credentials via `GCS_CREDENTIALS_FILE`)
- **Google Cloud Storage**: Project ID, bucket name, and credentials file
- **Podcast**: Metadata (title, description, author)

### 4. Gmail App Password

For Gmail, you'll need an app-specific password:
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate a new app password for "Mail"
4. Use this password in your `.env` file

### 5. Google Cloud Storage Setup

See [docs/SETUP_GCS.md](docs/SETUP_GCS.md) for detailed setup instructions.

Quick summary:
1. Create a Google Cloud project
2. Create a GCS bucket
3. Make bucket publicly accessible
4. Create a service account and download JSON credentials
5. Update your `.env` file

## Usage

Run the pipeline:

```bash
python main.py
```

## Automation (macOS)

To run automatically every day at **6:45 AM Pacific**, use `launchd`.

This project uses a `launchd` agent that runs every minute, but the wrapper script only executes the pipeline when it is **06:45 in `America/Los_Angeles`**. This keeps the schedule pinned to Pacific time even if you travel to other time zones.

2) Install the LaunchAgent:

```bash
mkdir -p ~/Library/LaunchAgents
cp "scripts/launchd/com.tldrpodcast.daily.plist" ~/Library/LaunchAgents/
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.tldrpodcast.daily.plist
launchctl enable "gui/$(id -u)/com.tldrpodcast.daily"
```

3) Verify it’s loaded:

```bash
launchctl print "gui/$(id -u)/com.tldrpodcast.daily" | head
```

Logs are written to `data/logs/`.

To change the pinned timezone or time, edit `scripts/run_daily_pipeline.sh` (variables `TARGET_TZ` and `TARGET_TIME`).

To uninstall:

```bash
launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/com.tldrpodcast.daily.plist
rm ~/Library/LaunchAgents/com.tldrpodcast.daily.plist
```

Run tests:

```bash
python -m unittest discover -s tests
```

The script will:
1. Fetch the latest email matching your subject filter
2. Clean and process the text
3. Generate an MP3 file using Google Cloud TTS
4. Upload the audio to Google Cloud Storage
5. Generate/update the RSS feed
6. Upload the feed to Google Cloud Storage

Subscribe to the feed URL in your podcast app!

## CI

GitHub Actions runs tests on push and pull requests (see .github/workflows/tests.yml).

## License

MIT
