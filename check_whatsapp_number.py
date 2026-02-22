"""Vérifier quel numéro WhatsApp est connecté à l'instance Ultramsg"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
TOKEN = os.getenv("ULTRAMSG_TOKEN")

if not INSTANCE_ID or not TOKEN:
    raise SystemExit(
        "ULTRAMSG_INSTANCE_ID/ULTRAMSG_TOKEN manquants. "
        "Renseignez-les dans votre .env (non versionné)."
    )

print("=" * 60)
print("VÉRIFICATION DU COMPTE WHATSAPP CONNECTÉ")
print("=" * 60)

# Vérifier le statut détaillé
status_url = f"https://api.ultramsg.com/{INSTANCE_ID}/instance/status"
status_params = {"token": TOKEN}

response = requests.get(status_url, params=status_params)
if response.status_code == 200:
    data = response.json()
    print("📱 Informations de l'instance:")
    print(f"   {data}")
    
    status_info = data.get("status", {})
    account_status = status_info.get("accountStatus", {})
    
    print(f"\n✅ Statut: {account_status.get('status')}")
    print(f"✅ Sous-statut: {account_status.get('substatus')}")

# Essayer d'obtenir les informations du compte
me_url = f"https://api.ultramsg.com/{INSTANCE_ID}/instance/me"
me_params = {"token": TOKEN}

print("\n📞 Tentative de récupération du numéro connecté...")
me_response = requests.get(me_url, params=me_params)
if me_response.status_code == 200:
    me_data = me_response.json()
    print(f"Réponse: {me_data}")
    if "phone" in me_data or "number" in me_data or "jid" in me_data:
        print(f"\n✅ Numéro WhatsApp connecté: {me_data}")
else:
    print(f"Status: {me_response.status_code}")
    print(f"Réponse: {me_response.text}")

print("\n" + "=" * 60)
print("⚠️ SOLUTION:")
print("=" * 60)
print("1. Allez sur: https://ultramsg.com/panel")
print("2. Connectez-vous à votre compte")
print("3. Sélectionnez l'instance: instance_xxxxx")
print("4. Vérifiez quel numéro WhatsApp est connecté")
print("5. Si ce n'est pas le bon, déconnectez et scannez à nouveau")
print("   le QR code avec le WhatsApp de +243845046384")
print("=" * 60)
