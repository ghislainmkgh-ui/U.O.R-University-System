# Configuration optimisée ESP32 CAM - Diagnostic et correction
# Supporte multiple formats avec fallback automatique
# MicroPython pour ESP32-CAM (AI-Thinker, TTGO, etc.)

import machine
import time
from machine import Pin, I2C
import esp32

# ============================================================================
# CONFIGURATION DES FORMATS SUPPORTÉS
# ============================================================================
# Les formats sont testés dans cet ordre (du plus compatible au moins compatible)

CAMERA_FORMATS = {
    'PIXFORMAT_GRAYSCALE': 0x01,  # Nuances de gris - TRÈS compatible
    'PIXFORMAT_RGB565': 0x02,      # RGB 16-bit - Très compatible
    'PIXFORMAT_YUV422': 0x03,      # YUV compressé - Compatible
    'PIXFORMAT_JPEG': 0x04,        # JPEG - Nécessite support hardware
}

CAMERA_FRAME_SIZES = {
    'FRAMESIZE_96X96': 0,
    'FRAMESIZE_QQVGA': 1,    # 160x120
    'FRAMESIZE_QCIF': 2,     # 176x144
    'FRAMESIZE_HQVGA': 3,    # 240x176
    'FRAMESIZE_240X240': 4,
    'FRAMESIZE_QVGA': 5,     # 320x240
    'FRAMESIZE_CIF': 6,      # 352x288
    'FRAMESIZE_HVGA': 7,     # 480x360
    'FRAMESIZE_VGA': 8,      # 640x480
    'FRAMESIZE_SVGA': 9,     # 800x600
    'FRAMESIZE_XGA': 10,     # 1024x768
    'FRAMESIZE_HD': 11,      # 1280x720
    'FRAMESIZE_SXGA': 12,    # 1280x1024
    'FRAMESIZE_UXGA': 13,    # 1600x1200
}

# ============================================================================
# CONFIGURATION CAMÉRA RECOMMANDÉE
# ============================================================================
class CameraConfig:
    """Configuration optimisée pour ESP32 CAM"""
    
    # Format d'image primaire (meilleur support)
    PRIMARY_FORMAT = CAMERA_FORMATS['PIXFORMAT_RGB565']
    
    # Format fallback (si RGB565 échoue)
    FALLBACK_FORMAT = CAMERA_FORMATS['PIXFORMAT_GRAYSCALE']
    
    # Taille d'image (QVGA = 320x240 = bon compromis vitesse/résolution)
    FRAME_SIZE = CAMERA_FRAME_SIZES['FRAMESIZE_QVGA']
    
    # Paramètres qualité
    QUALITY = 10  # 0-63, plus bas = meilleure qualité
    BRIGHTNESS = 0  # -2 à +2
    CONTRAST = 0    # -2 à +2
    SATURATION = 0  # -2 à +2
    
    # Paramètres caméra
    ENABLE_AUTO_WHITEBALANCE = True
    ENABLE_AUTO_EXPOSURE = True
    ENABLE_AWB_GAIN = True
    
    # Timeouts
    INIT_TIMEOUT_MS = 5000
    CAPTURE_TIMEOUT_MS = 3000

