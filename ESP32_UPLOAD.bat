@echo off
REM ESP32 CAM - Upload Automatique et Diagnostic
REM Double-clic pour uploader les fichiers et lancer le diagnostic

cls
echo.
echo =========================================================================
echo.
echo              ESP32 CAM - Upload Automatique + Diagnostic
echo.
echo =========================================================================
echo.

cd /d "%~dp0"

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouvé!
    pause
    exit /b 1
)

REM Installer ampy si nécessaire
python -m pip install adafruit-ampy --quiet 2>nul

REM Lancer le script d'upload
python esp32_upload_auto.py

pause
