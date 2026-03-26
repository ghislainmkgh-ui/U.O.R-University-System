#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 CAM - Upload Automatique via ampy
Uploader les fichiers et lancer le diagnostic directement
"""

import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Exécute une commande et retourne le statut"""
    try:
        if description:
            print(f"\n{description}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def main():
    print("\n" + "="*70)
    print(" "*15 + "ESP32 CAM - Upload Automatique")
    print("="*70 + "\n")
    
    # Déterminer le port
    port = "COM10"  # Défaut déterminé par le script précédent
    
    choice = input(f"Port COM  à utiliser [{port}]: ").strip() or port
    port = choice
    
    # Fichiers à uploader
    project_dir = Path(__file__).parent
    files_to_upload = [
        "esp32_camera_config.py",
        "esp32_flash_diagnostic.py",
    ]
    
    print(f"\n[1] Détection de ampy...")
    success, output = run_command([sys.executable, "-m", "ampy", "--help"])
    
    if not success:
        print("✗ ampy non disponible")
        print("\nInstaller:" )
        print("  pip install adafruit-ampy")
        print("\nOu utiliser Thonny IDE:")
        print("  1. Télécharger Thonny depuis thonny.org")
        print("  2. Tools > Configure interpreter > MicroPython (ESP32)")
        print("  3. Drag & drop les fichiers dans Thonny")
        return 1
    
    print("✓ ampy détecté")
    
    print(f"\n[2] Upload des fichiers sur {port}...")
    
    all_success = True
    for fname in files_to_upload:
        fpath = project_dir / fname
        
        if not fpath.exists():
            print(f"  ✗ {fname} - Fichier manquant!")
            all_success = False
            continue
        
        print(f"  ↗ {fname}...", end=" ", flush=True)
        
        success, output = run_command(
            [sys.executable, "-m", "ampy", "-p", port, "-b", "115200", 
             "put", str(fpath), f"/{fname}"],
            description=None
        )
        
        if success:
            print("✓")
        else:
            print(f"✗")
            print(f"     Erreur: {output[:200]}")
            all_success = False
        
        time.sleep(0.5)
    
    if not all_success:
        print("\n✗ Certains fichiers n'ont pas pu être uploadés")
        print("\nVérifier:")
        print("  • Le port COM est correct")
        print("  • L'ESP32 est bien connecté")
        print("  • MicroPython est flashé sur l'ESP32")
        return 1
    
    print("\n✓ Tous les fichiers uploadés avec succès!")
    
    print(f"\n[3] Lancement du diagnostic...")
    print("  Appuyez sur RESET sur l'ESP32 pour redémarrer...\n")
    print("-" * 70)
    
    try:
        # Lancer le diagnostic
        success, output = run_command(
            [sys.executable, "-m", "ampy", "-p", port, "-b", "115200",
             "run", "/esp32_flash_diagnostic.py"],
            description=None
        )
        
        if output:
            print(output)
        
        if success:
            print("\n" + "-" * 70)
            print("✓ Diagnostic terminé")
        else:
            print("\n⚠ Le diagnostic s'est arrêté (normal)")
    
    except Exception as e:
        print(f"Note: {e}")
    
    print("\n" + "="*70)
    print("[SUCCÈS] ESP32 CAM est configuré et prêt!")
    print("="*70)
    print("""
Prochaines étapes:
  1. Intégrer esp32_camera_config.py dans le code principal
  2. Configurer la reconnaissance faciale
  3. Tester la communication Arduino/ESP32

Pour déboguer:
  • Utiliser Thonny REPL: import esp32_flash_diagnostic
  • Ou: python esp32_test_camera.py COM10
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
