@echo off
REM === ESP32 CAM Flash Tool - Batch Launcher ===
REM Ce script lance l'outil de flash/diagnostic pour ESP32 CAM

echo.
echo ================================================================
echo  ESP32 CAM Flash Tool - Configuration and Diagnostics
echo ================================================================
echo.

REM Vérifier si Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou pas dans PATH
    echo.
    echo Installation requise:
    echo   1. Installer Python 3.8+ depuis python.org
    echo   2. Ajouter Python à PATH (cocher lors installation)
    echo.
    pause
    exit /b 1
)

echo Vérification des dépendances Python...
echo.

REM Vérifier esptool
python -m pip show esptool >nul 2>&1
if errorlevel 1 (
    echo [!] esptool.py manquant - installation...
    python -m pip install esptool
)

REM Vérifier ampy
python -m pip show adafruit-ampy >nul 2>&1
if errorlevel 1 (
    echo [!] ampy manquant - installation...
    python -m pip install adafruit-ampy
)

REM Vérifier pyserial
python -m pip show pyserial >nul 2>&1
if errorlevel 1 (
    echo [!] pyserial manquant - installation...
    python -m pip install pyserial
)

echo.
echo ================================================================
echo Outils vérifiés. Lancement de l'outil de flash...
echo ================================================================
echo.

REM Lancer le script Python
python esp32_flash_tool.py

pause
