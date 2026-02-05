"""
Guide de migration pour les anciennes implémentations
"""

# === AVANT (ancien code) ===
# from app.services.auth.face_recognition_service import FaceRecognitionService
# 
# service = FaceRecognitionService()
# if service.initialized:
#     encoding = service.register_face(image_path, student_id)
#     # encoding était retourné comme bytes

# === APRÈS (nouveau code avec SOLID) ===
from app.services.auth import FaceRecognitionService
import numpy as np

service = FaceRecognitionService()

# 1. Vérifier la disponibilité (remplace .initialized)
if service.is_available():
    
    # 2. Enregistrement (retourne maintenant numpy.ndarray)
    try:
        encoding = service.register_face(image_path, student_id)
        if encoding is not None:
            # Convertir en bytes pour stockage en base de données
            encoding_bytes = encoding.tobytes()
            # Sauvegarder encoding_bytes dans la base
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"Erreur: {e}")
    
    # 3. Vérification (accepte maintenant numpy.ndarray)
    # Récupérer depuis la base de données
    stored_encoding_bytes = ...  # depuis DB
    
    # Convertir bytes -> numpy array
    stored_encoding = np.frombuffer(stored_encoding_bytes, dtype=np.float64)
    
    # Vérifier avec tolérance personnalisée (optionnelle)
    try:
        is_match = service.verify_face(
            capture_path, 
            stored_encoding,
            tolerance=0.5  # Optionnel, utilise FACE_CONFIG par défaut
        )
    except (ValueError, RuntimeError) as e:
        print(f"Erreur: {e}")

# === Pour les TESTS ===
from app.services.auth import MockFaceRecognitionService

# Utiliser le mock pour les tests
mock_service = MockFaceRecognitionService(always_match=True)
assert mock_service.is_available() == True
encoding = mock_service.register_face("test.jpg", 1)
assert mock_service.verify_face("test.jpg", encoding) == True

# === Configuration personnalisée ===
from app.services.auth.face_recognition_config import FaceRecognitionConfig
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomConfig(FaceRecognitionConfig):
    DEFAULT_TOLERANCE: float = 0.7  # Plus permissif

custom_service = FaceRecognitionService(config=CustomConfig())

print("""
CHANGEMENTS IMPORTANTS:
1. .initialized -> .is_available()
2. Retour de register_face: bytes -> numpy.ndarray
3. Paramètre de verify_face: bytes -> numpy.ndarray
4. Nouvelles exceptions: ValueError, FileNotFoundError, RuntimeError
5. Validation stricte de tous les paramètres
6. Configuration via injection de dépendance
7. Interface abstraite pour dépendances inversées
""")
