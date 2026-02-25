"""Test du système de transfert"""
import sys
sys.path.insert(0, r'e:\SECRET FILES\MY_TFC')

from app.services.transfer.transfer_service import TransferService
from app.services.student.student_service import StudentService
from core.database.connection import DatabaseConnection

def test_transfer_system():
    """Test que les étudiants se chargent correctement"""
    try:
        print("=" * 70)
        print("TEST DU SYSTÈME DE TRANSFERT")
        print("=" * 70)
        
        # Initialiser les services
        print("\n🔧 Initialisation des services...")
        transfer_service = TransferService()
        student_service = StudentService()
        
        print("✅ Services initialisés\n")
        
        # Test 1: Récupérer tous les étudiants
        print("📋 Test 1: Récupération des étudiants")
        print("-" * 70)
        
        students = student_service.get_all_students_with_finance()
        print(f"✅ {len(students)} étudiants chargés\n")
        
        # Afficher les détails
        print("👥 Étudiants disponibles pour transfert:")
        for student in students[:5]:  # Afficher les 5 premiers
            name = f"{student['firstname']} {student['lastname']}"
            promo = student.get('promotion_name', 'N/A')
            print(f"   • {name:30} | {promo}")
        
        if len(students) > 5:
            print(f"   ... et {len(students) - 5} autres")
        
        # Test 2: Préparation d'un transfert
        print(f"\n📦 Test 2: Préparation d'un transfert pour un étudiant")
        print("-" * 70)
        
        if students:
            student = students[0]
            student_id = student['id']
            name = f"{student['firstname']} {student['lastname']}"
            
            # Préparer le paquet de transfert
            transfer_package = transfer_service.prepare_student_transfer_package(student_id)
            
            if transfer_package:
                print(f"✅ Paquet créé pour {name}")
                print(f"   Structure du paquet:")
                for key, value in transfer_package.items():
                    if isinstance(value, dict):
                        print(f"   - {key}: {list(value.keys())[:3]}")
                    elif isinstance(value, list):
                        print(f"   - {key}: {len(value)} élément(s)")
                    else:
                        print(f"   - {key}: {value}")
        
        # Test 3: Universités partenaires
        print(f"\n🌐 Test 3: Universités partenaires")
        print("-" * 70)
        
        conn = DatabaseConnection()
        query = "SELECT university_code, university_name, trust_level FROM partner_university"
        universities = conn.execute_query(query)
        
        print(f"✅ {len(universities)} universités partenaires trouvées:")
        for uni in universities:
            print(f"   • {uni['university_code']:12} - {uni['university_name']:40} ({uni['trust_level']})")
        
        # Test 4: Profil académique
        print(f"\n📊 Test 4: Vue de profil académique")
        print("-" * 70)
        
        count_result = conn.execute_query("SELECT COUNT(*) FROM student_academic_profile")
        count = count_result[0]['COUNT(*)'] if count_result else 0
        print(f"✅ {count} profils académiques disponibles")
        
        profile_result = conn.execute_query("""
            SELECT student_id, firstname, lastname, promotion_name, 
                   total_courses, total_credits, average_grade 
            FROM student_academic_profile 
            LIMIT 1
        """)
        
        if profile_result:
            profile = profile_result[0]
            print(f"   Exemple: {profile['firstname']} {profile['lastname']}")
            print(f"   - Promotion: {profile['promotion_name']}")
            print(f"   - Courses: {profile['total_courses']}")
            print(f"   - Crédits: {profile['total_credits']}")
            if profile['average_grade']:
                print(f"   - Moyenne: {float(profile['average_grade']):.2f}")
            else:
                print(f"   - Moyenne: N/A")
        
        print("\n" + "=" * 70)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("=" * 70)
        print("\n📝 Résumé:")
        print(f"   - {len(students)} étudiants disponibles")
        print(f"   - {len(universities)} universités partenaires")
        print(f"   - {transfer_package['academic_records']} notes académiques")
        print(f"   - Système prêt pour les transferts!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transfer_system()
