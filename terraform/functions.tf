
# Storage bucket for Cloud Function source code
resource "google_storage_bucket" "function_source" {
  name                        = "${var.project_id}-function-source"
  location                    = var.region
  uniform_bucket_level_access = true
  project                     = var.project_id
}

# Zip the source code
data "archive_file" "function_zip" {
  type        = "zip"
  output_path = "${path.module}/function_source.zip"
  source_dir  = "${path.module}/.." # Zip everything in project root
  excludes    = [".git", ".terraform", ".venv", "terraform", "tests", "brain", ".agent", "test_zip", ".DS_Store", "__pycache__"]
}

resource "google_storage_bucket_object" "function_archive" {
  name   = "function-source-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_source.name
  source = data.archive_file.function_zip.output_path
}

# [Discovery] get-portfolio: Retrieval of current Zerodha holdings and market positions
resource "google_cloudfunctions2_function" "get_portfolio" {
  name        = "get-portfolio"
  location    = var.region
  project     = var.project_id
  description = "Fetches portfolio data"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "1Gi"
    available_cpu      = "1"
    timeout_seconds    = 300
    
    vpc_connector = google_vpc_access_connector.connector.id
    
    environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }
  }
  
  depends_on = [google_project_service.apis]
}

# Cloud Function: calculate-allocations
resource "google_cloudfunctions2_function" "calculate_allocations" {
  name        = "calculate-allocations"
  location    = var.region
  project     = var.project_id
  description = "Calculates stock allocations"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "2Gi"
    available_cpu      = "1"
    timeout_seconds    = 300
    
    vpc_connector = google_vpc_access_connector.connector.id

     environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }
  }
  
  depends_on = [google_project_service.apis]
}

# Cloud Function: execute-trade
resource "google_cloudfunctions2_function" "execute_trade" {
  name        = "execute-trade"
  location    = var.region
  project     = var.project_id
  description = "Executes trades on Zerodha"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "2Gi"
    available_cpu      = "1"
    timeout_seconds    = 300
    
    vpc_connector = google_vpc_access_connector.connector.id
    vpc_connector_egress_settings = "ALL_TRAFFIC"
    service_account_email = google_service_account.zerodha_agent_sa.email

    environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }

    secret_environment_variables {
      key        = "KITE_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_api_key.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "KITE_ACCESS_TOKEN"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_access_token.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "KITE_API_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_api_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GMAIL_USER"
      project_id = var.project_id
      secret     = google_secret_manager_secret.gmail_user.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GMAIL_APP_PASSWORD"
      project_id = var.project_id
      secret     = google_secret_manager_secret.gmail_app_password.secret_id
      version    = "latest"
    }
  }
  
  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.kite_api_key_v1,
    google_secret_manager_secret_version.kite_access_token_v1,
    google_secret_manager_secret_version.kite_api_secret_v1,
    google_secret_manager_secret_version.gmail_user_v1,
    google_secret_manager_secret_version.gmail_app_password_v1
  ]
}

# Cloud Function: trigger-nudge
resource "google_cloudfunctions2_function" "trigger_nudge" {
  name        = "trigger-nudge"
  location    = var.region
  project     = var.project_id
  description = "Sends the bi-monthly rebalance notification"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "1Gi"
    available_cpu      = "1"
    timeout_seconds    = 300
    
    service_account_email = google_service_account.zerodha_agent_sa.email
    environment_variables = {
      PROJECT_ID      = var.project_id
      LOCATION        = var.region
      DASHBOARD_URL   = local.dashboard_url
    }

    secret_environment_variables {
      key        = "RECIPIENT_EMAIL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.recipient_email.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GMAIL_USER"
      project_id = var.project_id
      secret     = google_secret_manager_secret.gmail_user.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GMAIL_APP_PASSWORD"
      project_id = var.project_id
      secret     = google_secret_manager_secret.gmail_app_password.secret_id
      version    = "latest"
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.gmail_user_v1,
    google_secret_manager_secret_version.gmail_app_password_v1
  ]
}

