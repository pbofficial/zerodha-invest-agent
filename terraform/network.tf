resource "google_compute_network" "vpc" {
  name                    = "zerodha-agent-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "subnet" {
  name          = "zerodha-agent-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id
}

resource "google_vpc_access_connector" "connector" {
  name          = "zerodha-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  project       = var.project_id
  depends_on    = [google_project_service.apis]
}
