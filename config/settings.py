"""Configuration centralisée pour l'application U.O.R"""
import os
from dotenv import load_dotenv

load_dotenv()

# Base de données
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "uor_university")
DB_PORT = int(os.getenv("DB_PORT", 3306))

# Sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", 3600))
PASSWORD_MIN_LENGTH = 6  # 6 chiffres minimum

# Seuils financiers
FINANCIAL_THRESHOLD = float(os.getenv("FINANCIAL_THRESHOLD", 0.0))

# Taux de conversion FC -> USD pour affichage
USD_EXCHANGE_RATE_FC = float(os.getenv("USD_EXCHANGE_RATE_FC", 2700.0))

# Email
EMAIL_SERVICE = os.getenv("EMAIL_SERVICE", "gmail")  # ou autre
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# WhatsApp (Twilio - legacy)
WHATSAPP_ACCOUNT_SID = os.getenv("WHATSAPP_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID", ""))
WHATSAPP_AUTH_TOKEN = os.getenv("WHATSAPP_AUTH_TOKEN", os.getenv("TWILIO_AUTH_TOKEN", ""))
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", os.getenv("TWILIO_WHATSAPP_FROM", ""))

# Ultramsg WhatsApp API
ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID", "")
ULTRAMSG_TOKEN = os.getenv("ULTRAMSG_TOKEN", "")

# WhatsApp Templates (optional - for pre-approved content Messages)
WHATSAPP_TEMPLATE_ACCESS_CODE = os.getenv("WHATSAPP_TEMPLATE_ACCESS_CODE", "")
WHATSAPP_TEMPLATE_THRESHOLD_ALERT = os.getenv("WHATSAPP_TEMPLATE_THRESHOLD_ALERT", "")
WHATSAPP_USE_TEMPLATES = os.getenv("WHATSAPP_USE_TEMPLATES", "False").lower() == "true"

# Email branding
EMAIL_LOGO_PATH = os.getenv("EMAIL_LOGO_PATH", "")

# Arduino (OBSOLÈTE — conservé pour rétro-compatibilité)
ARDUINO_PORT      = os.getenv("ARDUINO_PORT",      "COM3")
ARDUINO_BAUD_RATE = int(os.getenv("ARDUINO_BAUD_RATE", 9600))

# ESP32 (Wi-Fi Socket) — serveur d'accès
ESP32_HOST              = os.getenv("ESP32_HOST",              "127.0.0.1")
ESP32_PORT              = int(os.getenv("ESP32_PORT",          5050))
ESP32_SOCKET_TIMEOUT    = float(os.getenv("ESP32_SOCKET_TIMEOUT", 1.5))
ESP32_STATUS_REFRESH_MS = int(os.getenv("ESP32_STATUS_REFRESH_MS", 5000))

# Serveur d'accès HTTP (access_server.py)
ACCESS_SERVER_HOST = os.getenv("ACCESS_SERVER_HOST", "0.0.0.0")

# Caméra IP (nouvelle architecture — remplace ESP32-CAM)
IP_CAMERA_URL          = os.getenv("IP_CAMERA_URL",          "")   # URL flux RTSP
IP_CAMERA_SNAPSHOT_URL = os.getenv("IP_CAMERA_SNAPSHOT_URL", "")   # URL snapshot HTTP
IP_CAMERA_USERNAME     = os.getenv("IP_CAMERA_USERNAME",     "")
IP_CAMERA_PASSWORD     = os.getenv("IP_CAMERA_PASSWORD",     "")
CAMERA_DEVICE_ID       = os.getenv("CAMERA_DEVICE_ID",       "")

# Caméra Yi IoT (fallback FTP image locale)
IP_CAMERA_FTP_ENABLED  = os.getenv("IP_CAMERA_FTP_ENABLED", "False").lower() == "true"
IP_CAMERA_FTP_HOST     = os.getenv("IP_CAMERA_FTP_HOST", "")
IP_CAMERA_FTP_PORT     = int(os.getenv("IP_CAMERA_FTP_PORT", 21))
IP_CAMERA_FTP_PATH     = os.getenv("IP_CAMERA_FTP_PATH", "/tmp/motion.jpg")
IP_CAMERA_FTP_USERNAME = os.getenv("IP_CAMERA_FTP_USERNAME", "")
IP_CAMERA_FTP_PASSWORD = os.getenv("IP_CAMERA_FTP_PASSWORD", "")

# Auto-découverte caméra Yi (utile si l'IP change après reboot DHCP)
IP_CAMERA_AUTO_DISCOVERY_ENABLED = os.getenv("IP_CAMERA_AUTO_DISCOVERY_ENABLED", "False").lower() == "true"
IP_CAMERA_DISCOVERY_SUBNET       = os.getenv("IP_CAMERA_DISCOVERY_SUBNET", "192.168.1.")
IP_CAMERA_DISCOVERY_IP_RANGE     = os.getenv("IP_CAMERA_DISCOVERY_IP_RANGE", "1-254")
IP_CAMERA_DISCOVERY_TIMEOUT      = float(os.getenv("IP_CAMERA_DISCOVERY_TIMEOUT", 0.35))
IP_CAMERA_DISCOVERY_MAX_WORKERS  = int(os.getenv("IP_CAMERA_DISCOVERY_MAX_WORKERS", 48))

# Reconnaissance faciale
FACE_RECOGNITION_TOLERANCE = float(os.getenv("FACE_RECOGNITION_TOLERANCE", 0.50))

# Application
APP_NAME = "U.O.R - Plateforme d'Accès aux Examens"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
