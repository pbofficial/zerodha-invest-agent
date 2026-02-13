variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-east4"
}

variable "allowed_user_email" {
  description = "Email address of the admin user allowed to access the dashboard"
  type        = string
}

variable "recipient_email" {
  description = "Email address to receive rebalance notifications"
  type        = string
}

variable "model_name" {
  description = "The Vertex AI model name"
  type        = string
  default     = "gemini-2.0-flash"
}

variable "apigee_mcp_endpoint" {
  description = "The internal Apigee MCP endpoint"
  type        = string
  default     = "https://10.140.24.2"
}
