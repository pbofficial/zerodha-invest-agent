
# Cloud Run: Portfolio Dashboard
resource "google_cloud_run_v2_service" "dashboard" {
  name     = "portfolio-dashboard"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.zerodha_agent_sa.email
    containers {
      image = "gcr.io/${var.project_id}/dashboard:latest" # Assuming user will build/push this image
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name = "RECIPIENT_EMAIL"
        value_source {
          secret_key_ref {
            secret  = "RECIPIENT_EMAIL"
            version = "latest"
          }
        }
      }

      env {
        name = "KITE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "KITE_API_KEY"
            version = "latest"
          }
        }
      }

      env {
        name = "KITE_ACCESS_TOKEN"
        value_source {
          secret_key_ref {
            secret  = "KITE_ACCESS_TOKEN"
            version = "latest"
          }
        }
      }



      env {
        name = "GMAIL_USER"
        value_source {
          secret_key_ref {
            secret  = "GMAIL_USER"
            version = "latest"
          }
        }
      }
      
      env {
        name = "GMAIL_APP_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "GMAIL_APP_PASSWORD"
            version = "latest"
          }
        }
      }
      
      resources {
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }
      env {
        name  = "DEPLOY_ID"
        value = var.deploy_id
      }

      env {
        name  = "DASHBOARD_URL"
        value = local.dashboard_url
      }
    }
  }
}

variable "deploy_id" {
  type    = string
  default = "initial"
}

resource "google_cloud_run_service_iam_member" "public_access_dashboard" {
  location = google_cloud_run_v2_service.dashboard.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.dashboard.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
