"""Service d'authentification principal"""
import logging
import secrets
from typing import Optional
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
        self._last_error = None

    def get_last_error(self) -> Optional[str]:
        """Retourne le dernier message d'erreur métier/technique."""
        return self._last_error

    def _set_last_error(self, message: Optional[str]):
        self._last_error = message

    def _get_table_columns(self, table_name: str) -> set:
        try:
            query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
            """
            rows = self.db.execute_query(query, (table_name,)) or []
            return {row.get("COLUMN_NAME") for row in rows if row.get("COLUMN_NAME")}
        except Exception as e:
            logger.error(f"Error fetching columns for {table_name}: {e}")
            return set()
    
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

    def authenticate_admin(self, username: str, password: str) -> dict:
        """Authentifie un administrateur"""
        try:
            query = "SELECT * FROM administrator WHERE username = %s AND is_active = 1"
            results = self.db.execute_query(query, (username,))

            if not results:
                logger.warning(f"Authentication failed: Admin {username} not found")
                return None

            admin = results[0]

            if not self.password_hasher.verify_password(password, admin['password_hash']):
                logger.warning(f"Authentication failed: Wrong password for admin {username}")
                return None

            logger.info(f"Admin {username} authenticated successfully")
            return admin
        except Exception as e:
            logger.error(f"Error authenticating admin: {e}")
            return None

    def authenticate(self, identifier: str, password: str):
        """Authentifie par numéro d'étudiant ou email.

        Returns:
            (user_dict, error_message)
        """
        if not identifier or not password:
            return None, "Please enter credentials"

        # 1) Try admin
        admin = self.authenticate_admin(identifier, password)
        if admin:
            admin["role"] = "admin"
            return admin, None

        # 2) Try student number
        user = self.authenticate_student(identifier, password)
        if user:
            user["role"] = "student"
            return user, None

        # 3) Try email
        try:
            query = "SELECT * FROM student WHERE email = %s"
            results = self.db.execute_query(query, (identifier,))
            if not results:
                return None, "Invalid credentials"

            student = results[0]
            if not self.password_hasher.verify_password(password, student['password_hash']):
                return None, "Invalid credentials"

            student["role"] = "student"
            logger.info(f"Student {student.get('email')} authenticated successfully")
            return student, None
        except Exception as e:
            logger.error(f"Error authenticating by email: {e}")
            return None, "Authentication error"

    def register_admin_account(self, username: str, email: str, password: str) -> tuple:
        """Crée un compte administrateur (table `administrator`).

        Returns:
            (success: bool, message: str)
        """
        try:
            username = (username or "").strip()
            email = (email or "").strip().lower()
            password = (password or "").strip()

            if not username or not email or not password:
                return False, "Username, email et mot de passe requis"
            if len(password) < 6:
                return False, "Le mot de passe doit avoir au moins 6 caractères"

            columns = self._get_table_columns("administrator")
            if not columns:
                return False, "Table administrator introuvable"
            if "username" not in columns or "password_hash" not in columns:
                return False, "La table administrator ne contient pas les colonnes requises"

            existing = self.db.execute_query(
                "SELECT id FROM administrator WHERE username = %s",
                (username,),
            )
            if existing:
                return False, "Ce nom d'utilisateur admin existe déjà"

            if "email" in columns:
                existing_email = self.db.execute_query(
                    "SELECT id FROM administrator WHERE LOWER(email) = %s",
                    (email,),
                )
                if existing_email:
                    return False, "Cet email admin existe déjà"

            password_hash = self.password_hasher.hash_password(password)

            insert_columns = ["username", "password_hash"]
            insert_values = [username, password_hash]

            if "email" in columns:
                insert_columns.append("email")
                insert_values.append(email)
            if "is_active" in columns:
                insert_columns.append("is_active")
                insert_values.append(1)

            query = (
                f"INSERT INTO administrator ({', '.join(insert_columns)}) "
                f"VALUES ({', '.join(['%s'] * len(insert_columns))})"
            )
            self.db.execute_update(query, tuple(insert_values))

            logger.info(f"Admin account created: {username}")
            return True, "Compte administrateur créé"

        except Exception as e:
            logger.error(f"Error creating admin account: {e}")
            return False, f"Erreur: {str(e)}"
    
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

    def reset_password_by_email(self, identifier: str, new_password: str) -> tuple:
        """Réinitialise le mot de passe via email ou matricule (flux 'mot de passe oublié').

        Returns:
            (success: bool, message: str)
        """
        try:
            identifier = (identifier or "").strip()
            if not identifier or not new_password:
                return False, "Identifiant et mot de passe requis"
            if len(new_password) < 4:
                return False, "Le mot de passe doit avoir au moins 4 caractères"

            new_hash = self.password_hasher.hash_password(new_password)

            # 1) Admin par username
            res = self.db.execute_query(
                "SELECT id FROM administrator WHERE username = %s", (identifier,)
            )
            if res:
                self.db.execute_update(
                    "UPDATE administrator SET password_hash = %s WHERE username = %s",
                    (new_hash, identifier),
                )
                logger.info(f"Admin password reset for '{identifier}'")
                return True, "Mot de passe réinitialisé avec succès"

            # 2) Étudiant par email
            res = self.db.execute_query(
                "SELECT id FROM student WHERE email = %s", (identifier,)
            )
            if res:
                self.db.execute_update(
                    "UPDATE student SET password_hash = %s WHERE email = %s",
                    (new_hash, identifier),
                )
                logger.info(f"Student password reset by email '{identifier}'")
                return True, "Mot de passe réinitialisé avec succès"

            # 3) Étudiant par matricule
            res = self.db.execute_query(
                "SELECT id FROM student WHERE student_number = %s", (identifier,)
            )
            if res:
                self.db.execute_update(
                    "UPDATE student SET password_hash = %s WHERE student_number = %s",
                    (new_hash, identifier),
                )
                logger.info(f"Student password reset by number '{identifier}'")
                return True, "Mot de passe réinitialisé avec succès"

            return False, "Aucun compte trouvé pour cet identifiant"

        except Exception as e:
            logger.error(f"reset_password_by_email error: {e}")
            return False, f"Erreur: {str(e)}"

    def authenticate_by_email_no_pw(self, email: str) -> dict:
        """Authentifie un utilisateur par email uniquement (flux OAuth — identité vérifiée par le provider).

        Returns:
            dict with 'role' key, or None if not found.
        """
        try:
            email_lower = (email or "").strip().lower()
            if not email_lower:
                return None

            # Vérifie dans administrator si une colonne email existe
            try:
                res = self.db.execute_query(
                    "SELECT * FROM administrator WHERE LOWER(email) = %s AND is_active = 1",
                    (email_lower,),
                )
                if res:
                    admin = res[0]
                    admin["role"] = "admin"
                    logger.info(f"OAuth admin login: {email_lower}")
                    return admin
            except Exception:
                pass  # colonne email absente dans administrator – non bloquant

            # Vérifie dans student
            res = self.db.execute_query(
                "SELECT * FROM student WHERE LOWER(email) = %s", (email_lower,)
            )
            if res:
                student = res[0]
                student["role"] = "student"
                logger.info(f"OAuth student login: {email_lower}")
                return student

            logger.warning(f"OAuth: no account for email '{email_lower}'")
            return None

        except Exception as e:
            logger.error(f"authenticate_by_email_no_pw error: {e}")
            return None

    def _generate_placeholder_password(self) -> str:
        """Génère un mot de passe temporaire non communiqué"""
        return secrets.token_urlsafe(24)

    def register_student_with_face(self, student: Student, password: Optional[str], face_encoding: Optional[bytes]) -> int:
        """
        Enregistre un nouvel étudiant avec encodage facial

        Args:
            student: Objet Student
            password: Mot de passe en clair
            face_encoding: Encodage facial en bytes

        Returns:
            ID de l'étudiant si succès, sinon 0
        """
        self._set_last_error(None)
        try:
            if password:
                valid, msg = self.validators.validate_numeric_password(password)
                if not valid:
                    error_msg = f"Mot de passe invalide: {msg}"
                    self._set_last_error(error_msg)
                    logger.warning(f"Invalid password for student {student.student_number}: {msg}")
                    return 0
                password_to_hash = password
            else:
                password_to_hash = self._generate_placeholder_password()

            password_hash = self.password_hasher.hash_password(password_to_hash)

            columns = self._get_table_columns("student")
            insert_columns = []
            insert_values = []

            def add_column(name, value):
                if name in columns:
                    insert_columns.append(name)
                    insert_values.append(value)

            add_column("student_number", student.student_number)
            add_column("firstname", student.firstname)
            add_column("lastname", student.lastname)
            add_column("email", student.email)
            add_column("phone_number", student.phone_number)
            add_column("promotion_id", student.promotion_id)
            add_column("passport_photo_path", student.passport_photo_path)
            add_column("passport_photo_blob", student.passport_photo_blob)
            add_column("password_hash", password_hash)
            add_column("face_encoding", face_encoding)
            add_column("academic_year_id", student.academic_year_id)

            placeholders = ", ".join(["%s"] * len(insert_columns))
            columns_sql = ", ".join(insert_columns)
            query = f"INSERT INTO student ({columns_sql}) VALUES ({placeholders})"
            self.db.execute_update(query, tuple(insert_values))

            result = self.db.execute_query(
                "SELECT id FROM student WHERE student_number = %s",
                (student.student_number,)
            )
            if not result:
                error_msg = "Étudiant inséré mais identifiant introuvable"
                self._set_last_error(error_msg)
                logger.error("Student inserted but ID not found")
                return 0

            student_id = result[0]["id"]
            self._set_last_error(None)
            if face_encoding is None:
                logger.info(f"Student {student.student_number} registered without face encoding")
            else:
                logger.info(f"Student {student.student_number} registered with face encoding")
            return student_id

        except Exception as e:
            error_msg = str(e)
            self._set_last_error(error_msg)
            logger.error(f"Error registering student with face: {e}")
            return 0
