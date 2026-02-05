"""Service de gestion des étudiants"""
import logging
from typing import List, Optional
from core.models.student import Student
from core.models.promotion import Promotion
from core.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class StudentService:
    """Service pour gérer les étudiants"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def create_student(self, student: Student) -> bool:
        """Crée un nouvel étudiant"""
        try:
            query = """
                INSERT INTO student (student_number, firstname, lastname, email, phone_number, promotion_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                student.student_number,
                student.firstname,
                student.lastname,
                student.email,
                student.phone_number,
                student.promotion_id
            )
            self.db.execute_update(query, params)
            logger.info(f"Student {student.student_number} created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return False
    
    def get_student(self, student_number: str) -> Optional[dict]:
        """Récupère un étudiant par numéro"""
        try:
            query = "SELECT * FROM student WHERE student_number = %s"
            results = self.db.execute_query(query, (student_number,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting student: {e}")
            return None
    
    def get_students_by_promotion(self, promotion_id: int) -> List[dict]:
        """Récupère tous les étudiants d'une promotion"""
        try:
            query = "SELECT * FROM student WHERE promotion_id = %s AND is_active = 1"
            return self.db.execute_query(query, (promotion_id,))
        except Exception as e:
            logger.error(f"Error getting students by promotion: {e}")
            return []
    
    def get_students_by_department(self, department_id: int) -> List[dict]:
        """Récupère tous les étudiants d'un département via les promotions"""
        try:
            query = """
                SELECT s.* FROM student s
                JOIN promotion p ON s.promotion_id = p.id
                WHERE p.department_id = %s AND s.is_active = 1
            """
            return self.db.execute_query(query, (department_id,))
        except Exception as e:
            logger.error(f"Error getting students by department: {e}")
            return []
    
    def deactivate_student(self, student_number: str) -> bool:
        """Désactive un étudiant"""
        try:
            query = "UPDATE student SET is_active = 0 WHERE student_number = %s"
            self.db.execute_update(query, (student_number,))
            logger.info(f"Student {student_number} deactivated")
            return True
        except Exception as e:
            logger.error(f"Error deactivating student: {e}")
            return False

    def update_face_encoding(self, student_id: int, face_encoding: bytes) -> bool:
        """Met à jour l'encodage du visage d'un étudiant"""
        try:
            query = "UPDATE student SET face_encoding = %s WHERE id = %s"
            self.db.execute_update(query, (face_encoding, student_id))
            logger.info(f"Face encoding updated for student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating face encoding: {e}")
            return False

    def get_all_students_with_finance(self) -> List[dict]:
        """Récupère tous les étudiants avec données financières"""
        try:
            query = """
                SELECT 
                    s.id,
                    s.student_number,
                    s.firstname,
                    s.lastname,
                    s.email,
                    s.promotion_id,
                    s.is_active,
                    fp.amount_paid,
                    fp.threshold_required,
                    fp.is_eligible
                FROM student s
                LEFT JOIN finance_profile fp ON fp.student_id = s.id
                WHERE s.is_active = 1
                ORDER BY s.created_at DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting students list: {e}")
            return []

    def get_promotions(self) -> List[dict]:
        """Récupère les promotions actives"""
        try:
            query = "SELECT id, name, year FROM promotion WHERE is_active = 1 ORDER BY year DESC, name"
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting promotions: {e}")
            return []
