#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de caméra ESP32 CAM - Serial Monitor
Connecte à l'ESP32 en série et affiche les logs du diagnostic

Usage:
    python esp32_test_camera.py COM4
    python esp32_test_camera.py /dev/ttyUSB0
"""

import serial
import sys
import time
from pathlib import Path

class ESP32SerialMonitor:
    """Moniteur série pour ESP32"""
    
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect(self, timeout=2):
        """Connecte au port série"""
        try:
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=timeout
            )
            print(f"✓ Connecté à {self.port} @ {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"✗ Impossible de se connecter: {e}")
            return False
    
    def read_logs(self, duration=30):
        """Lit les logs du microcontrôleur"""
        if not self.ser or not self.ser.is_open:
            print("✗ Port série non ouvert")
            return
        
        print(f"\nCaptureLogging des logs ({duration}s)...")
        print("(Appuyez sur Ctrl+C pour arrêter)\n")
        print("="*70)
        
        start_time = time.time()
        buffer = ""
        
        try:
            while True:
                if time.time() - start_time > duration:
                    print("\nTimeout atteint")
                    break
                
                # Lire caractères disponibles
                if self.ser.in_waiting > 0:
                    try:
                        byte = self.ser.read(1)
                        if byte:
                            char = byte.decode('utf-8', errors='ignore')
                            buffer += char
                            
                            # Afficher complete lines
                            if char == '\n':
                                print(buffer, end='')
                                buffer = ""
                    except Exception as e:
                        pass
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n\nInterrompu par utilisateur")
        except Exception as e:
            print(f"\n✗ Erreur: {e}")
        finally:
            if buffer:
                print(buffer)
            print("="*70)
    
    def send_command(self, command):
        """Envoie une commande au REPL"""
        if not self.ser or not self.ser.is_open:
            print("✗ Port série non ouvert")
            return
        
        cmd = command + "\r\n"
        self.ser.write(cmd.encode())
        print(f"→ {command}")
        
        # Attendre réponse
        time.sleep(0.5)
        response = self.ser.read_all().decode('utf-8', errors='ignore')
        if response:
            print(f"← {response}")
    
    def interactive_repl(self):
        """Lance le REPL interactif"""
        if not self.ser or not self.ser.is_open:
            print("✗ Port série non ouvert")
            return
        
        print("\nREPL Interactif (Ctrl+C pour quitter)")
        print("Exemples:")
        print("  >>> import esp32_camera_config")
        print("  >>> esp32_camera_config.camera_manager.capture_frame()")
        print()
        
        try:
            while True:
                cmd = input(">>> ")
                if cmd:
                    self.send_command(cmd)
        except KeyboardInterrupt:
            print("\n\nREPL fermé")
        except Exception as e:
            print(f"✗ Erreur: {e}")
    
    def close(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Port fermé")

def find_com_port():
    """Découvre le port COM"""
    try:
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if not ports:
            print("✗ Aucun port COM trouvé")
            return None
        
        if len(ports) == 1:
            return ports[0]
        
        print("Ports COM disponibles:")
        for i, p in enumerate(ports):
            print(f"  {i+1}. {p}")
        
        choice = input("Sélectionner [1]: ").strip() or "1"
        return ports[int(choice)-1]
    
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return None

def main():
    """Fonction principale"""
    
    # Obtenir le port
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = find_com_port()
    
    if not port:
        print("\nUsage: python esp32_test_camera.py [PORT]")
        print("Example: python esp32_test_camera.py COM4")
        return 1
    
    # Créer moniteur
    monitor = ESP32SerialMonitor(port)
    
    if not monitor.connect():
        return 1
    
    try:
        print("\n" + "="*70)
        print(" "*15 + "ESP32 CAM - Serial Monitor")
        print("="*70 + "\n")
        
        # Menu
        print("Mode:")
        print("  1. Lire les logs de démarrage (30s)")
        print("  2. Mode REPL interactif")
        print("  3. Diagnostic complet")
        print()
        
        choice = input("Choisir (1-3) [1]: ").strip() or "1"
        
        if choice == "1":
            monitor.read_logs(30)
        
        elif choice == "2":
            monitor.interactive_repl()
        
        elif choice == "3":
            # Lancer le diagnostic sur l'ESP32
            print("\nLancement du diagnostic sur ESP32...")
            monitor.send_command("import esp32_flash_diagnostic")
            time.sleep(0.5)
            monitor.read_logs(15)
        
        else:
            print("Choix invalide")
            return 1
    
    finally:
        monitor.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
