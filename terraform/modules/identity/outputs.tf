output "identity_platform_config_name" {
  description = "Identity Platform config name"
  value       = google_identity_platform_config.default.name
}

output "tenant_name" {
  description = "Identity Platform tenant name"
  value       = google_identity_platform_tenant.main.name
}

output "microsoft_idp_config_name" {
  description = "Microsoft IDP config name"
  value       = google_identity_platform_default_supported_idp_config.microsoft.name
}
