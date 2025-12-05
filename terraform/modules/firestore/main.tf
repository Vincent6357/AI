resource "google_firestore_database" "main" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location
  type        = "FIRESTORE_NATIVE"

  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
}

# Firestore indexes
resource "google_firestore_index" "agents_created_at" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "agents"

  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
}

resource "google_firestore_index" "documents_status" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "agents/{agentId}/documents"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }

  fields {
    field_path = "uploadedAt"
    order      = "DESCENDING"
  }
}

resource "google_firestore_index" "users_role" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "users"

  fields {
    field_path = "role"
    order      = "ASCENDING"
  }

  fields {
    field_path = "lastLogin"
    order      = "DESCENDING"
  }
}
