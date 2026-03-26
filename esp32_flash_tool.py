#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 CAM Flash Tool - Uploader et Diagnostic
Script pour flasher le firmware ESP32 CAM et diagnostiquer les problèmes

Utilise esptool et ampy pour:
1. Détecter le port COM
2. Uploader les fichiers MicroPython
3. Lancer le diagnostic
"""

import os
import sys
import subprocess
import time
import glob
from pathlib import Path

class ESP32FlashTool:
    """Outil de flash et diagnostic pour ESP32 CAM"""
    
    def __init__(self):
        self.port = None
        self.baud = 115200
        self.project_dir = Path(__file__).parent
        
    def print_header(self, text):
        """Affiche titre formaté"""
        print("\n" + "="*70)
        print(f" "*20 + text)
        print("="*70 + "\n")
    
    def detect_com_port(self):
        """Détecte le port COM de l'ESP32"""
        print("Détection du port COM...")
        
        # Chercher ports COM
        if sys.platform == 'win32':
            import serial.tools.list_ports
            ports = [p.device for p in serial.tools.list_ports.comports()]
        else:
            ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        if not ports:
            print("  ✗ Aucun port COM trouvé!")
            print("  Vérifier la connexion USB de l'ESP32")
            return None
        
        if len(ports) == 1:
            self.port = ports[0]
            print(f"  ✓ Port détecté: {self.port}")
            return self.port
        
        # Multiple ports - ask user
        print(f"  {len(ports)} ports trouvés:")
        for i, p in enumerate(ports):
            print(f"    {i+1}. {p}")
        
        choice = input("  Choisir (numéro) [1]: ").strip() or "1"
        try:
            self.port = ports[int(choice)-1]
            print(f"  ✓ Port sélectionné: {self.port}")
            return self.port
        except (ValueError, IndexError):
            print("  ✗ Choix invalide")
            return None
    
    def check_tools(self):
        """Vérifie que les outils Python/modules sont disponibles"""
        print("Vérification des outils requis...")
        
        tools_ok = True
        
        # pyserial
        try:
            import serial
            print("  ✓ pyserial disponible")
        except ImportError:
            print("  ✗ pyserial manquant")
            print("    Installation: pip install pyserial")
            tools_ok = False
        
        # esptool via module
        try:
            subprocess.run([sys.executable, '-m', 'esptool', '--help'], 
                         capture_output=True, timeout=2)
            print("  ✓ esptool disponible")
        except:
            print("  ⚠ esptool non trouvé (optionnel pour flash)")
        
        # ampy via module
        try:
            subprocess.run([sys.executable, '-m', 'esptool', '--help'], 
                         capture_output=True, timeout=2)
            print("  ✓ outils ampy/esptool disponibles")
        except:
            print("  ⚠ ampy/esptool non trouvés (mode diagnostic par REPL)")
        
        return tools_ok
    
    def list_upload_files(self):
        """Liste les fichiers à uploader"""
        files = [
            'esp32_camera_config.py',
            'esp32_flash_diagnostic.py',
        ]
        
        print("\nFichiers à uploader:")
        for idx, fname in enumerate(files, 1):
            fpath = self.project_dir / fname
            if fpath.exists():
                size = fpath.stat().st_size
                print(f"  ✓ {idx}. {fname} ({size} bytes)")
            else:
                print(f"  ✗ {idx}. {fname} - MANQUANT!")
        
        return files
    
    def upload_files(self, files):
        """Uploader les fichiers sur ESP32"""
        if not self.port:
            print("✗ Port COM non défini")
            return False
        
        self.print_header("Téléchargement des fichiers")
        
        for fname in files:
            fpath = self.project_dir / fname
            
            if not fpath.exists():
                print(f"⚠ {fname} introuvable - skippé")
                continue
            
            print(f"Envoi: {fname}...", end=" ")
            try:
                result = subprocess.run(
                    ['ampy', '-p', self.port, '-b', str(self.baud), 
                     'put', str(fpath), f'/{fname}'],
                    capture_output=True, timeout=10, text=True
                )
                
                if result.returncode == 0:
                    size = fpath.stat().st_size
                    print(f"✓ ({size} bytes)")
                else:
                    print(f"✗ Erreur: {result.stderr}")
                    return False
                    
                time.sleep(0.5)
                
            except subprocess.TimeoutExpired:
                print("✗ Timeout!")
                return False
            except Exception as e:
                print(f"✗ {e}")
                return False
        
        print("\n✓ Tous les fichiers uploadés avec succès")
        return True
    
    def run_diagnostic(self):
        """Lance le diagnostic sur ESP32"""
        if not self.port:
            print("✗ Port COM non défini")
            return False
        
        self.print_header("Diagnostic ESP32 CAM")
        
        print(f"Connection à {self.port}...")
        print("Appuyez sur RESET sur l'ESP32 pour lancer le boot diagnostic")
        print("(Ctrl+C pour arrêter)\n")
        
        try:
            # Utiliser miniterm d'esptool pour lire les logs
            subprocess.run([
                'esptool.py', '-p', self.port, '-b', str(self.baud),
                'read_flash', '0x0', '0x1'  # Juste connecter
            ], timeout=2)
            
        except:
            pass
        
        # Essayer avec ampy monitor
        try:
            print("Logs du microcontrôleur:\n")
            subprocess.run([
                'ampy', '-p', self.port, '-b', str(self.baud),
                'run', '/esp32_flash_diagnostic.py'
            ], timeout=30)
        except subprocess.TimeoutExpired:
            pass
        except KeyboardInterrupt:
            print("\n\nDiagnostic interrompu")
        except Exception as e:
            print(f"✗ Erreur: {e}")
            print("\nAlternative: Utiliser Thonny IDE ou ampy interactif")
    
    def interactive_repl(self):
        """Lance une session REPL interactive"""
        if not self.port:
            print("✗ Port COM non défini")
            return
        
        self.print_header("REPL Interactif MicroPython")
        
        print("Commandes utiles:")
        print("  >>> esp32camera.capture()     # Test capture")
        print("  >>> import esp32_camera_config")
        print("  >>> esp32_camera_config.initialize_with_diagnostics()")
        print("\n(Ctrl+D pour quitter)\n")
        
        try:
            subprocess.run([
                'ampy', '-p', self.port, '-b', str(self.baud),
                'repl'
            ])
        except KeyboardInterrupt:
            print("\n\nREPL fermé")
        except Exception as e:
            print(f"✗ Erreur: {e}")
    
    def run_full_process(self):
        """Exécute le processus complet"""
        self.print_header("ESP32 CAM Flash Tool")
        
        # 1. Vérifier outils
        if not self.check_tools():
            print("\n✗ Outils manquants - installer puis relancer")
            return False
        
        # 2. Détecter port
        if not self.detect_com_port():
            return False
        
        # 3. Lister fichiers
        files = self.list_upload_files()
        
        # 4. Confirmation
        response = input("\nProcéder au téléchargement? (o/n): ").strip().lower()
        if response not in ['o', 'yes', 'y']:
            print("Annulé")
            return False
        
        # 5. Upload
        if not self.upload_files(files):
            print("\n✗ Upload échoué")
            return False
        
        # 6. Diagnostic
        response = input("\nLancer la diagnostic? (o/n): ").strip().lower()
        if response in ['o', 'yes', 'y']:
            self.run_diagnostic()
        
        # 7. Mode interactif
        response = input("\nMode REPL interactif? (o/n): ").strip().lower()
        if response in ['o', 'yes', 'y']:
            self.interactive_repl()
        
        self.print_header("Processus terminé")
        return True

def main():
    """Fonction principale"""
    tool = ESP32FlashTool()
    
    try:
        success = tool.run_full_process()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrompu par utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
