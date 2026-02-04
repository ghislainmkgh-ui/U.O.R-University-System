import serial
import time

class ArduinoBridge:
    """Gère la communication série entre l'Arduino et le logiciel Python."""

    def __init__(self, port='COM3', baudrate=9600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2) # Attente de l'initialisation
        except Exception as e:
            print(f"Erreur de connexion Arduino : {e}")
            self.ser = None

    def ecouter_clavier(self, callback_validation):
        """Boucle d'écoute pour détecter le mot de passe tapé à la porte."""
        if not self.ser: return

        while True:
            if self.ser.in_waiting > 0:
                ligne = self.ser.readline().decode('utf-8').strip()
                
                if ligne.startswith("PASS:"):
                    mdp_tape = ligne.split(":")[1]
                    # On lance la validation (MDP -> VISAGE -> FINANCE)
                    callback_validation(mdp_tape)