@echo off
REM =========================================================================
REM ESP32 CAM - SETUP COMPLET (Windows)
REM NOTE: Ce script appartient à l'ancienne architecture ESP32 CAM / Arduino.
REM Il est conservé uniquement pour référence historique et ne fait pas partie
REM de la migration web actuelle.
REM Double-clic pour démarrer - Automatise TOUT
REM =========================================================================

setlocal enabledelayedexpansion

cls
echo.
echo =========================================================================
echo.
echo                  ESP32 CAM - CONFIGURATION COMPLETE
echo.
echo =========================================================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouvé!
    echo.
    echo Installer Python 3.8+ depuis: https://www.python.org/
    echo Important: Cocher "Add Python to PATH" lors installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python détecté
python --version

REM Véifier pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERREUR] pip non trouvé!
    pause
    exit /b 1
)

echo [OK] pip disponible

REM =========================================================================
echo.
echo [Étape 1/3] Vérification des dépendances Python...
echo.

python -m pip install pyserial --quiet
python -m pip install esptool --quiet
python -m pip install adafruit-ampy --quiet

echo [OK] Dépendances installées

REM =========================================================================
echo.
echo [Étape 2/3] Lancement du diagnostic ESP32...
echo.

python esp32_setup_wizard.py

REM =========================================================================
echo.
echo [Étape 3/3] Instructions finales
echo.

echo.
echo =========================================================================
echo                          PROCHAINES ÉTAPES
echo =========================================================================
echo.
echo 1. TÉLÉCHARGER THONNY IDE
echo    URL: https://thonny.org/
echo    Installer avec les paramètres par défaut
echo.
echo 2. CONFIGURER THONNY
echo    • Ouvrir Thonny
echo    • Tools menu ^> Configure interpreter
echo    • Sélectionner: "MicroPython (ESP32)"
echo    • Port: COM10
echo    • OK
echo.
echo 3. UPLOADER LES FICHIERS
echo    • Dans Thonny, ouvrir le fichier explorer (View menu)
echo    • Drag & drop ces fichiers dans l'ESP32:
echo      - esp32_camera_config.py
echo      - esp32_flash_diagnostic.py
echo.
echo 4. LANCER LE DIAGNOSTIC
echo    • Double-clic sur esp32_flash_diagnostic.py (dans l'explorateur ESP32)
echo    • Appuyer sur RESET sur l'ESP32
echo    • Attendre les logs du diagnostic
echo.
echo =========================================================================
echo.
echo Besoin d'aide?
echo  - Lire: ESP32_SETUP_GUIDE.txt
echo  - Ou:   ESP32_CAM_GUIDE.txt
echo.
echo =========================================================================
echo.

pause
