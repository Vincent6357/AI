# ✅ Ce qui est DÉJÀ FAIT

- ✅ Service Account GCP configuré (`ia-babymoov@babymoov-ia-479412.iam.gserviceaccount.com`)
- ✅ Credentials sauvegardées dans `credentials/service-account.json`
- ✅ Projet GCP : `babymoov-ia-479412`
- ✅ Région configurée : `europe-west9`
- ✅ Modèle Vertex AI : `gemini-2.0-flash-001`
- ✅ Infrastructure Terraform prête
- ✅ Backend FastAPI complet
- ✅ Dockerfiles et docker-compose configurés

---

# 🚀 CE QU'IL VOUS RESTE À FAIRE (3 étapes principales)

## ÉTAPE 1 : Activer les APIs GCP (5 minutes)

Certaines APIs doivent être activées dans votre projet GCP :

```bash
# Connexion à GCP
gcloud auth login
gcloud config set project babymoov-ia-479412

# Activer toutes les APIs nécessaires
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

**⏱️ Temps estimé** : 2-5 minutes

---

## ÉTAPE 2 : Configurer Firebase Authentication (15 minutes)

### 2.1. Créer/Associer le projet Firebase

1. Allez sur https://console.firebase.google.com/
2. Cliquez sur "Ajouter un projet"
3. **Sélectionnez votre projet existant** : `babymoov-ia-479412`
4. Confirmez le plan de facturation
5. Désactivez Google Analytics (optionnel)
6. Cliquez sur "Continuer"

### 2.2. Activer Authentication

1. Dans Firebase Console, allez dans **Authentication**
2. Cliquez sur **Commencer**
3. Allez dans l'onglet **Sign-in method**
4. Activez **Email/Password** (cliquez sur Email/Password > Activé > Enregistrer)

### 2.3. Récupérer les clés Firebase

1. Cliquez sur l'icône **⚙️ Paramètres** (en haut à gauche)
2. Sélectionnez **Paramètres du projet**
3. Descendez jusqu'à **Vos applications**
4. Cliquez sur **</>** (icône Web)
5. Nom de l'app : `Babymoov RAG App`
6. Cliquez sur **Enregistrer l'application**
7. **COPIEZ TOUTES LES VALEURS** affichées :

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",              // ← COPIEZ CETTE VALEUR
  authDomain: "babymoov-ia-479412.firebaseapp.com",
  projectId: "babymoov-ia-479412",
  storageBucket: "babymoov-ia-479412.appspot.com",
  messagingSenderId: "123456789012", // ← COPIEZ CETTE VALEUR
  appId: "1:123456789012:web:..."    // ← COPIEZ CETTE VALEUR
};
```

### 2.4. Mettre à jour votre fichier `.env`

Ouvrez le fichier `.env` et remplacez les valeurs Firebase :

```bash
# Firebase Configuration
FIREBASE_API_KEY=AIzaSy...  # ← Collez apiKey ici
FIREBASE_AUTH_DOMAIN=babymoov-ia-479412.firebaseapp.com  # ← Déjà configuré
FIREBASE_PROJECT_ID=babymoov-ia-479412  # ← Déjà configuré
FIREBASE_STORAGE_BUCKET=babymoov-ia-479412.appspot.com  # ← Déjà configuré
FIREBASE_MESSAGING_SENDER_ID=123456789012  # ← Collez messagingSenderId ici
FIREBASE_APP_ID=1:123456789012:web:...  # ← Collez appId ici
```

**⏱️ Temps estimé** : 10-15 minutes

---

## ÉTAPE 3 : Configurer Microsoft OAuth/SSO (20 minutes)

### 3.1. Créer une App Registration dans Azure AD

1. Allez sur https://portal.azure.com/
2. Cherchez **Azure Active Directory** dans la barre de recherche
3. Cliquez sur **App registrations** (dans le menu de gauche)
4. Cliquez sur **+ New registration**
5. Remplissez le formulaire :
   - **Name** : `Babymoov RAG Authentication`
   - **Supported account types** : Sélectionnez `Accounts in this organizational directory only`
   - **Redirect URI** :
     - Type : `Web`
     - URI : `https://babymoov-ia-479412.firebaseapp.com/__/auth/handler`
   - Cliquez sur **Register**

### 3.2. Récupérer les identifiants

Sur la page Overview de votre App Registration, **NOTEZ** :

