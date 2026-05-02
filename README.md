# Système de Gestion Universitaire — U.O.R

Système logiciel complet pour la gestion des étudiants, des finances et du contrôle d'accès de l'Université Officielle de Ruwenzori (U.O.R).

---

## 🛠️ Architecture

```
U.O.R-University-System/
├── config/                 # Configuration centralisée
├── core/                  # Couche fondamentale
│   ├── security/         # Chiffrement, hachage, validation
│   ├── database/         # Gestion des connexions DB
│   └── models/           # Entités métier
├── app/services/         # Couches métier
│   ├── auth/            # Authentification + reconnaissance faciale
│   ├── student/         # Gestion étudiants
│   ├── finance/         # Gestion financière
│   ├── access/          # Contrôle d'accès (logique principale)
│   └── integration/     # Services externes (email, WhatsApp)
├── ui/                   # Interface utilisateur
│   ├── theme/           # Thèmes (clair/sombre)
│   ├── i18n/            # Traductions (FR/EN)
│   ├── components/      # Widgets réutilisables
│   └── screens/         # Écrans (login, admin, terminal)
├── tests/               # Tests unitaires
├── logs/                # Fichiers de logs
└── main.py              # Point d'entrée
```

---

## 🚀 Installation

### 1. Prérequis
- Python 3.10+
- MySQL 5.7+
- Git

### 2. Cloner le projet
```bash
git clone https://github.com/ghislainmkgh-ui/U.O.R-University-System.git
cd U.O.R-University-System
```

### 3. Créer l'environnement virtuel
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Configurer la base de données
- Créer une base MySQL `uor_university`
- Importer le schéma : `mysql -u root -p uor_university < database/schema.sql`

### 6. Configurer l'environnement
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 7. Lancer l'application
```bash
python main.py
```

---

## 📚 Utilisation

### Connexion Admin
```
Username: admin
Password: admin123
```

### Structure des Étudiants
Les étudiants sont organisés de manière hiérarchique :
```
Faculté de Science
└── Département Informatique
    └── Promotion L1 (2024)
        ├── Étudiant 1 : JOHN DOE
        ├── Étudiant 2 : JANE SMITH
        └── Étudiant 3 : BOB WILLIAMS
```

---

## 🔑 Fonctionnalités Clés

### 1. Gestion des Étudiants
- ✅ Inscription avec génération de mot de passe unique
- ✅ Enregistrement du visage
- ✅ Désactivation de compte
- ✅ Transfert de dossier vers autre université

### 2. Gestion Financière
- ✅ Suivi des paiements
- ✅ Vérification du seuil automatique
- ✅ Notifications par email/WhatsApp
- ✅ Rapports financiers détaillés

### 3. Contrôle d'Accès
- ✅ Vérification multi-facteur (password + face + finance)
- ✅ Logs d'accès détaillés
- ✅ Refus automatique ou accordé
- ✅ Notifications en cas de tentative échouée

### 4. Rapports et Analytics
- ✅ Nombre d'étudiants éligibles/non éligibles
- ✅ Tentatives d'accès (réussies/échouées)
- ✅ Fraudes détectées
- ✅ Graphiques de tendances

---

## 🔒 Sécurité

### Meilleures Pratiques
✅ **Authentification** : Bcrypt 12 rounds  
✅ **Validation** : Toutes les entrées validées  
✅ **Injection SQL** : Requêtes paramétrées  
✅ **Logging** : Tous les accès enregistrés  
✅ **Chiffrement** : Connexions sécurisées DB  
✅ **CORS** : Contrôle d'accès cross-origin  

### Mots de Passe
- Minimum **6 chiffres**
- Générés **aléatoirement** pour chaque étudiant
- **Jamais** deux étudiants avec le même
- Hachés avec **bcrypt** en base de données

---

## 📝 Développement

### Ajouter une Nouvelle Feature

1. **Créer un service**
```python
# app/services/mon_service/mon_service.py
class MonService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def ma_methode(self):
        pass
```

2. **Créer un écran UI**
```python
# ui/screens/mon_ecran.py
class MonEcran(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._create_ui()
```

3. **Ajouter des traductions**
```python
# ui/i18n/translator.py
TRANSLATIONS["FR"]["nouvelle_cle"] = "Nouvelle valeur"
```

4. **Faire un commit**
```bash
git add .
git commit -m "feat: Description de la feature"
git push origin main
```

---

## 📞 Support et Contact

**Université Officielle de Ruwenzori (U.O.R)**  
Email: admin@uor.uni  
Téléphone: +243 XXX XXX XXX

---

## 📄 License

Propriétaire © 2026 U.O.R. Tous droits réservés.

---

## 🙏 Remerciements

Merci à tous les contributeurs et à l'équipe de développement U.O.R.
