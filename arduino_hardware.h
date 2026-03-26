// Configuration Matérielle Arduino Uno
// Séparation du code matériel pour meilleure organisation

#ifndef ARDUINO_HARDWARE_H
#define ARDUINO_HARDWARE_H

#include <Arduino.h>
#include <LiquidCrystal.h>
#include <Keypad.h>
#include <Servo.h>

// Configuration LCD
const int LCD_RS = 12;
const int LCD_EN = 11;
const int LCD_D4 = 5;
const int LCD_D5 = 4;
const int LCD_D6 = 3;
const int LCD_D7 = 2;

// Configuration clavier matriciel 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {9, 8, 7, 6};     // GPIO Arduino pour lignes
byte colPins[COLS] = {13, 10, A0, A1}; // GPIO Arduino pour colonnes

// Configuration servo
const int SERVO_PIN = A2; // GPIO A2 pour servo
const int SERVO_CLOSED_ANGLE = 0;   // Angle porte fermée
const int SERVO_OPEN_ANGLE = 90;    // Angle porte ouverte

// Configuration communication série
const long SERIAL_BAUDRATE = 9600;

// Variables globales matérielles
extern LiquidCrystal lcd;
extern Keypad keypad;
extern Servo doorServo;

// États matériels
enum HardwareState {
  HW_INIT,
  HW_READY,
  HW_ERROR
};

extern HardwareState hardwareState;

class ArduinoHardware {
  public:
    ArduinoHardware();
    bool initializeHardware();
    void updateLCD(const String& line1, const String& line2 = "");
    char readKeypad();
    void openDoor();
    void closeDoor();
    void sendToESP32(const String& message);
    String receiveFromESP32();
    void cleanup();

  private:
    bool lcdInitialized;
    bool keypadInitialized;
    bool servoInitialized;
    bool serialInitialized;
};

extern ArduinoHardware arduinoHW;

#endif