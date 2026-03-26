# Guide de Déploiement Système Accès Porte ESP32 Cam + Arduino Uno

## Vue d'ensemble
Ce système fournit un contrôle d'accès porte sécurisé utilisant une architecture distribuée :
- **ESP32 Cam** : Caméra, reconnaissance faciale, logique principale
- **Arduino Uno** : LCD, clavier matriciel, servo moteur
- **Communication** : Liaison série UART entre les deux cartes

## Prérequis Matériels
- Module ESP32 Cam
- Carte Arduino Uno
- Servo moteur (SG90 ou similaire)
- Clavier matriciel HX-543 4x4
- Écran LCD 16x2 (connexion directe GPIO, pas I2C)
- Alimentation 5V pour ESP32 et Arduino
- Potentiomètre 10KΩ (pour contraste LCD)
- Résistance 220Ω (pour rétroéclairage LCD)
- Fils de connexion et breadboard

## Architecture du Système

### ESP32 Cam - Rôles et Responsabilités
- Capture d'images caméra
- Traitement reconnaissance faciale
- Logique principale d'authentification
- Communication avec Arduino via UART
- Gestion des états du système

### Arduino Uno - Rôles et Responsabilités
- Affichage LCD
- Lecture clavier matriciel
- Contrôle servo moteur
- Réception commandes ESP32
- Gestion interface utilisateur locale

## Connexions Matérielles

### Broches ESP32 Cam
```
GPIO 3 (U0R): RX (réception série Arduino)
GPIO 1 (U0T): TX (transmission série Arduino)
```

### Broches Arduino Uno
```
Broche 0 (RX): Réception série ESP32
Broche 1 (TX): Transmission série ESP32
Broche 2: LCD D7
Broche 3: LCD D6
Broche 4: LCD D5
Broche 5: LCD D4
Broche 6: Clavier Ligne 4
Broche 7: Clavier Ligne 3
Broche 8: Clavier Ligne 2
Broche 9: Clavier Ligne 1
Broche 10: Clavier Colonne 2
Broche 11: LCD EN
Broche 12: LCD RS
Broche 13: Clavier Colonne 1
Broche A0: Clavier Colonne 3
Broche A1: Clavier Colonne 4
Broche A2: Signal Servo
```

### Connexion Série ESP32 ↔ Arduino
```
ESP32 GPIO 1 (U0T, TX) → Arduino Broche 0 (RX)
ESP32 GPIO 3 (U0R, RX) → Arduino Broche 1 (TX)
GND commun entre les deux cartes
```

## Installation Logicielle

### 1. Installation Arduino IDE
1. Télécharger Arduino IDE depuis https://www.arduino.cc/
2. Installer l'IDE Arduino
3. Ouvrir l'IDE et vérifier l'installation

### 2. Téléchargement Code Arduino
1. Ouvrir `arduino_door_access.ino` dans Arduino IDE
2. Sélectionner "Arduino Uno" comme carte (Outils > Type de carte)
3. Sélectionner le port COM correct (Outils > Port)
4. Téléverser le code sur Arduino (bouton →)

### 3. Installation MicroPython sur ESP32
```bash
# Utiliser esptool pour flasher le firmware MicroPython
pip install esptool
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 --baud 460800 write_flash -z 0x1000 esp32-20220117-v1.18.bin
```

### 4. Bibliothèques ESP32 Requises
Télécharger ces bibliothèques sur ESP32 :
- `esp32cam.py` - Contrôle caméra
- `face_recognition.py` - Reconnaissance faciale

### 5. Téléchargement Code ESP32
Télécharger `esp32_door_access.py` sur ESP32 et renommer en `main.py`.

### 6. Synchronisation des Cartes
1. Alimenter Arduino en premier
2. Attendre que Arduino affiche "Systeme Pret" sur LCD
3. Alimenter ESP32
4. Vérifier communication série établie

## Configuration