# ============================================================================
# DIAGNOSTIC ET INITIALISATION CAMÉRA
# ============================================================================
class ESP32CameraManager:
    """Gère l'initialisation et le diagnostic de la caméra"""
    
    def __init__(self):
        self.camera = None
        self.active_format = None
        self.active_framesize = None
        self.initialized = False
        self.last_error = None
        
    def log(self, message, level="INFO"):
        """Log avec timestamp"""
        timestamp = time.time()
        print(f"[{level}] [{timestamp}] {message}")
    
    def detect_camera_module(self):
        """Détecte le modèle de capteur"""
        try:
            self.log("Détection du module capteur...")
            # Tentative de détection via I2C (adresse standard OV = 0x42)
            i2c = I2C(scl=Pin(23), sda=Pin(25))  # Broches standard ESP32-CAM
            devices = i2c.scan()
            
            sensor_names = {
                0x21: "OV2640",
                0x42: "OV5640", 
                0x60: "OV3660",
            }
            
            detected_sensors = []
            for device_addr in devices:
                if device_addr in sensor_names:
                    sensor_name = sensor_names[device_addr]
                    detected_sensors.append(sensor_name)
                    self.log(f"  ✓ Capteur détecté: {sensor_name} (adresse 0x{device_addr:02x})")
            
            if not detected_sensors:
                self.log("  ⚠ Aucun capteur standard détecté (vérifier branchement I2C)")
            
            return detected_sensors
            
        except Exception as e:
            self.log(f"  ✗ Erreur détection: {e}", "ERROR")
            return []
    
    def initialize_camera(self, format_priority=None):
        """Initialise la caméra avec format fallback automatique"""
        
        if format_priority is None:
            format_priority = [
                CAMERA_FORMATS['PIXFORMAT_RGB565'],
                CAMERA_FORMATS['PIXFORMAT_GRAYSCALE'],
                CAMERA_FORMATS['PIXFORMAT_YUV422'],
            ]
        
        self.log("Initialisation caméra ESP32...")
        
        try:
            # Import du module caméra ESP32
            backend = "esp32camera"
            try:
                import esp32camera as cam_module
            except ImportError:
                import camera as cam_module
                backend = "camera"
                self.log("Backend caméra: module 'camera' (fallback)")
            
            # Tentative avec chaque format dans l'ordre de priorité
            for idx, format_code in enumerate(format_priority):
                format_name = self._format_name(format_code)
                self.log(f"  Tentative {idx+1}: Format {format_name}...", "INFO")
                
                try:
                    # Configuration caméra selon backend disponible
                    if backend == "esp32camera":
                        cam_module.init({
                            'format': format_code,
                            'framesize': CameraConfig.FRAME_SIZE,
                            'quality': CameraConfig.QUALITY,
                            'brightness': CameraConfig.BRIGHTNESS,
                            'contrast': CameraConfig.CONTRAST,
                            'saturation': CameraConfig.SATURATION,
                            'special_effect': 0,
                            'wb_mode': 1 if CameraConfig.ENABLE_AUTO_WHITEBALANCE else 0,
                            'ae_level': 0,  # Auto exposure
                            'aec_value': 300,
                            'agc': 1,
                            'agc_gain': 0,
                            'gainceiling': 0,
                        })
                    else:
                        # Module MicroPython standard: camera
                        if hasattr(cam_module, "deinit"):
                            try:
                                cam_module.deinit()
                            except Exception:
                                pass

                        fmt_map = {
                            CAMERA_FORMATS['PIXFORMAT_GRAYSCALE']: getattr(cam_module, "GRAYSCALE", None),
                            CAMERA_FORMATS['PIXFORMAT_RGB565']: getattr(cam_module, "RGB565", None),
                            CAMERA_FORMATS['PIXFORMAT_YUV422']: getattr(cam_module, "YUV422", None),
                            CAMERA_FORMATS['PIXFORMAT_JPEG']: getattr(cam_module, "JPEG", None),
                        }
                        framesize = getattr(cam_module, "QVGA", CameraConfig.FRAME_SIZE)
                        fmt_value = fmt_map.get(format_code)
                        if fmt_value is None:
                            raise Exception("Format non disponible dans module camera")

                        try:
                            cam_module.init(
                                0,
                                format=fmt_value,
                                framesize=framesize,
                                xclk_freq=20000000,
                            )
                        except TypeError:
                            cam_module.init(format=fmt_value, framesize=framesize)
                    
                    # Test de capture pour valider le format
                    test_buf = cam_module.capture()
                    if test_buf is not None:
                        self.log(f"  ✓ Format {format_name} opérationnel! "
                                f"(Taille buffer: {len(test_buf)} bytes)", "INFO")
                        self.camera = cam_module
                        self.active_format = format_code
                        self.active_framesize = CameraConfig.FRAME_SIZE
                        self.initialized = True
                        return True
                    
                except Exception as format_error:
                    self.log(f"  ✗ Format {format_name} échoué: {format_error}", "WARN")
                    continue
            
            # Aucun format ne fonctionne
            self.last_error = "Aucun format de caméra ne fonctionne"
            self.log(self.last_error, "ERROR")
            return False
            
        except ImportError:
            self.last_error = "Aucun module caméra disponible (esp32camera/camera)"
            self.log(f"✗ {self.last_error}", "ERROR")
            return False
        except Exception as e:
            self.last_error = str(e)
            self.log(f"✗ Erreur initialisation caméra: {e}", "ERROR")
            return False
    
    def capture_frame(self):
        """Capture une frame avec la caméra"""
        if not self.initialized or self.camera is None:
            self.log("Caméra non initialisée!", "ERROR")
            return None
        
        try:
            start_time = time.time()
            buffer = self.camera.capture()
            elapsed = (time.time() - start_time) * 1000
            
            if buffer is None:
                self.log("Capture échouée (buffer None)", "ERROR")
                return None
            
            self.log(f"Frame capturée: {len(buffer)} bytes en {elapsed:.1f}ms")
            return buffer
            
        except Exception as e:
            self.log(f"Erreur capture: {e}", "ERROR")
            return None
    
    def get_camera_status(self):
        """Retourne le statut de la caméra"""
        return {
            'initialized': self.initialized,
            'format': self._format_name(self.active_format) if self.active_format else "N/A",
            'framesize': self._framesize_name(self.active_framesize) if self.active_framesize else "N/A",
            'last_error': self.last_error,
        }
    
    @staticmethod
    def _format_name(format_code):
        """Retourne le nom du format"""
        format_names = {v: k for k, v in CAMERA_FORMATS.items()}
        return format_names.get(format_code, f"UNKNOWN(0x{format_code:02x})")
    
    @staticmethod
    def _framesize_name(size_code):
        """Retourne le nom de la taille"""
        size_names = {v: k for k, v in CAMERA_FRAME_SIZES.items()}
        return size_names.get(size_code, f"UNKNOWN({size_code})")

# ============================================================================
# INSTANCE GLOBALE
# ============================================================================
camera_manager = ESP32CameraManager()

def initialize_with_diagnostics():
    """Initialisation avec diagnostic complet"""
    print("\n" + "="*60)
    print("ESP32 CAM - DIAGNOSTIC COMPLET")
    print("="*60 + "\n")
    
    # Détection capteur
    sensors = camera_manager.detect_camera_module()
    
    # Initialisation caméra
    print()
    success = camera_manager.initialize_camera()
    
    if success:
        print("\n" + "="*60)
        print("✓ SUCCÈS - Caméra prête!")
        print("="*60)
        status = camera_manager.get_camera_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print("\n" + "="*60)
        print("✗ ÉCHEC - Caméra non opérationnelle")
        print("="*60)
        print(f"Erreur: {camera_manager.last_error}")
        print("\nVérifier:")
        print("  1. Câble caméra bien connecté")
        print("  2. Alimentation 5V suffisante")
        print("  3. Version MicroPython compatible")
    
    print()
    return success

# ============================================================================
# SCRIPT DE TEST AUTOMATIQUE
# ============================================================================
if __name__ == "__main__":
    initialize_with_diagnostics()
    
    # Test de capture si succès
    if camera_manager.initialized:
        print("\nTest de capture (3 frames):")
        for i in range(3):
            frame = camera_manager.capture_frame()
            time.sleep(1)
