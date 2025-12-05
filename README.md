# 🚀 Vertex AI RAG Demo - Multi-Tenant Enterprise RAG Application

Application RAG (Retrieval Augmented Generation) d'entreprise basée sur Google Cloud Platform avec Vertex AI, support multi-tenant et authentification Microsoft SSO.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![GCP](https://img.shields.io/badge/GCP-Vertex%20AI-orange.svg)

## 📋 Vue d'ensemble

Cette solution fournit une expérience ChatGPT personnalisée sur vos propres documents en utilisant le pattern RAG (Retrieval Augmented Generation). Elle utilise :

- **Vertex AI** pour le LLM (Gemini) et les embeddings
- **Vertex AI Search** pour l'indexation et la recherche de documents
- **Cloud Storage** pour le stockage des documents
- **Firestore** pour les métadonnées et la gestion multi-tenant
- **Cloud Run** pour l'hébergement scalable
- **Identity Platform + Microsoft SSO** pour l'authentification

### 🌟 Fonctionnalités principales

- ✅ **Multi-tenant** : Gestion d'agents multiples avec bases de connaissances isolées
- ✅ **Chat streaming** : Réponses en temps réel avec citations
- ✅ **Microsoft SSO** : Authentification d'entreprise via Azure AD
- ✅ **Gestion de rôles** : Admin / User avec contrôle d'accès
- ✅ **Upload de documents** : PDF, DOCX, TXT, MD, HTML, CSV
- ✅ **Indexation automatique** : Pipeline d'ingestion avec Vertex AI
- ✅ **Citations et sources** : Traçabilité des réponses
- ✅ **Interface moderne** : UI React responsive
- ✅ **Infrastructure as Code** : Terraform pour GCP
- ✅ **CI/CD** : GitHub Actions pour déploiement automatique

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                   Firebase Hosting / Cloud Run               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Identity Platform (Microsoft SSO)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Backend (FastAPI)                      │
│                      Cloud Run                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐    ┌──────────┐
   │ Vertex   │      │Firestore │    │  Cloud   │
   │   AI     │      │(Metadata)│    │ Storage  │
   │          │      │          │    │(Documents)│
   └──────────┘      └──────────┘    └──────────┘
```

## 🚀 Démarrage rapide

### Pré-requis

- Compte Google Cloud Platform (avec facturation activée)
- Compte Microsoft Azure AD (pour SSO)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://www.terraform.io/downloads) >= 1.5.0
- [Docker](https://www.docker.com/) et Docker Compose
- [Python](https://www.python.org/) >= 3.11
- [Node.js](https://nodejs.org/) >= 20

### Installation

1. **Cloner le repository**

```bash
git clone <votre-repo>
cd vertex-search-gemini-demo
```

2. **Configurer GCP et créer les credentials**

Suivez le guide complet de configuration : **[CONFIGURATION.md](./CONFIGURATION.md)**

Ce guide détaille :
- Configuration du projet GCP
- Activation des APIs
- Création du service account
- Configuration Firebase
- Configuration Microsoft OAuth
- Variables d'environnement

3. **Déployer l'infrastructure avec Terraform**

```bash
cd terraform

# Créer terraform.tfvars avec vos valeurs
cp terraform.tfvars.example terraform.tfvars

# Initialiser et appliquer
terraform init
terraform apply
```

4. **Lancer l'application localement**

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec vos valeurs (voir CONFIGURATION.md)

# Lancer avec Docker Compose
docker-compose up --build

# L'application sera disponible sur :
# - Backend: http://localhost:8080
# - Frontend: http://localhost:3000
```

## 📚 Documentation

- **[CONFIGURATION.md](./CONFIGURATION.md)** - Guide complet de configuration (clés, secrets, tokens)
- **[terraform/](./terraform/)** - Infrastructure as Code
- **[app/backend/](./app/backend/)** - Documentation de l'API backend
- **[app/frontend/](./app/frontend/)** - Documentation du frontend

## 🗂️ Structure du projet

```
.
├── app/
│   ├── backend/              # API FastAPI
│   │   ├── core/            # Configuration et auth
│   │   ├── models/          # Modèles Pydantic
│   │   ├── services/        # Services GCP
│   │   ├── routes/          # Routes API (via main.py)
│   │   └── main.py          # Application principale
│   └── frontend/            # Application React
│       ├── src/
│       │   ├── components/  # Composants React
│       │   ├── pages/       # Pages
│       │   └── services/    # Services API
│       └── Dockerfile
├── terraform/               # Infrastructure Terraform
│   ├── modules/            # Modules réutilisables
│   │   ├── storage/        # Cloud Storage
│   │   ├── firestore/      # Firestore
│   │   ├── cloudrun/       # Cloud Run
│   │   ├── identity/       # Identity Platform
│   │   └── vertexai/       # Vertex AI
│   └── main.tf             # Configuration principale
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD GitHub Actions
├── docker-compose.yml      # Développement local
├── CONFIGURATION.md        # Guide de configuration
└── README.md              # Ce fichier
```

