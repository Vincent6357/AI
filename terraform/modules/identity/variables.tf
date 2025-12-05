variable "project_id" {
  description = "GCP Project ID"
  type        = string
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
