# Simulation Système Accès Porte ESP32 + Arduino Uno - Test sur PC
# Cette simulation simule la communication entre ESP32 et Arduino
# ESP32: Caméra, reconnaissance faciale, logique principale
# Arduino: LCD, clavier, servo moteur
# Communication: Liaison série simulée

import time
import random
import sys
import os
import threading
import queue

# Classes mockées pour simulation
class MockUART:
    def __init__(self):
        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()

    def write(self, data):
        print(f"ESP32 → Arduino: {data.strip()}")
        self.tx_queue.put(data)

    def read(self):
        if not self.rx_queue.empty():
            return self.rx_queue.get().encode('utf-8')
        return None

    def any(self):
        return not self.rx_queue.empty()

class MockArduino:
    def __init__(self, uart):
        self.uart = uart
        self.state = "IDLE"
        self.password = ""
        self.correct_password = "1234"
        self.lcd_display = ["Systeme Pret", ""]

    def send_to_esp32(self, message):
        print(f"Arduino → ESP32: {message}")
        self.uart.rx_queue.put(message + '\n')

    def process_command(self, command):
        if command.startswith("STATE:"):
            self.state = command[6:]
            self.update_lcd()
        elif command.startswith("MESSAGE:"):
            message = command[8:]
            self.display_message(message)

    def simulate_keypad(self):
        """Simuler l'entrée clavier"""
        if self.state == "PASSWORD":
            # Simuler saisie mot de passe
            if random.random() < 0.3:  # 30% chance
                key = random.choice(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])
                self.password += key
                self.update_lcd()
            elif random.random() < 0.1:  # 10% chance de valider
                if self.password == self.correct_password:
                    self.send_to_esp32("PASSWORD_OK")
                    self.state = "FACE"
                else:
                    self.send_to_esp32("PASSWORD_INVALID")
                    self.state = "DENIED"
                self.update_lcd()
            elif random.random() < 0.05:  # 5% chance d'effacer
                self.password = ""
                self.update_lcd()

    def update_lcd(self):
        if self.state == "IDLE":
            self.lcd_display = ["Systeme Pret", ""]
        elif self.state == "PASSWORD":
            stars = "*" * len(self.password)
            self.lcd_display = ["Entrez MDP:", stars]
        elif self.state == "FACE":
            self.lcd_display = ["Regardez Camera", "Verification..."]
        elif self.state == "GRANTED":
            self.lcd_display = ["Acces Autorise", "Porte Ouverte"]
        elif self.state == "DENIED":
            self.lcd_display = ["Acces Refuse", ""]

        print(f"LCD: {self.lcd_display[0]}")
        if self.lcd_display[1]:
            print(f"LCD: {self.lcd_display[1]}")

    def display_message(self, message):
        self.lcd_display = [message, ""]
        print(f"LCD: {message}")

class MockCamera:
    def capture(self):
        print("Caméra ESP32 capture image...")
        time.sleep(0.5)
        return "mock_image"

class MockFaceRecognizer:
    def detect_faces(self, img):
        # Simuler détection visage
        faces_detected = random.randint(0, 2)
        print(f"Détection visages: {faces_detected} visage(s)")
        return ["face"] * faces_detected if faces_detected > 0 else []

    def recognize_face(self, img, known_faces):
        # Simuler reconnaissance (50% de succès)
        recognized = random.random() < 0.5
        print(f"Reconnaissance visage: {'Réussi' if recognized else 'Échec'}")
        return recognized

    def capture_and_detect_faces(self):
        # Simuler la détection de visages
        faces = []
        if random.random() < 0.7:  # 70% de chance de détecter un visage
            faces.append("visage1")
        if random.random() < 0.2:  # 20% de chance de visages multiples
            faces.append("visage2")
        return faces

class MockFaceRecognition:
    def detect_faces(self, img):
        return ["visage"] if random.random() < 0.8 else []

    def encode_face(self, img, face):
        return [random.random() for _ in range(128)]  # Encodage 128D mocké

    def compare_faces(self, known_faces, face_encoding, tolerance=0.4):
        # Simuler la comparaison de visages
        return random.random() < 0.6  # 60% de chance de correspondance

# États du système
STATE_IDLE = 0
STATE_PASSWORD = 1
STATE_FACIAL_RECOGNITION = 2
STATE_ACCESS_GRANTED = 3
STATE_ACCESS_DENIED = 4

class MockESP32System:
    def __init__(self, uart):
        self.uart = uart
        self.camera = MockCamera()
        self.face_recognizer = MockFaceRecognizer()
        self.known_faces = []  # Liste vide pour simulation
        self.current_state = STATE_IDLE
        self.password_validated = False

    def send_to_arduino(self, message):
        self.uart.write(message + '\n')

    def receive_from_arduino(self):
        if self.uart.any():
            try:
                data = self.uart.read().decode('utf-8').strip()
                return data
            except:
                return None
        return None

    def set_state(self, new_state):
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
        self.send_to_arduino(f"MESSAGE:{message}")

    def handle_arduino_message(self, message):
        if message == "PASSWORD_OK":
            self.password_validated = True
            self.set_state(STATE_FACIAL_RECOGNITION)
        elif message == "PASSWORD_INVALID":
            self.set_state(STATE_ACCESS_DENIED)

    def perform_facial_recognition(self):
        try:
            # Capturer image
            self.display_message("Capture Image...")
            time.sleep(1)
            img = self.camera.capture()

            if img:
                # Détecter visages
                self.display_message("Analyse Visage...")
                time.sleep(1)
                faces = self.face_recognizer.detect_faces(img)

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
                    time.sleep(1)
                    recognized = self.face_recognizer.recognize_face(img, self.known_faces)

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

    def run_logic(self):
        """Logique principale ESP32"""
        while True:
            # Vérifier messages d'Arduino
            arduino_message = self.receive_from_arduino()
            if arduino_message:
                self.handle_arduino_message(arduino_message)

            # Logique selon état
            if self.current_state == STATE_FACIAL_RECOGNITION:
                self.perform_facial_recognition()
                break  # Sortir après reconnaissance pour simulation

            time.sleep(0.1)

def run_simulation():
    """Fonction principale de simulation"""
    print("=== Simulation Système Accès Porte ESP32 + Arduino Uno ===")
    print("ESP32: Caméra, reconnaissance faciale, logique principale")
    print("Arduino: LCD, clavier, servo moteur")
    print("Communication: Liaison série simulée")
    print()

    # Initialiser communication simulée
    uart = MockUART()

    # Initialiser systèmes simulés
    esp32 = MockESP32System(uart)
    arduino = MockArduino(uart)

    print("Démarrage simulation système accès porte...")
    print("Appuyez sur Ctrl+C pour arrêter")
    print()

    # Démarrer Arduino (simulation clavier)
    arduino_thread = threading.Thread(target=lambda: arduino.simulate_keypad())
    arduino_thread.daemon = True
    arduino_thread.start()

    try:
        # Initialiser système
        esp32.display_message("Systeme Pret")
        time.sleep(1)

        # Simuler début processus d'authentification
        print("\n--- Simulation saisie mot de passe ---")
        arduino.state = "PASSWORD"
        arduino.update_lcd()

        # Attendre simulation clavier
        time.sleep(3)

        # Simuler reconnaissance faciale
        print("\n--- Simulation reconnaissance faciale ---")
        esp32.run_logic()

        print("\n=== Simulation terminée ===")

    except KeyboardInterrupt:
        print("\nSimulation arrêtée par l'utilisateur")

if __name__ == "__main__":
    run_simulation()