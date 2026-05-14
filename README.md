# U.O.R University System — Web Migration

> ⚠️ Note importante : ce dépôt contient le développement Web moderne dans `Web_app_migration`.
> Les anciens fichiers Arduino / ESP32 CAM / desktop sont conservés uniquement à des fins de documentation historique.
> Ils ne constituent pas la base du travail Web actuel.

Le projet Web moderne est en cours dans `Web_app_migration`.

Un système de contrôle d'accès porte sécurisé utilisant une architecture distribuée ESP32 Cam + Arduino Uno avec authentification par mot de passe + reconnaissance faciale.

## 🏗️ Architecture

### ESP32 Cam (Cœur Intelligent)
- **Caméra OV2640** intégrée pour capture d'images
- **Reconnaissance faciale** en temps réel avec TensorFlow Lite
- **Logique principale** d'authentification
- **Communication maître** avec Arduino via UART

### Arduino Uno (Interface Utilisateur)
- **Écran LCD 16x2** pour retours utilisateur
- **Clavier matriciel 4x4** pour saisie mot de passe
- **Servo moteur** pour contrôle verrouillage porte
- **Communication esclave** répondant aux commandes ESP32

### Communication Inter-Cartes
- **Protocole UART** (9600 bauds)
- **Commandes textuelles** synchronisées
- **Fiabilité temps réel** pour interface utilisateur

## 📁 Structure du Projet

```
├── esp32_door_access.py          # Code principal ESP32 (MicroPython)
├── arduino_door_access.ino       # Code Arduino (C++)
├── test_door_access_simulation.py # Simulation PC
├── HARDWARE_ASSEMBLY_GUIDE.md    # Guide assemblage matériel
├── ESP32_DEPLOYMENT_GUIDE.md     # Guide déploiement
├── DOOR_ACCESS_SYSTEM_SUMMARY.md  # Résumé technique
└── README.md                      # Ce fichier
```

## 🔧 Matériel Requis

### Composants Principaux
- ESP32 Cam module
- Arduino Uno
- Servo moteur SG90
- Clavier matriciel HX-543 4x4
- Écran LCD 16x2 (sans I2C)
- Breadboard et fils de connexion

### Alimentation
- 5V pour ESP32 (alimentation séparée recommandée)
- 5V pour Arduino (via USB ou adaptateur)
- Potentiomètre 10KΩ (contraste LCD)
- Résistance 220Ω (rétroéclairage LCD)

## 🚀 Démarrage Rapide

### 1. Assemblage Matériel
Suivre `HARDWARE_ASSEMBLY_GUIDE.md` pour connexions détaillées.

### 2. Programmation Arduino
1. Ouvrir `arduino_door_access.ino` dans Arduino IDE
2. Sélectionner "Arduino Uno" et port COM
3. Téléverser le code

### 3. Programmation ESP32
1. Flasher MicroPython sur ESP32
2. Télécharger `esp32_door_access.py` comme `main.py`
3. Télécharger bibliothèques caméra et reconnaissance faciale

### 4. Test du Système
Exécuter `test_door_access_simulation.py` pour validation.

## 🔐 Fonctionnalités Sécurité

### Authentification Multi-Facteurs
1. **Mot de passe PIN** (4 chiffres) via clavier
2. **Reconnaissance faciale** via caméra ESP32
3. **Validation croisée** entre les deux cartes

### Mesures Anti-Tampering
- Détection visages multiples
- Fermeture automatique porte (5 secondes)
- États sécurisés distribués
- Communication chiffrée optionnelle

## 🧪 Tests et Validation

### Simulation PC
```bash
python test_door_access_simulation.py
```

### Tests Matériel
1. Test composants individuels (LCD, clavier, servo, caméra)
2. Test communication série ESP32 ↔ Arduino
3. Test flux d'authentification complet
4. Test scénarios sécurité (mauvais mot de passe, visage inconnu)

## 📊 Performances

### Temps de Réponse
- Saisie clavier : <100ms
- Capture caméra : ~500ms
- Reconnaissance faciale : 2-3 secondes
- Ouverture porte : <1 seconde

### Consommation Énergie
- ESP32 (caméra active) : ~150mA
- Arduino (périphériques) : ~50mA
- Servo (mouvement) : 100-250mA
- **Total pic** : ~500mA

## 🔧 Dépannage

### Problèmes Courants
- **Communication série** : Vérifier connexions RX/TX et GND
- **LCD ne s'affiche pas** : Ajuster contraste, vérifier connexions
- **Servo ne bouge pas** : Vérifier alimentation et broches
- **Reconnaissance faciale échoue** : Vérifier éclairage et angle caméra

### Debug Mode
Activer prints de debug dans les deux codes pour diagnostiquer.

## 🚀 Améliorations Futures

### Fonctionnalités
- Support cartes RFID/NFC
- Surveillance à distance (MQTT)
- Restrictions horaires d'accès
- Base de données utilisateurs centralisée

### Optimisations
- TensorFlow Lite optimisé
- Mise en cache visages
- Mode veille basse consommation
- Interface web de configuration

## 📝 Licence

Ce projet est open source. Utilisez et modifiez selon vos besoins.

## 🤝 Contribution

Contributions bienvenues ! Ouvrez une issue pour suggestions ou bugs.

---

**Note** : Ce système est conçu pour usage éducatif et démonstration. Pour déploiement production, ajouter mesures sécurité supplémentaires (chiffrement, authentification forte, etc.).
- **Tests** : Structure prête pour les tests unitaires

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
│   └── integration/     # Services externes (email, WhatsApp, Arduino)
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
