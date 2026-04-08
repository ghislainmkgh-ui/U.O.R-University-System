/*
  ============================================================
  U.O.R - ESP32 Access Control (Single File Arduino IDE)
  ============================================================
  Architecture:
    - ESP32 + Keypad 4x4 + Servo + LEDs + LCD I2C
    - Envoi code -> serveur Python HTTP /verify_code
    - Réponse JSON: {"access":"granted|denied","name":"...","reason":"..."}

  IMPORTANT:
    1) Ce fichier est autonome (un seul .ino)
    2) Installer bibliothèques Arduino IDE:
       - Keypad by Mark Stanley, Alexander Brevig
       - LiquidCrystal I2C by Frank de Brabander
       - ESP32Servo by Kevin Harrington / John K. Bennett
    3) Carte: "ESP32 Dev Module"
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>

// ============================================================
// CONFIGURATION
// ============================================================
const char* WIFI_SSID     = "SOFTWARE ENGINEERING";
const char* WIFI_PASSWORD = "08450mkgh";

// IP du PC où tourne access_server.py (passerelle ICS Windows = 192.168.137.1)
const char* SERVER_URL = "http://192.168.137.1:5050/verify_code";

// LCD I2C
const uint8_t LCD_ADDR = 0x27;
const uint8_t LCD_COLS = 16;
const uint8_t LCD_ROWS = 2;
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

// Servo
const int SERVO_PIN = 18;
const int SERVO_OPEN_ANGLE = 90;
const int SERVO_CLOSED_ANGLE = 0;
const int DOOR_OPEN_DURATION_MS = 5000;
Servo doorServo;

// LEDs
const int LED_GREEN_PIN = 2;
const int LED_RED_PIN   = 4;

// Keypad 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }
};

// NOTE: adapte si ton cablage keypad est différent
byte rowPins[ROWS] = {13, 12, 14, 27};
byte colPins[COLS] = {26, 25, 33, 32};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// Saisie
String enteredCode = "";
unsigned long lastKeyTime = 0;
const unsigned long ENTRY_TIMEOUT_MS = 30000;
const int MAX_CODE_LEN = 10;

// ============================================================
// UTILITAIRES LCD / LED
// ============================================================
void lcdShow(const String& line1, const String& line2) {
  // Keepalive backlight: certains modules I2C perdent l'état après bruit/alim instable
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1.substring(0, LCD_COLS));
  lcd.setCursor(0, 1);
  lcd.print(line2.substring(0, LCD_COLS));
}

void blinkLed(int pin, int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(delayMs);
    digitalWrite(pin, LOW);
    delay(delayMs);
  }
}

void signalGranted() {
  digitalWrite(LED_RED_PIN, LOW);
  blinkLed(LED_GREEN_PIN, 2, 120);
  digitalWrite(LED_GREEN_PIN, HIGH);
}

void signalDenied() {
  digitalWrite(LED_GREEN_PIN, LOW);
  blinkLed(LED_RED_PIN, 4, 80);
}

void signalProcessing() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(LED_GREEN_PIN, HIGH);
    digitalWrite(LED_RED_PIN, LOW);
    delay(160);
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_RED_PIN, HIGH);
    delay(160);
  }
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
}

void signalKeyPressed() {
  digitalWrite(LED_GREEN_PIN, HIGH);
  delay(60);
  digitalWrite(LED_GREEN_PIN, LOW);
}

// ============================================================
// SERVO
// ============================================================
void closeDoor() {
  doorServo.write(SERVO_CLOSED_ANGLE);
}

void openDoorTimed() {
  doorServo.write(SERVO_OPEN_ANGLE);
  delay(DOOR_OPEN_DURATION_MS);
  closeDoor();
}

// ============================================================
// JSON léger (sans ArduinoJson)
// ============================================================
String extractJsonStringField(const String& json, const String& key) {
  // Cherche "key" : "value" (tolérant aux espaces)
  String keyPattern = "\"" + key + "\"";
  int keyPos = json.indexOf(keyPattern);
  if (keyPos < 0) return "";

  int colonPos = json.indexOf(':', keyPos + keyPattern.length());
  if (colonPos < 0) return "";

  int start = json.indexOf('"', colonPos);
  if (start < 0) return "";
  start += 1;

  int end = json.indexOf('"', start);
  if (end < 0) return "";
  return json.substring(start, end);
}

bool responseGranted(const String& json) {
  String access = extractJsonStringField(json, "access");
  access.toLowerCase();
  return access == "granted";
}

// ============================================================
// RÉSEAU / HTTP
// ============================================================
bool connectWiFi() {
  // Réinitialiser proprement le stack WiFi avant de relancer une connexion
  WiFi.disconnect(true);
  delay(200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  lcdShow("Connexion WiFi", WIFI_SSID);
  Serial.printf("Connexion WiFi a %s ...\n", WIFI_SSID);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 25) {
    delay(600);
    retries++;
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    String ip = WiFi.localIP().toString();
    Serial.println("WiFi connecte: " + ip);
    lcdShow("WiFi connecte", ip);
    delay(1000);
    return true;
  }

  Serial.println("ERREUR: WiFi non connecte");
  lcdShow("ERREUR WiFi", "Verifier reseau");
  return false;
}

String sendCodeToServer(const String& code, int& httpCode) {
  String payload = "{\"code\":\"" + code + "\"}";
  String body = "";
  httpCode = -1;

  // Réduit les faux -11: 2 tentatives POST avec nouveau client TCP à chaque fois
  for (int attempt = 1; attempt <= 2; attempt++) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(10000); // timeout de connexion TCP
    http.setTimeout(200000);       // timeout lecture réponse HTTP

    if (!http.begin(client, SERVER_URL)) {
      Serial.println("HTTP begin() failed");
      httpCode = -4;
      delay(250);
      continue;
    }

    http.addHeader("Content-Type", "application/json");

    // Keep-alive: blink LED vert pendant transmission pour confirmer activité
    blinkLed(LED_GREEN_PIN, 1, 100);
    httpCode = http.POST(payload);

    if (httpCode > 0) {
      body = http.getString();
      http.end();
      return body;
    }

    Serial.printf("POST tentative %d/2 echouee, code=%d\n", attempt, httpCode);
    http.end();
    delay(350);
  }

  return body;
}

// ============================================================
// FLUX MÉTIER
// ============================================================
void processCode() {
  String code = enteredCode;
  enteredCode = "";

  Serial.printf("Code saisi (%d car.) -> verification serveur\n", code.length());
  lcdShow("Verification...", "Capture camera");
  signalProcessing();

  if (WiFi.status() != WL_CONNECTED) {
    if (!connectWiFi()) {
      Serial.println("WiFi indisponible -> pas d'envoi HTTP");
      lcdShow("ACCES REFUSE", "WiFi indispo");
      signalDenied();
      delay(1200);
      lcdShow("Pret", "Code + #");
      return;
    }
  }

  int httpCode = -1;
  String response = sendCodeToServer(code, httpCode);

  if (httpCode <= 0) {
    Serial.printf("HTTP erreur: %d\n", httpCode);
    lcdShow("ACCES REFUSE", "Timeout reseau");
    signalDenied();
    delay(1200);
    lcdShow("Pret", "Code + #");
    return;
  }

  Serial.printf("HTTP %d -> %s\n", httpCode, response.c_str());

  if (responseGranted(response)) {
    String name = extractJsonStringField(response, "name");
    if (name.length() == 0) name = "Etudiant";

    Serial.println("ACCES ACCORDE - " + name);
    lcdShow("ACCES ACCORDE", name);
    signalGranted();
    openDoorTimed();
    digitalWrite(LED_GREEN_PIN, LOW);
  } else {
    String reason = extractJsonStringField(response, "reason");
    if (reason.length() == 0) reason = "Refuse";

    Serial.println("ACCES REFUSE - " + reason);
    lcdShow("ACCES REFUSE", reason);
    signalDenied();
  }

  delay(1000);
  lcdShow("Pret", "Code + #");
}

void handleKey(char key) {
  lastKeyTime = millis();

  if (key == '*') {
    enteredCode = "";
    Serial.println("Saisie annulee");
    lcdShow("Annule", "Entrez code");
    signalDenied();
    delay(400);
    lcdShow("Pret", "Code + #");
    return;
  }

  if (key == '#') {
    if (enteredCode.length() > 0) {
      processCode();
    }
    return;
  }

  if (enteredCode.length() < MAX_CODE_LEN) {
    enteredCode += key;
    String masked = "";
    for (int i = 0; i < enteredCode.length(); i++) masked += "*";
    lcdShow("Entrez code", masked);
    signalKeyPressed();
    Serial.println("Code: " + masked);
  } else {
    Serial.println("Code trop long");
    lcdShow("Code trop long", "Appuyez *");
    signalDenied();
  }
}

// ============================================================
// SETUP / LOOP
// ============================================================
void setup() {
  Serial.begin(115200);

  // Évite les latences supplémentaires liées au mode économiseur WiFi
  WiFi.setSleep(false);

  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);

  // Servo (ESP32Servo)
  doorServo.setPeriodHertz(50);
  doorServo.attach(SERVO_PIN, 500, 2400);
  closeDoor();

  // LCD
  Wire.begin(21, 22);
  Wire.setClock(100000);
  lcd.init();
  lcd.backlight();
  lcdShow("U.O.R Access", "Demarrage...");

  Serial.println("======================================");
  Serial.println(" U.O.R - ESP32 Access (Arduino IDE)");
  Serial.println("======================================");

  if (!connectWiFi()) {
    // Mode dégradé: continue et retente dans loop
    lcdShow("WiFi indispo", "Reessayer...");
  }

  blinkLed(LED_GREEN_PIN, 3, 90);
  lcdShow("Pret", "Code + #");
  Serial.println("Pret. Tapez code puis #");
}

void loop() {
  // Keepalive backlight (si module LCD sensible aux chutes de tension)
  static unsigned long lastBacklightKick = 0;
  if (millis() - lastBacklightKick > 1500) {
    lastBacklightKick = millis();
    lcd.backlight();
  }

  // Timeout de saisie
  if (enteredCode.length() > 0 && (millis() - lastKeyTime) > ENTRY_TIMEOUT_MS) {
    enteredCode = "";
    Serial.println("Timeout: code efface");
    lcdShow("Timeout", "Code efface");
    signalDenied();
    delay(500);
    lcdShow("Pret", "Code + #");
  }

  // Reconnexion WiFi auto (toutes les 30s pour ne pas saturer le stack)
  static unsigned long lastWiFiCheck = 0;
  if (millis() - lastWiFiCheck > 30000) {
    lastWiFiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi perdu, tentative de reconnexion...");
      connectWiFi();
      lcdShow("Pret", "Code + #");
    }
  }

  char key = keypad.getKey();
  if (key) {
    handleKey(key);
  }
}
