param (
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    [Parameter(Mandatory=$true)]
    [string]$RecipientEmail,
    [string]$Region = "us-east4",
    [string]$ApigeeEnv = "eval",
    [string]$ApigeeHost = "investment-agent.example.com"
)

$ErrorActionPreference = "Stop"

# Cleanup local artifacts to prevent upload bloat
if (Test-Path test_zip) { Remove-Item -Recurse -Force test_zip }

Write-Host "🚀 STARTING END-TO-END DEPLOYMENT: $ProjectId ($Region)" -ForegroundColor Blue

# 1. Enable Core APIs (Pre-requisite for Build & Terraform)
Write-Host "`n[1/3] Enabling Google Cloud APIs..." -ForegroundColor Yellow
gcloud services enable `
    cloudscheduler.googleapis.com `
    cloudfunctions.googleapis.com `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    artifactregistry.googleapis.com `
    vpcaccess.googleapis.com `
    secretmanager.googleapis.com `
    firestore.googleapis.com `
    aiplatform.googleapis.com `
    compute.googleapis.com `
    --project $ProjectId
if ($LASTEXITCODE -ne 0) { throw "API Enablement failed" }
Start-Sleep -Seconds 60 # Wait for API propagation

# Set the active project for gcloud (needed for subsequent scripts)
gcloud config set project $ProjectId

# 2. Container Build (Remote via Cloud Build)
Write-Host "`n[2/3] Building Dashboard Container via Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/${ProjectId}/dashboard:latest" . --project $ProjectId
if ($LASTEXITCODE -ne 0) { throw "Cloud Build failed" }
Start-Sleep -Seconds 60 # Wait for Registry propagation

# 3. Provision Infrastructure
Write-Host "`n[3/3] Provisioning Infrastructure with Terraform..." -ForegroundColor Yellow
$DeployId = Get-Date -Format "yyyyMMddHHmmss"
Set-Location terraform
terraform init
terraform apply -auto-approve `
    -var="project_id=$ProjectId" `
    -var="region=$Region" `
    -var="recipient_email=$RecipientEmail" `
    -var="allowed_user_email=$RecipientEmail" `
    -var="apigee_host=$ApigeeHost"
if ($LASTEXITCODE -ne 0) { throw "Terraform Apply failed" }

# 4. Deploy Apigee Proxy (Smart Bundling)
Write-Host "`n[4/4] Deploying Apigee Proxy..." -ForegroundColor Yellow
Set-Location ..
.\scripts\bundle_apigee.ps1 -Environment $ApigeeEnv
if ($LASTEXITCODE -ne 0) { throw "Apigee Deployment failed" }

Write-Host "`n✅ DEPLOYMENT SUCCESSFUL! ✅" -ForegroundColor Green
Write-Host "Next Steps:"
Write-Host "  1. Add secret versions in GCP Console: https://console.cloud.google.com/security/secret-manager"
Write-Host "  2. Test Nudge: gcloud functions call trigger-nudge --region $Region"
