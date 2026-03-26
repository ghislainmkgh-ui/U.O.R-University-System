# Configuration Matérielle ESP32 Cam - Version Corrigée
# Séparation du code matériel pour meilleure organisation
# Support multiple formats caméra avec fallback automatique

import machine
import time
from machine import Pin, PWM, UART
import esp32_camera_config  # Module de configuration caméra
import logging

# Configuration liaison série avec Arduino
ARDUINO_BAUDRATE = 9600
# Sur ESP32-CAM, on utilise les broches UART0 (U0T/U0R) :
# - U0T (GPIO 1) : TX (Transmission vers Arduino)
# - U0R (GPIO 3) : RX (Réception depuis Arduino)
ESP32_TX_PIN = 1  # GPIO 1 (U0T) pour transmission vers Arduino
ESP32_RX_PIN = 3  # GPIO 3 (U0R) pour réception depuis Arduino

logger = logging.getLogger(__name__)

class ESP32Hardware:
    """Classe gérant toute la configuration matérielle ESP32"""

    def __init__(self):
        self.uart = None
        self.camera_manager = None
        self.face_recognizer = None
        self.initialized = False

    def initialize_hardware(self):
        """Initialise tous les composants matériels ESP32"""
        try:
            # Initialisation liaison série avec Arduino (UART0)
            self.uart = UART(0, baudrate=ARDUINO_BAUDRATE, tx=ESP32_TX_PIN, rx=ESP32_RX_PIN)
            logger.info("UART ESP32 initialisé")

            # Initialisation caméra avec diagnostic
            self.camera_manager = esp32_camera_config.camera_manager
            if not self.camera_manager.initialize_camera():
                logger.error("Caméra ESP32 non initialisée!")
                logger.error(f"Erreur: {self.camera_manager.last_error}")
                return False
            
            camera_status = self.camera_manager.get_camera_status()
            logger.info(f"Caméra ESP32 initialisée: Format={camera_status['format']}, Size={camera_status['framesize']}")

            # Initialisation reconnaissance faciale (optionnel - peut être chargé plus tard)
            try:
                import face_recognition
                self.face_recognizer = face_recognition.FaceRecognizer()
                logger.info("Reconnaissance faciale initialisée")
            except ImportError:
                logger.warning("Module face_recognition non disponible - fonctionnalité désactivée")
                self.face_recognizer = None

            self.initialized = True
            logger.info("Configuration matérielle ESP32 terminée avec succès")
            return True

        except Exception as e:
            logger.error(f"Erreur initialisation matériel ESP32: {e}")
            self.initialized = False
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
        """Nettoie les ressources matérielles"""
        try:
            if self.uart:
                self.uart.deinit()
            self.initialized = False
            logger.info("Nettoyage matériel ESP32 terminé")
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")

    def get_hardware_status(self):
        """Retourne le statut du matériel"""
        status = {
            'uart': self.uart is not None and self.initialized,
            'initialized': self.initialized,
        }
        
        if self.camera_manager:
            status['camera'] = self.camera_manager.get_camera_status()
        
        if self.face_recognizer:
            status['face_recognizer'] = 'initialized'
        else:
            status['face_recognizer'] = 'unavailable'
        
        return status

# Instance globale pour accès facile
esp32_hw = ESP32Hardware()

# Fonctions utilitaires pour accès direct
def initialize_esp32_hardware():
    """Fonction utilitaire pour initialisation"""
    return esp32_hw.initialize_hardware()

def send_command_to_arduino(command):
    """Fonction utilitaire pour envoi commande"""
    return esp32_hw.send_to_arduino(command)

def receive_command_from_arduino():
    """Fonction utilitaire pour réception commande"""
    return esp32_hw.receive_from_arduino()

def capture_camera_image():
    """Fonction utilitaire pour capture image"""
    return esp32_hw.capture_image()

def detect_faces_in_image(image):
    """Fonction utilitaire pour détection visages"""
    return esp32_hw.detect_faces(image)

def recognize_face_in_image(image, known_faces):
    """Fonction utilitaire pour reconnaissance visage"""
    return esp32_hw.recognize_face(image, known_faces)

def cleanup_esp32_hardware():
    """Fonction utilitaire pour nettoyage"""
    esp32_hw.cleanup()

def get_esp32_hardware_status():
    """Fonction utilitaire pour obtenir le statut"""
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