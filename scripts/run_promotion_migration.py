"""
Script d'exécution de la migration pour ajouter threshold_amount à promotion

Ce script exécute automatiquement la migration SQL en utilisant les connexions
configurées dans le système.
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
from config.logger import logger


def execute_migration():
    """Exécute la migration SQL pour ajouter threshold_amount à promotion"""
    
    print("\n" + "="*80)
    print("MIGRATION: Ajout de threshold_amount à la table promotion")
    print("="*80 + "\n")
    
    db = DatabaseConnection()
    
    try:
        # 1. Vérifier si la colonne existe déjà
        print("🔍 Vérification de l'état actuel...")
        check_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'promotion' 
            AND TABLE_SCHEMA = 'uor_university'
            AND COLUMN_NAME = 'threshold_amount'
        """
        result = db.execute_query(check_query)
        
        if result and len(result) > 0:
            print("⚠️  La colonne 'threshold_amount' existe déjà!")
            print("✅ Migration déjà appliquée. Rien à faire.\n")
            return True
        
        print("✓ La colonne n'existe pas encore. Exécution de la migration...\n")
        
        # 2. Ajouter threshold_amount et description
        print("📝 Étape 1/3: Ajout des colonnes threshold_amount et description...")
        alter_query_1 = """
            ALTER TABLE promotion 
            ADD COLUMN threshold_amount DECIMAL(10, 2) DEFAULT 0.00 AFTER fee_usd,
            ADD COLUMN description TEXT AFTER year
        """
        db.execute_update(alter_query_1)
        print("   ✅ Colonnes ajoutées avec succès")
        
        # 3. Modifier fee_usd pour ajouter un commentaire
        print("\n📝 Étape 2/3: Ajout du commentaire sur fee_usd...")
        alter_query_2 = """
            ALTER TABLE promotion 
            MODIFY COLUMN fee_usd DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Frais académiques finaux de la promotion'
        """
        db.execute_update(alter_query_2)
        print("   ✅ Commentaire ajouté")
        
        # 4. Ajouter un commentaire sur threshold_amount
        print("\n📝 Étape 3/3: Ajout du commentaire sur threshold_amount...")
        alter_query_3 = """
            ALTER TABLE promotion 
            MODIFY COLUMN threshold_amount DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Seuil minimum requis pour éligibilité'
        """
        db.execute_update(alter_query_3)
        print("   ✅ Commentaire ajouté")
        
        # 5. Vérification finale
        print("\n🔍 Vérification de la structure des promotions...")
        verify_query = """
            SELECT 
                p.name AS promotion_name,
                p.year,
                d.name AS department_name,
                f.name AS faculty_name,
                p.fee_usd AS frais_finaux,
                p.threshold_amount AS seuil,
                p.is_active
            FROM promotion p
            JOIN department d ON p.department_id = d.id
            JOIN faculty f ON d.faculty_id = f.id
            ORDER BY f.name, d.name, p.year
            LIMIT 5
        """
        results = db.execute_query(verify_query)
        
        if results:
            print("\n📊 Aperçu des promotions (5 premières):")
            print("-" * 100)
            print(f"{'Promotion':<25} {'Année':<8} {'Département':<25} {'Frais':<12} {'Seuil':<12} {'Active':<8}")
            print("-" * 100)
            for row in results:
                promo = row['promotion_name'][:24]
                year = str(row['year'])
                dept = row['department_name'][:24]
                fee = f"${row['frais_finaux']:,.2f}"
                seuil = f"${row['seuil']:,.2f}"
                active = "✅" if row['is_active'] else "❌"
                print(f"{promo:<25} {year:<8} {dept:<25} {fee:<12} {seuil:<12} {active:<8}")
            print("-" * 100)
        
        print("\n" + "="*80)
        print("✅ ✅ ✅ MIGRATION RÉUSSIE! ✅ ✅ ✅")
        print("="*80)
        print("\n💡 Prochaines étapes:")
        print("   1. Configurer les frais/seuils: python scripts/configure_promotions.py")
        print("   2. Vérifier l'installation: python scripts/verify_promotion_architecture.py")
        print("   3. Lancer l'application: python main.py\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la migration: {e}")
        logger.error(f"Migration error: {e}")
        print("\n💡 Si la colonne existe déjà, c'est normal (migration déjà appliquée).")
        print("   Vous pouvez vérifier avec: python scripts/verify_promotion_architecture.py\n")
        return False


if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)
