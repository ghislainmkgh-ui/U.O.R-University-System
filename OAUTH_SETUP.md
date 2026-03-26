# Configuration OAuth — Connexion Google & GitHub

Ce guide explique comment activer les boutons de connexion Google et GitHub sur la page de login.

---

## Variables d'environnement requises

Ajoutez ces variables dans votre fichier `.env` à la racine du projet :

```env
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=votre_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=votre_client_secret

# GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=votre_client_id
GITHUB_OAUTH_CLIENT_SECRET=votre_client_secret
```

---

## Google OAuth — Étapes

1. Allez sur [console.cloud.google.com](https://console.cloud.google.com)
2. Créez un projet ou sélectionnez-en un existant
3. Activez l'API **Google Identity** (OAuth 2.0)
4. Allez dans **APIs & Services > Credentials**
5. Cliquez **Create Credentials > OAuth 2.0 Client ID**
6. Type d'application : **Desktop application**
7. Dans **Authorized redirect URIs**, ajoutez : `http://127.0.0.1` (le port est sélectionné automatiquement)
8. Copiez le **Client ID** et le **Client Secret** dans `.env`

---

## GitHub OAuth — Étapes

1. Allez sur [github.com/settings/developers](https://github.com/settings/developers)
2. Cliquez **New OAuth App**
3. Remplissez :
   - **Application name** : UOR University System
   - **Homepage URL** : `http://localhost`
   - **Authorization callback URL** : `http://127.0.0.1`
4. Cliquez **Register application**
5. Générez un **Client Secret** et copiez les deux dans `.env`

---

## Fonctionnement

- Quand l'utilisateur clique sur l'icône Google ou GitHub, le navigateur s'ouvre sur la page d'autorisation du fournisseur
- Un serveur HTTP local temporaire capte le callback avec le code d'autorisation
- L'email vérifié est extrait et comparé aux comptes existants dans la base de données
- Si un compte est trouvé, l'utilisateur est connecté automatiquement
- Si aucun compte ne correspond, un message l'en informe

> **Note** : Le flux OAuth ne crée pas de nouveau compte. Un compte administrateur ou étudiant avec le même email doit déjà exister dans le système.

---

## Dépendances Python requises

```txt
requests>=2.28.0
python-dotenv>=1.0.0
```

Vérifiez qu'elles sont présentes dans `requirements.txt` et installez-les si nécessaire :

```bash
pip install requests python-dotenv
```
