"""Service d'authentification principal"""
import logging
from core.security.password_hasher import PasswordHasher
from core.security.validators import Validators
from core.models.student import Student
from core.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service d'authentification pour les étudiants et administrateurs"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.password_hasher = PasswordHasher()
        self.validators = Validators()
    
    def register_student(self, student: Student, password: str) -> bool:
        """
        Enregistre un nouvel étudiant
        
        Args:
            student: Objet Student
            password: Mot de passe en clair
            
        Returns:
            True si l'enregistrement réussit
        """
        try:
            # Valider les entrées
            valid, msg = self.validators.validate_numeric_password(password)
            if not valid:
                logger.warning(f"Invalid password for student {student.student_number}: {msg}")
                return False
            
            # Hacher le mot de passe
            password_hash = self.password_hasher.hash_password(password)
            
            # Insérer en base de données
            query = """
                INSERT INTO student (student_number, firstname, lastname, email, phone_number, promotion_id, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                student.student_number,
                student.firstname,
                student.lastname,
                student.email,
                student.phone_number,
                student.promotion_id,
                password_hash
            )
            
            self.db.execute_update(query, params)
            logger.info(f"Student {student.student_number} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering student: {e}")
            return False
    
    def authenticate_student(self, student_number: str, password: str) -> dict:
        """
        Authentifie un étudiant
        
        Args:
            student_number: Numéro d'étudiant
            password: Mot de passe en clair
            
        Returns:
            Dictionnaire avec les données de l'étudiant ou None
        """
        try:
            # Récupérer l'étudiant de la base
            query = "SELECT * FROM student WHERE student_number = %s"
            results = self.db.execute_query(query, (student_number,))
            
            if not results:
                logger.warning(f"Authentication failed: Student {student_number} not found")
                return None
            
            student = results[0]
            
            # Vérifier le mot de passe
            if not self.password_hasher.verify_password(password, student['password_hash']):
                logger.warning(f"Authentication failed: Wrong password for {student_number}")
                return None
            
            logger.info(f"Student {student_number} authenticated successfully")
            return student
            
        except Exception as e:
            logger.error(f"Error authenticating student: {e}")
            return None
    
    def change_password(self, student_number: str, old_password: str, new_password: str) -> bool:
        """
        Change le mot de passe d'un étudiant
        
        Args:
            student_number: Numéro d'étudiant
            old_password: Ancien mot de passe
            new_password: Nouveau mot de passe
            
        Returns:
            True si le changement réussit
        """
        try:
            # Valider les entrées
            valid, msg = self.validators.validate_numeric_password(new_password)
            if not valid:
                logger.warning(f"Invalid new password for {student_number}: {msg}")
                return False
            
            # Authentifier avec l'ancien mot de passe
            student = self.authenticate_student(student_number, old_password)
            if not student:
                logger.warning(f"Password change failed: Authentication failed for {student_number}")
                return False
            
            # Hacher le nouveau mot de passe
            new_hash = self.password_hasher.hash_password(new_password)
            
            # Mettre à jour en base
            query = "UPDATE student SET password_hash = %s WHERE student_number = %s"
            self.db.execute_update(query, (new_hash, student_number))
            
            logger.info(f"Password changed successfully for {student_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False

    def register_student_with_face(self, student: Student, password: str, face_encoding: bytes) -> int:
        """
        Enregistre un nouvel étudiant avec encodage facial

        Args:
            student: Objet Student
            password: Mot de passe en clair
            face_encoding: Encodage facial en bytes

        Returns:
            ID de l'étudiant si succès, sinon 0
        """
        try:
            valid, msg = self.validators.validate_numeric_password(password)
            if not valid:
                logger.warning(f"Invalid password for student {student.student_number}: {msg}")
                return 0

            password_hash = self.password_hasher.hash_password(password)

            query = """
                INSERT INTO student (
                    student_number, firstname, lastname, email, phone_number, promotion_id, password_hash, face_encoding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                student.student_number,
                student.firstname,
                student.lastname,
                student.email,
                student.phone_number,
                student.promotion_id,
                password_hash,
                face_encoding
            )

            self.db.execute_update(query, params)

            result = self.db.execute_query(
                "SELECT id FROM student WHERE student_number = %s",
                (student.student_number,)
            )
            if not result:
                logger.error("Student inserted but ID not found")
                return 0

            student_id = result[0]["id"]
            logger.info(f"Student {student.student_number} registered with face encoding")
            return student_id

        except Exception as e:
            logger.error(f"Error registering student with face: {e}")
            return 0
