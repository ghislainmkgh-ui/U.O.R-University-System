"""Script pour ajouter des données de test au système"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random

def run_test_data():
    """Ajoute des données de test complètes"""
    try:
        # Connexion
        print("🔗 Connexion à la base de données...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="uor_university"
        )
        cursor = conn.cursor()
        
        # 1. Vérifier/ajouter universités partenaires
        print("\n📍 Vérification des universités partenaires...")
        cursor.execute("SELECT COUNT(*) FROM partner_university WHERE is_active = TRUE")
        partner_count = cursor.fetchone()[0]
        
        if partner_count < 4:
            print("➕ Ajout des universités partenaires...")
            partners = [
                ('Université de Kinshasa', 'UNIKIN', 'RDC', 'Kinshasa', 'VERIFIED'),
                ('Université Protestante au Congo', 'UPC', 'RDC', 'Kinshasa', 'VERIFIED'),
                ('Université Pédagogique Nationale', 'UPN', 'RDC', 'Kinshasa', 'VERIFIED'),
                ('Institut Supérieur de Commerce', 'ISC', 'RDC', 'Kinshasa', 'PENDING'),
                ('Université de Douala', 'UNIDOUALA', 'Cameroun', 'Douala', 'VERIFIED'),
                ('Université de Yaoundé', 'UY1', 'Cameroun', 'Yaoundé', 'VERIFIED'),
            ]
            
            for name, code, country, city, trust in partners:
                cursor.execute("""
                    INSERT IGNORE INTO partner_university 
                    (university_name, university_code, country, city, trust_level, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                """, (name, code, country, city, trust))
            
            conn.commit()
            print(f"✅ {len(partners)} universités partenaires ajoutées")
        
        # 2. Ajouter des étudiants de test
        print("\n👥 Ajout des étudiants de test...")
        
        students_data = [
            {
                'number': 'STU001',
                'firstname': 'Jean',
                'lastname': 'Dupont',
                'email': 'jean.dupont@uor.edu',
                'phone': '+243991234561'
            },
            {
                'number': 'STU002',
                'firstname': 'Marie',
                'lastname': 'Martin',
                'email': 'marie.martin@uor.edu',
                'phone': '+243991234562'
            },
            {
                'number': 'STU003',
                'firstname': 'Pierre',
                'lastname': 'Bernard',
                'email': 'pierre.bernard@uor.edu',
                'phone': '+243991234563'
            },
            {
                'number': 'STU004',
                'firstname': 'Sophie',
                'lastname': 'Garcia',
                'email': 'sophie.garcia@uor.edu',
                'phone': '+243991234564'
            },
            {
                'number': 'STU005',
                'firstname': 'Thomas',
                'lastname': 'Rodriguez',
                'email': 'thomas.rodriguez@uor.edu',
                'phone': '+243991234565'
            },
        ]
        
        # Récupérer les IDs des promotions
        cursor.execute("""
            SELECT id, name, department_id, year
            FROM promotion
            WHERE is_active = TRUE
            LIMIT 5
        """)
        promotions = cursor.fetchall()
        
        if not promotions:
            print("⚠️ Aucune promotion trouvée. Vérifiez la base de données.")
            cursor.close()
            conn.close()
            return False
        
        added_students = []
        for i, student_data in enumerate(students_data):
            promo = promotions[i % len(promotions)]
            promo_id = promo[0]
            
            cursor.execute("""
                INSERT IGNORE INTO student 
                (student_number, firstname, lastname, email, phone_number, promotion_id, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """, (
                student_data['number'],
                student_data['firstname'],
                student_data['lastname'],
                student_data['email'],
                student_data['phone'],
                promo_id,
                '$2b$12$test_password_hash'  # Hash temporaire
            ))
            
            # Récupérer l'ID de l'étudiant
            cursor.execute(f"SELECT id FROM student WHERE student_number = %s", (student_data['number'],))
            student_id_result = cursor.fetchone()
            
            if student_id_result:
                student_id = student_id_result[0]
                added_students.append({
                    'id': student_id,
                    'name': f"{student_data['firstname']} {student_data['lastname']}",
                    'promo_id': promo_id
                })
        
        conn.commit()
        print(f"✅ {len(added_students)} étudiants ajoutés / vérifiés")
        
        # 3. Ajouter des notes académiques pour chaque étudiant
        print("\n📚 Ajout des notes académiques...")
        
        courses = [
            ('Programmation Python', 'PY101', 6),
            ('Algorithmes Avancés', 'ALG201', 6),
            ('Bases de Données', 'DB101', 6),
            ('Mathématiques Discrètes', 'MATH101', 4),
            ('Programmation Web', 'WEB201', 6),
            ('Intelligence Artificielle', 'AI301', 8),
            ('Sécurité Informatique', 'SEC301', 6),
            ('Architecture des Systèmes', 'ARCH201', 4),
        ]
        
        grades = [14.0, 15.5, 16.0, 13.5, 17.0, 15.5, 14.5, 16.5]
        grade_letters = ['B', 'B+', 'A-', 'C+', 'A', 'B+', 'B', 'A-']
        
        records_added = 0
        for student in added_students:
            for j, (course_name, course_code, credits) in enumerate(courses):
                grade = grades[j]
                grade_letter = grade_letters[j]
                
                cursor.execute("""
                    INSERT IGNORE INTO academic_record
                    (student_id, promotion_id, course_name, course_code, credits, grade, grade_letter, semester, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PASSED')
                """, (
                    student['id'],
                    student['promo_id'],
                    course_name,
                    course_code,
                    credits,
                    grade,
                    grade_letter,
                    '1' if j < 4 else '2'
                ))
                records_added += 1
        
        conn.commit()
        print(f"✅ {records_added} notes académiques ajoutées")
        
        # 4. Ajouter des documents pour chaque étudiant
        print("\n📄 Ajout des documents...")
        
        documents = [
            ('CERTIFICATE', 'Certificat de Scolarité 2025-2026', 'Certificat'),
            ('BOOK', 'Introduction à Python 3', 'Livre'),
            ('THESIS', 'Mémoire de Fin d\'Études', 'Mémoire'),
            ('REPORT', 'Rapport de Stage', 'Rapport'),
        ]
        
        docs_added = 0
        for student in added_students:
            for doc_type, title, category in documents:
                cursor.execute("""
                    INSERT IGNORE INTO student_document
                    (student_id, document_type, title, category, status)
                    VALUES (%s, %s, %s, %s, 'ACTIVE')
                """, (
                    student['id'],
                    doc_type,
                    title,
                    category
                ))
                docs_added += 1
        
        conn.commit()
        print(f"✅ {docs_added} documents ajoutés")
        
        # 5. Ajouter des profils financiers
        print("\n💰 Ajout des profils financiers...")
        
        fin_added = 0
        for student in added_students:
            # Récupérer l'academic_year actif
            cursor.execute("SELECT academic_year_id FROM academic_year WHERE is_active = TRUE LIMIT 1")
            year_result = cursor.fetchone()
            year_id = year_result[0] if year_result else None
            
            # Créer un profil financier
            cursor.execute("""
                SELECT fee_usd, threshold_amount FROM promotion WHERE id = %s
            """, (student['promo_id'],))
            promo_fees = cursor.fetchone()
            
            if promo_fees:
                fee_usd, threshold = promo_fees
                # Convertir Decimal en float pour les calculs
                fee_usd = float(fee_usd) if fee_usd else 0
                threshold = float(threshold) if threshold else 0
                amount_paid = random.choice([threshold, threshold * 1.5, fee_usd])
                is_eligible = amount_paid >= threshold
                
                cursor.execute("""
                    INSERT IGNORE INTO finance_profile
                    (student_id, amount_paid, threshold_required, is_eligible, academic_year_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    student['id'],
                    amount_paid,
                    threshold or 0,
                    is_eligible,
                    year_id
                ))
                fin_added += 1
        
        conn.commit()
        print(f"✅ {fin_added} profils financiers créés")
        
        # Afficher un résumé
        print("\n" + "="*60)
        print("✅ DONNÉES DE TEST AJOUTÉES AVEC SUCCÈS")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM student WHERE is_active = TRUE")
        print(f"👥 Total étudiants: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM academic_record")
        print(f"📚 Total notes: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM student_document")
        print(f"📄 Total documents: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM partner_university WHERE is_active = TRUE")
        print(f"🌐 Universités partenaires: {cursor.fetchone()[0]}")
        
        print("\n📌 Étudiants crées/vérifiés:")
        for student in added_students:
            print(f"   - {student['name']} (ID: {student['id']})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"❌ Erreur de base de données: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_test_data()
    sys.exit(0 if success else 1)
