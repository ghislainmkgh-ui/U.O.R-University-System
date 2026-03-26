# Driver LCD 1602 Mode 4-bit Direct pour ESP32/MicroPython
# Connexion directe GPIO sans interface I2C

import time
from machine import Pin

# Commandes LCD
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Drapeaux pour le mode d'entrée d'affichage
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Drapeaux pour on/off d'affichage
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# Drapeaux pour déplacement affichage/cursor
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# Drapeaux pour set de fonction
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

class LCD1602:
    def __init__(self, rs_pin, en_pin, d4_pin, d5_pin, d6_pin, d7_pin, rw_pin=None, backlight_pin=None):
        # Initialiser les broches GPIO
        self.rs = Pin(rs_pin, Pin.OUT)  # Register Select (0=command, 1=data)
        self.en = Pin(en_pin, Pin.OUT)  # Enable
        self.d4 = Pin(d4_pin, Pin.OUT)  # Data bit 4
        self.d5 = Pin(d5_pin, Pin.OUT)  # Data bit 5
        self.d6 = Pin(d6_pin, Pin.OUT)  # Data bit 6
        self.d7 = Pin(d7_pin, Pin.OUT)  # Data bit 7

        # Broches optionnelles
        self.rw = Pin(rw_pin, Pin.OUT) if rw_pin is not None else None  # Read/Write (généralement connecté à GND)
        self.backlight = Pin(backlight_pin, Pin.OUT) if backlight_pin is not None else None

        # Variable pour stocker l'état d'affichage
        self.displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF

        # Initialiser LCD
        self._initialize_lcd()

    def _initialize_lcd(self):
        """Initialiser LCD en mode 4-bit"""
        # Attendre que LCD soit prêt
        time.sleep_ms(50)

        # Séquence d'initialisation pour mode 4-bit
        self.rs.value(0)  # Mode commande
        if self.rw:
            self.rw.value(0)  # Mode écriture

        # Envoyer 0x03 trois fois
        self._write_4bits(0x03)
        time.sleep_ms(5)
        self._write_4bits(0x03)
        time.sleep_ms(1)
        self._write_4bits(0x03)
        time.sleep_ms(1)

        # Passer en mode 4-bit
        self._write_4bits(0x02)

        # Configurer LCD: 4-bit, 2 lignes, 5x8 points
        self._write_command(LCD_FUNCTIONSET | LCD_4BITMODE | LCD_2LINE | LCD_5x8DOTS)

        # Activer affichage, cursor off, blink off
        self._write_command(LCD_DISPLAYCONTROL | self.displaycontrol)

        # Effacer écran
        self._write_command(LCD_CLEARDISPLAY)
        time.sleep_ms(2)

        # Mode entrée: increment, no shift
        self._write_command(LCD_ENTRYMODESET | LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT)

        # Allumer rétroéclairage si disponible
        if self.backlight:
            self.backlight.value(1)

    def _write_4bits(self, value):
        """Écrire 4 bits sur les broches de données"""
        self.d4.value((value >> 0) & 0x01)
        self.d5.value((value >> 1) & 0x01)
        self.d6.value((value >> 2) & 0x01)
        self.d7.value((value >> 3) & 0x01)

        # Pulse Enable
        self._pulse_enable()

    def _pulse_enable(self):
        """Générer pulse Enable"""
        self.en.value(0)
        time.sleep_us(1)
        self.en.value(1)
        time.sleep_us(1)
        self.en.value(0)
        time.sleep_us(100)

    def _write_command(self, cmd):
        """Écrire une commande"""
        self.rs.value(0)  # Mode commande
        if self.rw:
            self.rw.value(0)  # Mode écriture

        # Écrire les 4 bits de poids fort
        self._write_4bits(cmd >> 4)
        # Écrire les 4 bits de poids faible
        self._write_4bits(cmd & 0x0F)

    def _write_data(self, data):
        """Écrire des données"""
        self.rs.value(1)  # Mode données
        if self.rw:
            self.rw.value(0)  # Mode écriture

        # Écrire les 4 bits de poids fort
        self._write_4bits(data >> 4)
        # Écrire les 4 bits de poids faible
        self._write_4bits(data & 0x0F)

    def write_command(self, cmd):
        """Interface publique pour écrire commande"""
        self._write_command(cmd)

    def write_data(self, data):
        """Interface publique pour écrire données"""
        self._write_data(data)

    def clear(self):
        """Effacer affichage"""
        self._write_command(LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def home(self):
        """Retourner cursor à la position home"""
        self._write_command(LCD_RETURNHOME)
        time.sleep_ms(2)

    def set_cursor(self, col, row):
        """Définir position cursor"""
        if row == 0:
            self._write_command(LCD_SETDDRAMADDR | col)
        else:
            self._write_command(LCD_SETDDRAMADDR | (0x40 + col))

    def write(self, text):
        """Écrire texte sur LCD"""
        if isinstance(text, str):
            for char in text:
                self._write_data(ord(char))
        else:
            self._write_data(text)

    def display_on(self):
        """Allumer affichage"""
        self.displaycontrol |= LCD_DISPLAYON
        self._write_command(LCD_DISPLAYCONTROL | self.displaycontrol)

    def display_off(self):
        """Éteindre affichage"""
        self.displaycontrol &= ~LCD_DISPLAYON
        self._write_command(LCD_DISPLAYCONTROL | self.displaycontrol)

    def backlight_on(self):
        """Allumer rétroéclairage"""
        if self.backlight:
            self.backlight.value(1)

    def backlight_off(self):
        """Éteindre rétroéclairage"""
        if self.backlight:
            self.backlight.value(0)