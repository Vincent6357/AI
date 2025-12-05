terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "terraform-state-vertex-rag"  # Update with your bucket name
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",          # Vertex AI
    "run.googleapis.com",                 # Cloud Run
    "storage.googleapis.com",             # Cloud Storage
    "firestore.googleapis.com",           # Firestore
    "documentai.googleapis.com",          # Document AI
    "identitytoolkit.googleapis.com",     # Identity Platform
    "secretmanager.googleapis.com",       # Secret Manager
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",          # Cloud Build
    "discoveryengine.googleapis.com",     # Vertex AI Search
    "artifactregistry.googleapis.com",    # Artifact Registry
  ])

  service            = each.value
  disable_on_destroy = false
}

# Storage Module
module "storage" {
  source = "./modules/storage"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# Firestore Module
module "firestore" {
  source = "./modules/firestore"

  project_id = var.project_id
  location   = var.location

  depends_on = [google_project_service.apis]
}

# Identity Platform Module
module "identity" {
  source = "./modules/identity"

  project_id            = var.project_id
  microsoft_auth_config = var.microsoft_auth_config

  depends_on = [google_project_service.apis]
}

# Vertex AI Module
module "vertexai" {
  source = "./modules/vertexai"

  project_id          = var.project_id
  vertex_ai_location  = var.vertex_ai_location
  environment         = var.environment

  depends_on = [google_project_service.apis]
}

# Cloud Run Module
module "cloudrun" {
  source = "./modules/cloudrun"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  firebase_config     = var.firebase_config
  backend_image       = "gcr.io/${var.project_id}/rag-backend:latest"
  frontend_image      = "gcr.io/${var.project_id}/rag-frontend:latest"

  depends_on = [
    google_project_service.apis,
    module.storage,
    module.firestore,
    module.identity,
    module.vertexai
  ]
}

# Service Account for the application
resource "google_service_account" "app_sa" {
  account_id   = "rag-app-sa-${var.environment}"
  display_name = "RAG Application Service Account (${var.environment})"
  description  = "Service account for RAG application backend"
}

# IAM roles for the service account
resource "google_project_iam_member" "app_sa_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/discoveryengine.admin",
    "roles/documentai.apiUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "rag-app-${var.environment}"
  description   = "Docker repository for RAG application"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}
