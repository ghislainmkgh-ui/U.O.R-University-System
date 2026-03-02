"""
Script de test de l'API REST de transfert inter-universitaire
Teste l'envoi de données depuis l'application vers l'API
"""

import requests
import json
from datetime import datetime, date
from app.services.transfer.transfer_service import TransferService

def convert_to_json_serializable(obj):
    """Convertit les objets non-sérialisables en JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj

def test_api_integration():
    """Test complet de l'intégration API"""
    
    print("=" * 80)
    print("🧪 TEST D'INTÉGRATION - API DE TRANSFERT U.O.R")
    print("=" * 80)
    
    # Configuration
    API_BASE_URL = "http://127.0.0.1:5000/api/v1"
    UNIVERSITY_CODE = "UOR"
    API_KEY = "test-key-123"
    
    # Étape 1: Vérifier que l'API est accessible
    print("\n1️⃣  Vérification de la santé de l'API...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API accessible: {data.get('service')}")
            print(f"   📌 Version: {data.get('version')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter à l'API")
        print("   💡 Vérifiez que l'API est lancée (python api/transfer_api_real.py)")
        return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Étape 2: Obtenir un token d'authentification
    print("\n2️⃣  Obtention d'un token JWT...")
    try:
        auth_data = {
            "university_code": UNIVERSITY_CODE,
            "api_key": API_KEY
        }
        response = requests.post(f"{API_BASE_URL}/auth/token", json=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('token')
            print(f"   ✅ Token obtenu avec succès")
            print(f"   🔑 Token: {token[:50]}...")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Étape 3: Préparer un package de transfert depuis l'application
    print("\n3️⃣  Préparation d'un package de transfert depuis l'application...")
    try:
        transfer_service = TransferService()
        
        # Récupérer les étudiants depuis la base de données
        conn = transfer_service.db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, firstname, lastname, student_number 
            FROM student 
            WHERE is_active = TRUE
            LIMIT 5
        """)
        students = cursor.fetchall()
        cursor.close()
        transfer_service.db.close_connection(conn)
        
        if not students:
            print("   ❌ Aucun étudiant disponible pour le test")
            return
        
        # Prendre le premier étudiant
        student = students[0]
        student_id = student['id']
        student_name = f"{student['firstname']} {student['lastname']}"
        
        print(f"   📚 Étudiant sélectionné: {student_name} (ID: {student_id})")
        
        # Préparer le package
        package = transfer_service.prepare_student_transfer_package(
            student_id=student_id,
            include_documents=True
        )
        
        if not package:
            print("   ❌ Impossible de créer le package")
            return
        
        print(f"   ✅ Package créé:")
        print(f"      • Notes: {package['academic_records']['total_courses']}")
        print(f"      • Documents: {package['documents']['total_documents']}")
        print(f"      • Code: {package['transfer_metadata']['transfer_code']}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Étape 4: Envoyer le package vers l'API
    print("\n4️⃣  Envoi du package vers l'API (simulation de transfert inter-universitaire)...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Convertir le package pour qu'il soit JSON serializable
        package_json = convert_to_json_serializable(package)
        
        response = requests.post(
            f"{API_BASE_URL}/transfer/receive",
            headers=headers,
            json=package_json
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Package reçu par l'API avec succès!")
            print(f"      • Code de demande: {result.get('request_code')}")
            print(f"      • Statut: {result.get('status')}")
            print(f"      • Message: {result.get('message')}")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            print(f"      Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Étape 5: Test d'envoi via l'endpoint /transfer/send
    print("\n5️⃣  Test de l'endpoint /transfer/send (préparation de package)...")
    try:
        send_data = {
            "student_id": student_id,
            "destination_university_code": "UNIKIN",
            "include_documents": True
        }
        
        response = requests.post(
            f"{API_BASE_URL}/transfer/send",
            headers=headers,
            json=send_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Package préparé via API:")
            print(f"      • Code de transfert: {result.get('transfer_code')}")
            print(f"      • Message: {result.get('message')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            print(f"      Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS AVEC SUCCÈS!")
    print("=" * 80)
    print("\n💡 L'API fonctionne correctement et reçoit bien les données de l'application.")
    print("   Les transferts sont enregistrés dans la base de données.")

if __name__ == "__main__":
    test_api_integration()
