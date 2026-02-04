import face_recognition # Bibliothèque de référence pour la précision
import cv2
import numpy as np

class VisionEngine:
    """Moteur de traitement d'images pour la reconnaissance faciale sécurisée."""

    def __init__(self, tolerance=0.5):
        # Une tolérance plus basse (ex: 0.5) augmente la sécurité contre les faux positifs
        self.tolerance = tolerance

    def encoder_visage(self, image_path):
        """Transforme une photo d'inscription en signature numérique unique."""
        image = face_recognition.load_image_file(image_path)
        encodages = face_recognition.face_encodings(image)
        if len(encodages) > 0:
            return encodages[0]
        return None

    def verifier_identite(self, encodage_stocke, frame_camera):
        """Compare le scan de la porte avec les données de la base de données."""
        # Conversion de l'image caméra (BGR vers RGB pour face_recognition)
        rgb_frame = cv2.cvtColor(frame_camera, cv2.COLOR_BGR2RGB)
        
        # Localisation et encodage du visage actuel
        visages_detectes = face_recognition.face_encodings(rgb_frame)
        
        if not visages_detectes:
            return False, "Aucun visage détecté"

        # Comparaison mathématique (Distance Euclidienne)
        match = face_recognition.compare_faces([encodage_stocke], visages_detectes[0], tolerance=self.tolerance)
        
        if match[0]:
            return True, "Match réussi"
        return False, "Identité non reconnue"