# Guide d'Assemblage Matériel Système Accès Porte ESP32 Cam + Arduino Uno

## Vue d'ensemble Architecture
Le système utilise une architecture distribuée pour plus de stabilité et de puissance :
- **ESP32 Cam** : Caméra, reconnaissance faciale, logique principale
- **Arduino Uno** : LCD, clavier matriciel, servo moteur
- **Communication** : Liaison série UART entre les deux cartes

## Liste des Composants
- Module ESP32 Cam
- Carte Arduino Uno
- Servo moteur SG90
- Clavier matriciel HX-543 4x4
- Écran LCD 16x2 (sans module I2C)
- Breadboard et fils de connexion
- Alimentation 5V (pour ESP32 et Arduino)
- Potentiomètre 10KΩ (pour contraste LCD)
- Résistance 220Ω (pour rétroéclairage LCD)
- Mécanisme de verrouillage porte (connecté au servo)

## Schéma de Connexions

### Connexions ESP32 Cam
```
GPIO ESP32 | Fonction
-----------|---------
3 (U0R)     | RX (réception série Arduino)
1 (U0T)     | TX (transmission série Arduino)
GND        | Masse commune
```

### Connexions Arduino Uno
```
Broche Arduino | Composant       | Description
---------------|-----------------|-------------
12             | LCD RS          | Register Select
11             | LCD EN          | Enable
5              | LCD D4          | Data bit 4
4              | LCD D5          | Data bit 5
3              | LCD D6          | Data bit 6
2              | LCD D7          | Data bit 7
9              | Clavier Ligne 1 | Broche ligne 1
8              | Clavier Ligne 2 | Broche ligne 2
7              | Clavier Ligne 3 | Broche ligne 3
6              | Clavier Ligne 4 | Broche ligne 4
13             | Clavier Colonne 1| Broche colonne 1
10             | Clavier Colonne 2| Broche colonne 2
A0             | Clavier Colonne 3| Broche colonne 3
A1             | Clavier Colonne 4| Broche colonne 4
A2             | Signal Servo    | Fil orange
GND            | Masse Commune   | Tous composants
5V             | Alimentation    | LCD, Servo, Clavier
```

### Connexion Série ESP32 ↔ Arduino
```
ESP32 GPIO 1 (U0T, TX) → Arduino Broche 0 (RX)
ESP32 GPIO 3 (U0R, RX) → Arduino Broche 1 (TX)
GND ↔ GND
```

## Assemblage Étape par Étape

### Étape 1: Configuration Arduino Uno
1. Placer Arduino Uno sur breadboard
2. Connecter alimentation Arduino : USB ou alimentation externe 7-12V
3. Téléverser le code `arduino_door_access.ino` sur Arduino
4. Vérifier que Arduino fonctionne (LED L clignote)

### Étape 2: Configuration ESP32 Cam
1. Placer ESP32 Cam sur breadboard séparée
2. Connecter alimentation ESP32 : 5V à VIN, GND à GND
3. **Important** : Alimenter ESP32 séparément d'Arduino pour stabilité
4. Note: ESP32 Cam a caméra intégrée, assurer qu'elle soit bien assise

### Étape 3: Connexion Liaison Série (ESP32 ↔ Arduino)
**Connexion croisée :**
- ESP32 GPIO 1 (U0T, TX) → Arduino broche 0 (RX)
- ESP32 GPIO 3 (U0R, RX) → Arduino broche 1 (TX)
- ESP32 GND → Arduino GND

**Important :** La liaison série utilise les broches RX/TX matérielles d'Arduino (broches 0 et 1). Assurez-vous que ces broches ne sont pas utilisées pour d'autres composants.

### Étape 4: Connexion Écran LCD à Arduino (Mode Direct 4-bit)
**Broches de contrôle :**
- RS (Register Select) → Arduino broche 12
- EN (Enable) → Arduino broche 11
- RW (Read/Write) → GND (toujours en mode écriture)

**Broches de données (4-bit mode) :**
- D4 → Arduino broche 5
- D5 → Arduino broche 4
- D6 → Arduino broche 3
- D7 → Arduino broche 2

**Broches d'alimentation :**
- VDD → 5V (Arduino 5V)
- VSS → GND
- VEE → Potentiomètre 10KΩ pour contraste (connecter à GND via potentiomètre)
- LED+ → 5V via résistance 220Ω (rétroéclairage)
- LED- → GND

### Étape 5: Connexion Clavier HX-543 à Arduino
Le clavier HX-543 a 8 broches : 4 lignes + 4 colonnes

**Broches Lignes (connecter aux broches Arduino) :**
- Broche 1 (Ligne 1) → Arduino broche 9
- Broche 2 (Ligne 2) → Arduino broche 8
- Broche 3 (Ligne 3) → Arduino broche 7
- Broche 4 (Ligne 4) → Arduino broche 6

**Broches Colonnes (connecter aux broches Arduino) :**
- Broche 5 (Colonne 1) → Arduino broche 13
- Broche 6 (Colonne 2) → Arduino broche 10
- Broche 7 (Colonne 3) → Arduino broche A0
- Broche 8 (Colonne 4) → Arduino broche A1

### Étape 6: Connexion Servo Moteur à Arduino
1. Connecter fil signal servo (orange/jaune) à Arduino broche A2
2. Connecter fil alimentation servo (rouge) à 5V Arduino
3. Connecter fil masse servo (marron/noir) à GND Arduino
4. **Important** : Si le servo consomme beaucoup de courant, utiliser alimentation séparée

### Étape 7: Mécanisme de Verrouillage Porte
1. Attacher corne servo au mécanisme de verrouillage porte
2. Positionner servo pour que :
   - Position 0° = Porte verrouillée
   - Position 90° = Porte déverrouillée
