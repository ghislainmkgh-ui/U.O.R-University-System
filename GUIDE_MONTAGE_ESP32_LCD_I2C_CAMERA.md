# Guide de montage — ESP32 + Clavier 4x4 + Servo + LEDs + LCD I2C + Caméra IP

Ce guide correspond au firmware actuel `esp32_firmware.py` et à la nouvelle architecture (sans ESP32-CAM, sans Arduino Uno).

---

## 1) Ce qu’il te faut

- 1x ESP32 (WROOM/WROVER)
- 1x clavier matriciel 4x4
- 1x servo SG90 (ou MG996R avec alim externe)
- 2x LEDs (verte + rouge) + résistances 220Ω
- 1x LCD I2C (1602/2004 + backpack PCF8574)
- 1x caméra IP Wi-Fi
- Fils dupont + breadboard
- Alimentation 5V stable (recommandé, surtout avec servo)

---

## 2) Informations caméra nécessaires

Depuis ta photo, on voit:

- **ID caméra**: `A836980471JHVM230224`
- **Mot de passe par défaut**: `12345678`

⚠️ Important:
- L’**ID caméra** sert généralement à l’app mobile du fabricant (ajout P2P).
- Pour ce projet, le serveur Python a besoin d’une **URL locale**:
  - `IP_CAMERA_SNAPSHOT_URL` (HTTP)
  - `IP_CAMERA_URL` (RTSP)
- Donc il faut aussi récupérer l’**IP locale de la caméra** (ex: `192.168.1.50`).

### Variables à remplir dans `.env`

- `IP_CAMERA_USERNAME` (souvent `admin`)
- `IP_CAMERA_PASSWORD` (ici `12345678`, à changer ensuite)
- `IP_CAMERA_SNAPSHOT_URL` (ex: `http://192.168.1.50/capture`)
- `IP_CAMERA_URL` (ex: `rtsp://admin:12345678@192.168.1.50:554/stream1`)

---

## 3) Câblage ESP32 (pins utilisés par le firmware)

## 3.1 Clavier 4x4

Le firmware utilise:

- **Rows**: GPIO `13, 12, 14, 27`
- **Cols**: GPIO `26, 25, 33, 32`

Branche le connecteur du clavier dans l’ordre logique R1-R4 puis C1-C4.

---

## 3.2 Servo

- Signal servo → **GPIO18**
- VCC servo → **5V externe recommandé**
- GND servo → **GND commun** (très important avec ESP32)

⚠️ Ne pas alimenter un servo puissant directement depuis le 5V USB de la carte si instable.

---

## 3.3 LEDs

- LED verte anode → **GPIO2** via résistance 220Ω
- LED rouge anode → **GPIO4** via résistance 220Ω
- Cathodes des LEDs → GND

---

## 3.4 LCD I2C (ton cas)

Pins I2C recommandées sur ESP32:

- SDA → **GPIO21**
- SCL → **GPIO22**
- VCC → 5V (ou 3.3V selon module)
- GND → GND

✅ Bonne nouvelle: ces pins **n’entrent pas en conflit** avec les pins déjà utilisées par ton firmware actuel.

---

## 4) Schéma logique rapide

1. Étudiant tape code sur clavier
2. ESP32 envoie le code au serveur (`/verify_code`)
3. Serveur valide en base
4. Serveur capture image caméra IP
5. Serveur fait la reconnaissance faciale
6. Réponse vers ESP32
7. ESP32 ouvre/ferme la porte + LEDs

---

## 5) Checklist de mise en route

- [ ] Caméra connectée au même réseau Wi-Fi local
- [ ] IP locale caméra connue
- [ ] `IP_CAMERA_SNAPSHOT_URL` et/ou `IP_CAMERA_URL` testées
- [ ] ESP32 connecté au Wi-Fi
- [ ] `SERVER_URL` dans `esp32_firmware.py` pointe vers IP du PC serveur
- [ ] GND commun entre ESP32 et alimentation servo
- [ ] LCD I2C branché sur GPIO21/22

---

## 6) Test rapide conseillé

1. Démarre `access_server.py`
2. Vérifie endpoint santé: `/status`
3. Lance ESP32
4. Tape un code + `#`
5. Observe:
   - LEDs
   - mouvement servo
   - logs serveur (validation + capture + face recognition)

---

## 7) LCD I2C — déjà intégré ✅

Le support LCD I2C est **déjà codé** dans `esp32_firmware.py`.

Messages affichés automatiquement sur l'écran :

| Événement | Ligne 1 | Ligne 2 |
|---|---|---|
| Démarrage | `U.O.R Access` | `Demarrage...` |
| Connexion Wi-Fi | `Connexion WiFi` | `<SSID>` |
| Wi-Fi connecté | `WiFi connecte` | `<IP locale>` |
| Wi-Fi indispo | `WiFi indispo` | `Reessayer...` |
| Prêt | `Pret` | `Code + #` |
| Saisie en cours | `Entrez code` | `****` (masqué) |
| Vérification | `Verification...` | `Patientez` |
| Accès accordé | `ACCES ACCORDE` | `<Nom étudiant>` |
| Accès refusé | `ACCES REFUSE` | `<Raison>` |
| Timeout | `Timeout` | `Code efface` |
| Annulation | `Annule` | `Entrez code` |

**Pins LCD I2C** : SDA → GPIO21 · SCL → GPIO22 · Adresse `0x27`

### ⚠️ Librairies à uploader sur l'ESP32

Le firmware charge `i2c_lcd` et `lcd_api` dynamiquement. Si elles sont absentes, il continue en mode console (pas de crash). Pour activer le LCD, copie ces 2 fichiers sur la carte :

- [`lcd_api.py`](https://raw.githubusercontent.com/dhylands/python_lcd/master/lcd/lcd_api.py)
- [`i2c_lcd.py`](https://raw.githubusercontent.com/dhylands/python_lcd/master/lcd/machine_i2c_lcd.py) (renommer en `i2c_lcd.py`)

Commandes upload (Thonny ou mpremote) :
```bash
mpremote connect COM12 cp lcd_api.py :lcd_api.py
mpremote connect COM12 cp i2c_lcd.py :i2c_lcd.py
mpremote connect COM12 cp esp32_firmware.py :main.py
```
