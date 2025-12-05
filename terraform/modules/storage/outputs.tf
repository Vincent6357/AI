output "main_bucket_name" {
  description = "Main storage bucket name"
  value       = google_storage_bucket.main.name
}

output "main_bucket_url" {
  description = "Main storage bucket URL"
  value       = google_storage_bucket.main.url
}

output "temp_uploads_bucket_name" {
  description = "Temporary uploads bucket name"
  value       = google_storage_bucket.temp_uploads.name
}
