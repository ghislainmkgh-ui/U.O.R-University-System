"""Service pour la reconnaissance faciale (intégration face_recognition)"""
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service pour enregistrer et vérifier les visages"""
    
    def __init__(self):
        try:
            import face_recognition
            self.face_recognition = face_recognition
            self.initialized = True
        except ImportError:
            logger.warning("face_recognition library not installed. Install with: pip install face-recognition")
            self.initialized = False
    
    def register_face(self, image_path: str, student_id: int) -> Optional[bytes]:
        """
        Enregistre le visage d'un étudiant
        
        Args:
            image_path: Chemin vers l'image du visage
            student_id: ID de l'étudiant
            
        Returns:
            Encoding du visage ou None
        """
        if not self.initialized:
            logger.error("Face recognition service not initialized")
            return None
        
        try:
            image = self.face_recognition.load_image_file(image_path)
            face_encodings = self.face_recognition.face_encodings(image)
            
            if not face_encodings:
                logger.warning(f"No face found in image for student {student_id}")
                return None
            
            # Prendre le premier visage détecté
            face_encoding = face_encodings[0]
            logger.info(f"Face registered for student {student_id}")
            return face_encoding
            
        except Exception as e:
            logger.error(f"Error registering face: {e}")
            return None
    
    def verify_face(self, image_path: str, stored_encoding: bytes, tolerance: float = 0.6) -> bool:
        """
        Vérifie un visage contre un encoding stocké
        
        Args:
            image_path: Chemin vers l'image à vérifier
            stored_encoding: Encoding stocké en base
            tolerance: Tolérance de comparaison (0-1, plus bas = plus strict)
            
        Returns:
            True si le visage correspond
        """
        if not self.initialized or stored_encoding is None:
            logger.error("Face recognition not initialized or no stored encoding")
            return False
        
        try:
            image = self.face_recognition.load_image_file(image_path)
            face_encodings = self.face_recognition.face_encodings(image)
            
            if not face_encodings:
                logger.warning("No face found in verification image")
                return False
            
            # Comparaison avec le visage stocké
            matches = self.face_recognition.compare_faces(
                [np.frombuffer(stored_encoding, dtype=np.float64)],
                face_encodings[0],
                tolerance=tolerance
            )
            
            result = matches[0] if matches else False
            logger.info(f"Face verification result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying face: {e}")
            return False
