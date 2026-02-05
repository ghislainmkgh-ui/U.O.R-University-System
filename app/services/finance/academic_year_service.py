"""Service de gestion de l'année académique et périodes d'examens"""
import logging
from datetime import datetime, date
from typing import Optional, List
from core.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class AcademicYearService:
    """Service pour configurer les seuils et périodes d'examens"""

    def __init__(self):
        self.db = DatabaseConnection()

    def get_active_year(self) -> Optional[dict]:
        """Retourne l'année académique active"""
        try:
            query = "SELECT * FROM academic_year WHERE is_active = 1 ORDER BY start_date DESC LIMIT 1"
            rows = self.db.execute_query(query)
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting active academic year: {e}")
            return None

    def create_year(self, name: str, start_date: date, end_date: date,
                    threshold_amount: float, final_fee: float, partial_valid_days: int) -> bool:
        """Crée une nouvelle année académique et l'active"""
        try:
            self.db.execute_update("UPDATE academic_year SET is_active = 0 WHERE is_active = 1")
            query = """
                INSERT INTO academic_year (name, start_date, end_date, threshold_amount, final_fee, partial_valid_days, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_update(query, (
                name, start_date, end_date, threshold_amount, final_fee, partial_valid_days, 1
            ))
            return True
        except Exception as e:
            logger.error(f"Error creating academic year: {e}")
            return False

    def add_exam_period(self, academic_year_id: int, name: str, start_date: date, end_date: date) -> bool:
        """Ajoute une période d'examen"""
        try:
            query = """
                INSERT INTO exam_period (academic_year_id, name, start_date, end_date, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """
            self.db.execute_update(query, (academic_year_id, name, start_date, end_date))
            return True
        except Exception as e:
            logger.error(f"Error adding exam period: {e}")
            return False

    def get_exam_periods(self, academic_year_id: int) -> List[dict]:
        """Liste des périodes d'examen"""
        try:
            query = """
                SELECT * FROM exam_period
                WHERE academic_year_id = %s AND is_active = 1
                ORDER BY start_date ASC
            """
            return self.db.execute_query(query, (academic_year_id,))
        except Exception as e:
            logger.error(f"Error getting exam periods: {e}")
            return []

    def is_within_exam_period(self, academic_year_id: int, when: Optional[datetime] = None) -> bool:
        """Vérifie si la date courante est dans une période d'examen"""
        try:
            when = when or datetime.now()
            query = """
                SELECT COUNT(*) as cnt
                FROM exam_period
                WHERE academic_year_id = %s
                  AND is_active = 1
                  AND %s BETWEEN start_date AND end_date
            """
            rows = self.db.execute_query(query, (academic_year_id, when))
            return bool(rows and rows[0].get("cnt"))
        except Exception as e:
            logger.error(f"Error checking exam period: {e}")
            return False
