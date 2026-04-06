// [OBSOLÈTE] Pont série Arduino ↔ ESP32-CAM
// =============================================
// Ce fichier n'est plus utilisé dans la nouvelle architecture.
// La communication UART entre Arduino et ESP32-CAM est supprimée.
// L'ESP32 standard communique directement via Wi-Fi avec le serveur Python.
// Voir esp32_firmware.py pour le nouveau firmware.
// =============================================

// Ancien code conservé pour référence uniquement.

#include <SoftwareSerial.h>

SoftwareSerial espSerial(2, 3); // RX, TX

void setup() {
  Serial.begin(115200);  // USB serial
  espSerial.begin(115200); // Pins 2/3 serial
}

void loop() {
  // Forward from USB to ESP32
  if (Serial.available()) {
    espSerial.write(Serial.read());
  }
  // Forward from ESP32 to USB
  if (espSerial.available()) {
    Serial.write(espSerial.read());
  }
}