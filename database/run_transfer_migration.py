"""Script pour exécuter la migration du système de transfert"""
import mysql.connector
from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Exécute le script de migration SQL"""
    try:
        # Connexion à la base de données
        print("Connexion à la base de données...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # À ajuster selon votre configuration
            database="uor_university"
        )
        
        cursor = conn.cursor()
        
        # Lire le fichier SQL
        migration_file = Path(__file__).parent / "migrations" / "add_transfer_system.sql"
        print(f"Lecture du fichier de migration: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Séparer les commandes SQL par `;` et exécuter
        # Ignorer les commentaires et les lignes vides
        commands = sql_script.split(';')
        
        executed = 0
        skipped = 0
        
        for i, command in enumerate(commands, 1):
            command = command.strip()
            
            # Passer les commentaires et les lignes vides
            if not command or command.startswith('--') or command.startswith('#'):
                skipped += 1
                continue
            
            # Ignorer "COMMIT" s'il est seul
            if command.lower() == 'commit':
                try:
                    cursor.execute(command)
                    conn.commit()
                    executed += 1
                except Exception as e:
                    if "no transaction" not in str(e).lower():
                        print(f"  ⚠ Erreur sur COMMIT: {e}")
                continue
            
            try:
                # Ajouter le `;` si manquant
                if not command.endswith(';'):
                    command += ';'
                
                print(f"  ⏳ Exécution commande {i}...", end='')
                cursor.execute(command)
                print(f" ✓")
                executed += 1
            except mysql.connector.Error as e:
                # Ignorer les erreurs "table already exists"
                if "already exists" in str(e).lower():
                    print(f" ℹ️ (existe déjà)")
                    executed += 1
                else:
                    print(f" ✗")
                    print(f"    Erreur: {e}")
                    raise
        
        conn.commit()
        print(f"\n✅ Migration exécutée avec succès!")
        print(f"   Commandes exécutées: {executed}")
        print(f"   Lignes ignorées: {skipped}")
        print("\nTables créées:")
        print("  - academic_record (notes académiques)")
        print("  - student_document (documents et ouvrages)")
        print("  - transfer_history (historique des transferts)")
        print("  - transfer_request (demandes en attente)")
        print("  - partner_university (universités partenaires)")
        print("\nVues créées:")
        print("  - student_academic_profile")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
