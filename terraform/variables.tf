variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "location" {
  description = "GCP Location for global resources"
  type        = string
  default     = "europewest1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vertex_ai_location" {
  description = "Vertex AI location"
  type        = string
  default     = "us-central1"
}

variable "firebase_config" {
  description = "Firebase configuration for authentication"
  type = object({
    api_key             = string
    auth_domain         = string
    project_id          = string
    storage_bucket      = string
    messaging_sender_id = string
    app_id              = string
  })
  sensitive = true
}

variable "microsoft_auth_config" {
  description = "Microsoft OAuth configuration"
  type = object({
    client_id     = string
    client_secret = string
    tenant_id     = string
  })
  sensitive = true
}

variable "function_uri" {
  description = "Cloud Function URI for Identity Platform triggers"
  type        = string
  default     = ""
}