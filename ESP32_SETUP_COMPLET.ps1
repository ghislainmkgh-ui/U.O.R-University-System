#!/usr/bin/env pwsh
# ESP32 CAM - Setup Complet avec Thonny Integration (PowerShell)
# À exécuter: powershell -ExecutionPolicy Bypass -File ESP32_SETUP_COMPLET.ps1

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# =========================================================================
# COULEURS POUR LE TERMINAL
# =========================================================================

$colors = @{
    "header" = @{ ForegroundColor = "Cyan"; BackgroundColor = "Black" }
    "success" = @{ ForegroundColor = "Green"; BackgroundColor = "Black" }
    "error" = @{ ForegroundColor = "Red"; BackgroundColor = "Black" }
    "warning" = @{ ForegroundColor = "Yellow"; BackgroundColor = "Black" }
    "info" = @{ ForegroundColor = "White"; BackgroundColor = "Black" }
}

# =========================================================================
# FONCTIONS UTILITAIRES
# =========================================================================

function Write-Header {
    param([string]$text)
    Write-Host ""
    Write-Host ("=" * 70) @colors["header"]
    Write-Host (" " * (35 - $text.Length / 2) + $text) @colors["header"]
    Write-Host ("=" * 70) @colors["header"]
    Write-Host ""
}

function Write-Success {
    param([string]$text)
    Write-Host "[✓] $text" @colors["success"]
}

function Write-Error {
    param([string]$text)
    Write-Host "[✗] $text" @colors["error"]
}

function Write-Warning {
    param([string]$text)
    Write-Host "[!] $text" @colors["warning"]
}

function Write-Info {
    param([string]$text)
    Write-Host "[→] $text" @colors["info"]
}

# =========================================================================
# MAIN SCRIPT
# =========================================================================

Write-Header "ESP32 CAM - Configuration Automatique"

# Étape 1: Vérifier Python
Write-Info "Vérification de Python..."
$pythonInstalled = $null -ne (Get-Command python -ErrorAction SilentlyContinue)

if ($pythonInstalled) {
    $pythonVersion = python --version 2>&1
    Write-Success "Python détecté: $pythonVersion"
} else {
    Write-Error "Python non trouvé!"
    Write-Host ""
    Write-Host "Installer Python 3.8+ depuis: https://www.python.org/" @colors["warning"]
    Write-Host "Important: Cocher 'Add Python to PATH'" @colors["warning"]
    Write-Host ""
    Read-Host "Appuyer sur Entrée pour quitter"
    exit 1
}

# Étape 2: Vérifier/Installer dépendances
Write-Info "Installation des dépendances Python..."
Write-Host ""

$packages = @("pyserial", "esptool", "adafruit-ampy")
$allInstalled = $true

foreach ($pkg in $packages) {
    try {
        $output = python -m pip show $pkg 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$pkg - Déjà installé"
        } else {
            Write-Warning "$pkg - Installation..."
            python -m pip install $pkg --quiet 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$pkg - Installé"
            } else {
                Write-Error "$pkg - Échec installation"
                $allInstalled = $false
            }
        }
    } catch {
        Write-Error "$pkg - Erreur: $_"
        $allInstalled = $false
    }
}

if (-not $allInstalled) {
    Write-Host ""
    Write-Error "Certaines dépendances n'ont pas pu être installées"
    Write-Host "Essayer manuellement: python -m pip install pyserial esptool adafruit-ampy"
    Read-Host "Appuyer sur Entrée pour quitter"
    exit 1
}

# Étape 3: Vérifier fichiers ESP32
Write-Host ""
Write-Info "Vérification des fichiers ESP32..."

$requiredFiles = @(
    "esp32_camera_config.py",
    "esp32_flash_diagnostic.py",
    "esp32_setup_wizard.py"
)

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$missingFiles = @()

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $projectDir $file
    if (Test-Path $filePath) {
        Write-Success "$file présent"
    } else {
        Write-Error "$file manquant!"
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Error "Fichiers manquants: $($missingFiles -join ', ')"
    Read-Host "Appuyer sur Entrée pour quitter"
    exit 1
}

