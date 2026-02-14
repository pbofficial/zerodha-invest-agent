# Package Apigee Proxy
# Resolve Project Root (one level up from scripts folder)
$ProjectRoot = Resolve-Path "$PSScriptRoot/.."
$ProxyName = "investment-agent-mcp"
$SourcePath = "$ProjectRoot/apigee/proxies/$ProxyName/apiproxy"
$ZipPath = "$ProjectRoot/apigee/proxies/$ProxyName.zip"

# Zip the apiproxy folder using Python to ensure forward slashes
python "$PSScriptRoot/zip_proxy.py"
if ($LASTEXITCODE -ne 0) { throw "Bundling failed" }
Write-Host "✅ Proxy bundled successfully: $ZipPath"

Write-Host "`n🚀 Deploying to Apigee..." -ForegroundColor Cyan
$Org = "pb-ai-focus"
$Env = "eval"
$Token = gcloud auth print-access-token

# 1. Upload Proxy Bundle
Write-Host "Uploading bundle..."
$UploadUrl = "https://apigee.googleapis.com/v1/organizations/$Org/apis?action=import&name=investment-agent-mcp"
# Use curl.exe for a reliable multipart/form-data upload
$ResponseJson = & curl.exe -X POST $UploadUrl `
    -H "Authorization: Bearer $Token" `
    -F "file=@$ZipPath" `
    -s
$Response = $ResponseJson | ConvertFrom-Json
$Revision = $Response.revision
if (-not $Revision) { throw "Upload failed: $ResponseJson" }
Write-Host "✅ Uploaded Revision: $Revision"

# 2. Deploy to Environment
Write-Host "Deploying Revision $Revision to $Env..."
$DeployBody = @{
    serviceAccount = "zerodha-agent-sa@$Org.iam.gserviceaccount.com"
} | ConvertTo-Json

$DeployUrl = "https://apigee.googleapis.com/v1/organizations/$Org/environments/$Env/apis/investment-agent-mcp/revisions/$Revision/deployments?override=true"
try {
    Invoke-RestMethod -Uri $DeployUrl -Method Post -Headers @{Authorization="Bearer $Token"; "Content-Type"="application/json"} -Body $DeployBody
    Write-Host "`n✅ Successfully deployed to eval environment!" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    if ($_.Exception.Response) {
        $streamReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $ErrorDetails = $streamReader.ReadToEnd()
        Write-Host "Details: $ErrorDetails" -ForegroundColor Red
    } else {
        Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`n✨ END-TO-END APIGEE SETUP COMPLETE ✨" -ForegroundColor Green
