# Main storage bucket for application data
resource "google_storage_bucket" "main" {
  name          = "${var.project_id}-rag-main-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age                   = 90
      with_state            = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Bucket for temporary uploads
resource "google_storage_bucket" "temp_uploads" {
  name          = "${var.project_id}-rag-uploads-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7  # Delete after 7 days
    }
    action {
      type = "Delete"
    }
  }
}
