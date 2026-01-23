# Google Cloud Storage Setup Guide

## What is Google Cloud Storage (GCS)?

Google Cloud Storage is Google's cloud file storage service (similar to AWS S3). It's reliable, scalable, and perfect for hosting your podcast files.

**A GCS bucket** is like a folder where you store files. Each file in the bucket gets a public URL that podcast apps can access.

---

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **Select a project** (top left) → **New Project**
3. Enter a project name (e.g., "My Podcast")
4. Click **Create**
5. Wait for the project to be created, then select it
6. **Copy your Project ID** (you'll need this later)

---

### 2. Enable the Cloud Storage API

1. In the Google Cloud Console, search for "Cloud Storage API" in the top search bar
2. Click **Cloud Storage API**
3. Click **Enable**
4. Wait for it to enable (takes a few seconds)

---

### 3. Create a Storage Bucket

1. Go to **Cloud Storage** → **Buckets** (or search "Cloud Storage" in the top bar)
2. Click **Create Bucket**
3. **Name your bucket**: Choose a globally unique name (e.g., `my-podcast-tldr-ai`)
   - Must be lowercase, no spaces
   - Can use dashes and numbers
4. **Choose where to store data**: Select a region close to you (e.g., `us-east1`)
5. **Choose storage class**: Select "Standard"
6. **Access control**: Select **"Fine-grained"** (important for making files public)
7. Click **Create**

---

### 4. Make Bucket Publicly Accessible

You need to make your bucket public so podcast apps can download the audio files.

1. Click on your bucket name
2. Go to the **Permissions** tab
3. Click **Grant Access**
4. In "New principals", type: `allUsers`
5. In "Role", select: **Storage Object Viewer**
6. Click **Save**
7. Click **Allow Public Access** in the warning dialog

Now all files in your bucket will be publicly accessible!

---

### 5. Create a Service Account (for authentication)

The Python script needs credentials to upload files to your bucket.

1. Go to **IAM & Admin** → **Service Accounts** (search in top bar)
2. Click **Create Service Account**
3. **Name**: Enter something like "podcast-uploader"
4. Click **Create and Continue**
5. **Grant this service account access to project**:
   - Click the "Select a role" dropdown
   - Search for "Storage Object Admin"
   - Select **Storage Object Admin**
   - Click **Continue**
6. Click **Done**

---

### 6. Download Service Account Key (JSON file)

1. On the Service Accounts page, find your newly created service account
2. Click the **three dots** (⋮) on the right → **Manage keys**
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create**
6. A JSON file will download to your computer (e.g., `my-podcast-abc123.json`)
7. **Move this file to your project directory**:
   ```bash
   mv ~/Downloads/my-podcast-*.json /Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/gcs-credentials.json
   ```

⚠️ **Important**: Keep this file secure! Don't commit it to Git (it's already in `.gitignore`)

---

### 7. Update Your .env File

Copy your `.env.example` to `.env` (if you haven't already):

```bash
cp .env.example .env
```

Edit `.env` and update the GCS section:

```env
# Google Cloud Storage Configuration
GCP_PROJECT_ID=my-podcast-123456
GCS_BUCKET_NAME=my-podcast-tldr-ai
GCS_CREDENTIALS_FILE=/Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/gcs-credentials.json

# Podcast Metadata
PODCAST_IMAGE_URL=https://storage.googleapis.com/my-podcast-tldr-ai/podcast-cover.jpg

# RSS Feed
RSS_FEED_URL=https://storage.googleapis.com/my-podcast-tldr-ai/feed.xml
```

Replace:
- `my-podcast-123456` with your **Project ID** from step 1
- `my-podcast-tldr-ai` with your **Bucket Name** from step 3
- The path to your credentials JSON file

---

### 8. Test Your Setup

Run a quick test to verify everything works:

```bash
python3 -c "
from google.cloud import storage
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/gcs-credentials.json'
client = storage.Client()
bucket = client.bucket('my-podcast-tldr-ai')
print(f'✓ Successfully connected to bucket: {bucket.name}')
"
```

Replace `my-podcast-tldr-ai` with your bucket name.

If you see `✓ Successfully connected to bucket: ...`, you're good to go!

---

## Your Podcast URLs

After running the pipeline, your files will be available at:

- **Audio files**: `https://storage.googleapis.com/YOUR-BUCKET-NAME/episodes/digest_TIMESTAMP.mp3`
- **RSS Feed**: `https://storage.googleapis.com/YOUR-BUCKET-NAME/feed.xml`

Subscribe to the RSS feed URL in your podcast app!

---

## Cost Estimate

Google Cloud Storage pricing (as of 2026):
- **Storage**: $0.020 per GB per month (Standard class)
- **Network egress**: First 1 GB free, then $0.12 per GB (Americas)
- **Operations**: Very cheap (fractions of a cent)

**Example**: 
- 30 episodes × 10 MB each = 300 MB storage = **~$0.006/month**
- 100 downloads/month × 10 MB = 1 GB egress = **Free**

Essentially free for personal use! 🎉

---

## Troubleshooting

**Error: "Project ID not found"**
- Make sure you're using the Project ID, not the project name
- Find it in: Google Cloud Console → Dashboard → "Project info" card

**Error: "Permission denied"**
- Make sure the service account has "Storage Object Admin" role
- Check that the JSON credentials file path is correct

**Files not accessible publicly**
- Make sure you granted `allUsers` the "Storage Object Viewer" role on the bucket
- Files should be accessible at `https://storage.googleapis.com/BUCKET-NAME/FILE-PATH`

Need help? Check the [GCS documentation](https://cloud.google.com/storage/docs)
