@echo off
cls
echo ================================================================
echo         ACTIVATION WHATSAPP EN 3 ETAPES - U.O.R
echo ================================================================
echo.
echo Ce script va te guider pour activer WhatsApp pas a pas.
echo.
echo ETAPE 1/3: Obtenir le Token Twilio
echo ----------------------------------------------------------------
echo.
echo 1. Ouvre dans ton navigateur: https://console.twilio.com/
echo 2. Connecte-toi
echo 3. Dans "Account Info", clique "Show" sur "Auth Token"
echo 4. COPIE le token (32 caracteres)
echo.
pause
echo.
echo ETAPE 2/3: Mettre a jour le token
echo ----------------------------------------------------------------
echo.
echo Lance maintenant le script pour mettre a jour le token:
echo.
cd /d "E:\SECRET FILES\MY_TFC"
.venv\Scripts\python.exe scripts\update_twilio_token.py
echo.
pause
echo.
echo ETAPE 3/3: Rejoindre le Sandbox WhatsApp
echo ----------------------------------------------------------------
echo.
echo 1. Va sur: https://console.twilio.com/develop/sms/try-it-out/whatsapp-learn
echo 2. Note le code (ex: "join coffee-piano")
echo 3. Sur WhatsApp, ajoute le contact: +1 415 523 8886
echo 4. Envoie le message: join [ton-code]
echo 5. Attends la confirmation
echo.
pause
echo.
echo TEST FINAL: Verification WhatsApp
echo ----------------------------------------------------------------
echo.
echo Lance le test pour verifier que tout fonctionne:
echo.
.venv\Scripts\python.exe scripts\test_whatsapp.py
echo.
pause
