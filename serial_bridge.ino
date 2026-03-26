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