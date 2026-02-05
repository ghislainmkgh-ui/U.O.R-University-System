"""
Tests unitaires pour le service de reconnaissance faciale
Démontre les principes du génie logiciel: testabilité, isolation, mocks
"""
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.services.auth.face_recognition_service import (
    FaceRecognitionService,
    MockFaceRecognitionService
)
from app.services.auth.face_recognition_config import FACE_CONFIG


class TestFaceRecognitionService(unittest.TestCase):
    """Tests pour FaceRecognitionService"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.service = FaceRecognitionService()
    
    def test_service_initialization(self):
        """Test: Le service s'initialise correctement"""
        self.assertIsNotNone(self.service)
        # Le service peut être disponible ou non selon l'installation de face_recognition
        self.assertIsInstance(self.service.is_available(), bool)
    
    def test_validate_tolerance(self):
        """Test: Validation de la tolérance"""
        # Tolérance valide
        try:
            self.service._validate_tolerance(0.5)
            valid = True
        except ValueError:
            valid = False
        self.assertTrue(valid)
        
        # Tolérance invalide (hors limites)
        with self.assertRaises(ValueError):
            self.service._validate_tolerance(-0.1)
        
        with self.assertRaises(ValueError):
            self.service._validate_tolerance(1.5)
    
    def test_validate_student_id(self):
        """Test: Validation de l'ID étudiant"""
        # ID valide
        try:
            self.service._validate_student_id(123)
            valid = True
        except ValueError:
            valid = False
        self.assertTrue(valid)
        
        # ID invalide
        with self.assertRaises(ValueError):
            self.service._validate_student_id(0)
        
        with self.assertRaises(ValueError):
            self.service._validate_student_id(-5)
    
    def test_validate_face_encoding(self):
        """Test: Validation de l'encoding"""
        # Encoding valide (128 dimensions)
        valid_encoding = np.random.rand(128)
        self.assertTrue(self.service._validate_face_encoding(valid_encoding))
        
        # Encoding invalide (mauvaise dimension)
        invalid_encoding = np.random.rand(64)
        self.assertFalse(self.service._validate_face_encoding(invalid_encoding))
        
        # None
        self.assertFalse(self.service._validate_face_encoding(None))
        
        # Type invalide
        self.assertFalse(self.service._validate_face_encoding("not_an_array"))
    
    def test_config_immutability(self):
        """Test: La configuration est immuable"""
        with self.assertRaises(Exception):
            # Tentative de modification (devrait échouer avec dataclass frozen)
            FACE_CONFIG.DEFAULT_TOLERANCE = 0.9


class TestMockFaceRecognitionService(unittest.TestCase):
    """Tests pour MockFaceRecognitionService"""
    
    def test_mock_always_available(self):
        """Test: Le mock est toujours disponible"""
        mock_service = MockFaceRecognitionService()
        self.assertTrue(mock_service.is_available())
    
    def test_mock_register_face(self):
        """Test: Le mock génère un encoding factice"""
        mock_service = MockFaceRecognitionService()
        encoding = mock_service.register_face("fake_path.jpg", 123)
        
        self.assertIsNotNone(encoding)
        self.assertIsInstance(encoding, np.ndarray)
        self.assertEqual(encoding.shape, (128,))
    
    def test_mock_verify_face_always_true(self):
        """Test: Le mock retourne toujours True si configuré"""
        mock_service = MockFaceRecognitionService(always_match=True)
        fake_encoding = np.random.rand(128)
        
        result = mock_service.verify_face("fake_path.jpg", fake_encoding)
        self.assertTrue(result)
    
    def test_mock_verify_face_always_false(self):
        """Test: Le mock retourne toujours False si configuré"""
        mock_service = MockFaceRecognitionService(always_match=False)
        fake_encoding = np.random.rand(128)
        
        result = mock_service.verify_face("fake_path.jpg", fake_encoding)
        self.assertFalse(result)


class TestFaceRecognitionIntegration(unittest.TestCase):
    """Tests d'intégration (nécessitent face_recognition installé)"""
    
    def setUp(self):
        """Initialisation"""
        self.service = FaceRecognitionService()
    
    @unittest.skipIf(
        not FaceRecognitionService().is_available(),
        "face_recognition library not installed"
    )
    def test_service_available_when_library_installed(self):
        """Test: Le service est disponible quand la bibliothèque est installée"""
        self.assertTrue(self.service.is_available())
    
    def test_register_face_with_invalid_path(self):
        """Test: register_face échoue avec un chemin invalide"""
        if not self.service.is_available():
            self.skipTest("Service not available")
        
        with self.assertRaises(FileNotFoundError):
            self.service.register_face("non_existent_image.jpg", 123)


if __name__ == '__main__':
    unittest.main()
