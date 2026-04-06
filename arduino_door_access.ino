// [OBSOLÈTE] Système de Contrôle d'Accès Porte ESP32 Cam + Arduino Uno
// =========================================================================
// CE FICHIER N'EST PLUS UTILISÉ DANS LA NOUVELLE ARCHITECTURE.
//
// NOUVELLE ARCHITECTURE :
//   - L'Arduino Uno est remplacé par un ESP32 standard
//   - Le clavier matriciel et le servo sont directement connectés à l'ESP32
//   - Plus de communication UART entre ESP32 et Arduino
//   - Voir : esp32_firmware.py (MicroPython) à uploader sur l'ESP32
// =========================================================================

// Ancien code conservé pour référence uniquement.
//
// Système de Contrôle d'Accès Porte ESP32 Cam + Arduino Uno
// ESP32: Caméra, reconnaissance faciale, logique principale
// Arduino: LCD, clavier, servo moteur
// Communication: Liaison série UART

#include "arduino_hardware.h"

// États du système
#define STATE_IDLE 0
#define STATE_PASSWORD 1
#define STATE_FACIAL_RECOGNITION 2
#define STATE_ACCESS_GRANTED 3
#define STATE_ACCESS_DENIED 4

// Instance matériel Arduino
ArduinoHardware hardware;

// Variables système
int current_state = STATE_IDLE;
String entered_password = "";
unsigned long last_key_time = 0;
bool door_open = false;

void setup() {
    // Initialiser matériel Arduino
    if (!hardware.initializeHardware()) {
        // Erreur initialisation - clignoter LED
        while (true) {
            digitalWrite(13, HIGH);
            delay(500);
            digitalWrite(13, LOW);
            delay(500);
        }
    }

    // Message d'accueil
    hardware.displayMessage("Systeme Pret");
    delay(2000);
}

void loop() {
    // Vérifier messages ESP32
    String esp32_message = hardware.receiveFromESP32();
    if (esp32_message.length() > 0) {
        handleESP32Message(esp32_message);
    }

    // Logique principale selon état
    switch (current_state) {
        case STATE_IDLE:
            handleIdleState();
            break;

        case STATE_PASSWORD:
            handlePasswordState();
            break;

        case STATE_FACIAL_RECOGNITION:
            handleFacialRecognitionState();
            break;

        case STATE_ACCESS_GRANTED:
            handleAccessGrantedState();
            break;

        case STATE_ACCESS_DENIED:
            handleAccessDeniedState();
            break;
    }

    delay(100);
}

void handleIdleState() {
    // Attendre pression touche pour démarrer
    char key = hardware.readKeypad();
    if (key != NO_KEY) {
        // Démarrer processus authentification
        entered_password = "";
        setState(STATE_PASSWORD);
    }
}

void handlePasswordState() {
    hardware.displayMessage("Entrez Code:");
    hardware.displayPassword(entered_password);

    char key = hardware.readKeypad();
    if (key != NO_KEY) {
        last_key_time = millis();

        if (key == '#') {
            // Valider mot de passe
            if (validatePassword(entered_password)) {
                hardware.sendToESP32("PASSWORD_OK");
                setState(STATE_FACIAL_RECOGNITION);
            } else {
                hardware.sendToESP32("PASSWORD_INVALID");
                setState(STATE_ACCESS_DENIED);
            }
            entered_password = "";
        } else if (key == '*') {
            // Effacer dernier caractère
            if (entered_password.length() > 0) {
                entered_password.remove(entered_password.length() - 1);
            }
        } else if (key >= '0' && key <= '9') {
            // Ajouter chiffre
            if (entered_password.length() < 6) {
                entered_password += key;
            }
        }
    }

    // Timeout après 30 secondes d'inactivité
    if (millis() - last_key_time > 30000 && entered_password.length() > 0) {
        setState(STATE_ACCESS_DENIED);
        entered_password = "";
    }
}

void handleFacialRecognitionState() {
    // ESP32 gère la reconnaissance faciale
    // Attendre résultat
}

void handleAccessGrantedState() {
    hardware.displayMessage("Acces Autorise");
    hardware.openDoor();
    door_open = true;

    // Fermer porte après 5 secondes
    delay(5000);
    hardware.closeDoor();
    door_open = false;

    setState(STATE_IDLE);
}

void handleAccessDeniedState() {
    hardware.displayMessage("Acces Refuse");
    delay(3000);
    setState(STATE_IDLE);
}

void setState(int new_state) {
    current_state = new_state;

    // Notifier ESP32 du changement d'état
    String state_names[] = {"IDLE", "PASSWORD", "FACE", "GRANTED", "DENIED"};
    if (new_state >= 0 && new_state <= 4) {
        hardware.sendToESP32("STATE:" + state_names[new_state]);
    }
}

void handleESP32Message(String message) {
    if (message.startsWith("STATE:")) {
        String state = message.substring(6);
        if (state == "IDLE") current_state = STATE_IDLE;
        else if (state == "PASSWORD") current_state = STATE_PASSWORD;
        else if (state == "FACE") current_state = STATE_FACIAL_RECOGNITION;
        else if (state == "GRANTED") current_state = STATE_ACCESS_GRANTED;
        else if (state == "DENIED") current_state = STATE_ACCESS_DENIED;
    } else if (message.startsWith("MESSAGE:")) {
        String display_msg = message.substring(8);
        hardware.displayMessage(display_msg);
    }
}

bool validatePassword(String password) {
    // Mot de passe par défaut: 123456
    return password == "123456";
}