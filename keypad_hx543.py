# Driver Clavier HX-543 pour ESP32/MicroPython
# Interface Clavier Matriciel 4x4

from machine import Pin
import time

class KeypadHX543:
    def __init__(self, row_pins, col_pins):
        self.row_pins = [Pin(pin, Pin.OUT) for pin in row_pins]
        self.col_pins = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in col_pins]

        # Disposition du clavier
        self.keys = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]

        # Initialiser les lignes à haut
        for row in self.row_pins:
            row.value(1)

    def scan_keypad(self):
        for row_idx, row_pin in enumerate(self.row_pins):
            # Mettre la ligne actuelle à bas
            row_pin.value(0)

            # Vérifier chaque colonne
            for col_idx, col_pin in enumerate(self.col_pins):
                if col_pin.value() == 0:  # Touche appuyée (actif bas)
                    # Anti-rebond
                    time.sleep_ms(20)
                    if col_pin.value() == 0:
                        # Attendre le relâchement de la touche
                        while col_pin.value() == 0:
                            time.sleep_ms(10)
                        # Restaurer la ligne
                        row_pin.value(1)
                        return self.keys[row_idx][col_idx]

            # Restaurer la ligne
            row_pin.value(1)

        return None

    def get_key(self):
        return self.scan_keypad()