#!/bin/bash
# Verification script for Cloud Run Job setup

set -e

PROJECT_ID=$(gcloud config get-value project)
echo "🔍 Verifying TLDR Podcast Cloud Setup"
echo "Project: ${PROJECT_ID}"
echo ""

# Check 1: Cloud Run Job exists
echo "1. Checking Cloud Run Job..."
if gcloud run jobs describe tldr-podcast --region us-central1 &>/dev/null; then
    echo "   ✅ Job 'tldr-podcast' exists"
else
    echo "   ❌ Job 'tldr-podcast' not found"
    exit 1
fi

# Check 2: Environment variables configured
echo "2. Checking environment variables..."
ENV_COUNT=$(gcloud run jobs describe tldr-podcast --region us-central1 --format="value(spec.template.spec.containers[0].env)" 2>/dev/null | grep -c "name:" || echo "0")
if [ "$ENV_COUNT" -gt 5 ]; then
    echo "   ✅ Environment variables configured ($ENV_COUNT vars)"
else
    echo "   ⚠️  Only $ENV_COUNT environment variables found (should have ~10)"
    echo "   → Go to https://console.cloud.google.com/run/jobs"
    echo "   → Click tldr-podcast → Edit → Set EMAIL_*, PODCAST_*, GCS_* vars"
fi

# Check 3: Secret exists
echo "3. Checking GCS credentials secret..."
if gcloud secrets describe gcs-credentials &>/dev/null; then
    echo "   ✅ Secret 'gcs-credentials' exists"
    
    # Check if secret is referenced in job
    if gcloud run jobs describe tldr-podcast --region us-central1 --format=yaml 2>/dev/null | grep -q "gcs-credentials"; then
        echo "   ✅ Secret referenced in job"
    else
        echo "   ⚠️  Secret exists but not referenced in job"
        echo "   → Add secret reference in Cloud Console: Variables & Secrets tab"
    fi
else
    echo "   ❌ Secret 'gcs-credentials' not found"
fi

# Check 4: Cloud Scheduler
echo "4. Checking Cloud Scheduler..."
if gcloud scheduler jobs describe tldr-podcast-daily --location us-central1 &>/dev/null; then
    echo "   ✅ Scheduler job 'tldr-podcast-daily' exists"
    SCHEDULE=$(gcloud scheduler jobs describe tldr-podcast-daily --location us-central1 --format="value(schedule)")
    TZ=$(gcloud scheduler jobs describe tldr-podcast-daily --location us-central1 --format="value(timeZone)")
    echo "   📅 Schedule: $SCHEDULE ($TZ)"
else
    echo "   ⚠️  Scheduler job not configured yet"
    echo "   → Run the commands in step 5 of docs/CLOUD_QUICKSTART.md"
fi

# Check 5: Service account for scheduler
echo "5. Checking scheduler service account..."
SA_EMAIL="cloud-scheduler-tldr@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    echo "   ✅ Service account exists: $SA_EMAIL"
else
    echo "   ⚠️  Service account not created yet"
fi

echo ""
echo "📊 Summary:"
echo "   - Cloud Run Job: Deployed"
echo "   - Next steps: Check warnings above (⚠️) and follow the instructions"
echo ""
echo "🧪 Test your setup:"
echo "   gcloud run jobs execute tldr-podcast --region us-central1"
