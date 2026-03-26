# Système de Contrôle d'Accès Porte ESP32 Cam + Arduino Uno
# ESP32: Caméra, reconnaissance faciale, logique principale
# Arduino: LCD, clavier, servo moteur
# Communication: Liaison série UART

import time
import esp32_hardware

# États du système
STATE_IDLE = 0
STATE_PASSWORD = 1
STATE_FACIAL_RECOGNITION = 2
STATE_ACCESS_GRANTED = 3
STATE_ACCESS_DENIED = 4

class DoorAccessSystem:
    def __init__(self):
        # Initialisation du matériel ESP32
        self.hardware = esp32_hardware.esp32_hw
        if not self.hardware.initialize_hardware():
            print("Erreur initialisation matériel ESP32")
            return

        # Variables système
        self.current_state = STATE_IDLE
        self.password_validated = False
        self.door_open = False
        self.last_entry_time = 0
        self.concurrent_users = 0

        # Attendre Arduino
        time.sleep(2)
        self.send_to_arduino("STATE:IDLE")

    def send_to_arduino(self, message):
        """Envoie message à Arduino via liaison série"""
        return self.hardware.send_to_arduino(message)

    def receive_from_arduino(self):
        """Reçoit message d'Arduino"""
        return self.hardware.receive_from_arduino()

    def set_state(self, new_state):
        """Change état et notifie Arduino"""
        self.current_state = new_state
        state_names = {
            STATE_IDLE: "IDLE",
            STATE_PASSWORD: "PASSWORD",
            STATE_FACIAL_RECOGNITION: "FACE",
            STATE_ACCESS_GRANTED: "GRANTED",
            STATE_ACCESS_DENIED: "DENIED"
        }
        if new_state in state_names:
            self.send_to_arduino(f"STATE:{state_names[new_state]}")

    def display_message(self, message):
        """Affiche message sur LCD via Arduino"""
        self.send_to_arduino(f"MESSAGE:{message}")

    def run(self):
        """Boucle principale du système"""
        self.display_message("Systeme Pret")

        while True:
            # Vérifier messages d'Arduino
            arduino_message = self.receive_from_arduino()
            if arduino_message:
                self.handle_arduino_message(arduino_message)

            # Logique principale selon état
            if self.current_state == STATE_IDLE:
                # Attendre début processus
                time.sleep(0.1)

            elif self.current_state == STATE_PASSWORD:
                # Attendre validation mot de passe d'Arduino
                pass

            elif self.current_state == STATE_FACIAL_RECOGNITION:
                # Effectuer reconnaissance faciale
                self.perform_facial_recognition()

            elif self.current_state == STATE_ACCESS_GRANTED:
                # Accès autorisé - Arduino gère l'ouverture porte
                time.sleep(5)  # Attendre fermeture porte
                self.set_state(STATE_IDLE)

            elif self.current_state == STATE_ACCESS_DENIED:
                # Accès refusé
                time.sleep(3)
                self.set_state(STATE_IDLE)

            time.sleep(0.1)

    def handle_arduino_message(self, message):
        """Traite messages reçus d'Arduino"""
        if message == "PASSWORD_OK":
            self.password_validated = True
            self.set_state(STATE_FACIAL_RECOGNITION)
        elif message == "PASSWORD_INVALID":
            self.set_state(STATE_ACCESS_DENIED)

    def perform_facial_recognition(self):
        """Effectue reconnaissance faciale"""
        try:
            # Capturer image
            self.display_message("Capture Image...")
            img = self.hardware.capture_image()

            if img:
                # Détecter visages
                self.display_message("Analyse Visage...")
                faces = self.hardware.detect_faces(img)

                if len(faces) == 0:
                    self.display_message("Aucun Visage")
                    time.sleep(2)
                    self.set_state(STATE_ACCESS_DENIED)
                elif len(faces) > 1:
                    self.display_message("Trop Visages")
                    time.sleep(2)
                    self.set_state(STATE_ACCESS_DENIED)
                else:
                    # Reconnaissance visage
                    self.display_message("Verification...")
                    recognized = self.hardware.recognize_face(img, [])  # Liste vide pour simulation

                    if recognized and self.password_validated:
                        self.set_state(STATE_ACCESS_GRANTED)
                    else:
                        self.set_state(STATE_ACCESS_DENIED)
            else:
                self.display_message("Erreur Camera")
                time.sleep(2)
                self.set_state(STATE_ACCESS_DENIED)

        except Exception as e:
            self.display_message("Erreur Reconnaissance")
            time.sleep(2)
            self.set_state(STATE_ACCESS_DENIED)

# Programme principal
if __name__ == "__main__":
    system = DoorAccessSystem()
    system.run()