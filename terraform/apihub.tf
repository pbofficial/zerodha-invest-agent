
# Enterprise Pattern: Registering Tools in API Hub via REST API
# Using null_resource because google_apihub_api is not yet in the provider.

resource "null_resource" "register_apihub_tools" {
  for_each = {
    "get-market-snapshot"    = "Retrieve real-time NSE (National Stock Exchange) market prices and the user's current equity portfolio. Essential first step for gap analysis. Outputs include LTP (Last Traded Price) and quantity held."
    "check-financial-health" = "Audit a specific ticker for financial stability. This tool performs a Cynical Audit: it checks quarterly profit trends and issues a WARNING if net profits have declined for 2+ consecutive quarters. Use to filter out distressed stocks."
    "calculate-allocations"  = "Deterministic mathematical engine that converts Target Allocation (expressed in %) into precise Order Quantities based on a provided Cash Budget and current LTP. Does not perform market logic, only arithmetic."
    "get-market-news"        = "Search for cynical or risk-based news for NSE tickers. Focuses on management integrity, regulatory warnings, or fraud allegations. Necessary for final risk-clearing before order placement."
  }

  triggers = {
    description = each.value
    version     = "v1-mcp-branding"
  }

  provisioner "local-exec" {
    command = <<EOT
      $token = gcloud auth print-access-token
      $apiId = "${each.key}"
      $displayName = "${each.key}"
      $description = "${each.value}"
      
      # Enterprise Attributes for Registry Styling
      $attributes = @{
        "projects/${var.project_id}/locations/${var.region}/attributes/system-api-style" = @{
          enum_values = @{ values = @( @{ id = "mcp-api" } ) }
        }
        "projects/${var.project_id}/locations/${var.region}/attributes/system-maturity-level" = @{
          enum_values = @{ values = @( @{ id = "level-3" } ) }
        }
        "projects/${var.project_id}/locations/${var.region}/attributes/system-target-user" = @{
          enum_values = @{ values = @( @{ id = "internal" } ) }
        }
      }

      $body = @{
        displayName = $displayName
        description = $description
        attributes  = $attributes
      } | ConvertTo-Json -Depth 10 -Compress
      
      try {
        Write-Host "Re-registering Tool with MCP Branding: $apiId"
        # Force a clean update (Registry IDs are immutable for styles in some versions)
        Invoke-RestMethod -Uri "https://apihub.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/apis/$apiId" `
          -Method Delete `
          -Headers @{ Authorization = "Bearer $token" } -ErrorAction SilentlyContinue
        
        # Create with MCP Style
        Invoke-RestMethod -Uri "https://apihub.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/apis?apiId=$apiId" `
          -Method Post `
          -Headers @{ Authorization = "Bearer $token" } `
          -Body $body `
          -ContentType "application/json"
        Write-Host "Successfully registered $apiId with MCP Style"
      } catch {
        Write-Host "Error registering $apiId : $($_.Exception.Message)"
        throw $_.Exception
      }
    EOT
    interpreter = ["powershell", "-Command"]
  }
}
