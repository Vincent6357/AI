# Backend Cloud Run service
resource "google_cloud_run_v2_service" "backend" {
  name     = "rag-backend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.backend_image

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "FIREBASE_API_KEY"
        value = var.firebase_config.api_key
      }

      env {
        name  = "FIREBASE_AUTH_DOMAIN"
        value = var.firebase_config.auth_domain
      }

      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.firebase_config.project_id
      }

      env {
        name  = "FIREBASE_STORAGE_BUCKET"
        value = var.firebase_config.storage_bucket
      }

      env {
        name  = "FIREBASE_MESSAGING_SENDER_ID"
        value = var.firebase_config.messaging_sender_id
      }

      env {
        name  = "FIREBASE_APP_ID"
        value = var.firebase_config.app_id
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }

        cpu_idle = false
      }

      ports {
        container_port = 8080
      }
    }

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 10 : 3
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Frontend Cloud Run service
resource "google_cloud_run_v2_service" "frontend" {
  name     = "rag-frontend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.frontend_image

      env {
        name  = "VITE_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "VITE_FIREBASE_API_KEY"
        value = var.firebase_config.api_key
      }

      env {
        name  = "VITE_FIREBASE_AUTH_DOMAIN"
        value = var.firebase_config.auth_domain
      }

      env {
        name  = "VITE_FIREBASE_PROJECT_ID"
        value = var.firebase_config.project_id
      }

      env {
        name  = "VITE_FIREBASE_STORAGE_BUCKET"
        value = var.firebase_config.storage_bucket
      }

      env {
        name  = "VITE_FIREBASE_MESSAGING_SENDER_ID"
        value = var.firebase_config.messaging_sender_id
      }

      env {
        name  = "VITE_FIREBASE_APP_ID"
        value = var.firebase_config.app_id
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 80
      }
    }

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 5 : 2
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM binding to allow public access (adjust based on requirements)
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
