# ESP32 CAM - Flash Script MicroPython
# À uploader directement sur l'ESP32 CAM comme fichier boot.py ou main.py
# Ce script fait un diagnostic complet et initialise la caméra

import time
import machine
from machine import Pin
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print(" "*15 + "ESP32 CAM - BOOT DIAGNOSTIC")
print("="*70)

# ============================================================================
# STEP 1: Vérification alimentation et santé du système
# ============================================================================
print("\n[1/5] Vérification santé système...")
try:
    # Freeboard info
    import esp
    flash_id = esp.flash_id()
    chip_id = machine.unique_id()
    
    print(f"  ✓ Chip ID: {chip_id.hex()}")
    print(f"  ✓ Flash ID: 0x{flash_id:06x}")
    print(f"  ✓ Fréquence CPU: {machine.freq() // 1000000} MHz")
    
except Exception as e:
    print(f"  ✗ Erreur: {e}")

# ============================================================================
# STEP 2: Détection capteur caméra via I2C
# ============================================================================
print("\n[2/5] Analyse I2C - Détection capteur caméra...")
try:
    from machine import I2C
    
    # I2C pins sur ESP32-CAM standard
    i2c = I2C(id=1, scl=Pin(23), sda=Pin(25), freq=400000)
    devices = i2c.scan()
    
    sensor_map = {
        0x21: "OV2640 (le plus courant)",
        0x30: "OV7670",
        0x42: "OV5640",
        0x60: "OV3660",
    }
    
    print(f"  Devices I2C détectés: {[hex(d) for d in devices]}")
    
    if not devices:
        print("  ⚠ ATTENTION: Aucun device I2C détecté!")
        print("    → Vérifier connexion caméra (nappe SPI/JTAG)")
        print("    → Vérifier alimentation 3.3V sur capteur")
    
    for addr in devices:
        name = sensor_map.get(addr, "UNKNOWN")
        print(f"  ✓ Capteur trouvé: {name} @ 0x{addr:02x}")
    
except Exception as e:
    print(f"  ✗ Erreur I2C: {e}")
    print("    → GPIO 23/25 bien configurés?")

# ============================================================================
# STEP 3: Test module esp32camera
# ============================================================================
print("\n[3/5] Test module esp32camera...")
try:
    import esp32camera
    print("  ✓ Module esp32camera téléchargé")
    
    # Lister les fonctions disponibles
    available = [x for x in dir(esp32camera) if not x.startswith('_')]
    print(f"  ✓ Fonctions disponibles: {available}")
    
except ImportError as e:
    print(f"  ✗ Module esp32camera NON DISPONIBLE: {e}")
    print("    → Installation: ampy put esp32camera.py /")
    print("    → Ou via WebREPL: télécharger depuis GitHub")
    esp32camera = None

# ============================================================================
# STEP 4: Tentative initialisation caméra (multiple formats)
# ============================================================================
print("\n[4/5] Initialisation caméra - Test formats...")

formats_to_test = [
    (0x01, "GRAYSCALE (nuances de gris)"),
    (0x02, "RGB565 (RGB 16-bit)"),
    (0x03, "YUV422 (YUV compressé)"),
    (0x04, "JPEG (compression)"),
]

camera_ready = False
active_format = None

if esp32camera is not None:
    for format_id, format_name in formats_to_test:
        try:
            print(f"  Tentative: {format_name}...", end=" ")
            
            # Configuration minimale
            esp32camera.init({
                'format': format_id,
                'framesize': 5,  # QVGA 320x240 (bon compromis vitesse/taille)
                'quality': 10,
                'brightness': 0,
                'contrast': 0,
                'saturation': 0,
                'special_effect': 0,
                'wb_mode': 1,
                'ae_level': 0,
                'aec_value': 300,
                'agc': 1,
                'agc_gain': 0,
                'gainceiling': 0,
            })
            
            # Test capture
            time.sleep(0.5)
            frame = esp32camera.capture()
            
            if frame is not None and len(frame) > 0:
                print(f"✓ OK ({len(frame)} bytes)")
                print(f"    ✓✓ Format VALIDÉ: {format_name}")
                camera_ready = True
                active_format = format_name
                break
            else:
                print("✗ Buffer vide")
                
        except OSError as os_err:
            if "0x106" in str(os_err):
                print(f"✗ Format non supporté (error 0x106)")
            else:
                print(f"✗ Erreur: {os_err}")
        except Exception as e:
            print(f"✗ {e}")

if not camera_ready:
    print("\n  ⚠ AUCUN FORMAT NE FONCTIONNE!")
    print("  Diagnostique:")
    print("    → Le capteur n'est pas détecté via I2C")
    print("    → Vérifier connexion SPI (câble caméra)")
    print("    → Vérifier alimentation 3.3V + GND")
    print("    → Essayer tirer GPIO 32 en HIGH (pin reset)")

# ============================================================================
# STEP 5: Résumé et recommandations
# ============================================================================
print("\n[5/5] Résumé et configuration recommandée...")

print("\n" + "="*70)
if camera_ready:
    print(" "*20 + "✓ CAMÉRA OPÉRATIONNELLE")
    print("="*70)
    print(f"\nFormat actif: {active_format}")
    print("Résolution: QVGA (320x240)")
    print("\nProchain: Intégrer esp32camera_config.py pour reconnaissance faciale")
else:
    print(" "*15 + "✗ CAMÉRA NON OPÉRATIONNELLE")
    print("="*70)
    print("\nActions recommandées:")
    print("  1. Vérifier alimentation 5V → régulateur 3.3V")
    print("  2. Vérifier câble 22 broches (respecter sens)")
    print("  3. Tirer GPIO 32 en HIGH (reset capteur)")
    print("  4. Rebooter ESP32 après changement de hardware")
    print("\nConnexion utile:")
    print("  - Serial: 115200 baud pour logs en direct")
    print("  - WebREPL: pour diagnostique interactive")

print("\n" + "="*70)
print(f"\nTemps boot: {time.time():.2f}s")
print("="*70 + "\n")

# ============================================================================
# BOUCLE PRINCIPALE - KEEP ALIVE
# ============================================================================
print("Système en attente de commandes REPL...")
print("Tapez: esp32camera.capture() pour test capture")

while True:
    time.sleep(1)