3. Tester plage de mouvement servo
4. Sécuriser montage servo

## Considérations Alimentation

### Tensions Requises
- ESP32: 5V
- LCD: 5V
- Servo: 4.8-6V (typiquement 5V)
- Clavier: 3.3-5V

### Courants Requis
- ESP32 (veille): ~80mA
- ESP32 (avec caméra): ~150mA
- LCD: ~20mA
- Servo: 100-250mA (selon charge)
- **Courant total pic**: ~500mA

### Alimentation Recommandée
- Adaptateur 5V, 1A
- Utiliser condensateurs pour stabilisation tension
- Considérer alimentation séparée pour servo

## Test des Composants Individuels

### Test 1: Arduino Uno
```cpp
// Code de test Arduino de base
void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH);
  delay(1000);
  digitalWrite(13, LOW);
  delay(1000);
}
```
**Résultat attendu :** LED L d'Arduino clignote chaque seconde

### Test 2: Communication Série ESP32 ↔ Arduino
**Sur Arduino :**
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    char data = Serial.read();
    Serial.print("Reçu: ");
    Serial.println(data);
  }
}
```

**Sur ESP32 :**
```python
from machine import UART
# Utiliser UART0 (U0T/U0R) sur ESP32-CAM
uart = UART(0, baudrate=9600, tx=1, rx=3)
uart.write('A')
```
**Résultat attendu :** Arduino reçoit et renvoie le caractère 'A'

### Test 3: Écran LCD
```cpp
#include <LiquidCrystal.h>
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  lcd.begin(16, 2);
  lcd.print("Test LCD OK");
}

void loop() {
  // Rien à faire
}
```
**Résultat attendu :** LCD affiche "Test LCD OK"

### Test 4: Clavier
```cpp
#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {9, 8, 7, 6};
byte colPins[COLS] = {13, 10, A0, A1};
Keypad keypad = makeKeypad(keys);

void setup() {
  Serial.begin(9600);
}

void loop() {
  char key = keypad.getKey();
  if (key) {
    Serial.println(key);
  }
}
```
**Résultat attendu :** Appuyer sur les touches affiche les caractères dans le moniteur série

### Test 5: Servo Moteur
```cpp
#include <Servo.h>
Servo servo;

void setup() {
  servo.attach(A2);
  servo.write(0);
}

void loop() {
  servo.write(90);
  delay(1000);
  servo.write(0);
  delay(1000);
}
```
**Résultat attendu :** Servo alterne entre 0° et 90°

### Test 6: Caméra ESP32
```python
from esp32cam import Camera
camera = Camera()
img = camera.capture()
print("Image capturée")
```
**Résultat attendu :** ESP32 capture une image sans erreur

## Boîtier et Montage

### Boîtier Recommandé
- Boîte plastique étanche
- Taille: 200x150x100mm minimum
- Ouïes de ventilation pour dissipation chaleur
- Passages de câbles pour fils externes

### Placement Composants
1. ESP32 Cam: Sécuriser avec entretoises
2. Écran LCD: Monter sur panneau frontal
3. Clavier: Monter sur panneau frontal
4. Servo: Monter près mécanisme porte
5. Potentiomètre contraste: Accès facile pour ajustement

### Gestion Câbles
- Utiliser colliers de serrage pour organisation
- Étiqueter toutes connexions
- Fournir soulagement de tension pour câbles externes

## Précautions de Sécurité

### Sécurité Électrique
- Vérifier doublement toutes connexions avant mise sous tension
- Utiliser calibres de fil appropriés
- Mettre à terre toutes parties métalliques
- Installer fusible sur ligne alimentation

### Sécurité Mécanique
- Assurer mécanisme porte ne peut causer blessure
- Tester couple servo approprié pour application
- Fournir mécanisme de déverrouillage manuel
- Installer bouton arrêt d'urgence

### Protection Environnementale
- Rendre étanches tous composants externes
- Protéger contre pénétration humidité
- Assurer ventilation adéquate
- Utiliser composants plage température appropriée

## Dépannage Problèmes Courants

### Servo ne bouge pas
- Vérifier tension alimentation et courant
- Vérifier fréquence PWM (50Hz)
- Tester valeurs duty cycle
- Vérifier connexion fil signal servo

### LCD ne s'affiche pas
- Vérifier toutes connexions GPIO
- Ajuster potentiomètre contraste
- Vérifier alimentation rétroéclairage
- Tester avec script simple LCD

### LCD affiche caractères étranges
- Ajuster contraste avec potentiomètre
- Vérifier connexions broches de données
- S'assurer mode 4-bit correct
- Vérifier timing initialisation

### Clavier ne répond pas
- Vérifier connexions broches lignes/colonnes
- Tester avec multimètre pour continuité
- Vérifier pas de courts-circuits

### Caméra ne fonctionne pas
- Assurer caméra bien assise
- Vérifier connexions alimentation et I2C caméra
- Vérifier firmware caméra
- Tester avec script capture simple

## Test Système Final

1. Mettre système sous tension
2. Ajuster contraste LCD avec potentiomètre
3. Vérifier LCD affiche "Systeme Pret"
4. Tester saisie clavier (devrait s'afficher sur LCD)
5. Tester mot de passe et reconnaissance faciale
6. Vérifier porte s'ouvre/ferme correctement
7. Tester fonctionnalités sécurité (visages multiples, mauvais mot de passe)

## Conseils Maintenance

- Nettoyer régulièrement lentille caméra
- Vérifier étalonnage servo moteur
- Ajuster contraste LCD si nécessaire
- Mettre à jour base données visages si nécessaire
- Surveiller logs système pour erreurs
- Tester alimentation de secours
- Inspecter câbles pour usure

Le système est maintenant prêt pour déploiement!