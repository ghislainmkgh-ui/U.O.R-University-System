# Système de Contrôle d'Accès Porte - Nouvelle Architecture
# ============================================================
# ESP32 standard (sans caméra intégrée) + Caméra IP + Serveur Python
#
# SUPPRIMIÉ (ancienne architecture) :
#   - Communication UART avec Arduino Uno
#   - Capture image sur ESP32-CAM (OV2640)
#   - Reconnaissance faciale embarquée (TensorFlow Lite)
#
# NOUVEAU FLUX :
#   1. Étudiant tape code sur le clavier matriciel
#   2. ESP32 envoie HTTP POST au serveur Python avec le code
#   3. Serveur Python :
#       a. Valide le code en base de données
#       b. Capture image depuis la caméra IP (RTSP/HTTP snapshot)
#       c. Reconnaissance faciale (OpenCV + face_recognition)
#       d. Retourne {"access": "granted|denied"}
#   4. ESP32 active servo (porte) et LEDs selon réponse
# ============================================================

import time
import esp32_hardware

CONFIRM_KEY       = '#'
CANCEL_KEY        = '*'
MAX_CODE_LEN      = 10
ENTRY_TIMEOUT_S   = 30   # secondes avant effacement code
DOOR_OPEN_SECS    = 5    # secondes d'ouverture


class DoorAccessSystem:
    """Système d'accès : clavier → HTTP → serveur Python → caméra IP → visage → porte."""

    def __init__(self):
        self.hardware = esp32_hardware.esp32_hw
        if not self.hardware.initialize_hardware():
            print("ERREUR: Impossible d'initialiser le matériel ESP32")
            return
        self.entered_code  = ""
        self.last_key_time = 0
        print("Système d'accès U.O.R prêt")
        print("→ Tapez votre code, puis # pour valider, * pour annuler")

    def run(self):
        while True:
            # Timeout saisie
            if self.entered_code and (time.time() - self.last_key_time) > ENTRY_TIMEOUT_S:
                print("Timeout — code effacé")
                self.entered_code = ""
                self.hardware.signal_access_denied()

            key = self.hardware.read_keypad()
            if key is None:
                time.sleep_ms(20)
                continue

            self.last_key_time = time.time()
            self._handle_key(key)

    def _handle_key(self, key: str):
        if key == CANCEL_KEY:
            if self.entered_code:
                print("Saisie annulée")
            self.entered_code = ""
            self.hardware.signal_access_denied()
            return

        if key == CONFIRM_KEY:
            if not self.entered_code:
                return
            self._process_code()
            return

        # Touche alphanumérique
        if len(self.entered_code) < MAX_CODE_LEN:
            self.entered_code += key
            print(f"Code: {'*' * len(self.entered_code)}")
            # Flash vert = touche enregistrée
            self.hardware.led_green.value(1)
            time.sleep_ms(60)
            self.hardware.led_green.value(0)
        else:
            print("Code trop long — appuyez * pour effacer")
            self.hardware.signal_access_denied()

    def _process_code(self):
        code = self.entered_code
        self.entered_code = ""
        print(f"Code saisi ({len(code)} car.) → envoi au serveur...")
        self.hardware.signal_processing()

        result = self.hardware.send_code_to_server(code)

        if result.get("access") == "granted":
            name       = result.get("name", "Étudiant")
            confidence = result.get("confidence", 0)
            print(f"✓ ACCÈS ACCORDÉ — {name}  (confiance: {confidence:.0%})")
            self.hardware.signal_access_granted()
            self.hardware.open_door(DOOR_OPEN_SECS)
            self.hardware.led_green.value(0)
        else:
            reason = result.get("reason", "Accès refusé")
            print(f"✗ ACCÈS REFUSÉ — {reason}")
            self.hardware.signal_access_denied()

        time.sleep(1)


if __name__ == "__main__":
    system = DoorAccessSystem()
    system.run()