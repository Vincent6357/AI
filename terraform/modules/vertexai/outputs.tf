output "dataset_name" {
  description = "Vertex AI dataset name"
  value       = google_vertex_ai_dataset.default.name
}

output "tensorboard_name" {
  description = "Vertex AI tensorboard name"
  value       = google_vertex_ai_tensorboard.default.name
}

output "featurestore_name" {
  description = "Vertex AI featurestore name"
  value       = google_vertex_ai_featurestore.default.name
}
