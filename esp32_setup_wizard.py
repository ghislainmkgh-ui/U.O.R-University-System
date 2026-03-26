#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 CAM - Setup & Diagnostic Complet
Identifie le bon port COM et fournit des instructions d'upload

Étapes:
1. Détecter le bon port COM (demander à l'utilisateur)
2. Afficher instructions pour Thonny IDE
3. Confirmer upload + lancer diagnostic
"""

import sys
import time
import serial
from pathlib import Path

def find_com_ports():
    """Retourne tous les ports COM disponibles"""
    try:
        import serial.tools.list_ports
        return list(serial.tools.list_ports.comports())
    except:
        return []

def main():
    print("\n" + "="*70)
    print(" "*10 + "ESP32 CAM - Configuration & Diagnostic")
    print("="*70 + "\n")
    
    # Étape 1: Détecter ports
    print("[ÉTAPE 1] Détection des ports COM...\n")
    ports = find_com_ports()
    
    if not ports:
        print("✗ Aucun port COM détecté!")
        print("\nVérifier:")
        print("  • L'ESP32 CAM est connecté en USB")
        print("  • Le driver CH340/CP2102 est installé")
        print("  • L'ESP32 apparaît dans Gestionnaire des périphériques")
        return 1
    
    print(f"✓ {len(ports)} port(s) trouvé(s):\n")
    
    esp32_port = None
    
    for i, p in enumerate(ports, 1):
        desc = p.description.lower()
        
        # Identifier ports ESP32 probables
        is_esp32 = any(x in desc for x in ['ch340', 'cp2102', 'usb serial', 'esp32', 'silabs'])
        is_intel_amt = 'intel' in desc or 'amt' in desc
        
        symbol = ""
        if is_esp32:
            symbol = "  <- Probablement l'ESP32!" if not esp32_port else ""
            if not esp32_port:
                esp32_port = p.device
        elif is_intel_amt:
            symbol = "  (NOT l'ESP32 - Intel AMT)"
        
        print(f"  {i}. {p.device:6} - {p.description:40} {symbol}")
    
    print()
    default_choice = "2" if esp32_port else "1"  # Généralement le 2e port pour ESP32
    
    choice = input(f"Choisir le port ESP32 (numéro) [{default_choice}]: ").strip() or default_choice
    
    try:
        port = ports[int(choice) - 1].device
        print(f"\n✓ Port sélectionné: {port}\n")
    except (ValueError, IndexError):
        print("✗ Choix invalide")
        return 1
    
    # Étape 2: Instructions d'upload
    print("="*70)
    print("[ÉTAPE 2] Upload des fichiers sur ESP32 CAM")
    print("="*70 + "\n")
    
    print("Avant de continuer, les fichiers doivent être uploadés sur l'ESP32:")
    print()
    print("OPTION A - Thonny IDE (RECOMMANDÉ):")
    print("-" * 70)
    print("  1. Télécharger Thonny IDE: https://thonny.org/")
    print("  2. Installer et lancer Thonny")
    print("  3. Aller à: Tools → Configure interpreter")
    print("  4. Sélectionner: MicroPython (ESP32)")
    print("  5. Port: " + port)
    print("  6. Click OK")
    print("  7. Drag & drop dans Thonny (à gauche) ces fichiers:")
    print("     • esp32_camera_config.py")
    print("     • esp32_flash_diagnostic.py")
    print()
    
    print("OPTION B - esptool.py (Avancé):")
    print("-" * 70)
    print("  python -m esptool -p " + port + " --baud 115200 write_flash 0x1000 app.bin")
    print()
    
    print("OPTION C - WebREPL:")
    print("-" * 70)
    print("  • Si l'ESP32 a WebREPL , connecter d'abord au Wi-Fi")
    print("  • Puis uploader via l'interface Web")
    print()
    
    response = input("Fichiers uploadés? (o/n) [n]: ").strip().lower() or "n"
    
    if response not in ['o', 'y', 'yes']:
        print("\n⚠ À faire en premier:\n")
        project_dir = Path(__file__).parent
        print(f"  1. Ouvrir Thonny IDE")
        print(f"  2. Drag-drop depuis {project_dir}:")
        print(f"     • esp32_camera_config.py")
        print(f"     • esp32_flash_diagnostic.py")
        print(f"  3. Relancer ce script une fois l'upload terminé\n")
        return 0
    
    # Étape 3: Diagnostic
    print("\n" + "="*70)
    print("[ÉTAPE 3] Diagnostic de la caméra")
    print("="*70 + "\n")
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        print(f"✓ Connecté à {port}\n")
        print("Appuyez sur RESET sur l'ESP32 pour redémarrer le diagnostic...")
        print()
        print("-" * 70)
        print("LOGS ESP32:")
        print("-" * 70 + "\n")
        
        start = time.time()
        diagnostic_done = False
        last_output = ""
        
        while time.time() - start < 30:
            
            if ser.in_waiting:
                data = ser.read(1).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
                last_output += data
                
                # Détecter fin diagnostic
                if "OPÉRATIONNELLE" in last_output or "OPERATIONAL" in last_output:
                    diagnostic_done = True
            
            time.sleep(0.01)
        
        print("\n\n" + "-" * 70)
        print("FIN DU DIAGNOSTIC")
        print("-" * 70)
        
        # Résultat
        if "OPÉRATIONNELLE" in last_output or "operational" in last_output.lower():
            print("\n✓ CAMÉRA OPÉRATIONNELLE!\n")
        else:
            print("\n⚠ Vérifier les logs ci-dessus pour identifier le problème\n")
        
        # Menu
        print("\nOptions:")
        print("  1. Mode REPL interactif")
        print("  2. Quitter")
        print()
        
        menu_choice = input("Choisir (1-2) [2]: ").strip() or "2"
        
        if menu_choice == "1":
            print("\n" + "="*70)
            print("Mode REPL Interactif")
            print("="*70 + "\n")
            print("Commandes utiles:")
            print("  >>> import esp32_camera_config")
            print("  >>> esp32_camera_config.camera_manager.capture_frame()")
            print("  >>> camera_manager = esp32_camera_config.camera_manager")
            print("  >>> print(camera_manager.get_camera_status())")
            print()
            print("(Ctrl+C pour quitter)\n")
            
            try:
                while True:
                    cmd = input(">>> ")
                    if cmd:
                        ser.write((cmd + "\r\n").encode())
                        time.sleep(0.5)
                        
                        # Lire réponse
                        while ser.in_waiting:
                            print(ser.read(1).decode('utf-8', errors='ignore'), end='', flush=True)
            
            except KeyboardInterrupt:
                print("\n\nREPL fermé")
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"✗ Erreur de connexion: {e}")
        print("\nVérifier:")
        print("  • Le port COM est correct")
        print("  • L'ESP32 n'est pas utilisé par une autre application")
        print("  • Le câble USB est bien connecté")
        return 1
    
    except KeyboardInterrupt:
        print("\n\nInterrompu")
        return 0
    
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return 1
    
    print("\n✓ Diagnostic termié\n")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ Erreur: {e}\n")
        sys.exit(1)
