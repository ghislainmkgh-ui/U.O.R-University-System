"""Script robuste pour exécuter la migration"""
import mysql.connector
from pathlib import Path
import re

def run_migration():
    """Exécute la migration SQL de manière robuste"""
    try:
        print("=" * 70)
        print("MIGRATION DU SYSTÈME DE TRANSFERT")
        print("=" * 70)
        
        # Connexion à la base de données
        print("\n🔗 Connexion à la base de données...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="uor_university"
        )
        print("✅ Connecté à uor_university\n")
        
        cursor = conn.cursor()
        
        # Lire le fichier SQL
        migration_file = Path(__file__).parent / "migrations" / "add_transfer_system.sql"
        print(f"📄 Lecture du fichier: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Séparer les commandes par `;`
        raw_commands = sql_content.split(';')
        
        # Nettoyer et filtrer les commandes
        commands = []
        for cmd in raw_commands:
            # Supprimer les espaces au début et fin
            cmd = cmd.strip()
            
            # Ignorer les lignes vides et commentaires
            if not cmd:
                continue
            
            # Supprimer les commentaires en début de ligne
            lines = cmd.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Ignorer les commentaires et lignes vides
                if line and not line.startswith('--') and not line.startswith('#'):
                    cleaned_lines.append(line)
            
            if cleaned_lines:
                cleaned_cmd = ' '.join(cleaned_lines)
                commands.append(cleaned_cmd)
        
        print(f"📋 {len(commands)} commandes SQL trouvées\n")
        
        # Exécuter chaque commande
        executed = 0
        skipped = 0
        errors = []
        
        print("⏳ Exécution des commandes:\n")
        
        for i, command in enumerate(commands, 1):
            # Ajouter le `;` si manquant
            if not command.endswith(';'):
                command += ';'
            
            # Extraire le type de commande
            cmd_type = command.split()[0].upper()
            
            # Afficher le type de commande
            status = f"[{i:2d}/{len(commands)}] {cmd_type:10}"
            
            try:
                cursor.execute(command)
                print(f"  ✅ {status} - Succès")
                executed += 1
                
            except mysql.connector.Error as e:
                error_msg = str(e).lower()
                
                # Ignorer les erreurs courantes et non critiques
                if "already exists" in error_msg:
                    print(f"  ⚠️  {status} - Existe déjà (ignoré)")
                    executed += 1
                    skipped += 1
                elif "no transaction" in error_msg:
                    print(f"  ⚠️  {status} - Aucune transaction (ignoré)")
                    skipped += 1
                else:
                    print(f"  ❌ {status} - ERREUR")
                    print(f"     {e}")
                    errors.append((i, command, str(e)))
        
        # Valider la transaction
        try:
            conn.commit()
            print(f"\n✅ Transaction validée\n")
        except Exception as e:
            print(f"\n❌ Erreur lors de la validation: {e}\n")
            errors.append(("COMMIT", "", str(e)))
        
        # Résumé
        print("=" * 70)
        print("RÉSUMÉ DE LA MIGRATION")
        print("=" * 70)
        print(f"✅ Commandes exécutées: {executed}")
        print(f"⚠️  Avertissements: {skipped}")
        print(f"❌ Erreurs critiques: {len(errors)}")
        
        if errors:
            print("\n⚠️  ERREURS DÉTECTÉES:")
            for idx, cmd, msg in errors:
                print(f"\n  Commande {idx}:")
                print(f"  {cmd[:100]}...")
                print(f"  Erreur: {msg}")
        
        # Vérifier les tables créées
        print("\n📋 Vérification des tables créées:")
        print("-" * 70)
        
        tables = ['academic_record', 'student_document', 'transfer_history', 
                 'transfer_request', 'partner_university']
        
        all_created = True
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}")
            except:
                print(f"  ❌ {table}")
                all_created = False
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        if all_created and len(errors) == 0:
            print("✅ MIGRATION COMPLÉTÉE AVEC SUCCÈS!")
        else:
            print("⚠️  MIGRATION INCOMPLÈTE - Vérifier les erreurs ci-dessus")
        print("=" * 70)
        
        return all_created and len(errors) == 0
        
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_migration()
    sys.exit(0 if success else 1)
