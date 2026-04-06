"""
Service de Reconnaissance Faciale — côté serveur Python
========================================================
Compare le visage capturé par la caméra IP avec la photo
de référence de l'étudiant stockée en base de données.

Bibliothèques requises :
  pip install face-recognition opencv-python

Sources de photo de référence (par priorité) :
  1. passport_photo_blob : blob binaire stocké en BD  (priorité)
  2. passport_photo_path : chemin absolu vers fichier image  (fallback)

Si aucune photo de référence n'est disponible → accès refusé.
Si face_recognition n'est pas installé → mode dégradé (accès accordé sur code valide uniquement).

CONFIGURATION :
  FACE_RECOGNITION_TOLERANCE dans .env (défaut 0.50)
  Plus la valeur est basse → plus strict (0.4 = strict, 0.6 = permissif)
"""

import logging
import numpy as np
import cv2

logger = logging.getLogger(__name__)

try:
    import face_recognition as _fr
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("Bibliothèque face_recognition chargée avec succès")
except ImportError:
    _fr = None
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning(
        "face_recognition non installé — reconnaissance faciale désactivée. "
        "Installez avec : pip install face-recognition"
    )


class FaceRecognitionService:
    """
    Identifie un étudiant par comparaison faciale entre :
      - La frame capturée par la caméra IP (image live)
      - La photo de référence de l'étudiant (BD ou fichier)
    """

    def __init__(self, tolerance: float = None):
        from config.settings import FACE_RECOGNITION_TOLERANCE
        self.tolerance = tolerance if tolerance is not None else FACE_RECOGNITION_TOLERANCE
        logger.info(
            f"FaceRecognitionService initialisé — "
            f"tolérance={self.tolerance} "
            f"(face_recognition: {'DISPONIBLE' if FACE_RECOGNITION_AVAILABLE else 'NON DISPONIBLE'})"
        )

    # ── API publique ──────────────────────────────────────────────────────────

    def identify_student(
        self,
        frame: np.ndarray,
        student: dict,
    ) -> tuple[bool, float]:
        """
        Compare le visage dans `frame` avec la photo de référence de l'étudiant.

        Args:
            frame:    Image BGR numpy array capturée par la caméra IP.
            student:  Dict contenant passport_photo_blob et/ou passport_photo_path.

        Returns:
            (recognized: bool, confidence: float entre 0.0 et 1.0)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning(
                "face_recognition non disponible — accès accordé sur code valide uniquement (mode dégradé)"
            )
            return True, 1.0

        # Obtenir l'encodage facial de référence
        ref_encoding = self._get_reference_encoding(student)
        if ref_encoding is None:
            student_id = student.get("id", "?")
            logger.warning(
                f"Aucune photo de référence pour étudiant id={student_id} — accès refusé"
            )
            return False, 0.0

        # Convertir BGR → RGB (face_recognition utilise RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Détecter les visages dans la frame
        face_locations = _fr.face_locations(rgb_frame, model="hog")
        if not face_locations:
            logger.warning("Aucun visage détecté dans la frame de la caméra IP")
            return False, 0.0

        if len(face_locations) > 1:
            logger.info(f"{len(face_locations)} visages détectés — sélection du plus grand")
            # Sélectionner le visage avec la plus grande hauteur (top, right, bottom, left)
            face_locations = [max(face_locations, key=lambda f: f[2] - f[0])]

        # Encoder le visage capturé
        face_encodings = _fr.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            logger.warning("Encodage du visage détecté impossible")
            return False, 0.0

        captured_encoding = face_encodings[0]

        # Calculer la distance entre visage capturé et référence
        distance   = _fr.face_distance([ref_encoding], captured_encoding)[0]
        recognized = bool(distance <= self.tolerance)
        confidence = float(max(0.0, 1.0 - distance))

        logger.info(
            f"Résultat reconnaissance: distance={distance:.3f} / tolérance={self.tolerance} "
            f"→ {'✓ RECONNU' if recognized else '✗ NON RECONNU'}  (confiance={confidence:.2f})"
        )

        return recognized, confidence

    # ── Méthodes privées ──────────────────────────────────────────────────────

    def _get_reference_encoding(self, student: dict) -> np.ndarray | None:
        """Encode le visage de référence de l'étudiant (blob BD ou fichier)."""
        # Priorité 1 : blob binaire stocké en BD
        blob = student.get("passport_photo_blob")
        if blob:
            return self._encode_from_bytes(bytes(blob), source="blob BD")

        # Priorité 2 : chemin fichier
        path = student.get("passport_photo_path")
        if path:
            return self._encode_from_file(path)

        return None

    def _encode_from_bytes(self, data: bytes, source: str = "blob") -> np.ndarray | None:
        """Encode un visage depuis des données binaires (JPEG, PNG…)."""
        try:
            img_array = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None:
                logger.error(f"Décodage image {source} échoué (format non supporté)")
                return None
            return self._encode_image(img, source=source)
        except Exception as e:
            logger.error(f"Erreur encodage depuis {source}: {e}")
            return None

    def _encode_from_file(self, path: str) -> np.ndarray | None:
        """Encode un visage depuis un fichier image."""
        try:
            img = cv2.imread(path)
            if img is None:
                logger.error(f"Fichier image introuvable ou illisible: {path}")
                return None
            return self._encode_image(img, source=f"fichier:{path}")
        except Exception as e:
            logger.error(f"Erreur lecture fichier image '{path}': {e}")
            return None

    def _encode_image(self, img_bgr: np.ndarray, source: str) -> np.ndarray | None:
        """Retourne l'encodage 128D du visage trouvé dans une image BGR."""
        try:
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            locations = _fr.face_locations(rgb, model="hog")
            if not locations:
                logger.warning(f"Aucun visage trouvé dans la photo de référence ({source})")
                return None
            encodings = _fr.face_encodings(rgb, [locations[0]])
            if not encodings:
                return None
            return encodings[0]
        except Exception as e:
            logger.error(f"Erreur encodage image ({source}): {e}")
            return None
