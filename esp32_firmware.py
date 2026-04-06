# ============================================================
# Firmware ESP32 - Système Contrôle d'Accès U.O.R
# Nouvelle Architecture (sans ESP32-CAM, sans Arduino)
# ============================================================
#
# MATÉRIEL :
#   - ESP32 standard (WROOM, WROVER, etc.) - PAS l'ESP32-CAM
#   - Clavier matriciel 4x4 (HX543 ou compatible)
#   - Servo moteur SG90/MG996R (contrôle porte)
#   - 2 LEDs : verte (accès accordé) + rouge (accès refusé)
#   - Connexion Wi-Fi (réseau local)
#
# FLUX D'AUTHENTIFICATION :
#   1. Étudiant tape son code + # sur le clavier matriciel
#   2. ESP32 envoie le code au serveur Python via HTTP POST
#   3. Serveur Python : valide code BD → capture image caméra IP → reconnaissance faciale
#   4. Serveur renvoie {"access": "granted"|"denied", "name": "..."}
#   5. ESP32 active servo (ouvre porte) si accordé, LED rouge si refusé
#
# UPLOAD SUR ESP32 :
#   Renommer ce fichier en "main.py" et l'uploader via Thonny ou ampy.
#   → ampy -p COM5 put esp32_firmware.py /main.py
# ============================================================

import network
import urequests
import time
import json
from machine import Pin, PWM, I2C

try:
    # Bibliothèque MicroPython classique pour LCD I2C (PCF8574)
    from i2c_lcd import I2cLcd
except ImportError:
    I2cLcd = None

# ============================================================
# CONFIGURATION — À ADAPTER À VOTRE INSTALLATION
# ============================================================

WIFI_SSID     = "MKGH SOFTWARE"  # Nom de votre réseau Wi-Fi
WIFI_PASSWORD = "87654321"  # Mot de passe Wi-Fi

# IP/port du serveur Python sur le réseau local (access_server.py)
SERVER_URL = "http://192.168.1.100:5050"

# ── GPIO Clavier 4×4 ─────────────────────────────────────────
# Lignes (OUTPUT) : connectées aux rangées du clavier
ROW_PINS = [13, 12, 14, 27]
# Colonnes (INPUT PULL-DOWN) : connectées aux colonnes du clavier
COL_PINS = [26, 25, 33, 32]

# ── Servo moteur ─────────────────────────────────────────────
SERVO_PIN           = 18
SERVO_OPEN_NS       = 2_400_000   # ~180° → porte ouverte
SERVO_CLOSED_NS     =   600_000   # ~0°   → porte fermée
DOOR_OPEN_DURATION  = 5           # secondes d'ouverture

# ── LEDs de statut (optionnel) ───────────────────────────────
LED_GREEN_PIN = 2
LED_RED_PIN   = 4

# ── Saisie clavier ───────────────────────────────────────────
KEYPAD_LAYOUT = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D'],
]
CONFIRM_KEY    = '#'   # Valider la saisie
CANCEL_KEY     = '*'   # Effacer / annuler
MAX_CODE_LEN   = 10
ENTRY_TIMEOUT  = 30    # secondes avant effacement automatique
SERVER_TIMEOUT = 30    # secondes d'attente réponse serveur

# ── LCD I2C (optionnel) ──────────────────────────────────────
LCD_ENABLED   = True
LCD_SDA_PIN   = 21
LCD_SCL_PIN   = 22
LCD_I2C_ADDR  = 0x27
LCD_ROWS      = 2
LCD_COLS      = 16


