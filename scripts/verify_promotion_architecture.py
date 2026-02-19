"""
Script de vérification de l'architecture basée sur les promotions

Ce script vérifie que:
1. La colonne threshold_amount existe dans la table promotion
2. Les promotions ont des valeurs configurées
3. Les étudiants sont correctement liés à leurs promotions
4. Les calculs financiers utilisent bien les promotions

Usage:
    python scripts/verify_promotion_architecture.py
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection


class ArchitectureVerifier:
    def __init__(self):
        self.db = DatabaseConnection()
        self.errors = []
        self.warnings = []
        
    def verify_schema(self):
        """Vérifie que la colonne threshold_amount existe"""
        print("\n1️⃣ Vérification du schéma de la base de données...")
        
        query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'promotion' 
            AND TABLE_SCHEMA = 'uor_university'
            AND COLUMN_NAME = 'threshold_amount'
        """
        
        result = self.db.execute_query(query)
        
        if result and len(result) > 0:
            print("   ✅ La colonne 'threshold_amount' existe dans la table 'promotion'")
            return True
        else:
            print("   ❌ La colonne 'threshold_amount' n'existe PAS dans la table 'promotion'")
            self.errors.append("Migration SQL non exécutée - Exécuter: database/migrations/add_promotion_threshold.sql")
            return False
    
    def verify_promotions_configured(self):
        """Vérifie que les promotions ont des frais configurés"""
        print("\n2️⃣ Vérification de la configuration des promotions...")
        
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN fee_usd > 0 AND threshold_amount > 0 THEN 1 ELSE 0 END) as configured,
                SUM(CASE WHEN fee_usd = 0 OR threshold_amount = 0 THEN 1 ELSE 0 END) as unconfigured
            FROM promotion
            WHERE is_active = 1
        """
        
        result = self.db.execute_query(query)
        
        if result and len(result) > 0:
            total = result[0]['total']
            configured = result[0]['configured']
            unconfigured = result[0]['unconfigured']
            
            print(f"   📊 Total promotions actives: {total}")
            print(f"   ✅ Promotions configurées (fee + seuil): {configured}")
            print(f"   ⚠️  Promotions non configurées: {unconfigured}")
            
            if unconfigured > 0:
                self.warnings.append(f"{unconfigured} promotion(s) sans frais/seuil configurés")
                print("\n   💡 Pour configurer: python scripts/configure_promotions.py")
            
            return unconfigured == 0
        
        return False
    
    def verify_student_links(self):
        """Vérifie que les étudiants sont liés à des promotions"""
        print("\n3️⃣ Vérification des liens étudiants → promotions...")
        
        query = """
            SELECT 
                COUNT(*) as total_students,
                SUM(CASE WHEN s.promotion_id IS NOT NULL THEN 1 ELSE 0 END) as with_promotion,
                SUM(CASE WHEN s.promotion_id IS NULL THEN 1 ELSE 0 END) as without_promotion
            FROM student s
            WHERE s.is_active = 1
        """
        
        result = self.db.execute_query(query)
        
        if result and len(result) > 0:
            total = result[0]['total_students']
            with_promo = result[0]['with_promotion']
            without_promo = result[0]['without_promotion']
            
            print(f"   📊 Total étudiants actifs: {total}")
            print(f"   ✅ Avec promotion: {with_promo}")
            print(f"   ❌ Sans promotion: {without_promo}")
            
            if without_promo > 0:
                self.errors.append(f"{without_promo} étudiant(s) sans promotion assignée")
            
            return without_promo == 0
        
        return True
    
    def verify_promotion_data(self):
        """Affiche les promotions et leurs frais"""
        print("\n4️⃣ État détaillé des promotions...")
        
        query = """
            SELECT 
                f.name AS faculty,
                d.name AS department,
                p.name AS promotion,
                p.year,
                p.fee_usd,
                p.threshold_amount,
                COUNT(s.id) AS student_count
            FROM promotion p
            JOIN department d ON p.department_id = d.id
            JOIN faculty f ON d.faculty_id = f.id
            LEFT JOIN student s ON s.promotion_id = p.id AND s.is_active = 1
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY f.name, d.name, p.year
        """
        
        results = self.db.execute_query(query)
        
        if results:
            current_faculty = None
            for row in results:
                faculty = row['faculty']
                dept = row['department']
                promo = row['promotion']
                year = row['year']
                fee = float(row['fee_usd'] or 0)
                threshold = float(row['threshold_amount'] or 0)
                students = row['student_count']
                
                if faculty != current_faculty:
                    print(f"\n   🏛️ {faculty}")
                    current_faculty = faculty
                
                status = "✅" if fee > 0 and threshold > 0 else "⚠️"
                print(f"      {status} {dept} / {promo} ({year})")
                print(f"         Frais: ${fee:,.2f} | Seuil: ${threshold:,.2f} | Étudiants: {students}")
        else:
            print("   ❌ Aucune promotion active trouvée")
            self.errors.append("Aucune promotion active dans la base de données")
    
    def verify_finance_service_usage(self):
        """Vérifie un échantillon de calculs financiers"""
        print("\n5️⃣ Vérification des calculs financiers...")
        
        # Récupérer un étudiant avec paiement pour tester
        query = """
            SELECT 
                s.id,
                s.firstname,
                s.lastname,
                p.name AS promotion,
                p.fee_usd,
                p.threshold_amount,
                fp.amount_paid,
                fp.is_eligible
            FROM student s
            JOIN promotion p ON s.promotion_id = p.id
            LEFT JOIN finance_profile fp ON fp.student_id = s.id
            WHERE s.is_active = 1
            AND p.fee_usd > 0
            LIMIT 1
        """
        
        result = self.db.execute_query(query)
        
        if result and len(result) > 0:
            student = result[0]
            name = f"{student['firstname']} {student['lastname']}"
            promo = student['promotion']
            fee = Decimal(str(student['fee_usd'] or 0))
            threshold = Decimal(str(student['threshold_amount'] or 0))
            paid = Decimal(str(student['amount_paid'] or 0))
            eligible = student['is_eligible']
            
            print(f"\n   👤 Étudiant test: {name}")
            print(f"      Promotion: {promo}")
            print(f"      Frais promotion: ${fee}")
            print(f"      Seuil promotion: ${threshold}")
            print(f"      Montant payé: ${paid}")
            print(f"      Éligible: {'✅ Oui' if eligible else '❌ Non'}")
            
            # Vérifier la logique
            should_be_eligible = paid >= threshold if threshold > 0 else False
            
            if eligible == should_be_eligible:
                print("      ✅ Logique de calcul correcte")
            else:
                print("      ⚠️ Incohérence dans le calcul d'éligibilité")
                self.warnings.append("Incohérence d'éligibilité détectée - vérifier finance_service.py")
        else:
            print("   ⚠️ Aucun étudiant avec promotion configurée trouvé pour le test")
    
    def generate_report(self):
        """Génère le rapport final"""
        print("\n" + "="*80)
        print("RAPPORT DE VÉRIFICATION")
        print("="*80)
        
        if not self.errors and not self.warnings:
            print("\n✅ ✅ ✅ TOUT EST PARFAIT! ✅ ✅ ✅")
            print("\nL'architecture basée sur les promotions est correctement configurée.")
            print("Le système est prêt à être utilisé!")
        else:
            if self.errors:
                print("\n❌ ERREURS DÉTECTÉES:")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
            
            if self.warnings:
                print("\n⚠️  AVERTISSEMENTS:")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
            
            print("\n💡 ACTIONS RECOMMANDÉES:")
            if self.errors:
                print("   1. Résoudre les erreurs listées ci-dessus")
                print("   2. Exécuter la migration SQL si nécessaire")
                print("   3. Configurer les promotions via: python scripts/configure_promotions.py")
        
        print("\n" + "="*80 + "\n")
    
    def run_all_checks(self):
        """Exécute toutes les vérifications"""
        print("\n" + "="*80)
        print("VÉRIFICATION DE L'ARCHITECTURE BASÉE SUR LES PROMOTIONS")
        print("="*80)
        
        self.verify_schema()
        self.verify_promotions_configured()
        self.verify_student_links()
        self.verify_promotion_data()
        self.verify_finance_service_usage()
        self.generate_report()


if __name__ == "__main__":
    verifier = ArchitectureVerifier()
    verifier.run_all_checks()
