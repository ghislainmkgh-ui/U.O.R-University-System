"""Test de diagnostic pour WhatsApp via Ultramsg"""
import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID", "")
ULTRAMSG_TOKEN = os.getenv("ULTRAMSG_TOKEN", "")

print("=" * 60)
print("DIAGNOSTIC WHATSAPP - ULTRAMSG")
print("=" * 60)
print(f"\nInstance ID: {ULTRAMSG_INSTANCE_ID}")
print(f"Token: {ULTRAMSG_TOKEN[:10]}...{ULTRAMSG_TOKEN[-5:] if len(ULTRAMSG_TOKEN) > 15 else ''}")
print(f"\nInstance configurée: {bool(ULTRAMSG_INSTANCE_ID)}")
print(f"Token configuré: {bool(ULTRAMSG_TOKEN)}")

if not ULTRAMSG_INSTANCE_ID or not ULTRAMSG_TOKEN:
    print("\n❌ ERREUR: Les identifiants Ultramsg ne sont pas configurés dans .env")
    exit(1)

print("\n" + "=" * 60)
print("TEST 1: Vérifier l'état de l'instance")
print("=" * 60)

try:
    # Test de l'instance
    status_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/instance/status"
    status_params = {"token": ULTRAMSG_TOKEN}
    
    response = requests.get(status_url, params=status_params, timeout=10)
    print(f"\nStatut HTTP: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse API: {result}")
        
        account_status = result.get("accountStatus", "unknown")
        print(f"\nStatut du compte: {account_status}")
        
        if account_status == "authenticated":
            print("✅ Instance WhatsApp ACTIVE et CONNECTÉE")
        elif account_status == "unauthenticated":
            print("❌ Instance WhatsApp NON CONNECTÉE")
            print("\n🔧 SOLUTION:")
            print("1. Allez sur https://api.ultramsg.com/")
            print("2. Connectez-vous avec votre compte")
            print(f"3. Cliquez sur votre instance ({ULTRAMSG_INSTANCE_ID})")
            print("4. Scannez le QR code avec WhatsApp")
            print("5. Attendez que le statut devienne 'authenticated'")
        else:
            print(f"⚠️  Statut inconnu: {account_status}")
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")
        print(f"Réponse: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur de connexion: {e}")
    exit(1)

print("\n" + "=" * 60)
print("TEST 2: Envoi d'un message de test")
print("=" * 60)

test_number = input("\nEntrez le numéro WhatsApp de test (ex: +243123456789): ").strip()

if not test_number:
    print("❌ Aucun numéro fourni. Test annulé.")
    exit(1)

# Normaliser le numéro
if not test_number.startswith("+"):
    test_number = "+" + test_number

print(f"\nEnvoi à: {test_number}")

try:
    send_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": test_number,
        "body": "🔔 Message de test - U.O.R\n\nSi vous recevez ce message, WhatsApp fonctionne correctement!"
    }
    
    response = requests.post(send_url, data=payload, timeout=10)
    print(f"\nStatut HTTP: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Réponse API: {result}")
        
        if result.get("sent") == "true" or result.get("sent") == True:
            print("\n✅ MESSAGE ENVOYÉ AVEC SUCCÈS!")
            print("Vérifiez WhatsApp pour confirmer la réception.")
        else:
            print("\n❌ L'envoi a échoué")
            print(f"Raison: {result.get('error', 'Inconnue')}")
            print(f"Message: {result.get('message', 'Aucun détail')}")
            
            # Conseils de dépannage
            print("\n🔧 SOLUTIONS POSSIBLES:")
            print("1. Vérifiez que le numéro est au format international (+243...)")
            print("2. Assurez-vous que le numéro existe sur WhatsApp")
            print("3. Vérifiez que votre instance Ultramsg est active")
            print("4. Vérifiez votre quota de messages sur Ultramsg")
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")
        print(f"Réponse: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur de connexion: {e}")
    exit(1)

print("\n" + "=" * 60)
print("FIN DU DIAGNOSTIC")
print("=" * 60)
