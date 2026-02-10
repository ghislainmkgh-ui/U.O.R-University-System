"""
Script pour ajouter les données de la Faculté des Sciences de l'Ingénieur (FSI)
Exécute la migration SQL pour ajouter FSI, G.I, G.C et les promotions associées
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Exécute la migration pour ajouter FSI"""
    migration_file = Path(__file__).parent / "migrations" / "add_fsi_faculty_data.sql"
    
    if not migration_file.exists():
        logger.error(f"Fichier de migration introuvable: {migration_file}")
        return False
    
    try:
        db = DatabaseConnection()
        
        # Lire le fichier SQL
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Séparer les commandes SQL
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        logger.info("Début de la migration FSI...")
        
        for statement in statements:
            if statement:
                try:
                    if statement.upper().startswith('SELECT'):
                        results = db.execute_query(statement)
                        if results:
                            logger.info(f"Résultats: {results}")
                    else:
                        db.execute_update(statement)
                        logger.info(f"Commande exécutée avec succès")
                except Exception as e:
                    logger.warning(f"Avertissement lors de l'exécution: {e}")
        
        logger.info("✅ Migration FSI terminée avec succès!")
        logger.info("Faculté 'Sciences de l'Ingénieur (FSI)' ajoutée")
        logger.info("Départements 'Génie Informatique (G.I)' et 'Génie Civil (G.C)' ajoutés")
        logger.info("Promotions 'L3-LMD/G.I' et 'L2-LMD/G.I' ajoutées")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
