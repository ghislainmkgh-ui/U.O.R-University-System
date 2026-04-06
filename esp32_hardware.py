# ============================================================
# Matériel ESP32 - Nouvelle Architecture (sans ESP32-CAM, sans Arduino)
# ============================================================
# Rôle : clavier matriciel 4x4 + servo moteur + Wi-Fi HTTP
# La reconnaissance faciale et la capture image sont déléguées :
#   → au serveur Python (access_server.py)
#   → qui utilise une caméra IP (RTSP ou HTTP snapshot)
#
# SUPPRIMÉ (ancienne architecture) :
#   - UART vers Arduino (liaison série)
#   - Module caméra OV2640 / esp32camera
#   - TensorFlow Lite sur ESP32
# ============================================================

import network
import urequests
import time
import json
from machine import Pin, PWM

# ── Configuration réseau ─────────────────────────────────────
WIFI_SSID     = "VOTRE_SSID_WIFI"
WIFI_PASSWORD = "VOTRE_MOT_DE_PASSE_WIFI"
SERVER_URL    = "http://192.168.1.100:5050"   # IP du serveur Python

# ── GPIO clavier 4×4 ─────────────────────────────────────────
ROW_PINS = [13, 12, 14, 27]   # Lignes (OUTPUT)
COL_PINS = [26, 25, 33, 32]   # Colonnes (INPUT PULL-DOWN)

KEYPAD_LAYOUT = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D'],
]

# ── GPIO servo moteur ─────────────────────────────────────────
SERVO_PIN       = 18
SERVO_OPEN_NS   = 2_400_000   # ~180° porte ouverte
SERVO_CLOSED_NS =   600_000   # ~0°   porte fermée

# ── GPIO LEDs ─────────────────────────────────────────────────
LED_GREEN_PIN = 2
LED_RED_PIN   = 4

import logging
logger = logging.getLogger(__name__)

class ESP32Hardware:
    """
    Matériel ESP32 standard pour contrôle d'accès.
    Gère : clavier matriciel 4x4, servo moteur, Wi-Fi, LEDs.
    La reconnaissance faciale et la caméra sont côté serveur Python.
    """

    def __init__(self):
        self.rows        = [Pin(p, Pin.OUT, value=0) for p in ROW_PINS]
        self.cols        = [Pin(p, Pin.IN,  Pin.PULL_DOWN) for p in COL_PINS]
        self.servo       = PWM(Pin(SERVO_PIN), freq=50)
        self.led_green   = Pin(LED_GREEN_PIN, Pin.OUT, value=0)
        self.led_red     = Pin(LED_RED_PIN,   Pin.OUT, value=0)
        self.wlan        = network.WLAN(network.STA_IF)
        self.initialized = False
        self._close_door()

    def initialize_hardware(self) -> bool:
        """Initialise le matériel ESP32 et connecte au Wi-Fi."""
        try:
            self._close_door()
            if not self.connect_wifi():
                return False
            self.initialized = True
            logger.info("Matériel ESP32 initialisé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur initialisation matériel ESP32: {e}")
            self.initialized = False
            return False

    def connect_wifi(self) -> bool:
        """Connecte l'ESP32 au réseau Wi-Fi."""
        self.wlan.active(True)
        if self.wlan.isconnected():
            return True
        self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(20):
            if self.wlan.isconnected():
                logger.info(f"Wi-Fi connecté: {self.wlan.ifconfig()[0]}")
                return True
            time.sleep(1)
        logger.error("Échec connexion Wi-Fi")
        return False

    def send_to_arduino(self, message):
        """Envoie un message à Arduino via liaison série"""
        if self.uart and self.initialized:
            try:
                self.uart.write(message + '\n')
                time.sleep(0.1)  # Délai pour transmission
                return True
            except Exception as e:
                logger.error(f"Erreur envoi Arduino: {e}")
                return False
        return False

    def receive_from_arduino(self):
        """Reçoit un message d'Arduino"""
        if self.uart and self.initialized:
            if self.uart.any():
                try:
                    data = self.uart.read().decode('utf-8').strip()
                    return data
                except Exception as e:
                    logger.error(f"Erreur réception Arduino: {e}")
                    return None
        return None

    def capture_image(self):
        """Capture une image avec la caméra ESP32 (format auto-détecté)"""
        if not self.initialized or self.camera_manager is None:
            logger.error("Caméra non initialisée")
            return None
        
        try:
            frame = self.camera_manager.capture_frame()
            if frame is not None:
                logger.debug(f"Image capturée: {len(frame)} bytes")
            return frame
        except Exception as e:
            logger.error(f"Erreur capture image: {e}")
            return None

    def detect_faces(self, image):
        """Détecte les visages dans une image"""
        if self.face_recognizer and self.initialized:
            try:
                return self.face_recognizer.detect_faces(image)
            except Exception as e:
                logger.error(f"Erreur détection visages: {e}")
                return []
        return []

    def recognize_face(self, image, known_faces):
        """Reconnaît un visage dans une image"""
        if self.face_recognizer and self.initialized:
            try:
                return self.face_recognizer.recognize_face(image, known_faces)
            except Exception as e:
                logger.error(f"Erreur reconnaissance visage: {e}")
                return False
        logger.warning("Face recognizer non disponible")
        return False

    def cleanup(self):
        """Nettoie les ressources matérielles."""
        try:
            self._close_door()
            self.servo.deinit()
            self.initialized = False
            logger.info("Nettoyage matériel ESP32 terminé")
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")

    def get_hardware_status(self) -> dict:
        """Retourne le statut du matériel."""
        return {
            "initialized":   self.initialized,
            "wifi_connected": self.wlan.isconnected(),
            "wifi_ip":       self.wlan.ifconfig()[0] if self.wlan.isconnected() else None,
            "server_url":    SERVER_URL,
            "hardware":      "ESP32 standard (clavier 4x4 + servo + Wi-Fi)",
        }

# Instance globale
esp32_hw = ESP32Hardware()

# Fonctions utilitaires
def initialize_esp32_hardware():
    return esp32_hw.initialize_hardware()

def cleanup_esp32_hardware():
    esp32_hw.cleanup()

def get_esp32_hardware_status():
    return esp32_hw.get_hardware_status()

# ============================================================================
# DIAGNOSTIC AU DÉMARRAGE (MicroPython)
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("ESP32 Hardware Initialization")
    print("="*60)
    
    success = initialize_esp32_hardware()
    
    if success:
        print("\n✓ All systems operational!")
        print(get_esp32_hardware_status())
    else:
        print("\n✗ Hardware initialization failed!")
        print("Check connections and power supply")
    
    print("\n" + "="*60)