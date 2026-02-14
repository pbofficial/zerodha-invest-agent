# Package Apigee Proxy
param (
    [string]$Environment = "eval"
)

# Resolve Project Root (one level up from scripts folder)
$ProjectRoot = Resolve-Path "$PSScriptRoot/.."
$ProxyName = "investment-agent-mcp"
$SourcePath = "$ProjectRoot/apigee/proxies/$ProxyName/apiproxy"
$ZipPath = "$ProjectRoot/apigee/proxies/$ProxyName.zip"

# Zip the apiproxy folder using Python to ensure forward slashes
# BUT FIRST: Smart Bundling - Inject Real URLs
$BuildDir = "$PSScriptRoot/../build_temp"
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null
Copy-Item -Recurse -Path "$SourcePath" -Destination "$BuildDir"

Write-Host "[INFO] Fetching Cloud Run URLs for Smart Bundling..."
function Get-RunUrl ($ServiceName) {
    try {
        $url = gcloud run services describe $ServiceName --region us-east4 --format="value(status.url)"
        if (-not $url) { throw "Could not find URL for $ServiceName" }
        return $url
    } catch {
        Write-Warning "Failed to fetch URL for $ServiceName. Using placeholder."
        return "https://PLACEHOLDER-SERVICE-URL" 
    }
}

$PortfolioUrl = Get-RunUrl "get-portfolio"
$AllocationsUrl = Get-RunUrl "calculate-allocations"
$HealthUrl = Get-RunUrl "check-financial-health"
$NewsUrl = Get-RunUrl "get-market-news"

Write-Host "[INFO] Injecting URLs into Proxy Targets..."
$TargetsDir = "$BuildDir/apiproxy/targets"

function Replace-FileContent {
    param ($Path, $Pattern, $Replacement)
    Write-Host "  -> Replacing $Pattern in $(Split-Path $Path -Leaf)"
    (Get-Content $Path) -replace $Pattern, $Replacement | Set-Content $Path
}

Replace-FileContent "$TargetsDir/get-portfolio.xml" "GET_PORTFOLIO_URL_PLACEHOLDER" $PortfolioUrl
Replace-FileContent "$TargetsDir/calculate-allocations.xml" "CALCULATE_ALLOCATIONS_URL_PLACEHOLDER" $AllocationsUrl
Replace-FileContent "$TargetsDir/check-financial-health.xml" "CHECK_FINANCIAL_HEALTH_URL_PLACEHOLDER" $HealthUrl
Replace-FileContent "$TargetsDir/get-market-news.xml" "GET_MARKET_NEWS_URL_PLACEHOLDER" $NewsUrl

# Now Zip from the TEMP dir
$SourcePath = "$BuildDir/apiproxy"
python "$PSScriptRoot/zip_proxy.py" "$SourcePath" "$ZipPath"
if ($LASTEXITCODE -ne 0) { throw "Bundling failed" }
Write-Host "[SUCCESS] Smart Bundle created: $ZipPath"

Write-Host "`n[DEPLOY] Deploying to Apigee..." -ForegroundColor Cyan
$Org = gcloud config get-value project
Write-Host "Target Org: $Org"
$Env = $Environment
Write-Host "Target Env: $Env"
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
Write-Host "[SUCCESS] Uploaded Revision: $Revision"

# 2. Deploy to Environment
Write-Host "Deploying Revision $Revision to $Env..."
$DeployBody = @{
    serviceAccount = "zerodha-agent-sa@$Org.iam.gserviceaccount.com"
} | ConvertTo-Json

$DeployUrl = "https://apigee.googleapis.com/v1/organizations/$Org/environments/$Env/apis/investment-agent-mcp/revisions/$Revision/deployments?override=true"
try {
    Invoke-RestMethod -Uri $DeployUrl -Method Post -Headers @{Authorization="Bearer $Token"; "Content-Type"="application/json"} -Body $DeployBody
    Write-Host "`n[SUCCESS] Successfully deployed to eval environment!" -ForegroundColor Green
} catch {
    Write-Host "`n[ERROR] Deployment failed!" -ForegroundColor Red
    if ($_.Exception.Response) {
        $streamReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $ErrorDetails = $streamReader.ReadToEnd()
        Write-Host "Details: $ErrorDetails" -ForegroundColor Red
    } else {
        Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`n[DONE] END-TO-END APIGEE SETUP COMPLETE" -ForegroundColor Green
