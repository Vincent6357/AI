# Enable Identity Platform
resource "google_identity_platform_config" "default" {
  provider = google-beta
  project  = var.project_id

  autodelete_anonymous_users = true

  sign_in {
    allow_duplicate_emails = false

    anonymous {
      enabled = false
    }

    email {
      enabled           = true
      password_required = true
    }
  }

  blocking_functions {
    triggers {
      event_type   = "beforeCreate"
      function_uri = ""  # Fournir une chaîne vide si pas de Cloud Function
    }
  }
}  # <-- ACCOLADE MANQUANTE AJOUTÉE ICI


# Identity Platform tenant for multi-tenancy
resource "google_identity_platform_tenant" "main" {
  provider     = google-beta
  project      = var.project_id
  display_name = "RAG Application Tenant"

  allow_password_signup = true

  depends_on = [google_identity_platform_config.default]
}

# OAuth IDP config for Microsoft
resource "google_identity_platform_default_supported_idp_config" "microsoft" {
  provider = google-beta
  project  = var.project_id

  idp_id        = "microsoft.com"
  client_id     = var.microsoft_auth_config.client_id
  client_secret = var.microsoft_auth_config.client_secret
  enabled       = true

  depends_on = [google_identity_platform_config.default]
}

# Store Microsoft tenant ID in Secret Manager
resource "google_secret_manager_secret" "microsoft_tenant_id" {
  secret_id = "microsoft-tenant-id"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "microsoft_tenant_id_version" {
  secret      = google_secret_manager_secret.microsoft_tenant_id.id
  secret_data = var.microsoft_auth_config.tenant_id
}