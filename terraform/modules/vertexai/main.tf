# Note: Vertex AI doesn't require explicit infrastructure setup via Terraform
# Most Vertex AI resources are created dynamically via the API

# Create a Vertex AI Dataset for potential fine-tuning
resource "google_vertex_ai_dataset" "default" {
  display_name          = "rag-dataset-${var.environment}"
  metadata_schema_uri   = "gs://google-cloud-aiplatform/schema/dataset/metadata/text_1.0.0.yaml"
  region                = var.vertex_ai_location
  project               = var.project_id
}

# Vertex AI Endpoint for custom models (optional)
# Uncomment if you need custom model deployment
# resource "google_vertex_ai_endpoint" "default" {
#   name         = "rag-endpoint-${var.environment}"
#   display_name = "RAG Endpoint (${var.environment})"
#   location     = var.vertex_ai_location
#   project      = var.project_id
#   description  = "Endpoint for RAG custom models"
# }

# Vertex AI Tensorboard for experiment tracking
resource "google_vertex_ai_tensorboard" "default" {
  display_name = "rag-tensorboard-${var.environment}"
  description  = "Tensorboard for RAG experiments"
  region       = var.vertex_ai_location
  project      = var.project_id
}

# Vertex AI Feature Store for potential caching
resource "google_vertex_ai_featurestore" "default" {
  name   = "rag_featurestore_${var.environment}"
  region = var.vertex_ai_location
  project = var.project_id

  online_serving_config {
    fixed_node_count = 1
  }

  encryption_spec {
    kms_key_name = ""
  }
}
