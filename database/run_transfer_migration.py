"""Script pour exécuter la migration du système de transfert"""
import mysql.connector
from pathlib import Path
import sys

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
        
        # Séparer les commandes SQL
        commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        # Exécuter chaque commande
        print(f"Exécution de {len(commands)} commandes SQL...")
        for i, command in enumerate(commands, 1):
            if command and not command.isspace():
                try:
                    # Skip les commentaires
                    if command.strip().startswith('#') or command.strip().startswith('--'):
                        continue
                    
                    cursor.execute(command)
                    print(f"  ✓ Commande {i}/{len(commands)} exécutée")
                except mysql.connector.Error as e:
                    # Ignorer les erreurs "table already exists"
                    if "already exists" in str(e).lower():
                        print(f"  ⚠ Commande {i}: Table existe déjà (ignoré)")
                    else:
                        print(f"  ✗ Erreur commande {i}: {e}")
                        raise
        
        conn.commit()
        print("\n✅ Migration exécutée avec succès!")
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