## 🔧 Utilisation

### 1. Connexion

1. Accédez à l'application
2. Cliquez sur "Sign in with Microsoft"
3. Authentifiez-vous avec votre compte Microsoft
4. Le premier utilisateur devient automatiquement administrateur

### 2. Créer un agent (Admin uniquement)

1. Allez dans "Agents"
2. Cliquez sur "Nouvel Agent"
3. Entrez un nom et une description
4. L'agent sera créé avec :
   - Un bucket Cloud Storage dédié
   - Un corpus Vertex AI RAG
   - Un Data Store pour la recherche

### 3. Uploader des documents (Admin uniquement)

1. Sélectionnez un agent
2. Cliquez sur "Documents"
3. Uploadez vos fichiers (PDF, DOCX, TXT, MD, HTML, CSV)
4. Les documents seront automatiquement :
   - Stockés dans Cloud Storage
   - Indexés par Vertex AI
   - Disponibles pour le RAG

### 4. Chatter avec vos documents

1. Sélectionnez un agent
2. Posez vos questions
3. Recevez des réponses avec citations et sources
4. Explorez le processus de réflexion (retrieval contexts)

## 🔐 Sécurité

- ✅ Authentification via Firebase + Microsoft SSO
- ✅ Contrôle d'accès basé sur les rôles (RBAC)
- ✅ Tokens JWT pour les API
- ✅ Isolation multi-tenant (buckets et corpus dédiés)
- ✅ Secrets gérés par Secret Manager
- ✅ HTTPS obligatoire en production

**⚠️ Important** : Ne commitez jamais :
- `service-account.json`
- `.env`
- `terraform.tfvars`

Ces fichiers sont déjà dans `.gitignore`.

## 💰 Estimation des coûts

Les coûts dépendent de votre utilisation. Composants principaux :

- **Vertex AI** : Pay-per-use (tokens, embeddings)
- **Cloud Run** : Pay-per-request + temps CPU
- **Cloud Storage** : Stockage + opérations
- **Firestore** : Lectures/écritures + stockage
- **Vertex AI Search** : Recherches + indexation

Pour optimiser les coûts :
- Utilisez des quotas et limites
- Configurez l'autoscaling de Cloud Run (min=0 en dev)
- Nettoyez régulièrement les anciens documents

## 🚀 Déploiement en production

### Avec GitHub Actions

1. Configurez les secrets GitHub :
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY` (contenu du service-account.json)

2. Push sur `main` déclenchera automatiquement :
   - Tests
   - Build des images Docker
   - Push vers GCR
   - Déploiement sur Cloud Run

### Manuellement

```bash
# Backend
cd app/backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-backend
gcloud run deploy rag-backend --image gcr.io/$PROJECT_ID/rag-backend --region europe-west1

# Frontend
cd app/frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-frontend
gcloud run deploy rag-frontend --image gcr.io/$PROJECT_ID/rag-frontend --region europe-west1
```

## 🧪 Tests

```bash
# Backend
cd app/backend
pip install pytest pytest-asyncio
pytest tests/

# Frontend
cd app/frontend
npm test
```

## 🛠️ Technologies utilisées

### Backend
- FastAPI
- Google Cloud Platform SDK
- Firebase Admin SDK
- Vertex AI SDK
- Pydantic

### Frontend
- React
- TypeScript
- Vite
- Firebase SDK
- Material-UI / Tailwind CSS

### Infrastructure
- Terraform
- Docker
- GitHub Actions
- Cloud Run
- Cloud Storage
- Firestore
- Vertex AI

## 📖 API Documentation

Une fois l'application déployée, accédez à la documentation interactive :

- Swagger UI : `http://your-backend-url/docs`
- ReDoc : `http://your-backend-url/redoc`

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.

## 🆘 Support

- 📧 Email : support@example.com
- 💬 Issues : [GitHub Issues](https://github.com/votre-repo/issues)
- 📚 Documentation : [CONFIGURATION.md](./CONFIGURATION.md)

## 🙏 Remerciements

Basé sur l'architecture de [azure-search-openai-demo](https://github.com/Azure-Samples/azure-search-openai-demo), adapté pour Google Cloud Platform.

---

**Développé avec ❤️ pour l'écosystème Google Cloud**
