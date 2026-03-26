// Implémentation Configuration Matérielle Arduino Uno

#include "arduino_hardware.h"

// Déclaration des objets matériels
LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
Servo doorServo;

// Variables d'état
HardwareState hardwareState = HW_INIT;

// Instance globale
ArduinoHardware arduinoHW;

ArduinoHardware::ArduinoHardware() :
  lcdInitialized(false),
  keypadInitialized(false),
  servoInitialized(false),
  serialInitialized(false) {
}

bool ArduinoHardware::initializeHardware() {
  hardwareState = HW_INIT;

  // Initialisation LCD
  lcd.begin(16, 2);
  lcd.print("Initialisation...");
  lcdInitialized = true;

  // Initialisation servo
  doorServo.attach(SERVO_PIN);
  doorServo.write(SERVO_CLOSED_ANGLE); // Position initiale fermée
  servoInitialized = true;

  // Initialisation communication série
  Serial.begin(SERIAL_BAUDRATE);
  serialInitialized = true;

  // Le clavier n'a pas besoin d'initialisation spécifique
  keypadInitialized = true;

  // Test des composants
  if (lcdInitialized && servoInitialized && serialInitialized && keypadInitialized) {
    updateLCD("Systeme Pret", "");
    hardwareState = HW_READY;
    return true;
  } else {
    updateLCD("Erreur Init", "Verifiez connexions");
    hardwareState = HW_ERROR;
    return false;
  }
}

void ArduinoHardware::updateLCD(const String& line1, const String& line2) {
  if (lcdInitialized) {
    lcd.clear();
    lcd.print(line1);
    if (line2.length() > 0) {
      lcd.setCursor(0, 1);
      lcd.print(line2);
    }
  }
}

char ArduinoHardware::readKeypad() {
  if (keypadInitialized) {
    return keypad.getKey();
  }
  return NO_KEY;
}

void ArduinoHardware::openDoor() {
  if (servoInitialized) {
    doorServo.write(SERVO_OPEN_ANGLE);
    updateLCD("Acces Autorise", "Porte Ouverte");
  }
}

void ArduinoHardware::closeDoor() {
  if (servoInitialized) {
    doorServo.write(SERVO_CLOSED_ANGLE);
    updateLCD("Porte Fermee", "");
  }
}

void ArduinoHardware::sendToESP32(const String& message) {
  if (serialInitialized) {
    Serial.println(message);
  }
}

String ArduinoHardware::receiveFromESP32() {
  if (serialInitialized && Serial.available()) {
    return Serial.readStringUntil('\n');
  }
  return "";
}

void ArduinoHardware::cleanup() {
  if (servoInitialized) {
    doorServo.detach();
  }
  if (serialInitialized) {
    Serial.end();
  }
  hardwareState = HW_INIT;
}