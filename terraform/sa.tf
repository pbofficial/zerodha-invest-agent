resource "google_service_account" "zerodha_agent_sa" {
  account_id   = "zerodha-agent-sa"
  display_name = "Zerodha Invest Agent Service Account"
  project      = var.project_id
}