# Étape 4: Détecter ports COM
Write-Host ""
Write-Info "Détection des ports COM..."

$ports = Get-WmiObject -Query "SELECT Name, Description FROM Win32_SerialPort"

if ($ports.Count -eq 0) {
    Write-Error "Aucun port COM trouvé!"
    Write-Host ""
    Write-Host "Vérifier:" @colors["warning"]
    Write-Host "  • ESP32 CAM est connecté en USB" @colors["warning"]
    Write-Host "  • Driver CH340/CP2102 est installé" @colors["warning"]
    Write-Host "  • Gestionnaire des périphériques montre l'ESP32" @colors["warning"]
    Read-Host "Appuyer sur Entrée pour quitter"
    exit 1
}

Write-Success "Port(s) COM détecté(s):"
Write-Host ""

$portList = @()
$index = 1

foreach ($port in $ports) {
    $desc = $port.Description
    $device = $port.Name
    
    # Identifier ESP32
    $isESP32 = $desc -match "CH340|CP2102|USB Serial|ESP32" -and $desc -notmatch "Intel|AMT"
    $indicator = if ($isESP32) { " <- Probablement l'ESP32" } else { "" }
    
    Write-Host "  $index. $device - $desc$indicator" @colors["info"]
    $portList += $device
    $index++
}

Write-Host ""

if ($portList.Count -eq 1) {
    $selectedPort = $portList[0]
    Write-Info "Port automatiquement sélectionné: $selectedPort"
} else {
    $choice = Read-Host "Sélectionner le port ESP32 (numéro) [1]"
    $choice = if ([string]::IsNullOrWhiteSpace($choice)) { "1" } else { $choice }
    
    try {
        $idx = [int]$choice - 1
        if ($idx -ge 0 -and $idx -lt $portList.Count) {
            $selectedPort = $portList[$idx]
            Write-Success "Port sélectionné: $selectedPort"
        } else {
            Write-Error "Choix invalide"
            exit 1
        }
    } catch {
        Write-Error "Entrée invalide"
        exit 1
    }
}

# Étape 5: Lancer le diagnostic
Write-Host ""
Write-Header "Diagnostic ESP32"

Write-Host ""
Write-Info "Lancement du wizard de diagnostic..."
Write-Host ""

cd $projectDir
python esp32_setup_wizard.py

# Étape 6: Instructions finales
Write-Host ""
Write-Header "Configuration Terminée"

Write-Host ""
Write-Host "PROCHAINES ÉTAPES:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. TÉLÉCHARGER THONNY IDE" -ForegroundColor White
Write-Host "   URL: https://thonny.org/" @colors["info"]
Write-Host ""
Write-Host "2. CONFIGURER THONNY" -ForegroundColor White
Write-Host "   • Ouvrir Thonny" @colors["info"]
Write-Host "   • Tools > Configure interpreter" @colors["info"]
Write-Host "   • Sélectionner: MicroPython (ESP32)" @colors["info"]
Write-Host "   • Port: $selectedPort" @colors["info"]
Write-Host "   • Click OK" @colors["info"]
Write-Host ""
Write-Host "3. UPLOADER LES FICHIERS" -ForegroundColor White
Write-Host "   • Dans Thonny, drag & drop:" @colors["info"]
Write-Host "     - esp32_camera_config.py" @colors["info"]
Write-Host "     - esp32_flash_diagnostic.py" @colors["info"]
Write-Host ""
Write-Host "4. LANCER LE DIAGNOSTIC" -ForegroundColor White
Write-Host "   • Double-clic sur esp32_flash_diagnostic.py" @colors["info"]
Write-Host "   • Appuyer sur RESET sur l'ESP32" @colors["info"]
Write-Host ""
Write-Host "FICHIERS D'AIDE:" -ForegroundColor Yellow
Write-Host "   • ESP32_SETUP_GUIDE.txt" @colors["info"]
Write-Host "   • ESP32_CAM_GUIDE.txt" @colors["info"]
Write-Host ""

Write-Host "=" * 70 -ForegroundColor Cyan

Read-Host "Appuyer sur Entrée pour terminer"
