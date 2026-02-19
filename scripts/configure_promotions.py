#!/usr/bin/env python3
"""
Script de configuration des frais et seuils par promotion

NOUVELLE ARCHITECTURE FINANCIÈRE:
Les frais académiques et seuils sont maintenant définis au niveau des PROMOTIONS
et non plus au niveau des années académiques.

Usage:
    python scripts/configure_promotions.py

Ce script permet de:
1. Visualiser toutes les promotions actuelles avec leurs frais
2. Mettre à jour les frais/seuils d'une promotion spécifique
3. Mettre à jour en masse toutes les promotions d'un département
4. Créer de nouvelles promotions avec frais configurés
"""

import sys
import os
from decimal import Decimal

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
from config.logger import logger


class PromotionConfigurator:
    def __init__(self):
        self.db = DatabaseConnection()
        
    def show_all_promotions(self):
        """Affiche toutes les promotions avec leurs frais et nombre d'étudiants"""
        print("\n" + "="*100)
        print("CONFIGURATION DES PROMOTIONS - FRAIS ACADÉMIQUES ET SEUILS")
        print("="*100)
        
        query = """
            SELECT 
                f.name AS faculty_name,
                d.name AS department_name,
                p.id AS promotion_id,
                p.name AS promotion_name,
                p.year AS promotion_year,
                p.fee_usd,
                p.threshold_amount,
                p.is_active,
                COUNT(s.id) AS student_count
            FROM promotion p
            JOIN department d ON p.department_id = d.id
            JOIN faculty f ON d.faculty_id = f.id
            LEFT JOIN student s ON s.promotion_id = p.id AND s.is_active = 1
            GROUP BY p.id
            ORDER BY f.name, d.name, p.year, p.name
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("\n❌ Aucune promotion trouvée dans la base de données.")
            return
        
        current_faculty = None
        current_dept = None
        
        for row in results:
            faculty = row['faculty_name']
            dept = row['department_name']
            promo = row['promotion_name']
            year = row['promotion_year']
            fee = float(row['fee_usd'] or 0)
            threshold = float(row['threshold_amount'] or 0)
            students = row['student_count']
            is_active = row['is_active']
            
            # Afficher la faculté si elle change
            if faculty != current_faculty:
                print(f"\n📚 FACULTÉ: {faculty}")
                current_faculty = faculty
                current_dept = None
            
            # Afficher le département si il change
            if dept != current_dept:
                print(f"  └── 📂 Département: {dept}")
                current_dept = dept
            
            # Statut
            status = "✅ Active" if is_active else "❌ Inactive"
            
            # Vérifier si les frais sont configurés
            config_status = "⚠️ NON CONFIGURÉ" if fee == 0 or threshold == 0 else "✓"
            
            print(f"      └── {promo} ({year}) - {status} {config_status}")
            print(f"          • Frais finaux: ${fee:,.2f}")
            print(f"          • Seuil requis: ${threshold:,.2f}")
            print(f"          • Étudiants inscrits: {students}")
        
        print("\n" + "="*100 + "\n")
    
    def update_promotion(self, promotion_id: int, fee: Decimal, threshold: Decimal):
        """Met à jour les frais d'une promotion par ID"""
        query = """
            UPDATE promotion 
            SET fee_usd = %s, threshold_amount = %s
            WHERE id = %s
        """
        self.db.execute_update(query, (str(fee), str(threshold), promotion_id))
        logger.info(f"Promotion {promotion_id} mise à jour: Fee=${fee}, Threshold=${threshold}")
        print(f"✅ Promotion mise à jour avec succès!")
    
    def update_by_name(self, promo_name: str, year: int, dept_name: str, fee: Decimal, threshold: Decimal):
        """Met à jour une promotion par nom"""
        query = """
            SELECT p.id 
            FROM promotion p
            JOIN department d ON p.department_id = d.id
            WHERE p.name = %s AND p.year = %s AND d.name = %s
        """
        results = self.db.execute_query(query, (promo_name, year, dept_name))
        
        if not results:
            print(f"❌ Promotion '{promo_name}' ({year}) du département '{dept_name}' non trouvée.")
            return False
        
        promotion_id = results[0]['id']
        self.update_promotion(promotion_id, fee, threshold)
        return True
    
    def update_department_promotions(self, dept_name: str, fee: Decimal, threshold: Decimal):
        """Met à jour toutes les promotions d'un département"""
        query = """
            UPDATE promotion p
            JOIN department d ON p.department_id = d.id
            SET p.fee_usd = %s, p.threshold_amount = %s
            WHERE d.name = %s
        """
        self.db.execute_update(query, (str(fee), str(threshold), dept_name))
        print(f"✅ Toutes les promotions du département '{dept_name}' ont été mises à jour!")
    
    def interactive_mode(self):
        """Mode interactif pour configurer les promotions"""
        while True:
            print("\n" + "="*60)
            print("CONFIGURATION DES PROMOTIONS - MENU INTERACTIF")
            print("="*60)
            print("\n1. Afficher toutes les promotions")
            print("2. Mettre à jour une promotion spécifique")
            print("3. Mettre à jour toutes les promotions d'un département")
            print("4. Configurer rapidement les promotions de Génie Informatique")
            print("5. Quitter")
            
            choice = input("\nChoisissez une option (1-5): ").strip()
            
            if choice == "1":
                self.show_all_promotions()
                
            elif choice == "2":
                promo_name = input("Nom de la promotion (ex: L3-LMD/G.I): ").strip()
                year = int(input("Année (ex: 2025): ").strip())
                dept_name = input("Nom du département (ex: Génie Informatique): ").strip()
                fee = Decimal(input("Frais finaux en USD (ex: 800.00): ").strip())
                threshold = Decimal(input("Seuil requis en USD (ex: 560.00): ").strip())
                
                self.update_by_name(promo_name, year, dept_name, fee, threshold)
                
            elif choice == "3":
                dept_name = input("Nom du département: ").strip()
                fee = Decimal(input("Frais finaux pour toutes les promotions: ").strip())
                threshold = Decimal(input("Seuil requis pour toutes les promotions: ").strip())
                
                confirm = input(f"\n⚠️ Cela va mettre à jour TOUTES les promotions de '{dept_name}'. Confirmer? (oui/non): ").strip().lower()
                if confirm == "oui":
                    self.update_department_promotions(dept_name, fee, threshold)
                else:
                    print("❌ Opération annulée.")
                    
            elif choice == "4":
                # Configuration rapide pour Génie Informatique (exemple)
                print("\nConfiguration rapide pour Génie Informatique:")
                configs = [
                    ("L1-LMD/G.I", 2025, "Génie Informatique", 500, 350),
                    ("L2-LMD/G.I", 2025, "Génie Informatique", 650, 455),
                    ("L3-LMD/G.I", 2025, "Génie Informatique", 800, 560),
                ]
                
                print("\nFrais proposés:")
                for name, year, dept, fee, threshold in configs:
                    print(f"  • {name}: ${fee} (seuil: ${threshold})")
                
                confirm = input("\nAppliquer ces configurations? (oui/non): ").strip().lower()
                if confirm == "oui":
                    for name, year, dept, fee, threshold in configs:
                        self.update_by_name(name, year, dept, Decimal(str(fee)), Decimal(str(threshold)))
                else:
                    print("❌ Opération annulée.")
                    
            elif choice == "5":
                print("\n👋 Au revoir!")
                break
                
            else:
                print("❌ Option invalide. Veuillez choisir 1-5.")


def main():
    """Point d'entrée principal"""
    print("\n🎓 SYSTÈME DE CONFIGURATION DES PROMOTIONS")
    print("   Architecture basée sur les promotions (v2.0)")
    print("   Chaque promotion peut avoir ses propres frais et seuils\n")
    
    configurator = PromotionConfigurator()
    
    # Si des arguments sont passés, mode non-interactif
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            configurator.show_all_promotions()
        else:
            print("Usage: python configure_promotions.py [show]")
    else:
        # Mode interactif
        configurator.interactive_mode()


if __name__ == "__main__":
    main()
