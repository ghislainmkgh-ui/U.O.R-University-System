"""Service de gestion des étudiants"""
import logging
import re
from decimal import Decimal
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
                    s.passport_photo_path,
                    s.passport_photo_blob,
                    s.promotion_id,
                    s.is_active,
                    fp.amount_paid,
                    fp.threshold_required,
                    fp.is_eligible
                FROM student s
                LEFT JOIN finance_profile fp ON fp.student_id = s.id
                WHERE s.is_active = 1
                ORDER BY s.lastname ASC, s.firstname ASC, s.student_number ASC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting students list: {e}")
            return []

    def get_promotions(self) -> List[dict]:
        """Récupère les promotions actives"""
        try:
            query = "SELECT id, name, year, fee_usd FROM promotion WHERE is_active = 1 ORDER BY year DESC, name"
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting promotions: {e}")
            return []

    def get_promotions_with_fees(self) -> List[dict]:
        """Récupère les promotions avec frais académiques"""
        try:
            query = """
                SELECT p.id, p.name, p.year, p.fee_usd, d.name as department_name
                FROM promotion p
                JOIN department d ON p.department_id = d.id
                WHERE p.is_active = 1
                ORDER BY p.year DESC, p.name
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting promotions with fees: {e}")
            return []

    def update_promotion_fee(self, promotion_id: int, fee_usd: Decimal) -> bool:
        """Met à jour les frais académiques d'une promotion"""
        try:
            query = "UPDATE promotion SET fee_usd = %s, updated_at = NOW() WHERE id = %s"
            self.db.execute_update(query, (str(fee_usd), promotion_id))
            logger.info(f"Promotion {promotion_id} fee updated: {fee_usd}")
            return True
        except Exception as e:
            logger.error(f"Error updating promotion fee: {e}")
            return False

    def get_faculties(self) -> List[dict]:
        """Récupère les facultés actives"""
        try:
            query = "SELECT id, name, code FROM faculty WHERE is_active = 1 ORDER BY name"
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting faculties: {e}")
            return []

    def get_departments_by_faculty(self, faculty_id: int) -> List[dict]:
        """Récupère les départements actifs d'une faculté"""
        try:
            query = """
                SELECT id, name, code
                FROM department
                WHERE faculty_id = %s AND is_active = 1
                ORDER BY name
            """
            return self.db.execute_query(query, (faculty_id,))
        except Exception as e:
            logger.error(f"Error getting departments by faculty: {e}")
            return []

    def get_promotions_by_department(self, department_id: int) -> List[dict]:
        """Récupère les promotions actives d'un département"""
        try:
            query = """
                SELECT id, name, year
                FROM promotion
                WHERE department_id = %s AND is_active = 1
                ORDER BY year DESC, name
            """
            return self.db.execute_query(query, (department_id,))
        except Exception as e:
            logger.error(f"Error getting promotions by department: {e}")
            return []

    def _normalize_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value or "").lower().strip())
    
    def _extract_keywords(self, value: str) -> set:
        """Extrait les mots-clés significatifs d'une chaîne"""
        normalized = str(value or "").lower()
        # Remplace les caractères spéciaux par des espaces
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        # Split et filtre les mots courts
        words = {w for w in normalized.split() if len(w) >= 2}
        return words

    def _match_by_normalized(self, items: List[dict], input_value: str, fields: List[str]) -> List[dict]:
        key = self._normalize_key(input_value)
        if not key:
            return []

        matches = []
        
        # 1. Match exact (normalisé)
        for item in items:
            for field in fields:
                if key == self._normalize_key(item.get(field)):
                    matches.append(item)
                    break

        if matches:
            return matches

        # 2. Match partiel (inclusion)
        for item in items:
            for field in fields:
                field_normalized = self._normalize_key(item.get(field))
                if key in field_normalized or field_normalized in key:
                    matches.append(item)
                    break

        if matches:
            return matches

        # 3. Match par mots-clés (au moins 50% des mots en commun)
        input_keywords = self._extract_keywords(input_value)
        if not input_keywords:
            return []
        
        scored_matches = []
        for item in items:
            for field in fields:
                field_keywords = self._extract_keywords(item.get(field))
                if field_keywords:
                    common = input_keywords & field_keywords
                    if common:
                        score = len(common) / max(len(input_keywords), len(field_keywords))
                        if score >= 0.3:  # Au moins 30% de mots en commun
                            scored_matches.append((score, item))
                            break
        
        if scored_matches:
            # Trier par score décroissant
            scored_matches.sort(reverse=True, key=lambda x: x[0])
            return [item for score, item in scored_matches]

        return []

    def find_faculty_by_input(self, input_value: str) -> List[dict]:
        """Recherche une faculté par nom ou code (saisie manuelle)"""
        faculties = self.get_faculties()
        return self._match_by_normalized(faculties, input_value, ["name", "code"])

    def find_department_by_input(self, input_value: str, faculty_id: Optional[int] = None) -> List[dict]:
        """Recherche un département par nom ou code"""
        try:
            if faculty_id:
                departments = self.get_departments_by_faculty(faculty_id)
            else:
                query = """
                    SELECT id, name, code, faculty_id
                    FROM department
                    WHERE is_active = 1
                    ORDER BY name
                """
                departments = self.db.execute_query(query)
            return self._match_by_normalized(departments, input_value, ["name", "code"])
        except Exception as e:
            logger.error(f"Error finding department by input: {e}")
            return []

    def find_promotion_by_input(self, input_value: str, department_id: Optional[int] = None) -> List[dict]:
        """Recherche une promotion par nom et/ou année"""
        try:
            if department_id:
                promotions = self.get_promotions_by_department(department_id)
            else:
                query = """
                    SELECT id, name, year, department_id
                    FROM promotion
                    WHERE is_active = 1
                    ORDER BY year DESC, name
                """
                promotions = self.db.execute_query(query)

            key = self._normalize_key(input_value)
            if not key:
                return []

            matches = []
            
            # 1. Match exact sur nom, nom+année ou variations
            for promo in promotions:
                name = promo.get("name")
                year = promo.get("year")
                if key == self._normalize_key(name):
                    matches.append(promo)
                    continue
                if key == self._normalize_key(f"{name}{year}"):
                    matches.append(promo)
                    continue
                if key == self._normalize_key(f"{name} {year}"):
                    matches.append(promo)
                    continue
                if key == self._normalize_key(f"{name}-{year}"):
                    matches.append(promo)
                    continue

            if matches:
                return matches

            # 2. Match partiel sur nom
            for promo in promotions:
                name = promo.get("name")
                name_normalized = self._normalize_key(name)
                if key in name_normalized or name_normalized in key:
                    matches.append(promo)

            if matches:
                return matches

            # 3. Match par mots-clés
            input_keywords = self._extract_keywords(input_value)
            if not input_keywords:
                return []
            
            scored_matches = []
            for promo in promotions:
                name = promo.get("name")
                year = str(promo.get("year") or "")
                combined = f"{name} {year}"
                field_keywords = self._extract_keywords(combined)
                if field_keywords:
                    common = input_keywords & field_keywords
                    if common:
                        score = len(common) / max(len(input_keywords), len(field_keywords))
                        if score >= 0.3:
                            scored_matches.append((score, promo))
            
            if scored_matches:
                scored_matches.sort(reverse=True, key=lambda x: x[0])
                return [item for score, item in scored_matches]

            return []
        except Exception as e:
            logger.error(f"Error finding promotion by input: {e}")
            return []
