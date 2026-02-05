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
                INSERT INTO Student (student_number, firstname, lastname, email, promotion_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                student.student_number,
                student.firstname,
                student.lastname,
                student.email,
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
            query = "SELECT * FROM Student WHERE student_number = %s"
            results = self.db.execute_query(query, (student_number,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting student: {e}")
            return None
    
    def get_students_by_promotion(self, promotion_id: int) -> List[dict]:
        """Récupère tous les étudiants d'une promotion"""
        try:
            query = "SELECT * FROM Student WHERE promotion_id = %s AND is_active = 1"
            return self.db.execute_query(query, (promotion_id,))
        except Exception as e:
            logger.error(f"Error getting students by promotion: {e}")
            return []
    
    def get_students_by_department(self, department_id: int) -> List[dict]:
        """Récupère tous les étudiants d'un département via les promotions"""
        try:
            query = """
                SELECT s.* FROM Student s
                JOIN Promotion p ON s.promotion_id = p.id
                WHERE p.department_id = %s AND s.is_active = 1
            """
            return self.db.execute_query(query, (department_id,))
        except Exception as e:
            logger.error(f"Error getting students by department: {e}")
            return []
    
    def deactivate_student(self, student_number: str) -> bool:
        """Désactive un étudiant"""
        try:
            query = "UPDATE Student SET is_active = 0 WHERE student_number = %s"
            self.db.execute_update(query, (student_number,))
            logger.info(f"Student {student_number} deactivated")
            return True
        except Exception as e:
            logger.error(f"Error deactivating student: {e}")
            return False
