# Cloud Deployment - Quick Reference

## Initial Setup (One-time)

1. **Enable APIs** (2 min):
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com
```

2. **Store Credentials** (1 min):
```bash
gcloud secrets create gcs-credentials --data-file=credentials/project-*.json
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding gcs-credentials \
  --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

3. **Deploy** (3 min):
```bash
./deploy.sh
```

4. **Configure Secrets in Console**:
   - Open https://console.cloud.google.com/run/jobs
   - Click `tldr-podcast` → **Edit**
   - Go to **Variables & Secrets** section:
     - Add all EMAIL_*, PODCAST_*, GCS_BUCKET_NAME vars
     - Reference Secret: `gcs-credentials` → env var `GCS_CREDENTIALS_JSON`

5. **Set Up Scheduler** (2 min):
```bash
# Create service account for scheduler
gcloud iam service-accounts create cloud-scheduler-tldr --display-name "TLDR Podcast Scheduler"
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="cloud-scheduler-tldr@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permission to invoke Cloud Run Job
gcloud run jobs add-iam-policy-binding tldr-podcast \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --region us-central1

# Create the scheduler job (triggers daily at 6:45 AM Pacific)
gcloud scheduler jobs create http tldr-podcast-daily \
  --location us-central1 \
  --schedule "45 6 * * *" \
  --time-zone "America/Los_Angeles" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/tldr-podcast:run" \
  --http-method POST \
  --oauth-service-account-email "${SA_EMAIL}"
```

## Daily Operations

**View logs**:
```bash
gcloud run jobs executions list --job tldr-podcast --region us-central1 --limit 5
# Get logs for specific execution
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=tldr-podcast" --limit 50 --format=text
```

**Manual trigger**:
```bash
gcloud run jobs execute tldr-podcast --region us-central1
```

**Scheduler trigger test**:
```bash
gcloud scheduler jobs run tldr-podcast-daily --location us-central1
```

**Update code**:
```bash
./deploy.sh  # Builds and deploys automatically
```

## Rollback

Stop cloud automation:
```bash
gcloud scheduler jobs delete tldr-podcast-daily --location us-central1
```

Your local v1.0 still works unchanged:
```bash
python main.py
```

## Cost: ~$0.20/month
