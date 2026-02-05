# Cloud Deployment Guide

Deploy your TLDR Podcast to Google Cloud Run with automated daily execution.

## Prerequisites

- Google Cloud account
- `gcloud` CLI installed ([install guide](https://cloud.google.com/sdk/docs/install))
- Existing GCS bucket and credentials (from v1.0 setup)

## Quick Start (5 minutes)

### 1. Enable Required APIs

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Store Credentials in Secret Manager

Instead of a JSON file, store your service account key:

```bash
# Upload your credentials
gcloud secrets create gcs-credentials \
  --data-file=credentials/project-*.json

# Grant Cloud Run access to the secret
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding gcs-credentials \
  --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy to Cloud Run

```bash
./deploy.sh
```

This will:
- Build a Docker container
- Push to Google Container Registry
- Deploy to Cloud Run

### 4. Configure Environment Variables

After deployment, go to [Cloud Run Console](https://console.cloud.google.com/run):

1. Click your service → **Edit & Deploy New Revision**
2. Go to **Variables & Secrets** tab
3. Update these environment variables:

```
EMAIL_USERNAME=your@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_SUBJECT_FILTER=TLDR AI
EMAIL_FOLDER=AI Newsletters
GCS_BUCKET_NAME=your-bucket-name
PODCAST_TITLE=Your Podcast Name
PODCAST_DESCRIPTION=Your description
PODCAST_AUTHOR=Your Name
PODCAST_EMAIL=your@email.com
```

4. Add the secret reference:
   - Click **Reference a Secret**
   - Select `gcs-credentials`
   - Expose as environment variable: `GCS_CREDENTIALS_JSON`

### 5. Update Code to Use Secret Manager

Add to [src/config/__init__.py](src/config/__init__.py):

```python
import json
import tempfile

# ... existing code ...

# In Cloud Run, credentials come from Secret Manager as env var
if os.getenv('GCS_CREDENTIALS_JSON'):
    # Write to temp file for google-cloud-storage library
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(os.getenv('GCS_CREDENTIALS_JSON'))
        GCS_CREDENTIALS_FILE = f.name
else:
    # Local development: use file
    GCS_CREDENTIALS_FILE = os.getenv('GCS_CREDENTIALS_FILE')
```

### 6. Set Up Daily Automation

Create a Cloud Scheduler job to run at 6:45 AM Pacific:

```bash
# Get your Cloud Run URL
SERVICE_URL=$(gcloud run services describe tldr-podcast \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

# Create service account for scheduler
gcloud iam service-accounts create cloud-scheduler-tldr \
  --display-name "TLDR Podcast Scheduler"

PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="cloud-scheduler-tldr@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permission to invoke Cloud Run
gcloud run services add-iam-policy-binding tldr-podcast \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --region us-central1

# Create the scheduler job
gcloud scheduler jobs create http tldr-podcast-daily \
  --location us-central1 \
  --schedule "45 6 * * *" \
  --time-zone "America/Los_Angeles" \
  --uri "${SERVICE_URL}" \
  --http-method POST \
  --oidc-service-account-email "${SA_EMAIL}"
```

### 7. Test It

Manually trigger the job:

```bash
gcloud scheduler jobs run tldr-podcast-daily --location us-central1
```

Check logs:

```bash
gcloud run logs read tldr-podcast --region us-central1 --limit 50
```

## Cost Estimate

- Cloud Run: ~$0.10/month (1 execution/day, 2min runtime)
- Cloud Scheduler: $0.10/month (1 job)
- Cloud Build: Free tier covers builds
- **Total: ~$0.20/month**

## Troubleshooting

**"Permission denied" errors:**
- Ensure service account has Secret Manager access
- Check IAM permissions on your GCS bucket

**Container fails to start:**
```bash
# Check build logs
gcloud builds list --limit 5

# Check runtime logs
gcloud run logs read tldr-podcast --region us-central1
```

**Scheduler not triggering:**
```bash
# Verify job exists
gcloud scheduler jobs list --location us-central1

# Check execution history
gcloud scheduler jobs describe tldr-podcast-daily --location us-central1
```

## Rollback to Local

Your v1.0 local setup is unchanged. Just run:

```bash
python main.py
```

## Next Steps

Once stable:
1. Disable local launchd automation (if running)
2. Monitor costs in GCP Console
3. Set up budget alerts
