resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_project_iam_member" "browser_viewer" {
  project = var.project_id
  role    = "roles/viewer"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_project_iam_member" "secret_viewer" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

# --- Enterprise Pattern: Apigee -> API Hub Permissions ---

resource "google_project_iam_member" "apigee_apihub_viewer" {
  project = var.project_id
  role    = "roles/apihub.viewer"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-apigee.iam.gserviceaccount.com"
}
