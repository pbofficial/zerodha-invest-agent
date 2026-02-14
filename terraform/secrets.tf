
resource "google_secret_manager_secret" "kite_api_key" {
  secret_id = "KITE_API_KEY"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "kite_access_token" {
  secret_id = "KITE_ACCESS_TOKEN"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "kite_api_secret" {
  secret_id = "KITE_API_SECRET"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "gmail_user" {
  secret_id = "GMAIL_USER"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "gmail_app_password" {
  secret_id = "GMAIL_APP_PASSWORD"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "recipient_email" {
  secret_id = "RECIPIENT_EMAIL"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "allowed_user_id" {
  secret_id = "ALLOWED_USER_ID"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "apigee_api_key" {
  secret_id = "APIGEE_API_KEY"
  replication {
    auto {}
  }
  project = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "kite_api_key_v1" {
  secret      = google_secret_manager_secret.kite_api_key.id
  secret_data = "placeholder_replace_me"
}

resource "google_secret_manager_secret_version" "kite_access_token_v1" {
  secret      = google_secret_manager_secret.kite_access_token.id
  secret_data = "placeholder_replace_me"
}

resource "google_secret_manager_secret_version" "kite_api_secret_v1" {
  secret      = google_secret_manager_secret.kite_api_secret.id
  secret_data = "placeholder_replace_me"
}

resource "google_secret_manager_secret_version" "gmail_user_v1" {
  secret      = google_secret_manager_secret.gmail_user.id
  secret_data = "placeholder_replace_me"
}

resource "google_secret_manager_secret_version" "gmail_app_password_v1" {
  secret      = google_secret_manager_secret.gmail_app_password.id
  secret_data = "placeholder_replace_me"
}

resource "google_secret_manager_secret_version" "recipient_email_v1" {
  secret      = google_secret_manager_secret.recipient_email.id
  secret_data = var.recipient_email
}

resource "google_secret_manager_secret_version" "allowed_user_id_v1" {
  secret      = google_secret_manager_secret.allowed_user_id.id
  secret_data = "placeholder_replace_me" 
}

resource "google_secret_manager_secret_version" "apigee_api_key_v1" {
  secret      = google_secret_manager_secret.apigee_api_key.id
  secret_data = "placeholder_replace_me"
}

data "google_project" "project" {}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_project_iam_member" "secret_uploader" {
  project = var.project_id
  role    = "roles/secretmanager.secretVersionAdder"
  member  = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "kite_api_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.kite_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "kite_access_token_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.kite_access_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}
