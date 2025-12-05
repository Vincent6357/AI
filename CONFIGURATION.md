# 📚 Guide de Configuration - Vertex AI RAG Demo

Ce document vous guide à travers toutes les étapes de configuration nécessaires pour déployer et exécuter l'application RAG basée sur Google Cloud Platform.

## 📋 Table des matières

1. [Pré-requis](#pré-requis)
2. [Configuration Google Cloud Platform](#configuration-google-cloud-platform)
3. [Configuration Firebase Authentication](#configuration-firebase-authentication)
4. [Configuration Microsoft OAuth (SSO)](#configuration-microsoft-oauth-sso)
5. [Configuration Terraform](#configuration-terraform)
6. [Variables d'environnement](#variables-denvironnement)
7. [Déploiement](#déploiement)
8. [Tests et Validation](#tests-et-validation)

---

## 🔧 Pré-requis

### Outils nécessaires

- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5.0
- [Docker](https://docs.docker.com/get-docker/)
- [Node.js](https://nodejs.org/) >= 20.x
- [Python](https://www.python.org/downloads/) >= 3.11
- [Git](https://git-scm.com/)

### Comptes nécessaires

- Compte Google Cloud Platform (avec facturation activée)
- Compte Microsoft Azure AD (pour SSO)
- Accès admin pour configurer les applications

---

## ☁️ Configuration Google Cloud Platform

### 1. Créer et configurer le projet GCP

```bash
# Connexion à GCP
gcloud auth login

# Créer un nouveau projet (ou utiliser un existant)
export PROJECT_ID="vertex-rag-demo"  # Changez selon vos besoins
gcloud projects create $PROJECT_ID --name="Vertex RAG Demo"

# Définir le projet actif
gcloud config set project $PROJECT_ID

# Activer la facturation (requis)
# Allez sur: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID
```

### 2. Activer les APIs nécessaires

```bash
# Activer toutes les APIs requises
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  documentai.googleapis.com \
  identitytoolkit.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  cloudbuild.googleapis.com \
  discoveryengine.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Créer un Service Account

```bash
# Créer le service account
gcloud iam service-accounts create rag-app-sa \
  --display-name="RAG Application Service Account" \
  --description="Service account for RAG application"

# Obtenir l'email du service account
export SA_EMAIL="rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Attribuer les rôles nécessaires
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/discoveryengine.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/documentai.apiUser"

# Créer une clé JSON pour le service account
gcloud iam service-accounts keys create ./credentials/service-account.json \
  --iam-account=$SA_EMAIL

echo "✅ Service account créé et clé sauvegardée dans ./credentials/service-account.json"
```

**⚠️ IMPORTANT**: Ne commitez JAMAIS le fichier `service-account.json` dans Git. Il est déjà dans le `.gitignore`.

---

## 🔐 Configuration Firebase Authentication

### 1. Créer un projet Firebase

1. Allez sur [Firebase Console](https://console.firebase.google.com/)
2. Cliquez sur "Ajouter un projet"
3. Sélectionnez votre projet GCP existant (`vertex-rag-demo`)
4. Activez Google Analytics (optionnel)
5. Cliquez sur "Créer le projet"

### 2. Configurer Firebase Authentication

1. Dans la console Firebase, allez dans **Authentication** > **Sign-in method**
2. Activez **Email/Password**
3. Configurez les domaines autorisés :
   - Ajoutez `localhost` pour le développement
   - Ajoutez votre domaine de production

### 3. Récupérer les clés Firebase

1. Allez dans **Paramètres du projet** (⚙️ en haut à gauche)
2. Descendez jusqu'à "Vos applications"
3. Cliquez sur **</> Web** pour créer une application web
4. Enregistrez l'application et copiez les valeurs suivantes :

```javascript
// Vous verrez quelque chose comme ça :
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "vertex-rag-demo.firebaseapp.com",
  projectId: "vertex-rag-demo",
  storageBucket: "vertex-rag-demo.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456"
};
```

**📝 Notez ces valeurs**, vous en aurez besoin pour le fichier `.env`.

---

## 🔑 Configuration Microsoft OAuth (SSO)

### 1. Créer une App Registration dans Azure AD

1. Allez sur [Azure Portal](https://portal.azure.com/)
2. Naviguez vers **Azure Active Directory** > **App registrations**
3. Cliquez sur **New registration**
4. Configurez :
   - **Name**: `Vertex RAG Demo`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**:
     - Type: `Web`
     - URL: `https://vertex-rag-demo.firebaseapp.com/__/auth/handler`
     - (Ajoutez aussi `http://localhost:3000/__/auth/handler` pour le dev)
5. Cliquez sur **Register**

### 2. Récupérer les identifiants

Après la création, notez :

- **Application (client) ID** : affiché sur la page Overview
- **Directory (tenant) ID** : affiché sur la page Overview

### 3. Créer un Client Secret

1. Allez dans **Certificates & secrets**
2. Cliquez sur **New client secret**
3. Description: `Firebase Integration`
4. Expiration: `24 months` (ou selon votre politique)
5. Cliquez sur **Add**
6. **⚠️ COPIEZ IMMÉDIATEMENT LA VALEUR** (elle ne sera plus visible après)

**📝 Notez** :
- `MICROSOFT_CLIENT_ID` = Application (client) ID
- `MICROSOFT_CLIENT_SECRET` = Valeur du secret (Value, pas Secret ID)
- `MICROSOFT_TENANT_ID` = Directory (tenant) ID

### 4. Configurer les permissions API

1. Allez dans **API permissions**
2. Cliquez sur **Add a permission**
3. Sélectionnez **Microsoft Graph**
4. Sélectionnez **Delegated permissions**
5. Ajoutez :
   - `openid`
   - `profile`
   - `email`
   - `User.Read`
6. Cliquez sur **Add permissions**
7. Cliquez sur **Grant admin consent for [Your Organization]**

### 5. Ajouter Microsoft comme provider dans Firebase

1. Retournez dans **Firebase Console** > **Authentication** > **Sign-in method**
2. Cliquez sur **Add new provider** > **Microsoft**
3. Activez le provider
4. Entrez :
   - **Application (client) ID**
   - **Application (client) secret**
   - **Tenant ID** (optionnel, utilisez `common` pour multi-tenant)
5. Copiez l'**OAuth redirect URI** fournie par Firebase
6. Retournez dans **Azure AD** > votre App Registration > **Authentication**
7. Ajoutez cette URI dans les **Redirect URIs**
8. Sauvegardez

---

## 🏗️ Configuration Terraform

### 1. Créer le bucket pour le state Terraform

```bash
# Créer un bucket pour stocker l'état Terraform
export TF_STATE_BUCKET="${PROJECT_ID}-terraform-state"

gsutil mb -p $PROJECT_ID -l europe-west1 gs://$TF_STATE_BUCKET

# Activer le versioning
gsutil versioning set on gs://$TF_STATE_BUCKET

echo "✅ Bucket Terraform state créé: gs://$TF_STATE_BUCKET"
```

### 2. Configurer les variables Terraform

Créez le fichier `terraform/terraform.tfvars` :

```hcl
# terraform/terraform.tfvars
project_id         = "vertex-rag-demo"
region             = "europe-west1"
location           = "europe"
environment        = "dev"
vertex_ai_location = "us-central1"

# Firebase Configuration
firebase_config = {
  api_key             = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  auth_domain         = "vertex-rag-demo.firebaseapp.com"
  project_id          = "vertex-rag-demo"
  storage_bucket      = "vertex-rag-demo.appspot.com"
  messaging_sender_id = "123456789012"
  app_id              = "1:123456789012:web:abcdef123456"
}

# Microsoft OAuth Configuration
microsoft_auth_config = {
  client_id     = "12345678-1234-1234-1234-123456789abc"
  client_secret = "votre-client-secret-microsoft"
  tenant_id     = "87654321-4321-4321-4321-cba987654321"
}
```

**⚠️ SÉCURITÉ** :
- Ne commitez JAMAIS `terraform.tfvars`
- Il est déjà dans le `.gitignore`
- Utilisez plutôt **Secret Manager** ou **Terraform Cloud** en production

### 3. Initialiser et déployer Terraform

```bash
cd terraform

# Mettre à jour le backend dans main.tf avec votre bucket
# Ouvrez main.tf et changez:
# backend "gcs" {
#   bucket = "VOTRE-BUCKET-TERRAFORM-STATE"
#   prefix = "terraform/state"
# }

# Initialiser Terraform
terraform init

# Vérifier le plan
terraform plan

# Appliquer (créer l'infrastructure)
terraform apply

# Notez les outputs (URLs des services, etc.)
terraform output
```

---

## 🔐 Variables d'environnement

### 1. Créer le fichier `.env` pour le développement local

Copiez `.env.example` vers `.env` et remplissez :

```bash
cp .env.example .env
```

Éditez `.env` :

```bash
# Google Cloud Platform Configuration
GCP_PROJECT_ID=vertex-rag-demo
GCP_REGION=europe-west1
GCP_LOCATION=europe
VERTEX_AI_LOCATION=us-central1
ENVIRONMENT=dev

# Firebase Configuration
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=vertex-rag-demo.firebaseapp.com
FIREBASE_PROJECT_ID=vertex-rag-demo
FIREBASE_STORAGE_BUCKET=vertex-rag-demo.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456

# Vertex AI Models
DEFAULT_MODEL=gemini-1.5-pro
EMBEDDING_MODEL=text-embedding-004

# Storage (remplissez après déploiement Terraform)
MAIN_BUCKET_NAME=vertex-rag-demo-rag-main-dev
TEMP_UPLOADS_BUCKET=vertex-rag-demo-rag-uploads-dev

# Application Settings
MAX_FILE_SIZE_MB=50
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4096
DEFAULT_TOP_K=5
DEFAULT_SIMILARITY_THRESHOLD=0.7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO

# Service Account
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
```

### 2. Variables pour le Frontend

Créez `app/frontend/.env` :

```bash
VITE_API_URL=http://localhost:8080
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_FIREBASE_AUTH_DOMAIN=vertex-rag-demo.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=vertex-rag-demo
VITE_FIREBASE_STORAGE_BUCKET=vertex-rag-demo.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456
```

---

## 🚀 Déploiement

### Option 1: Déploiement local avec Docker Compose

```bash
# S'assurer que le fichier .env est configuré
# S'assurer que ./credentials/service-account.json existe

# Créer le dossier credentials si nécessaire
mkdir -p credentials

# Builder et démarrer les conteneurs
docker-compose up --build

# L'application sera disponible sur:
# - Backend: http://localhost:8080
# - Frontend: http://localhost:3000
```

### Option 2: Déploiement manuel sur Cloud Run

#### Backend

```bash
cd app/backend

# Build et push l'image
gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-backend

# Deploy sur Cloud Run
gcloud run deploy rag-backend \
  --image gcr.io/$PROJECT_ID/rag-backend \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=europe-west1"

# Récupérer l'URL du backend
gcloud run services describe rag-backend --region=europe-west1 --format='value(status.url)'
```

#### Frontend

```bash
cd app/frontend

# Build avec les bonnes variables d'environnement
# Mettre à jour VITE_API_URL avec l'URL du backend

# Build et push
gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-frontend

# Deploy
gcloud run deploy rag-frontend \
  --image gcr.io/$PROJECT_ID/rag-frontend \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated

# Récupérer l'URL
gcloud run services describe rag-frontend --region=europe-west1 --format='value(status.url)'
```

### Option 3: Déploiement avec GitHub Actions

1. Créer les secrets GitHub :

```bash
# Dans votre repo GitHub, allez dans Settings > Secrets and variables > Actions
# Ajoutez les secrets suivants:
```

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | votre-project-id |
| `GCP_SA_KEY` | Contenu de `service-account.json` |

2. Push sur la branche `main` déclenchera automatiquement le déploiement

---

## ✅ Tests et Validation

### 1. Tester l'authentification Firebase

```bash
# Utiliser l'interface frontend
# 1. Ouvrir http://localhost:3000
# 2. Cliquer sur "Sign in with Microsoft"
# 3. Se connecter avec un compte Microsoft
# 4. Vérifier que vous êtes redirigé vers l'application
```

### 2. Tester le backend

```bash
# Health check
curl http://localhost:8080/health

# Devrait retourner:
# {"status":"healthy","service":"vertex-rag-backend"}
```

### 3. Créer votre premier agent

1. Connectez-vous en tant qu'admin (premier utilisateur)
2. Allez dans "Agents"
3. Cliquez sur "Nouvel Agent"
4. Remplissez le nom et la description
5. L'agent sera créé avec un bucket GCS et un corpus Vertex AI

### 4. Uploader des documents

1. Sélectionnez un agent
2. Cliquez sur "Documents"
3. Uploadez des PDF, DOCX, TXT, etc.
4. Attendez l'indexation (le statut passera de "uploaded" à "indexed")

### 5. Tester le chat

1. Sélectionnez un agent avec des documents indexés
2. Posez une question sur le contenu
3. Vérifiez que la réponse contient des citations

---

## 🔧 Dépannage

### Erreur "Permission denied" lors du déploiement

```bash
# Vérifier que le service account a les bonnes permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:rag-app-sa*"
```

### Erreur "Firebase Authentication failed"

- Vérifiez que les domaines sont autorisés dans Firebase Console
- Vérifiez que les variables d'environnement Firebase sont correctes
- Vérifiez que Microsoft OAuth est bien configuré

### Erreur "Vertex AI quota exceeded"

- Vérifiez vos quotas : https://console.cloud.google.com/iam-admin/quotas
- Demandez une augmentation si nécessaire

### Documents non indexés

- Vérifiez les logs Cloud Run
- Vérifiez que le bucket GCS existe et contient le fichier
- Vérifiez que le corpus Vertex AI existe

---

## 📚 Ressources supplémentaires

- [Documentation Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Documentation Firebase Authentication](https://firebase.google.com/docs/auth)
- [Documentation Cloud Run](https://cloud.google.com/run/docs)
- [Documentation Firestore](https://cloud.google.com/firestore/docs)
- [Microsoft OAuth Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)

---

## 🆘 Support

Pour des questions ou problèmes :
- Ouvrez une issue sur GitHub
- Consultez les logs Cloud Run : `gcloud run services logs read rag-backend --region=europe-west1`
- Vérifiez Cloud Logging : https://console.cloud.google.com/logs

---

**✨ Votre application RAG avec Vertex AI est maintenant configurée !**
