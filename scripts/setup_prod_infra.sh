#!/bin/bash
set -e

PROJECT_ID="conthunt-prod"
REGION="us-central1"
DB_INSTANCE_NAME="conthunt-prod"
DB_PASSWORD=$(openssl rand -base64 20)

echo "Setting up infrastructure for Project: $PROJECT_ID in $REGION..."

# 1. Enable APIs
echo "Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    compute.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    --project "$PROJECT_ID"

# 2. Storage Buckets
echo "Creating GCS Buckets..."
gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$PROJECT_ID-media" || echo "Bucket media already exists"
gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$PROJECT_ID-raw" || echo "Bucket raw already exists"

# Cors for media bucket (Allow GET from everywhere for now, or restrict to domain)
echo '[{"origin": ["*"],"method": ["GET", "HEAD", "PUT", "POST"],"responseHeader": ["Content-Type"],"maxAgeSeconds": 3600}]' > cors.json
gsutil cors set cors.json "gs://$PROJECT_ID-media"
rm cors.json

# 3. Artifact Registry
echo "Creating Artifact Registries..."
gcloud artifacts repositories create conthunt-backend \
    --repository-format=docker \
    --location="$REGION" \
    --description="Backend Docker repository" \
    --project="$PROJECT_ID" || echo "Repo conthunt-backend already exists"

gcloud artifacts repositories create conthunt-frontend \
    --repository-format=docker \
    --location="$REGION" \
    --description="Frontend Docker repository" \
    --project="$PROJECT_ID" || echo "Repo conthunt-frontend already exists"

# 4. Cloud SQL
echo "Creating Cloud SQL Instance (This takes 5-10 minutes)..."
gcloud sql instances create "$DB_INSTANCE_NAME" \
    --database-version=POSTGRES_17 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --storage-type=SSD \
    --storage-size=10 \
    --root-password="$DB_PASSWORD" || echo "Instance $DB_INSTANCE_NAME already exists (or failed)"

echo "Creating Database 'conthunt'..."
gcloud sql databases create conthunt --instance="$DB_INSTANCE_NAME" --project="$PROJECT_ID" || echo "Database conthunt already exists"

echo "=================================================="
echo "Setup Complete!"
echo "Cloud SQL Root Password: $DB_PASSWORD"
echo "SAVE THIS PASSWORD NOW!"
echo "=================================================="
