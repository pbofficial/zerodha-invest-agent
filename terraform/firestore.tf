resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# Seed: Agent Settings
resource "google_firestore_document" "agent_settings" {
  project     = var.project_id
  database    = google_firestore_database.database.name
  collection  = "config"
  document_id = "agent_settings"
  fields      = jsonencode({
    agent_settings = {
      mapValue = {
        fields = {
          model_name = { stringValue = var.model_name }
          location   = { stringValue = var.region }
          risk_threshold = { integerValue = 8 }
        }
      }
    }
    investment_goals = {
      mapValue = {
        fields = {
          budget = { integerValue = 10000 }
          target_portfolio = { stringValue = "RELIANCE, HDFCBANK, INFOSYS" }
        }
      }
    }
    scoring_rules = {
      mapValue = {
        fields = {
          noise = { integerValue = 0 }
          context = { integerValue = 5 }
          critical = { integerValue = 10 }
        }
      }
    }
  })

  lifecycle {
    ignore_changes = [fields]
  }
}

# Seed: Universe (Example)
resource "google_firestore_document" "universe" {
  project     = var.project_id
  database    = google_firestore_database.database.name
  collection  = "config"
  document_id = "universe"
  fields      = jsonencode({
    assets = {
      arrayValue = {
        values = [
          {
            mapValue = {
              fields = {
                ticker = { stringValue = "RELIANCE" }
                sector = { stringValue = "Energy" }
                type   = { stringValue = "Core" }
              }
            }
          },
          {
            mapValue = {
              fields = {
                ticker = { stringValue = "HDFCBANK" }
                sector = { stringValue = "Finance" }
                type   = { stringValue = "Core" }
              }
            }
          }
        ]
      }
    }
  })

  lifecycle {
    ignore_changes = [fields]
  }
}