- **Application (client) ID** : `12345678-abcd-...` ← IMPORTANT
- **Directory (tenant) ID** : `87654321-dcba-...` ← IMPORTANT

### 3.3. Créer un Client Secret

1. Dans le menu de gauche, cliquez sur **Certificates & secrets**
2. Onglet **Client secrets**, cliquez sur **+ New client secret**
3. Description : `Firebase Integration`
4. Expires : `24 months`
5. Cliquez sur **Add**
6. **⚠️ COPIEZ IMMÉDIATEMENT LA VALUE** (colonne "Value", pas "Secret ID")
   - Cette valeur ne sera plus visible après !

### 3.4. Configurer les permissions API

1. Dans le menu de gauche, cliquez sur **API permissions**
2. Cliquez sur **+ Add a permission**
3. Sélectionnez **Microsoft Graph**
4. Sélectionnez **Delegated permissions**
5. Cochez :
   - `openid`
   - `profile`
   - `email`
   - `User.Read`
6. Cliquez sur **Add permissions**
7. Cliquez sur **✓ Grant admin consent for [Your Organization]**
8. Confirmez en cliquant sur **Yes**

### 3.5. Ajouter Microsoft comme provider dans Firebase

1. Retournez dans **Firebase Console** > **Authentication** > **Sign-in method**
2. Cliquez sur **Add new provider**
3. Sélectionnez **Microsoft**
4. Cliquez sur **Enable**
5. Entrez :
   - **Web SDK configuration**
     - **Application (client) ID** : collez la valeur de l'étape 3.2
     - **Application (client) secret** : collez la Value du secret de l'étape 3.3
   - **OpenID Connect configuration** (optionnel)
     - Laissez vide ou utilisez `common` pour multi-tenant
6. **COPIEZ** l'URL de redirection fournie par Firebase (en bas)
   - Ex : `https://babymoov-ia-479412.firebaseapp.com/__/auth/handler`
7. Cliquez sur **Save**

### 3.6. Ajouter l'URL de redirection Firebase dans Azure AD

1. Retournez dans **Azure Portal** > votre App Registration
2. Cliquez sur **Authentication** (menu de gauche)
3. Sous **Platform configurations** > **Web**, cliquez sur **Add URI**
4. Collez l'URL de redirection Firebase de l'étape 3.5
5. Cliquez sur **Save**

### 3.7. Mettre à jour vos fichiers de configuration

Mettez à jour `.env` :

```bash
# Pas de variables Microsoft dans .env, elles sont dans terraform.tfvars
```

Mettez à jour `terraform/terraform.tfvars` :

```hcl
microsoft_auth_config = {
  client_id     = "12345678-abcd-..."  # ← Collez Application (client) ID
  client_secret = "votre-secret-value"  # ← Collez Client secret VALUE
  tenant_id     = "87654321-dcba-..."   # ← Collez Directory (tenant) ID
}
```

**⏱️ Temps estimé** : 15-20 minutes

---

## ÉTAPE 4 : Déployer l'infrastructure Terraform (10 minutes)

Une fois Firebase et Microsoft OAuth configurés :

```bash
cd terraform

# Vérifier que terraform.tfvars est bien rempli
cat terraform.tfvars

# Créer le bucket pour le state Terraform (une seule fois)
gsutil mb -p babymoov-ia-479412 -l europe-west9 gs://babymoov-ia-479412-terraform-state
gsutil versioning set on gs://babymoov-ia-479412-terraform-state

# Initialiser Terraform
terraform init

# Voir ce qui va être créé
terraform plan

# Créer l'infrastructure
terraform apply
# Tapez "yes" pour confirmer
```

**Ce qui sera créé** :
- Buckets Cloud Storage
- Base de données Firestore
- Configuration Identity Platform
- Services Cloud Run (backend + frontend)
- Permissions IAM

**⏱️ Temps estimé** : 5-10 minutes

---

## ÉTAPE 5 : Tester localement (5 minutes)

```bash
# Retourner à la racine
cd ..

# Vérifier que .env est bien configuré
cat .env

# Lancer avec Docker Compose
docker-compose up --build

# L'application sera disponible sur :
# - Backend: http://localhost:8080
# - Frontend: http://localhost:3000
```

### Tester l'authentification :

