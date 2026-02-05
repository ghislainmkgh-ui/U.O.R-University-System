"""Service de gestion des finances"""
import logging
import random
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
from core.database.connection import DatabaseConnection
from app.services.finance.academic_year_service import AcademicYearService
from app.services.integration.notification_service import NotificationService
from app.services.auth.authentication_service import AuthenticationService

logger = logging.getLogger(__name__)


class FinanceService:
    """Service pour gérer les paiements et seuils financiers"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.academic_service = AcademicYearService()
        self.notification_service = NotificationService()
        self.auth_service = AuthenticationService()
    
    def get_student_finance(self, student_id: int) -> Optional[dict]:
        """Récupère le profil financier d'un étudiant"""
        try:
            query = "SELECT * FROM finance_profile WHERE student_id = %s"
            results = self.db.execute_query(query, (student_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting finance profile: {e}")
            return None

    def create_finance_profile(self, student_id: int, threshold_required: Decimal = None) -> bool:
        """Crée un profil financier initial pour un étudiant"""
        try:
            active_year = self.academic_service.get_active_year()
            if active_year:
                threshold_amount = Decimal(str(active_year.get('threshold_amount') or 0))
                final_fee = Decimal(str(active_year.get('final_fee') or 0))
                academic_year_id = active_year.get('id')
            else:
                threshold_amount = Decimal(str(threshold_required or 0))
                final_fee = Decimal(str(threshold_required or 0))
                academic_year_id = None

            query = """
                INSERT INTO finance_profile (
                    student_id,
                    amount_paid,
                    threshold_required,
                    final_fee,
                    academic_year_id,
                    is_eligible,
                    last_payment_date,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            now = datetime.now()
            params = (
                student_id,
                "0",
                str(threshold_amount),
                str(final_fee),
                academic_year_id,
                0,
                None,
                now,
                now
            )
            self.db.execute_update(query, params)
            logger.info(f"Finance profile created for student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating finance profile: {e}")
            return False
    
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
            threshold = Decimal(str(finance.get('threshold_required') or 0))
            final_fee = Decimal(str(finance.get('final_fee') or threshold))

            is_eligible = 1 if new_amount >= threshold else 0
            now = datetime.now()

            query = """
                UPDATE finance_profile 
                SET amount_paid = %s, last_payment_date = %s, is_eligible = %s, updated_at = %s
                WHERE student_id = %s
            """
            params = (str(new_amount), now, is_eligible, now, student_id)
            self.db.execute_update(query, params)

            if is_eligible:
                is_full_paid = new_amount >= final_fee
                self._issue_access_code_if_needed(student_id, is_full_paid)

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
                FROM student s
                JOIN finance_profile f ON s.id = f.student_id
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
                FROM student s
                JOIN finance_profile f ON s.id = f.student_id
                WHERE f.amount_paid < f.threshold_required AND s.is_active = 1
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting non-eligible students: {e}")
            return []

    def is_access_code_valid(self, student_id: int) -> bool:
        """Vérifie la validité du mot de passe d'accès"""
        try:
            finance = self.get_student_finance(student_id)
            if not finance:
                return False

            expires_at = finance.get('access_code_expires_at')
            access_type = finance.get('access_code_type')
            academic_year_id = finance.get('academic_year_id')

            if expires_at and isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)

            if expires_at and datetime.now() > expires_at:
                return False

            if access_type == 'full' and academic_year_id:
                if not self.academic_service.is_within_exam_period(academic_year_id):
                    return False

            return True
        except Exception as e:
            logger.error(f"Error checking access code validity: {e}")
            return False

    def update_financial_thresholds(self, academic_year_id: int, threshold_amount: Decimal,
                                   final_fee: Decimal, partial_valid_days: int) -> bool:
        """Met à jour le seuil et invalide les accès partiels"""
        try:
            now = datetime.now()
            query_year = """
                UPDATE academic_year
                SET threshold_amount = %s, final_fee = %s, partial_valid_days = %s, updated_at = %s
                WHERE id = %s
            """
            self.db.execute_update(query_year, (str(threshold_amount), str(final_fee), partial_valid_days, now, academic_year_id))

            query_fp = """
                UPDATE finance_profile
                SET threshold_required = %s, final_fee = %s, updated_at = %s
                WHERE academic_year_id = %s
            """
            self.db.execute_update(query_fp, (str(threshold_amount), str(final_fee), now, academic_year_id))

            self._invalidate_partial_access_codes(academic_year_id)
            self._notify_threshold_change(academic_year_id, threshold_amount, final_fee)

            logger.info("Financial thresholds updated and partial codes invalidated")
            return True
        except Exception as e:
            logger.error(f"Error updating thresholds: {e}")
            return False

    def _issue_access_code_if_needed(self, student_id: int, is_full_paid: bool) -> None:
        """Génère et délivre un nouveau mot de passe si éligible"""
        try:
            finance = self.get_student_finance(student_id)
            if not finance:
                return

            academic_year_id = finance.get('academic_year_id')
            access_type = 'full' if is_full_paid else 'partial'

            active_year = self.academic_service.get_active_year()
            if not active_year:
                return

            if access_type == 'full':
                expires_at = active_year.get('end_date')
            else:
                days = int(active_year.get('partial_valid_days') or 30)
                expires_at = datetime.now() + timedelta(days=days)

            access_code = self._generate_access_code()
            password_hash = self.auth_service.password_hasher.hash_password(access_code)

            self.db.execute_update(
                "UPDATE student SET password_hash = %s WHERE id = %s",
                (password_hash, student_id)
            )

            query = """
                UPDATE finance_profile
                SET access_code_issued_at = %s, access_code_expires_at = %s, access_code_type = %s, updated_at = %s
                WHERE student_id = %s
            """
            now = datetime.now()
            self.db.execute_update(query, (now, expires_at, access_type, now, student_id))

            student_row = self.db.execute_query("SELECT * FROM student WHERE id = %s", (student_id,))
            if student_row:
                student = student_row[0]
                self.notification_service.send_access_code_notification(
                    student_email=student.get('email'),
                    student_phone=student.get('phone_number'),
                    student_name=f"{student.get('firstname')} {student.get('lastname')}",
                    access_code=access_code,
                    expires_at=expires_at,
                    access_type=access_type
                )
        except Exception as e:
            logger.error(f"Error issuing access code: {e}")

    def _invalidate_partial_access_codes(self, academic_year_id: int) -> None:
        """Expire tous les accès partiels après changement de seuil"""
        try:
            now = datetime.now()
            query = """
                UPDATE finance_profile
                SET access_code_expires_at = %s, updated_at = %s
                WHERE academic_year_id = %s AND access_code_type = 'partial'
            """
            self.db.execute_update(query, (now, now, academic_year_id))
        except Exception as e:
            logger.error(f"Error invalidating partial access codes: {e}")

    def _notify_threshold_change(self, academic_year_id: int, threshold_amount: Decimal, final_fee: Decimal) -> None:
        """Notifie les étudiants du changement de seuil"""
        try:
            query = """
                SELECT s.email, s.phone_number, s.firstname, s.lastname
                FROM student s
                JOIN finance_profile f ON s.id = f.student_id
                WHERE f.academic_year_id = %s AND s.is_active = 1
            """
            students = self.db.execute_query(query, (academic_year_id,))
            for s in students:
                self.notification_service.send_threshold_change_notification(
                    student_email=s.get('email'),
                    student_phone=s.get('phone_number'),
                    student_name=f"{s.get('firstname')} {s.get('lastname')}",
                    threshold=float(threshold_amount),
                    final_fee=float(final_fee)
                )
        except Exception as e:
            logger.error(f"Error notifying threshold change: {e}")

    def _generate_access_code(self) -> str:
        """Génère un mot de passe numérique (6 chiffres)"""
        return f"{random.randint(0, 999999):06d}"
