# Job 1: Daily Nudge (9 PM ET / 1:30 AM UTC Next Day)
resource "google_cloud_scheduler_job" "daily_nudge" {
  name             = "daily-nudge"
  description      = "Sends daily investment pulse email to user"
  schedule         = "0 20 * * *" # Daily at 8:00 PM ET
  time_zone        = "America/New_York"
  attempt_deadline = "180s"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.trigger_nudge.service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }
}

# Job 2: Morning Order Execution (9:15 AM IST Daily)
resource "google_cloud_scheduler_job" "morning_execution_job" {
  name             = "morning-execution"
  description      = "Executes queued orders when market opens"
  schedule         = "15 9 * * 1-5" # Mon-Fri at 9:15 AM IST
  time_zone        = "Asia/Kolkata"
  attempt_deadline = "180s"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.morning_execution.service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }
}

resource "google_service_account" "scheduler_invoker" {
  account_id   = "scheduler-invoker"
  display_name = "Cloud Scheduler Service Account"
  project      = var.project_id
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker_get_portfolio" {
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.get_portfolio.service_config[0].service
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker_morning_execution" {
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.morning_execution.service_config[0].service
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker_trigger_nudge" {
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.trigger_nudge.service_config[0].service
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}
