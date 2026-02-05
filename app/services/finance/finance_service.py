"""Service de gestion des finances"""
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional
from core.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class FinanceService:
    """Service pour gérer les paiements et seuils financiers"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_student_finance(self, student_id: int) -> Optional[dict]:
        """Récupère le profil financier d'un étudiant"""
        try:
            query = "SELECT * FROM FinanceProfile WHERE student_id = %s"
            results = self.db.execute_query(query, (student_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting finance profile: {e}")
            return None
    
    def is_threshold_reached(self, student_id: int) -> bool:
        """Vérifie si le seuil financier est atteint"""
        try:
            finance = self.get_student_finance(student_id)
            if not finance:
                logger.warning(f"No finance profile found for student {student_id}")
                return False
            
            amount_paid = Decimal(str(finance['amount_paid']))
            threshold = Decimal(str(finance['threshold_required']))
            
            is_eligible = amount_paid >= threshold
            logger.info(f"Student {student_id} threshold check: {is_eligible}")
            return is_eligible
            
        except Exception as e:
            logger.error(f"Error checking threshold: {e}")
            return False
    
    def record_payment(self, student_id: int, amount: Decimal) -> bool:
        """Enregistre un paiement pour un étudiant"""
        try:
            finance = self.get_student_finance(student_id)
            if not finance:
                logger.error(f"No finance profile for student {student_id}")
                return False
            
            new_amount = Decimal(str(finance['amount_paid'])) + amount
            
            query = """
                UPDATE FinanceProfile 
                SET amount_paid = %s, last_payment_date = %s
                WHERE student_id = %s
            """
            params = (str(new_amount), datetime.now(), student_id)
            self.db.execute_update(query, params)
            
            logger.info(f"Payment recorded for student {student_id}: {amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording payment: {e}")
            return False
    
    def get_eligible_students(self) -> list:
        """Récupère tous les étudiants éligibles"""
        try:
            query = """
                SELECT s.*, f.amount_paid, f.threshold_required
                FROM Student s
                JOIN FinanceProfile f ON s.id = f.student_id
                WHERE f.amount_paid >= f.threshold_required AND s.is_active = 1
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting eligible students: {e}")
            return []
    
    def get_non_eligible_students(self) -> list:
        """Récupère tous les étudiants non éligibles"""
        try:
            query = """
                SELECT s.*, f.amount_paid, f.threshold_required
                FROM Student s
                JOIN FinanceProfile f ON s.id = f.student_id
                WHERE f.amount_paid < f.threshold_required AND s.is_active = 1
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting non-eligible students: {e}")
            return []
