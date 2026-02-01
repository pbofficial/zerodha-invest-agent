#!/bin/bash
set -e

# Check if required parameters are passed
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: ./deploy.sh <PROJECT_ID> <RECIPIENT_EMAIL> [REGION]"
  echo "Default REGION is us-east4"
  exit 1
fi

PROJECT_ID=$1
RECIPIENT_EMAIL=$2
REGION=${3:-us-east4}

echo "🚀 STARTING END-TO-END DEPLOYMENT: $PROJECT_ID ($REGION)"

# 1. Enable Core APIs
echo -e "\n[1/3] Enabling Google Cloud APIs..."
gcloud services enable \
    cloudscheduler.googleapis.com \
    cloudfunctions.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    compute.googleapis.com \
    --project "$PROJECT_ID"

sleep 60 # Wait for API propagation

# 2. Container Build
echo -e "\n[2/3] Building Dashboard Container via Cloud Build..."
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/dashboard:latest" . --project "$PROJECT_ID"

sleep 60 # Wait for Registry propagation

# 3. Provision Infrastructure
echo -e "\n[3/3] Provisioning Infrastructure with Terraform..."
DEPLOY_ID=$(date +%Y%m%d%H%M%S)
cd terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="deploy_id=$DEPLOY_ID" -var="recipient_email=$RECIPIENT_EMAIL" -var="allowed_user_email=$RECIPIENT_EMAIL" -auto-approve

echo -e "\n✅ DEPLOYMENT SUCCESSFUL! ✅"
echo "Next Steps:"
echo "  1. Add secret versions in GCP Console: https://console.cloud.google.com/security/secret-manager"
echo "  2. Test Nudge: gcloud functions call trigger-nudge --region $REGION"
