resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudbuild.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com"
  ])

  project = var.project_id
  service = each.key
  disable_on_destroy = false
}
