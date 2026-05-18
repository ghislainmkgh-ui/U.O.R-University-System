/*
  ============================================================
  U.O.R - ESP32 Access Control Prototype
  ============================================================
  Cette version gère :
    - validation code + reconnaissance faciale
    - ouverture de porte pendant une fenêtre courte
    - détection de passage unique avec deux HC-SR04
    - état salle occupée / libre
    - sortie intérieure par bouton
    - accès autorités par badge RFID (optionnel)

  Bibliothèques Arduino IDE nécessaires :
    - Keypad by Mark Stanley, Alexander Brevig
    - LiquidCrystal I2C by Frank de Brabander
    - ESP32Servo by Kevin Harrington / John K. Bennett
    - MFRC522 by GithubCommunity (optionnel pour RFID)

  Carte : "ESP32 Dev Module"
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>

#define USE_RFID 0
// Avec deux HC-SR04 sur GPIO18/19, le MFRC522 SPI reste désactivé.
// Pour les badges autorités, préférer PN532 I2C ou remapper SPI avant USE_RFID=1.
#if USE_RFID
#include <SPI.h>
#include <MFRC522.h>
#endif

// ============================================================
// CONFIGURATION
// ============================================================

const char* WIFI_SSID     = "SOFTWARE ENGINEERING";
const char* WIFI_PASSWORD = "08450mkgh";

const char* VALIDATE_CODE_URL = "http://192.168.137.1:5050/validate_code";
const char* VERIFY_FACE_URL   = "http://192.168.137.1:5050/verify_face";
const char* VERIFY_BADGE_URL  = "http://192.168.137.1:5050/verify_badge"; // optional server endpoint
const char* HARDWARE_EVENT_URL = "http://192.168.137.1:5050/hardware_event";
const char* DEVICE_ID = "ESP32_DOOR_01";

const uint8_t LCD_ADDR = 0x27;
const uint8_t LCD_COLS = 16;
const uint8_t LCD_ROWS = 2;
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);
bool lcdAvailable = false;

const int SERVO_PIN = 4;
const int SERVO_OPEN_ANGLE = 90;
const int SERVO_CLOSED_ANGLE = 0;
const int DOOR_OPEN_DURATION_MS = 2200;
const int SERVO_MOVE_STEP_DELAY_MS = 25;
const int SERVO_STEP_DEGREES = 4;
Servo doorServo;

const int LED_GREEN_PIN = 2;
const int LED_RED_PIN   = 15;

const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }
};
byte rowPins[ROWS] = {13, 12, 14, 27};
byte colPins[COLS] = {26, 25, 33, 32};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String enteredCode = "";
unsigned long lastKeyTime = 0;
const unsigned long ENTRY_TIMEOUT_MS = 30000;
const int MAX_CODE_LEN = 10;

const int ULTRASON_OUT_TRIG_PIN = 16;
const int ULTRASON_OUT_ECHO_PIN = 17;
const int ULTRASON_IN_TRIG_PIN  = 18;
const int ULTRASON_IN_ECHO_PIN  = 19;

const float ENTRY_ZONE_CLEAR_CM = 30.0; // zone libre si > 30 cm
const float ENTRY_DETECT_CM = 20.0;    // personne detectee si <= 20 cm
const unsigned long ENTRY_WINDOW_MS = 2400;
const unsigned long PASSAGE_STABLE_MS = 350;
const unsigned long EXIT_WINDOW_MS = 3000;

const int DOOR_SENSOR_PIN = 34;
const int EXIT_BUTTON_PIN = 35;

const unsigned long HTTP_CONNECT_TIMEOUT_MS = 10000;
const unsigned long HTTP_TIMEOUT_VALIDATE_MS = 12000;
const unsigned long HTTP_TIMEOUT_VERIFY_FACE_MS = 65000;
const unsigned long FACE_PREPARE_DELAY_MS = 2200;

#if USE_RFID
const int RFID_SS_PIN  = 5;
const int RFID_RST_PIN = 0;
MFRC522 rfid(RFID_SS_PIN, RFID_RST_PIN);

const char* AUTHORITY_BADGES[] = {
  "04AABBCCDD",
  "0455667788"
};
const int AUTHORITY_BADGE_COUNT = sizeof(AUTHORITY_BADGES) / sizeof(AUTHORITY_BADGES[0]);
#endif

enum SystemState {
  STATE_IDLE,
  STATE_PROCESSING_CODE,
  STATE_PROCESSING_FACE,
  STATE_AWAIT_ENTRY,
  STATE_OCCUPIED,
  STATE_EXIT_REQUESTED,
  STATE_AUTHORITY_CHECK
};

SystemState systemState = STATE_IDLE;
bool roomOccupied = false;
String currentSessionId = "";
unsigned long lastWiFiCheck = 0;

// ============================================================
// UTILITAIRES LCD / LED
// ============================================================

bool i2cDevicePresent(uint8_t address) {
  Wire.beginTransmission(address);
  return (Wire.endTransmission() == 0);
}

void initLcdSafely() {
  Wire.begin(21, 22);
  Wire.setClock(100000);
  delay(250);

  bool hasLcd = i2cDevicePresent(LCD_ADDR);
  if (!hasLcd) {
    Serial.println("ATTENTION: LCD non detecte sur 0x27");
    lcdAvailable = false;
    return;
  }

  lcdAvailable = true;
  for (int i = 0; i < 3; i++) {
    lcd.init();
    delay(40);
  }
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("U.O.R Access");
  lcd.setCursor(0, 1);
  lcd.print("LCD initialise");
  delay(500);
  lcd.clear();
}

void lcdShow(const String& line1, const String& line2) {
  if (!lcdAvailable) return;
  lcd.backlight();
  int pages = max(1, max((line1.length() + LCD_COLS - 1) / LCD_COLS,
                         (line2.length() + LCD_COLS - 1) / LCD_COLS));
  for (int page = 0; page < pages; page++) {
    String p1 = line1.substring(page * LCD_COLS, min((int)line1.length(), (page + 1) * LCD_COLS));
    String p2 = line2.substring(page * LCD_COLS, min((int)line2.length(), (page + 1) * LCD_COLS));
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(p1);
    lcd.setCursor(0, 1);
    lcd.print(p2);
    if (pages > 1 && page < pages - 1) {
      delay(900);
    }
  }
}

void blinkLed(int pin, int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(delayMs);
    digitalWrite(pin, LOW);
    delay(delayMs);
  }
}

void clearStatusLeds() {
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
}

void signalGranted() {
  digitalWrite(LED_RED_PIN, LOW);
  blinkLed(LED_GREEN_PIN, 2, 90);
  digitalWrite(LED_GREEN_PIN, LOW);
}

void signalDenied() {
  digitalWrite(LED_GREEN_PIN, LOW);
  blinkLed(LED_RED_PIN, 2, 90);
  digitalWrite(LED_RED_PIN, HIGH);
}

void signalProcessing() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(LED_GREEN_PIN, HIGH);
    digitalWrite(LED_RED_PIN, LOW);
    delay(120);
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_RED_PIN, HIGH);
    delay(120);
  }
  clearStatusLeds();
}

void signalKeyPressed() {
  digitalWrite(LED_GREEN_PIN, HIGH);
  delay(60);
  digitalWrite(LED_GREEN_PIN, LOW);
}

// ============================================================
// SERVO
// ============================================================

void moveDoorSafely(int fromAngle, int toAngle) {
  if (fromAngle == toAngle) {
    doorServo.write(toAngle);
    return;
  }

  int step = (toAngle > fromAngle) ? SERVO_STEP_DEGREES : -SERVO_STEP_DEGREES;
  int angle = fromAngle;
  while ((step > 0 && angle < toAngle) || (step < 0 && angle > toAngle)) {
    angle += step;
    if ((step > 0 && angle > toAngle) || (step < 0 && angle < toAngle)) {
      angle = toAngle;
    }
    doorServo.write(angle);
    delay(SERVO_MOVE_STEP_DELAY_MS);
  }
}

void closeDoor() {
  moveDoorSafely(doorServo.read(), SERVO_CLOSED_ANGLE);
}

void openDoor() {
  moveDoorSafely(doorServo.read(), SERVO_OPEN_ANGLE);
}

// ============================================================
// ULTRASON
// ============================================================

float readUltrasonicDistanceCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) {
    return -1.0;
  }
  return duration * 0.0343 / 2.0;
}

bool isUltrasonicZoneClear(int trigPin, int echoPin) {
  float distance = readUltrasonicDistanceCm(trigPin, echoPin);
  if (distance < 0) {
    return false;
  }
  return distance > ENTRY_ZONE_CLEAR_CM;
}

bool isEntryZonesClear() {
  return isUltrasonicZoneClear(ULTRASON_OUT_TRIG_PIN, ULTRASON_OUT_ECHO_PIN) &&
         isUltrasonicZoneClear(ULTRASON_IN_TRIG_PIN, ULTRASON_IN_ECHO_PIN);
}

enum PassageDirection {
  PASSAGE_ENTRY,
  PASSAGE_EXIT
};

enum PassageResult {
  PASSAGE_CONFIRMED,
  PASSAGE_TIMEOUT,
  PASSAGE_INVALID
};

PassageResult waitForDirectionalPassage(PassageDirection direction, unsigned long windowMs) {
  unsigned long startMs = millis();
  bool firstPresent = false;
  bool secondPresent = false;
  bool firstSeen = false;
  bool secondSeen = false;
  unsigned long secondClearMs = 0;
  int firstCount = 0;
  int secondCount = 0;

  const bool entryDirection = direction == PASSAGE_ENTRY;
  const char* firstLabel = entryDirection ? "exterieure" : "interieure";
  const char* secondLabel = entryDirection ? "interieure" : "exterieure";

  while (millis() - startMs < windowMs) {
    float outsideDistance = readUltrasonicDistanceCm(ULTRASON_OUT_TRIG_PIN, ULTRASON_OUT_ECHO_PIN);
    float insideDistance  = readUltrasonicDistanceCm(ULTRASON_IN_TRIG_PIN, ULTRASON_IN_ECHO_PIN);

    bool outsideDetected = (outsideDistance > 0 && outsideDistance <= ENTRY_DETECT_CM);
    bool insideDetected  = (insideDistance > 0 && insideDistance <= ENTRY_DETECT_CM);
    bool firstDetected = entryDirection ? outsideDetected : insideDetected;
    bool secondDetected = entryDirection ? insideDetected : outsideDetected;

    if (!firstSeen && firstDetected && secondDetected) {
      Serial.println("Passage invalide : deux zones detectees en meme temps");
      return PASSAGE_INVALID;
    }

    if (!firstSeen && secondDetected) {
      Serial.println("Passage invalide : ordre inverse detecte");
      return PASSAGE_INVALID;
    }

    if (firstDetected && !firstPresent) {
      firstPresent = true;
      firstSeen = true;
      firstCount++;
      Serial.printf("Zone %s detectee #%d\n", firstLabel, firstCount);
    }
    if (!firstDetected && firstPresent) {
      firstPresent = false;
    }

    if (secondDetected && !secondPresent) {
      if (!firstSeen) {
        Serial.println("Passage invalide : deuxieme zone avant la premiere");
        return PASSAGE_INVALID;
      }
      secondPresent = true;
      secondSeen = true;
      secondCount++;
      Serial.printf("Zone %s detectee #%d\n", secondLabel, secondCount);
    }
    if (!secondDetected && secondPresent) {
      secondPresent = false;
      secondClearMs = millis();
    }

    if (firstCount > 1 || secondCount > 1) {
      Serial.println("Passage invalide : detections multiples");
      return PASSAGE_INVALID;
    }

    if (firstSeen && secondSeen && !secondPresent && secondClearMs > 0 && millis() - secondClearMs > PASSAGE_STABLE_MS) {
      return PASSAGE_CONFIRMED;
    }

    delay(80);
  }

  Serial.println("Passage incomplet : timeout");
  return PASSAGE_TIMEOUT;
}

// ============================================================
// DOOR / EXIT
// ============================================================

bool isDoorClosed() {
  return digitalRead(DOOR_SENSOR_PIN) == LOW;
}

bool isExitButtonPressed() {
  return digitalRead(EXIT_BUTTON_PIN) == LOW;
}

PassageResult openDoorForEntry() {
  openDoor();
  PassageResult passage = waitForDirectionalPassage(PASSAGE_ENTRY, ENTRY_WINDOW_MS);
  closeDoor();
  return passage;
}

PassageResult processExitDoor() {
  openDoor();
  unsigned long openStart = millis();
  bool doorOpened = false;

  while (millis() - openStart < 1500) {
    if (!isDoorClosed()) {
      doorOpened = true;
      break;
    }
    delay(80);
  }

  if (!doorOpened) {
    Serial.println("Sortie echouee : porte n'a pas ouvert");
    closeDoor();
    return PASSAGE_TIMEOUT;
  }

  PassageResult passage = waitForDirectionalPassage(PASSAGE_EXIT, EXIT_WINDOW_MS);
  closeDoor();

  if (passage != PASSAGE_CONFIRMED) {
    return passage;
  }

  unsigned long closeStart = millis();
  while (millis() - closeStart < 1500) {
    if (isDoorClosed()) {
      Serial.println("Sortie confirmee : passage + porte refermee");
      return PASSAGE_CONFIRMED;
    }
    delay(80);
  }

  Serial.println("Sortie detectee, mais porte non confirmee fermee");
  return PASSAGE_TIMEOUT;
}

// ============================================================
// JSON / HTTP
// ============================================================

String extractJsonStringField(const String& json, const String& key) {
  String pattern = String("\"") + key + "\"";
  int keyPos = json.indexOf(pattern);
  if (keyPos < 0) return "";

  int colonPos = json.indexOf(':', keyPos + pattern.length());
  if (colonPos < 0) return "";

  int quoteStart = json.indexOf('"', colonPos);
  if (quoteStart < 0) return "";
  int quoteEnd = json.indexOf('"', quoteStart + 1);
  if (quoteEnd < 0) return "";
  return json.substring(quoteStart + 1, quoteEnd);
}

bool responseGranted(const String& json) {
  String access = extractJsonStringField(json, "access");
  access.toLowerCase();
  return access == "granted";
}

bool responseCodeValid(const String& json) {
  String access = extractJsonStringField(json, "access");
  access.toLowerCase();
  return access == "pending_face" || access == "granted";
}

String jsonBool(bool value) {
  return value ? "true" : "false";
}

String deviceStateJson() {
  return String("\"device_id\":\"") + DEVICE_ID + "\"," +
         "\"room_occupied\":" + jsonBool(roomOccupied) + "," +
         "\"door_closed\":" + jsonBool(isDoorClosed()) + "," +
         "\"entry_zone_clear\":" + jsonBool(isEntryZonesClear());
}

String sendCodeToServer(const String& url, const String& code, int& httpCode, uint16_t readTimeoutMs = HTTP_TIMEOUT_VALIDATE_MS) {
  String payload = "{\"code\":\"" + code + "\"," + deviceStateJson() + "}";
  String body = "";
  httpCode = -1;

  for (int attempt = 1; attempt <= 2; attempt++) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(HTTP_CONNECT_TIMEOUT_MS);
    http.setTimeout(readTimeoutMs);
    if (!http.begin(client, url)) {
      Serial.println("HTTP begin() failed");
      httpCode = -4;
      delay(250);
      continue;
    }
    http.addHeader("Content-Type", "application/json");
    blinkLed(LED_GREEN_PIN, 1, 100);
    httpCode = http.POST(payload);
    if (httpCode > 0) {
      body = http.getString();
      http.end();
      return body;
    }
    Serial.printf("POST attempt %d failed, code=%d\n", attempt, httpCode);
    http.end();
    delay(350);
  }
  return body;
}

String sendJsonToServer(const String& url, const String& payload, int& httpCode, uint16_t readTimeoutMs = HTTP_TIMEOUT_VALIDATE_MS) {
  String body = "";
  httpCode = -1;

  for (int attempt = 1; attempt <= 2; attempt++) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(HTTP_CONNECT_TIMEOUT_MS);
    http.setTimeout(readTimeoutMs);
    if (!http.begin(client, url)) {
      httpCode = -4;
      delay(250);
      continue;
    }
    http.addHeader("Content-Type", "application/json");
    httpCode = http.POST(payload);
    if (httpCode > 0) {
      body = http.getString();
      http.end();
      return body;
    }
    http.end();
    delay(350);
  }
  return body;
}

void sendHardwareEvent(const String& eventName, const String& sessionId = "") {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  String payload = "{\"event\":\"" + eventName + "\"," + deviceStateJson();
  if (sessionId.length() > 0) {
    payload += ",\"session_id\":\"" + sessionId + "\"";
  }
  payload += "}";
  int httpCode = -1;
  String response = sendJsonToServer(HARDWARE_EVENT_URL, payload, httpCode, 6000);
  Serial.printf("EVENT %s -> HTTP %d %s\n", eventName.c_str(), httpCode, response.c_str());
}

// ============================================================
// AUTHORITY RFID (OPTIONAL)
// ============================================================

#if USE_RFID
bool isKnownAuthorityBadge(const String& badgeId) {
  for (int i = 0; i < AUTHORITY_BADGE_COUNT; i++) {
    if (badgeId == AUTHORITY_BADGES[i]) {
      return true;
    }
  }
  return false;
}

bool readAuthorityBadge(String& badgeId) {
  if (!rfid.PICC_IsNewCardPresent()) {
    return false;
  }
  if (!rfid.PICC_ReadCardSerial()) {
    return false;
  }
  badgeId = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    badgeId += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    badgeId += String(rfid.uid.uidByte[i], HEX);
  }
  badgeId.toUpperCase();
  rfid.PICC_HaltA();
  return true;
}

bool processAuthorityBadge(const String& badgeId) {
  Serial.println("Badge autorite lu : " + badgeId);

  if (WiFi.status() != WL_CONNECTED && !connectWiFi()) {
    lcdShow("Reseau indispo", "Badge refuse");
    signalDenied();
    delay(1200);
    clearStatusLeds();
    return false;
  }

  String payload = "{\"badge_id\":\"" + badgeId + "\"," + deviceStateJson() + "}";
  int httpCode = -1;
  String response = sendJsonToServer(VERIFY_BADGE_URL, payload, httpCode, HTTP_TIMEOUT_VALIDATE_MS);
  Serial.printf("BADGE HTTP %d -> %s\n", httpCode, response.c_str());

  if (httpCode <= 0 || !responseGranted(response)) {
    lcdShow("Badge non valide", "Refuse");
    signalDenied();
    delay(1200);
    clearStatusLeds();
    lcdShow("Entrez le code", "Puis appuyez #");
    return false;
  }
  lcdShow("Autorite valide", "Ouverture... ");
  signalGranted();
  openDoor();
  delay(2000);
  closeDoor();
  String sessionId = extractJsonStringField(response, "session_id");
  sendHardwareEvent("authority_access", sessionId);
  clearStatusLeds();
  lcdShow("Entree autorisee", "Autorite");
  delay(1200);
  lcdShow(roomOccupied ? "Salle occupee" : "Entrez le code", roomOccupied ? "Attente sortie" : "Puis appuyez #");
  return true;
}
#endif

// ============================================================
// PROCESS_DEMANDE
// ============================================================

void denyAccess(const String& message) {
  closeDoor();
  lcdShow("Acces refuse", message);
  signalDenied();
  delay(1300);
  clearStatusLeds();
  lcdShow(roomOccupied ? "Salle occupee" : "Entrez le code", roomOccupied ? "Attente sortie" : "Puis appuyez #");
}

void grantAccess(const String& name, const String& sessionId) {
  currentSessionId = sessionId;
  lcdShow("Acces accorde", name);
  signalGranted();
  PassageResult passage = openDoorForEntry();
  if (passage != PASSAGE_CONFIRMED) {
    sendHardwareEvent(passage == PASSAGE_TIMEOUT ? "entry_failed" : "passage_invalid", currentSessionId);
    currentSessionId = "";
    denyAccess("Passage non valide");
    return;
  }
  roomOccupied = true;
  sendHardwareEvent("entry_confirmed", currentSessionId);
  clearStatusLeds();
  lcdShow("Salle occupee", "Attente sortie");
}

void processCode() {
  String code = enteredCode;
  enteredCode = "";

  Serial.printf("Code saisi (%d car.) -> verification serveur\n", code.length());
  lcdShow("Verification...", "Validation code");
  signalProcessing();

  if (WiFi.status() != WL_CONNECTED && !connectWiFi()) {
    denyAccess("Reseau indisponible");
    return;
  }

  int httpCode = -1;
  String response = sendCodeToServer(VALIDATE_CODE_URL, code, httpCode, HTTP_TIMEOUT_VALIDATE_MS);
  if (httpCode <= 0) {
    denyAccess("Reseau indispo");
    return;
  }

  Serial.printf("HTTP %d -> %s\n", httpCode, response.c_str());
  if (!responseCodeValid(response)) {
    String reason = extractJsonStringField(response, "reason");
    if (reason.length() == 0) reason = "Code incorrect";
    denyAccess(reason);
    return;
  }

  String name = extractJsonStringField(response, "name");
  if (name.length() == 0) name = "Etudiant";

  lcdShow("Code valide", "Regardez camera");
  delay(FACE_PREPARE_DELAY_MS);
  lcdShow("Analyse visage", "Ne bougez pas");

  response = sendCodeToServer(VERIFY_FACE_URL, code, httpCode, HTTP_TIMEOUT_VERIFY_FACE_MS);
  if (httpCode <= 0) {
    denyAccess("Timeout visage");
    return;
  }

  Serial.printf("HTTP FACE %d -> %s\n", httpCode, response.c_str());
  if (responseGranted(response)) {
    String sessionId = extractJsonStringField(response, "session_id");
    if (!isDoorClosed()) {
      sendHardwareEvent("entry_failed", sessionId);
      denyAccess("Porte ouverte");
      return;
    }
    if (!isEntryZonesClear()) {
      sendHardwareEvent("entry_failed", sessionId);
      denyAccess("Zone occupee");
      return;
    }
    grantAccess(name, sessionId);
  } else {
    String reason = extractJsonStringField(response, "reason");
    if (reason.length() == 0) reason = "Non reconnu";
    denyAccess(reason);
  }
}

void handleKey(char key) {
  lastKeyTime = millis();

  if (key == '*') {
    enteredCode = "";
    Serial.println("Saisie annulee");
    lcdShow("Saisie annulee", "Recommencez");
    signalDenied();
    delay(400);
    clearStatusLeds();
    lcdShow(roomOccupied ? "Salle occupee" : "Entrez le code", roomOccupied ? "Attente sortie" : "Puis appuyez #");
    return;
  }

  if (key == '#') {
    if (enteredCode.length() == 0) {
      return;
    }
    if (roomOccupied) {
      denyAccess("Salle occupee");
      return;
    }
    if (!isDoorClosed()) {
      denyAccess("Porte ouverte");
      return;
    }
    if (!isEntryZonesClear()) {
      denyAccess("Zone occupee");
      return;
    }
    processCode();
    return;
  }

  if (enteredCode.length() < MAX_CODE_LEN) {
    enteredCode += key;
    String masked;
    for (int i = 0; i < enteredCode.length(); i++) {
      masked += "*";
    }
    lcdShow("Code en cours", masked + " #");
    signalKeyPressed();
    Serial.println("Saisie: " + masked);
  } else {
    Serial.println("Code trop long");
    lcdShow("Code trop long", "Appuyez sur *");
    signalDenied();
    delay(600);
    clearStatusLeds();
  }
}

// ============================================================
// RESEAU / HTTP
// ============================================================

bool connectWiFi() {
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

// ============================================================
// SETUP / LOOP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(100);

  WiFi.setSleep(false);

  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  clearStatusLeds();

  pinMode(ULTRASON_OUT_TRIG_PIN, OUTPUT);
  pinMode(ULTRASON_OUT_ECHO_PIN, INPUT);
  pinMode(ULTRASON_IN_TRIG_PIN, OUTPUT);
  pinMode(ULTRASON_IN_ECHO_PIN, INPUT);

  pinMode(DOOR_SENSOR_PIN, INPUT_PULLUP);
  pinMode(EXIT_BUTTON_PIN, INPUT_PULLUP);

#if USE_RFID
  SPI.begin();
  rfid.PCD_Init();
#endif

  doorServo.setPeriodHertz(50);
  doorServo.attach(SERVO_PIN, 500, 2400);
  closeDoor();

  initLcdSafely();
  lcdShow("U.O.R Access", "Demarrage...");

  Serial.println("======================================");
  Serial.println(" U.O.R - ESP32 Access Prototype");
  Serial.println("======================================");

  if (!connectWiFi()) {
    lcdShow("WiFi indispo", "Reessayer...");
  } else {
    sendHardwareEvent("state_sync", currentSessionId);
  }

  blinkLed(LED_GREEN_PIN, 3, 90);
  lcdShow("Entrez le code", "Puis appuyez #");
}

void loop() {
  static unsigned long lastBacklightKick = 0;
  if (millis() - lastBacklightKick > 1500) {
    lastBacklightKick = millis();
    if (lcdAvailable) {
      lcd.backlight();
    }
  }

  if (enteredCode.length() > 0 && (millis() - lastKeyTime) > ENTRY_TIMEOUT_MS) {
    enteredCode = "";
    Serial.println("Timeout: code efface");
    lcdShow("Temps ecoule", "Code efface");
    signalDenied();
    delay(500);
    clearStatusLeds();
    lcdShow(roomOccupied ? "Salle occupee" : "Entrez le code", roomOccupied ? "Attente sortie" : "Puis appuyez #");
  }

  if (millis() - lastWiFiCheck > 30000) {
    lastWiFiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi perdu, tentative de reconnexion...");
      connectWiFi();
      lcdShow(roomOccupied ? "Salle occupee" : "Entrez le code", roomOccupied ? "Attente sortie" : "Puis appuyez #");
    } else {
      sendHardwareEvent("state_sync", currentSessionId);
    }
  }

  char key = keypad.getKey();
  if (key) {
    handleKey(key);
  }

  if (roomOccupied && isExitButtonPressed()) {
    Serial.println("Sortie demandee");
    lcdShow("Sortie demandee", "Attendez...");
    signalProcessing();
    sendHardwareEvent("exit_requested", currentSessionId);
    PassageResult exitPassage = processExitDoor();
    if (exitPassage == PASSAGE_CONFIRMED) {
      roomOccupied = false;
      sendHardwareEvent("exit_confirmed", currentSessionId);
      currentSessionId = "";
      clearStatusLeds();
      lcdShow("Sortie realisee", "Salle libre");
      delay(1200);
    } else {
      sendHardwareEvent(exitPassage == PASSAGE_TIMEOUT ? "exit_failed" : "passage_invalid", currentSessionId);
      denyAccess("Sortie non confirmee");
    }
    lcdShow("Entrez le code", "Puis appuyez #");
    delay(600);
  }

#if USE_RFID
  String badgeId;
  if (readAuthorityBadge(badgeId)) {
    processAuthorityBadge(badgeId);
    delay(800);
  }
#endif
}