# Cloud Function: morning-execution
resource "google_cloudfunctions2_function" "morning_execution" {
  name        = "morning-execution"
  location    = var.region
  project     = var.project_id
  description = "Executes queued orders at market open"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "1Gi"
    available_cpu      = "1"
    timeout_seconds    = 300
    
    service_account_email = google_service_account.zerodha_agent_sa.email
    environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }

    secret_environment_variables {
      key        = "KITE_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_api_key.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "KITE_ACCESS_TOKEN"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_access_token.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "KITE_API_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.kite_api_secret.secret_id
      version    = "latest"
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.kite_api_key_v1,
    google_secret_manager_secret_version.kite_access_token_v1,
    google_secret_manager_secret_version.kite_api_secret_v1
  ]
}

# Cloud Function: check-financial-health
resource "google_cloudfunctions2_function" "check_financial_health" {
  name        = "check-financial-health"
  location    = var.region
  project     = var.project_id
  description = "Checks quarterly profit trends for a ticker"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512Mi"
    available_cpu      = "0.5"
    timeout_seconds    = 60
    
    vpc_connector = google_vpc_access_connector.connector.id
    
    environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }
  }
  
  depends_on = [google_project_service.apis]
}

# Cloud Function: get-market-news
resource "google_cloudfunctions2_function" "get_market_news" {
  name        = "get-market-news"
  location    = var.region
  project     = var.project_id
  description = "Fetches recent negative financial news via DDG"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512Mi"
    available_cpu      = "0.5"
    timeout_seconds    = 60
    
    vpc_connector = google_vpc_access_connector.connector.id
    
    environment_variables = {
      PROJECT_ID = var.project_id
      LOCATION   = var.region
    }
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_service_iam_member" "invoker_execute_trade" {
  location = google_cloudfunctions2_function.execute_trade.location
  project  = google_cloudfunctions2_function.execute_trade.project
  service  = google_cloudfunctions2_function.execute_trade.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

# Apigee Service Agent Invoker Permissions
resource "google_cloud_run_service_iam_member" "apigee_invoker_get_portfolio" {
  location = google_cloudfunctions2_function.get_portfolio.location
  project  = google_cloudfunctions2_function.get_portfolio.project
  service  = google_cloudfunctions2_function.get_portfolio.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-apigee.iam.gserviceaccount.com"
}

resource "google_cloud_run_service_iam_member" "apigee_invoker_calculate_allocations" {
  location = google_cloudfunctions2_function.calculate_allocations.location
  project  = google_cloudfunctions2_function.calculate_allocations.project
  service  = google_cloudfunctions2_function.calculate_allocations.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-apigee.iam.gserviceaccount.com"
}

resource "google_cloud_run_service_iam_member" "apigee_invoker_check_health" {
  location = google_cloudfunctions2_function.check_financial_health.location
  project  = google_cloudfunctions2_function.check_financial_health.project
  service  = google_cloudfunctions2_function.check_financial_health.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-apigee.iam.gserviceaccount.com"
}

resource "google_cloud_run_service_iam_member" "apigee_invoker_market_news" {
  location = google_cloudfunctions2_function.get_market_news.location
  project  = google_cloudfunctions2_function.get_market_news.project
  service  = google_cloudfunctions2_function.get_market_news.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-apigee.iam.gserviceaccount.com"
}

resource "google_cloud_run_service_iam_member" "invoker_get_portfolio" {
  location = google_cloudfunctions2_function.get_portfolio.location
  project  = google_cloudfunctions2_function.get_portfolio.project
  service  = google_cloudfunctions2_function.get_portfolio.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_cloud_run_service_iam_member" "invoker_calculate_allocations" {
  location = google_cloudfunctions2_function.calculate_allocations.location
  project  = google_cloudfunctions2_function.calculate_allocations.project
  service  = google_cloudfunctions2_function.calculate_allocations.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_cloud_run_service_iam_member" "invoker_check_health" {
  location = google_cloudfunctions2_function.check_financial_health.location
  project  = google_cloudfunctions2_function.check_financial_health.project
  service  = google_cloudfunctions2_function.check_financial_health.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}

resource "google_cloud_run_service_iam_member" "invoker_market_news" {
  location = google_cloudfunctions2_function.get_market_news.location
  project  = google_cloudfunctions2_function.get_market_news.project
  service  = google_cloudfunctions2_function.get_market_news.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.zerodha_agent_sa.email}"
}
