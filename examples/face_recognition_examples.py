"""
Exemples d'utilisation du FaceRecognitionService
Démonstration des principes du génie logiciel en action
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import numpy as np
from app.services.auth import (
    FaceRecognitionService,
    MockFaceRecognitionService,
    IFaceRecognitionService,
    FACE_CONFIG
)


# ============================================================================
# EXEMPLE 1: Utilisation basique (Simple et robuste)
# ============================================================================
def exemple_1_utilisation_basique():
    """Enregistrement et vérification d'un visage"""
    print("=== EXEMPLE 1: Utilisation basique ===\n")
    
    # Créer le service
    service = FaceRecognitionService()
    
    # Vérifier la disponibilité
    if not service.is_available():
        print("❌ Service non disponible. Installer: pip install face-recognition")
        return
    
    print("✅ Service de reconnaissance faciale prêt\n")
    
    # Enregistrer un visage
    student_id = 123
    image_path = "photos/student_123.jpg"
    
    try:
        print(f"📸 Enregistrement du visage pour l'étudiant {student_id}...")
        encoding = service.register_face(image_path, student_id)
        
        if encoding is not None:
            print(f"✅ Visage enregistré (shape: {encoding.shape})")
            print(f"   Type: {type(encoding)}")
            
            # Convertir pour stockage en base de données
            encoding_bytes = encoding.tobytes()
            print(f"   Taille en bytes: {len(encoding_bytes)}")
            
            # Simuler la vérification
            print(f"\n🔍 Vérification du visage...")
            is_match = service.verify_face(image_path, encoding, tolerance=0.5)
            print(f"   Résultat: {'✅ Match' if is_match else '❌ Pas de match'}")
        else:
            print("❌ Aucun visage détecté dans l'image")
    
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {image_path}")
    except ValueError as e:
        print(f"❌ Erreur de validation: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


# ============================================================================
# EXEMPLE 2: Injection de dépendances (SOLID - DIP)
# ============================================================================
class AccessController:
    """Contrôleur d'accès utilisant l'injection de dépendances"""
    
    def __init__(self, face_service: IFaceRecognitionService):
        """
        Le contrôleur dépend de l'interface, pas de l'implémentation concrète
        (Dependency Inversion Principle)
        """
        self._face_service = face_service
    
    def validate_student_access(self, image_path: str, stored_encoding: np.ndarray) -> bool:
        """Valide l'accès d'un étudiant"""
        if not self._face_service.is_available():
            print("⚠️ Service de reconnaissance faciale indisponible")
            return False
        
        return self._face_service.verify_face(
            image_path, 
            stored_encoding,
            tolerance=FACE_CONFIG.SECURITY_HIGH_TOLERANCE
        )


def exemple_2_injection_dependances():
    """Démonstration de l'injection de dépendances"""
    print("\n=== EXEMPLE 2: Injection de dépendances ===\n")
    
    # En production: service réel
    real_service = FaceRecognitionService()
    controller_prod = AccessController(real_service)
    print(f"✅ Contrôleur de production créé")
    
    # En test: mock service
    mock_service = MockFaceRecognitionService(always_match=True)
    controller_test = AccessController(mock_service)
    print(f"✅ Contrôleur de test créé")
    
    # Les deux contrôleurs ont la même interface!
    fake_encoding = np.random.rand(128)
    
    print(f"\n🧪 Test avec mock (toujours True):")
    result_test = controller_test.validate_student_access("test.jpg", fake_encoding)
    print(f"   Résultat: {result_test}")
    
    # Principe: Le code client ne sait pas quelle implémentation est utilisée


# ============================================================================
# EXEMPLE 3: Gestion d'erreurs robuste (Fail Fast)
# ============================================================================
def exemple_3_gestion_erreurs():
    """Démonstration de la validation précoce"""
    print("\n=== EXEMPLE 3: Gestion d'erreurs robuste ===\n")
    
    service = FaceRecognitionService()
    
    if not service.is_available():
        print("⚠️ Service non disponible - tests limités")
        return
    
    # Test 1: Chemin invalide
    print("Test 1: Chemin invalide")
    try:
        service.register_face("", 123)
        print("   ❌ Devrait lever ValueError")
    except ValueError as e:
        print(f"   ✅ ValueError correctement levée: {e}")
    
    # Test 2: ID étudiant invalide
    print("\nTest 2: ID étudiant invalide")
    try:
        service.register_face("test.jpg", -1)
        print("   ❌ Devrait lever ValueError")
    except ValueError as e:
        print(f"   ✅ ValueError correctement levée: {e}")
    
    # Test 3: Tolérance invalide
    print("\nTest 3: Tolérance invalide")
    try:
        fake_encoding = np.random.rand(128)
        service.verify_face("test.jpg", fake_encoding, tolerance=2.0)
        print("   ❌ Devrait lever ValueError")
    except ValueError as e:
        print(f"   ✅ ValueError correctement levée: {e}")
    
    print("\n✅ Toutes les validations fonctionnent correctement")


# ============================================================================
# EXEMPLE 4: Configuration personnalisée (OCP)
# ============================================================================
from dataclasses import dataclass, field
from app.services.auth.face_recognition_config import FaceRecognitionConfig

@dataclass(frozen=True)
class StrictSecurityConfig(FaceRecognitionConfig):
    """Configuration avec sécurité maximale"""
    DEFAULT_TOLERANCE: float = 0.4  # Plus strict
    SECURITY_HIGH_TOLERANCE: float = 0.3  # Très strict
    MAX_IMAGE_SIZE_MB: int = 5  # Taille limitée


def exemple_4_configuration_personnalisee():
    """Utilisation d'une configuration personnalisée"""
    print("\n=== EXEMPLE 4: Configuration personnalisée ===\n")
    
    # Service avec configuration par défaut
    service_default = FaceRecognitionService()
    print(f"✅ Service par défaut créé")
    
    # Service avec configuration stricte
    strict_config = StrictSecurityConfig()
    service_strict = FaceRecognitionService(config=strict_config)
    print(f"✅ Service strict créé")
    
    print(f"\nConfiguration par défaut:")
    print(f"   Tolérance: {FACE_CONFIG.DEFAULT_TOLERANCE}")
    print(f"   Sécurité: {FACE_CONFIG.SECURITY_HIGH_TOLERANCE}")
    
    print(f"\nConfiguration stricte:")
    print(f"   Tolérance: {strict_config.DEFAULT_TOLERANCE}")
    print(f"   Sécurité: {strict_config.SECURITY_HIGH_TOLERANCE}")
    
    # Principe: Extension sans modification (OCP)


# ============================================================================
# EXEMPLE 5: Tests unitaires avec Mock (LSP)
# ============================================================================
def exemple_5_tests_avec_mock():
    """Utilisation du mock pour les tests"""
    print("\n=== EXEMPLE 5: Tests avec Mock ===\n")
    
    # Créer un mock qui matche toujours
    mock_always_match = MockFaceRecognitionService(always_match=True)
    
    # Test 1: Enregistrement
    encoding = mock_always_match.register_face("fake.jpg", 999)
    print(f"✅ Mock - Enregistrement: {encoding.shape}")
    
    # Test 2: Vérification (toujours True)
    result = mock_always_match.verify_face("fake.jpg", encoding)
    print(f"✅ Mock - Vérification (always_match=True): {result}")
    assert result == True
    
    # Créer un mock qui ne matche jamais
    mock_never_match = MockFaceRecognitionService(always_match=False)
    result = mock_never_match.verify_face("fake.jpg", encoding)
    print(f"✅ Mock - Vérification (always_match=False): {result}")
    assert result == False
    
    print("\n✅ Tests avec mock réussis (Liskov Substitution Principle)")


# ============================================================================
# EXEMPLE 6: Workflow complet (Intégration)
# ============================================================================
def exemple_6_workflow_complet():
    """Workflow complet d'enregistrement et vérification"""
    print("\n=== EXEMPLE 6: Workflow complet ===\n")
    
    # Simuler avec mock (en attendant face_recognition)
    service = MockFaceRecognitionService()
    
    print("📋 Scénario: Inscription d'un nouvel étudiant")
    print("-" * 50)
    
    # Étape 1: Vérifier la disponibilité
    if service.is_available():
        print("✅ Étape 1: Service disponible")
    else:
        print("❌ Service indisponible")
        return
    
    # Étape 2: Enregistrer le visage
    student_id = 456
    photo_inscription = "photos/inscription_456.jpg"
    
    encoding = service.register_face(photo_inscription, student_id)
    if encoding is not None:
        print(f"✅ Étape 2: Visage enregistré pour l'étudiant {student_id}")
        
        # Étape 3: Sauvegarder en base de données
        encoding_bytes = encoding.tobytes()
        print(f"✅ Étape 3: Encoding converti en bytes ({len(encoding_bytes)} bytes)")
        
        # Simuler la sauvegarde en DB
        db_storage = {"student_id": student_id, "face_encoding": encoding_bytes}
        print(f"✅ Étape 4: Encoding sauvegardé en base de données")
        
        # Étape 5: Simulation - Vérification à la porte d'examen
        print(f"\n🚪 Scénario: Accès à la salle d'examen")
        print("-" * 50)
        
        photo_porte = "photos/camera_porte_456.jpg"
        
        # Récupérer l'encoding depuis la DB
        stored_encoding = np.frombuffer(db_storage["face_encoding"], dtype=np.float64)
        
        # Vérifier le visage
        is_match = service.verify_face(photo_porte, stored_encoding, tolerance=0.5)
        
        if is_match:
            print(f"✅ Étape 5: Visage vérifié - ACCÈS AUTORISÉ")
        else:
            print(f"❌ Étape 5: Visage non reconnu - ACCÈS REFUSÉ")
    else:
        print("❌ Étape 2: Échec de l'enregistrement")


# ============================================================================
# MAIN: Exécuter tous les exemples
# ============================================================================
def main():
    """Exécute tous les exemples"""
    print("=" * 70)
    print("   DÉMONSTRATION DU SERVICE DE RECONNAISSANCE FACIALE")
    print("   Architecture SOLID & Principes du Génie Logiciel")
    print("=" * 70)
    
    try:
        # exemple_1_utilisation_basique()  # Nécessite face_recognition
        exemple_2_injection_dependances()
        exemple_3_gestion_erreurs()
        exemple_4_configuration_personnalisee()
        exemple_5_tests_avec_mock()
        exemple_6_workflow_complet()
        
        print("\n" + "=" * 70)
        print("   ✅ TOUS LES EXEMPLES TERMINÉS AVEC SUCCÈS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