### Configuration Arduino
Le code Arduino (`arduino_door_access.ino`) contient :
- Mot de passe par défaut : "1234"
- Broches LCD et clavier préconfigurées
- Paramètres servo moteur

**Modification mot de passe Arduino :**
```cpp
const String correct_password = "1234";  // Changer pour votre mot de passe
```

### Configuration ESP32
Le code ESP32 (`esp32_door_access.py`) gère :
- Communication série avec Arduino
- Reconnaissance faciale
- Logique d'authentification

**Configuration liaison série ESP32 :**
```python
ARDUINO_UART = UART(0, baudrate=9600, tx=1, rx=3)  # GPIO 1=TX (U0T), GPIO 3=RX (U0R)
```

### Entraînement Reconnaissance Faciale
1. Capturer images visages autorisés sur ESP32
2. Générer encodages visages
3. Stocker dans base de données ESP32

## Fonctionnalités Sécurité

### Authentification Multi-Facteurs
1. **Saisie mot de passe** : Via clavier Arduino (PIN 4 chiffres)
2. **Vérification reconnaissance faciale** : Via caméra ESP32
3. **Flux d'authentification séquentiel** : Mot de passe d'abord, puis visage

### Mesures Anti-Tampering
- **Détection visages multiples** : Bloque accès si plusieurs visages
- **Fermeture automatique porte** : Après 5 secondes d'accès autorisé
- **Contrôle accès basé sur états** : Machine à états distribuée
- **Communication sécurisée** : Liaison série dédiée entre cartes

### Architecture Distribuée Avantages
- **Stabilité accrue** : Séparation des tâches critiques
- **Performance améliorée** : ESP32 dédié à l'IA, Arduino aux E/S
- **Maintenance facilitée** : Composants modulaires
- **Évolutivité** : Possibilité d'ajouter fonctionnalités indépendamment

### Mesures Anti-Tampering
- Détection visages multiples bloque accès
- Fermeture automatique porte après entrée
- Contrôle accès basé sur états

## Test

### Test Simulation
Exécuter `test_door_access_simulation.py` sur PC pour valider logique distribuée.

### Étapes Test Matériel

#### Tests Arduino
1. **Test LCD** : Vérifier affichage "Systeme Pret"
2. **Test clavier** : Appuyer touches, vérifier affichage sur LCD
3. **Test servo** : Vérifier mouvement à l'ouverture porte

#### Tests ESP32
1. **Test caméra** : Vérifier capture image fonctionnelle
2. **Test communication série** : Vérifier envoi/réception avec Arduino

#### Tests Intégrés
1. **Test authentification mot de passe** : Saisir "1234", vérifier transmission à ESP32
2. **Test reconnaissance faciale** : Après mot de passe OK, vérifier processus caméra
3. **Test ouverture porte** : Vérifier servo actionné après authentification complète
4. **Test sécurité** : Essayer accès avec mauvais mot de passe ou visage inconnu

## Dépannage

### Problèmes Courants
1. **Servo ne bouge pas**: Vérifier alimentation et fréquence PWM
2. **LCD ne s'affiche pas**: Vérifier connexions GPIO et ajuster contraste
3. **Clavier ne répond pas**: Vérifier connexions lignes/colonnes
4. **Caméra ne fonctionne pas**: Assurer caméra bien assise
5. **Reconnaissance faciale échoue**: Vérifier éclairage et angle

### Mode Debug
Activer prints debug en décommentant instructions print.

## Optimisation Performance
- Utiliser TensorFlow Lite pour reconnaissance faciale efficace
- Implémenter mise en cache détection visage
- Optimiser paramètres traitement image
- Utiliser entrées interrupt pour clavier

## Maintenance
- Mettre à jour régulièrement base données visages
- Vérifier étalonnage servo moteur
- Surveiller logs système pour anomalies

## Améliorations Futures
- Ajouter support RFID/NFC
- Implémenter surveillance à distance via MQTT
- Ajouter restrictions accès temporelles
- Intégrer système contrôle accès centralisé