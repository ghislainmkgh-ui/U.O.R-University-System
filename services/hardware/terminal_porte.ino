#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>
// ... (autres inclusions)

// Adresse 0x27 pour un LCD 16x2
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  lcd.init();
  lcd.backlight();
  afficherMessage("U.O.R. ACCES", "ENTREZ VOTRE CODE");
  // ... reste du setup
}

void afficherMessage(String ligne1, String ligne2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(ligne1);
  lcd.setCursor(0, 1);
  lcd.print(ligne2);
}

void loop() {
  char key = keypad.getKey();
  if (key) {
    if (key == '#') {
      afficherMessage("VERIFICATION...", "PATIENTEZ");
      envoyerRequeteAuBureau(inputPassword);
      inputPassword = "";
    } else {
      // Feedback visuel pendant qu'il tape (ex: ****)
      lcd.setCursor(inputPassword.length(), 1);
      lcd.print("*");
      inputPassword += key;
    }
  }

  // Ecoute de la réponse du serveur
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    gererReponseServeur(cmd);
  }
}

void gererReponseServeur(String cmd) {
  if (cmd == "SCAN_VISAGE") {
    afficherMessage("CODE VALIDE", "SCANNEZ VISAGE");
  } else if (cmd == "ACCES_OK") {
    afficherMessage("SUCCES", "PORTE OUVERTE");
    ouvrirPorte(); // Active le servo
    delay(3000);
    afficherMessage("U.O.R. ACCES", "ENTREZ VOTRE CODE");
  } else if (cmd == "ERR_FINANCE") {
    afficherMessage("REFUSE", "SEUIL NON ATTEINT");
    delay(3000);
    afficherMessage("U.O.R. ACCES", "ENTREZ VOTRE CODE");
  } else if (cmd == "ERR_AUTH") {
    afficherMessage("ERREUR", "CODE INVALIDE");
    delay(2000);
    afficherMessage("U.O.R. ACCES", "ENTREZ VOTRE CODE");
  }
}