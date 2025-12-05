output "backend_url" {
  description = "Backend Cloud Run service URL"
  value       = module.cloudrun.backend_url
}

output "frontend_url" {
  description = "Frontend Cloud Run service URL"
  value       = module.cloudrun.frontend_url
}

output "service_account_email" {
  description = "Service account email for the application"
  value       = google_service_account.app_sa.email
}

output "storage_bucket_name" {
  description = "Main storage bucket name"
  value       = module.storage.main_bucket_name
}

output "firestore_database" {
  description = "Firestore database name"
  value       = module.firestore.database_name
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}
