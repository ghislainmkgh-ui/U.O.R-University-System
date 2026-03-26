#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 CAM - Simple Diagnostic and Flash Tool
Outil simplifié pour diagnostiquer l'ESP32 CAM via le port série

Installation des dépendances:
  pip install pyserial
"""

import sys
import time
import serial
from pathlib import Path

def find_com_port():
    """Détecte les ports COM/série disponibles"""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            print("✗ Aucun port COM/série trouvé")
            print("\nVérifier:")
            print("  1. L'ESP32 est connecté en USB")
            print("  2. Le driver CH340/CP2102 est installé")  
            print("  3. L'ESP32 apparaît dans Gestionnaire des périphériques")
            return None
        
        if len(ports) == 1:
            return ports[0].device, ports[0].description
        
        print(f"\n{len(ports)} port(s) détecté(s):\n")
        for i, p in enumerate(ports, 1):
            print(f"  {i}. {p.device:10} - {p.description}")
        
        choice = input("\nChoisir le port (numéro) [1]: ").strip() or "1"
        try:
            idx = int(choice) - 1
            return ports[idx].device, ports[idx].description
        except (ValueError, IndexError):
            print("✗ Choix invalide")
            return None
    
    except Exception as e:
        print(f"✗ Erreur lors de la recherche de ports: {e}")
        return None

def connect_serial(port, baudrate=115200, timeout=2):
    """Connecte au port série"""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(0.5)  # Attendre stabilisation
        return ser
    except Exception as e:
        print(f"✗ Impossible de se connecter à {port}: {e}")
        return None

def read_until(ser, target=None, timeout=3):
    """Lit depuis le port jusqu'à une cible ou timeout"""
    start = time.time()
    buffer = ""
    
    while time.time() - start < timeout:
        if ser.in_waiting:
            try:
                data = ser.read(1).decode('utf-8', errors='ignore')
                buffer += data
                print(data, end='', flush=True)
                
                if target and target in buffer:
                    return buffer
            except:
                pass
        time.sleep(0.01)
    
    return buffer

def main():
    print("\n" + "="*70)
    print(" "*15 + "ESP32 CAM - Diagnostic Tool")
    print("="*70 + "\n")
    
    # 1. Détecter port
    print("[1/3] Détection du port série...\n")
    port_info = find_com_port()
    
    if not port_info:
        return 1
    
    port, description = port_info
    print(f"\n✓ Port sélectionné: {port}")
    print(f"  Description: {description}\n")
    
    # 2. Connecter
    print("[2/3] Connexion au ESP32...\n")
    ser = connect_serial(port)
    
    if not ser:
        return 1
    
    print(f"✓ Connecté à {port} @ 115200 baud\n")
    
    # 3. Lancer diagnostic
    print("[3/3] Capture des logs de diagnostic...\n")
    print("="*70)
    print("LOGS ESP32 BOOT & CAMERA DIAGNOSTIC:")
    print("="*70 + "\n")
    
    # Attendre les logs de boot
    start_time = time.time()
    boot_complete = False
    
    try:
        while time.time() - start_time < 30:  # 30 secondes max
            
            if ser.in_waiting:
                try:
                    data = ser.read(1).decode('utf-8', errors='ignore')
                    print(data, end='', flush=True)
                    
                    if "CAMÉRA OPÉRATIONNELLE" in data or "OPÉRATIONNELLE" in data:
                        boot_complete = True
                
                except Exception as e:
                    pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\n" + "="*70)
    
    # 4. Menu post-diagnostic
    print("\nOptions:")
    print("  1. Mode REPL interactif")
    print("  2. Quitter")
    print()
    
    choice = input("Choisir (1-2) [2]: ").strip() or "2"
    
    if choice == "1":
        print("\nMode REPL Interactif")
        print("-" * 70)
        print("Exemples de commandes:")
        print("  >>> import esp32_camera_config")
        print("  >>> esp32_camera_config.camera_manager.capture_frame()")
        print("  >>> camera_manager = esp32_camera_config.camera_manager")
        print("  >>> status = camera_manager.get_camera_status()")
        print("  >>> print(status)")
        print("\n(Ctrl+C pour quitter)\n")
        
        try:
            while True:
                cmd = input(">>> ")
                if cmd:
                    cmd_bytes = (cmd + "\r\n").encode()
                    ser.write(cmd_bytes)
                    time.sleep(0.5)
                    
                    # Lire la réponse
                    output = ""
                    while ser.in_waiting:
                        try:
                            output += ser.read(1).decode('utf-8', errors='ignore')
                        except:
                            pass
                    
                    if output:
                        print(output)
        
        except KeyboardInterrupt:
            print("\n\nREPL fermé")
        except Exception as e:
            print(f"✗ Erreur: {e}")
    
    # Fermer
    ser.close()
    print("\n✓ Port fermé\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ Erreur: {e}\n")
        sys.exit(1)
