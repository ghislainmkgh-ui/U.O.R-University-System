# Comment obtenir un token d'accès

1. Demandez à l’équipe U.O.R votre `university_code` et votre `api_key` (identifiants fournis lors de l’intégration).
2. Faites une requête HTTP POST vers l’endpoint suivant :

```
POST https://votre-api.com/api/v1/auth/token
Content-Type: application/json

{
  "university_code": "VOTRE_CODE",
  "api_key": "VOTRE_API_KEY"
}
```

3. La réponse contiendra un token JWT à utiliser dans le header `Authorization` pour toutes les requêtes protégées :

```
Authorization: Bearer <token>
```

Remplacez `https://votre-api.com` par l’URL réelle de l’API qui vous sera communiquée par U.O.R (exemple : https://api.uor-university.com).
# Documentation à fournir aux partenaires

## Présentation
Cette API permet aux universités partenaires d’effectuer des transferts d’étudiants de façon sécurisée et standardisée avec l’U.O.R.

## Authentification
Toutes les requêtes (sauf `/api/v1/health` et `/api/v1/auth/token`) nécessitent un token JWT dans le header :

```
Authorization: Bearer <token>
```
Pour obtenir un token :
- **POST** `/api/v1/auth/token`
  - Corps : `{ "university_code": "...", "api_key": "..." }`
  - Réponse : `{ "token": "...", "expires_in": 86400, ... }`

## Endpoints principaux

- **POST** `/api/v1/transfer/receive`  
  Reçoit un package de transfert d’une université partenaire.
  - Corps attendu :
    ```json
    {
      "transfer_metadata": { ... },
      "student_info": { ... },
      "academic_records": { ... },
      "documents": { ... },
      "academic_profile": { ... }
    }
    ```
  - Réponse succès :
    ```json
    { "success": true, "request_code": "REQ-...", "message": "Transfer request received and pending review", "status": "PENDING_REVIEW" }
    ```

- **POST** `/api/v1/transfer/send`  
  Prépare un package de transfert pour un étudiant donné.
  - Corps attendu :
    ```json
    { "student_id": 123, "destination_university_code": "UNIKIN" }
    ```
  - Réponse succès :
    ```json
    { "success": true, "transfer_code": "...", "package": { ... } }
    ```

- **GET** `/api/v1/transfer/status/<transfer_code>`  
  Récupère le statut d’un transfert.
  - Réponse exemple :
    ```json
    { "success": true, "transfer_code": "...", "status": "PENDING" }
    ```

- **GET** `/api/v1/universities`  
  Liste les universités partenaires.
  - Réponse exemple :
    ```json
    { "success": true, "count": 2, "universities": [ { "university_name": "...", ... } ] }
    ```

- **GET** `/api/v1/health`  
  Vérifie la santé de l’API.

## Exemple d’appel (curl)

```bash
# Obtenir un token
curl -X POST https://votre-api.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{ "university_code": "UOR", "api_key": "votre_cle" }'

# Envoyer un transfert
curl -X POST https://votre-api.com/api/v1/transfer/receive \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "transfer_metadata": { ... }, ... }'
```

## Bonnes pratiques
- Utilisez toujours HTTPS.
- Protégez votre clé API et votre token.
- Contactez l’équipe U.O.R pour toute question d’intégration.
# Schéma d'architecture de l'API

```mermaid
flowchart TD
  Client[Client (Web/App/Postman...)]
  subgraph API Layer
    API[API (transfer_api.py)]
  end
  subgraph Services
    Service1[Services (services/)]
    Core[Core (core/)]
  end
  DB[(Base de données)]
  Config[Configuration (config/)]
  Logs[Logs (logs/)]

  Client -- Requête HTTP --> API
  API -- Appelle fonctions --> Service1
  API -- Utilise --> Config
  API -- Écrit/Lit --> Logs
  Service1 -- Appelle --> Core
  Core -- Requêtes SQL --> DB
  Service1 -- Peut accéder --> DB
```
# U.O.R API de Réception de Transferts Inter-Universitaires

## Endpoint principal

- **POST** `/api/v1/transfer/receive`
  - Reçoit un package de transfert d'une université partenaire.
  - Authentification : Header `Authorization: Bearer <token>` (JWT)
  - Corps attendu (JSON) :
    ```json
    {
      "transfer_metadata": { ... },
      "student_info": { ... },
      "academic_records": { ... },
      "documents": { ... },
      "academic_profile": { ... }
    }
    ```
  - Réponse (succès) :
    ```json
    {
      "success": true,
      "request_code": "REQ-...",
      "message": "Transfer request received and pending review",
      "status": "PENDING_REVIEW"
    }
    ```
  - Réponse (erreur) :
    ```json
    {
      "success": false,
      "error": "..."
    }
    ```

## Authentification
- **POST** `/api/v1/auth/token`
  - Donne un token JWT pour une université partenaire.
  - Corps attendu : `{ "university_code": "...", "api_key": "..." }`

## Autres endpoints
- **GET** `/api/v1/health` : Vérifie la santé de l’API.
- **GET** `/api/v1/transfer/status/<transfer_code>` : Statut d’un transfert.

## Sécurité
- Utilisez toujours HTTPS en production.
- Changez la clé secrète dans la config Flask.

## Contact
Pour toute question, contactez l’équipe technique U.O.R.