# ============================================================
# CLASSE PRINCIPALE
# ============================================================
class ESP32AccessController:
    """Contrôleur d'accès ESP32 — clavier matriciel + servo + HTTP"""

    def __init__(self):
        # Clavier : lignes en sortie, colonnes en entrée avec pull-down
        self.rows = [Pin(p, Pin.OUT, value=0) for p in ROW_PINS]
        self.cols = [Pin(p, Pin.IN,  Pin.PULL_DOWN) for p in COL_PINS]

        # Servo
        self.servo = PWM(Pin(SERVO_PIN), freq=50)
        self._close_door()

        # LEDs
        self.led_green = Pin(LED_GREEN_PIN, Pin.OUT, value=0)
        self.led_red   = Pin(LED_RED_PIN,   Pin.OUT, value=0)

        # État saisie
        self.entered_code   = ""
        self.last_key_time  = 0

        # Wi-Fi
        self.wlan = network.WLAN(network.STA_IF)

        # LCD I2C (optionnel)
        self.lcd = None
        self._init_lcd()
        self.lcd_write("U.O.R Access", "Demarrage...")

    # ── LCD I2C ──────────────────────────────────────────────
    def _init_lcd(self):
        if not LCD_ENABLED:
            return

        if I2cLcd is None:
            print("LCD: lib i2c_lcd absente (mode console uniquement)")
            return

        try:
            i2c = I2C(0, scl=Pin(LCD_SCL_PIN), sda=Pin(LCD_SDA_PIN), freq=400000)
            self.lcd = I2cLcd(i2c, LCD_I2C_ADDR, LCD_ROWS, LCD_COLS)
            self.lcd.clear()
            print("LCD: initialisé")
        except Exception as e:
            self.lcd = None
            print(f"LCD: init échouée ({e})")

    def lcd_write(self, line1: str = "", line2: str = ""):
        if not self.lcd:
            return

        try:
            self.lcd.clear()
            self.lcd.move_to(0, 0)
            self.lcd.putstr((line1 or "")[:LCD_COLS])
            self.lcd.move_to(0, 1)
            self.lcd.putstr((line2 or "")[:LCD_COLS])
        except Exception as e:
            print(f"LCD write erreur: {e}")

    # ── Wi-Fi ────────────────────────────────────────────────
    def connect_wifi(self) -> bool:
        self.wlan.active(True)
        if self.wlan.isconnected():
            print("WiFi déjà connecté:", self.wlan.ifconfig()[0])
            self.lcd_write("WiFi deja OK", self.wlan.ifconfig()[0])
            return True

        print(f"Connexion à '{WIFI_SSID}'...")
        self.lcd_write("Connexion WiFi", WIFI_SSID)
        self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        for _ in range(20):
            if self.wlan.isconnected():
                print("WiFi connecté :", self.wlan.ifconfig()[0])
                self.lcd_write("WiFi connecte", self.wlan.ifconfig()[0])
                return True
            time.sleep(1)

        print("ERREUR : connexion WiFi impossible")
        self.lcd_write("ERREUR WiFi", "Verifier reseau")
        return False

    # ── Clavier ──────────────────────────────────────────────
    def read_key(self) -> str | None:
        """Retourne la touche pressée ou None (anti-rebond inclus)."""
        for r, row_pin in enumerate(self.rows):
            row_pin.value(1)
            for c, col_pin in enumerate(self.cols):
                if col_pin.value():
                    time.sleep_ms(40)          # anti-rebond
                    if col_pin.value():
                        while col_pin.value():  # attendre relâchement
                            time.sleep_ms(10)
                        row_pin.value(0)
                        return KEYPAD_LAYOUT[r][c]
            row_pin.value(0)
        return None

    # ── Servo ────────────────────────────────────────────────
    def _open_door(self):
        self.servo.duty_ns(SERVO_OPEN_NS)

    def _close_door(self):
        self.servo.duty_ns(SERVO_CLOSED_NS)

    def open_door_timed(self):
        """Ouvre la porte puis la referme après DOOR_OPEN_DURATION secondes."""
        self._open_door()
        time.sleep(DOOR_OPEN_DURATION)
        self._close_door()

    # ── LEDs ─────────────────────────────────────────────────
    def _blink(self, led: Pin, times: int, delay_ms: int):
        for _ in range(times):
            led.value(1); time.sleep_ms(delay_ms)
            led.value(0); time.sleep_ms(delay_ms)

    def signal_granted(self):
        self.led_red.value(0)
        self._blink(self.led_green, 2, 120)
        self.led_green.value(1)

    def signal_denied(self):
        self.led_green.value(0)
        self._blink(self.led_red, 4, 80)

    def signal_processing(self):
        """Clignotement alterné vert/rouge = traitement en cours."""
        for _ in range(5):
            self.led_green.value(1); self.led_red.value(0); time.sleep_ms(180)
            self.led_green.value(0); self.led_red.value(1); time.sleep_ms(180)
        self.led_green.value(0); self.led_red.value(0)

    def signal_key_pressed(self):
        """Court flash vert = touche enregistrée."""
        self.led_green.value(1); time.sleep_ms(60); self.led_green.value(0)

    # ── Communication serveur ─────────────────────────────────
    def send_code_to_server(self, code: str) -> dict:
        """
        POST /verify_code {"code": "..."} → serveur Python.
        Le serveur valide le code en BD, capture l'image caméra IP,
        effectue la reconnaissance faciale et renvoie le résultat.

        Retourne : {"access": "granted"|"denied", "name": "...", "reason": "..."}
        """
        try:
            payload = json.dumps({"code": code})
            headers = {"Content-Type": "application/json"}
            resp = urequests.post(
                f"{SERVER_URL}/verify_code",
                data=payload,
                headers=headers,
                timeout=SERVER_TIMEOUT,
            )
            result = resp.json()
            resp.close()
            return result
        except OSError as e:
            print(f"Erreur réseau: {e}")
            return {"access": "denied", "reason": "Erreur réseau - vérifier WiFi"}
        except Exception as e:
            print(f"Erreur serveur: {e}")
            return {"access": "denied", "reason": "Erreur communication serveur"}

    # ── Boucle principale ─────────────────────────────────────
    def run(self):
        print("=" * 50)
        print("  U.O.R - Système Contrôle d'Accès (ESP32)")
        print("=" * 50)
        self.lcd_write("U.O.R Access", "Init systeme")

        if not self.connect_wifi():
            # Clignoter rouge indéfiniment si pas de WiFi
            while True:
                self.lcd_write("WiFi indispo", "Reessayer...")
                self._blink(self.led_red, 1, 400)
                time.sleep_ms(200)

        # Signal: prêt
        self._blink(self.led_green, 3, 100)
        print("Prêt. Tapez votre code puis # pour valider, * pour annuler.")
        self.lcd_write("Pret", "Code + #")

        while True:
            # Timeout saisie
            if self.entered_code and (time.time() - self.last_key_time) > ENTRY_TIMEOUT:
                print("Timeout — code effacé")
                self.entered_code = ""
                self.lcd_write("Timeout", "Code efface")
                self.signal_denied()
                continue

            key = self.read_key()
            if key is None:
                time.sleep_ms(15)
                continue

            self.last_key_time = time.time()
            self._handle_key(key)

    def _handle_key(self, key: str):
        if key == CANCEL_KEY:
            if self.entered_code:
                print("Saisie annulée")
            self.entered_code = ""
            self.lcd_write("Annule", "Entrez code")
            self.signal_denied()
            return

        if key == CONFIRM_KEY:
            if not self.entered_code:
                return
            self._process_code()
            return

        # Touche alphanumérique → ajouter au code
        if len(self.entered_code) < MAX_CODE_LEN:
            self.entered_code += key
            print(f"Code : {'*' * len(self.entered_code)}")
            self.lcd_write("Entrez code", '*' * len(self.entered_code))
            self.signal_key_pressed()
        else:
            print("Code trop long — appuyez * pour effacer")
            self.lcd_write("Code trop long", "Appuyez *")
            self.signal_denied()

    def _process_code(self):
        code = self.entered_code
        self.entered_code = ""

        print(f"Code saisi ({len(code)} car.) → envoi au serveur pour validation...")
        self.lcd_write("Verification...", "Patientez")
        self.signal_processing()

        result = self.send_code_to_server(code)

        if result.get("access") == "granted":
            name       = result.get("name", "Étudiant")
            confidence = result.get("confidence", 0)
            print(f"✓ ACCÈS ACCORDÉ — {name}  (confiance: {confidence:.0%})")
            self.lcd_write("ACCES ACCORDE", (name or "Etudiant")[:LCD_COLS])
            self.signal_granted()
            self.open_door_timed()
            self.led_green.value(0)
        else:
            reason = result.get("reason", "Accès refusé")
            print(f"✗ ACCÈS REFUSÉ — {reason}")
            self.lcd_write("ACCES REFUSE", str(reason)[:LCD_COLS])
            self.signal_denied()

        self.lcd_write("Pret", "Code + #")
        time.sleep(1)


# ============================================================
# DÉMARRAGE
# ============================================================
_controller = ESP32AccessController()
_controller.run()
