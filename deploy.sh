#!/bin/bash
set -euo pipefail

# Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="${2:-us-central1}"
SERVICE_NAME="tldr-podcast"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying TLDR Podcast to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Build and push container
echo "📦 Building container..."
gcloud builds submit --tag "${IMAGE_NAME}" --project "${PROJECT_ID}"

# Deploy to Cloud Run Jobs (batch workload, not a web service)
echo "☁️  Deploying to Cloud Run Jobs..."
gcloud run jobs deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --memory 1Gi \
  --task-timeout 10m \
  --max-retries 0 \
  --set-env-vars "EMAIL_USERNAME=__SECRET__" \
  --set-env-vars "EMAIL_PASSWORD=__SECRET__" \
  --set-env-vars "EMAIL_SUBJECT_FILTER=__SECRET__" \
  --set-env-vars "EMAIL_FOLDER=inbox" \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-env-vars "GCS_BUCKET_NAME=__SECRET__" \
  --set-env-vars "PODCAST_TITLE=__SECRET__" \
  --set-env-vars "PODCAST_DESCRIPTION=__SECRET__" \
  --set-env-vars "PODCAST_AUTHOR=__SECRET__" \
  --set-env-vars "PODCAST_EMAIL=__SECRET__"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "⚠️  IMPORTANT: You need to set secrets manually:"
echo "   Go to Cloud Run Jobs console: https://console.cloud.google.com/run/jobs"
echo "   Click ${SERVICE_NAME} → Edit → Variables & Secrets"
echo "   Update environment variables marked as __SECRET__"
echo ""
echo "📅 Next: Set up Cloud Scheduler to trigger the job daily:"
echo "   See docs/CLOUD_QUICKSTART.md for scheduler setup commands"