1. Ouvrez http://localhost:3000
2. Cliquez sur "Sign in with Microsoft"
3. Connectez-vous avec votre compte Microsoft
4. ✅ Vous devriez être redirigé vers l'application
5. Le premier utilisateur devient automatiquement **Admin**

**⏱️ Temps estimé** : 5 minutes (premier build Docker)

---

## ÉTAPE 6 (Optionnelle) : Déployer en production

### Option A : Déploiement manuel

```bash
# Backend
cd app/backend
gcloud builds submit --tag gcr.io/babymoov-ia-479412/rag-backend --project babymoov-ia-479412
gcloud run deploy rag-backend \
  --image gcr.io/babymoov-ia-479412/rag-backend \
  --region europe-west9 \
  --platform managed \
  --allow-unauthenticated \
  --project babymoov-ia-479412

# Frontend
cd ../frontend
gcloud builds submit --tag gcr.io/babymoov-ia-479412/rag-frontend --project babymoov-ia-479412
gcloud run deploy rag-frontend \
  --image gcr.io/babymoov-ia-479412/rag-frontend \
  --region europe-west9 \
  --platform managed \
  --allow-unauthenticated \
  --project babymoov-ia-479412
```

### Option B : Déploiement avec GitHub Actions

1. Allez dans **GitHub** > votre repository > **Settings** > **Secrets and variables** > **Actions**
2. Ajoutez les secrets :
   - `GCP_PROJECT_ID` = `babymoov-ia-479412`
   - `GCP_SA_KEY` = Copiez TOUT le contenu de `credentials/service-account.json`
3. Push sur la branche `main` → déploiement automatique !

---

# 📋 CHECKLIST COMPLÈTE

Cochez au fur et à mesure :

- [ ] **ÉTAPE 1** : APIs GCP activées
- [ ] **ÉTAPE 2** : Firebase configuré et clés récupérées
  - [ ] Firebase Authentication activé
  - [ ] Clés Firebase dans `.env`
- [ ] **ÉTAPE 3** : Microsoft OAuth configuré
  - [ ] App Registration créée dans Azure AD
  - [ ] Client Secret créé et copié
  - [ ] Permissions API configurées
  - [ ] Microsoft provider ajouté dans Firebase
  - [ ] Credentials dans `terraform.tfvars`
- [ ] **ÉTAPE 4** : Infrastructure Terraform déployée
  - [ ] `terraform init` réussi
  - [ ] `terraform apply` réussi
- [ ] **ÉTAPE 5** : Test local avec Docker Compose
  - [ ] Backend démarre sur :8080
  - [ ] Frontend démarre sur :3000
  - [ ] Authentification Microsoft fonctionne
- [ ] **ÉTAPE 6** (Optionnel) : Déploiement en production

---

# ⏱️ TEMPS TOTAL ESTIMÉ

- **Configuration minimale** (étapes 1-3) : ~40-50 minutes
- **Déploiement et test** (étapes 4-5) : ~15-20 minutes
- **TOTAL** : **1h à 1h30**

---

# 🆘 En cas de problème

## Erreur "Permission denied"

```bash
# Vérifier les permissions du service account
gcloud projects get-iam-policy babymoov-ia-479412 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:ia-babymoov*"

# Ajouter les permissions manquantes
gcloud projects add-iam-policy-binding babymoov-ia-479412 \
  --member="serviceAccount:ia-babymoov@babymoov-ia-479412.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## Firebase Authentication ne fonctionne pas

1. Vérifiez que le domaine est autorisé :
   - Firebase Console > Authentication > Settings > Authorized domains
   - Ajoutez `localhost` pour le développement
2. Vérifiez que les clés dans `.env` sont correctes

## Microsoft OAuth échoue

1. Vérifiez que l'URL de redirection Firebase est bien dans Azure AD
2. Vérifiez que les permissions API ont été "granted"
3. Vérifiez que le Client Secret n'a pas expiré

---

# 📚 Ressources utiles

- **Configuration complète** : Voir [CONFIGURATION.md](./CONFIGURATION.md)
- **Documentation Vertex AI** : https://cloud.google.com/vertex-ai/docs
- **Documentation Firebase** : https://firebase.google.com/docs
- **Logs Cloud Run** : `gcloud run services logs read rag-backend --region=europe-west9`

---

**🎯 Suivez ces étapes dans l'ordre et vous aurez votre application RAG opérationnelle !**
