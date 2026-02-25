"""Script pour vérifier l'état de la base de données"""
import mysql.connector

def verify_database():
    """Vérifie les tables et l'état de la base de données"""
    try:
        print("=" * 60)
        print("VÉRIFICATION DE LA BASE DE DONNÉES")
        print("=" * 60)
        
        # Connexion à la base de données
        print("\n🔗 Connexion à la base de données...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="uor_university"
        )
        print("✅ Connecté à uor_university")
        
        cursor = conn.cursor()
        
        # Vérifier les tables du système de transfert
        print("\n📋 Vérification des tables du système de transfert:")
        print("-" * 60)
        
        tables_to_check = [
            'academic_record',
            'student_document',
            'transfer_history',
            'transfer_request',
            'partner_university'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table:25} | {count:4} enregistrements")
            except mysql.connector.Error as e:
                print(f"❌ {table:25} | N'existe pas")
        
        # Vérifier les vues
        print("\n📊 Vérification des vues:")
        print("-" * 60)
        
        views_to_check = ['student_academic_profile']
        
        for view in views_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                count = cursor.fetchone()[0]
                print(f"✅ {view:25} | {count:4} enregistrements")
            except mysql.connector.Error as e:
                print(f"❌ {view:25} | N'existe pas")
        
        # Vérifier les tables existantes relatives aux étudiants
        print("\n📚 Tables existantes (base des étudiants):")
        print("-" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM student")
        print(f"✅ student              | {cursor.fetchone()[0]} enregistrements")
        
        cursor.execute("SELECT COUNT(*) FROM faculty")
        print(f"✅ faculty              | {cursor.fetchone()[0]} enregistrements")
        
        cursor.execute("SELECT COUNT(*) FROM department")
        print(f"✅ department           | {cursor.fetchone()[0]} enregistrements")
        
        cursor.execute("SELECT COUNT(*) FROM promotion")
        print(f"✅ promotion            | {cursor.fetchone()[0]} enregistrements")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Vérification terminée")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_database()
