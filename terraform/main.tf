terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  # Dynamically construct the MODERN Cloud Run URL format
  # Format: https://{service-name}-{project-number}.{region}.a.run.app
  dashboard_url = "https://portfolio-dashboard-${data.google_project.project.number}.${var.region}.run.app"
}
