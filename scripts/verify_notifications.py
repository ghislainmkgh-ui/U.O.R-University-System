"""Vérification rapide: Toutes les méthodes de notification existent"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.integration.notification_service import NotificationService

def verify():
    service = NotificationService()
    
    print("=" * 60)
    print("✅ VÉRIFICATION DES NOTIFICATIONS U.O.R")
    print("=" * 60)
    
    methods = [
        'send_payment_notification',
        'send_access_denied_notification',
        'send_access_code_notification',
        'send_threshold_change_notification',
        'send_welcome_notification',  # NOUVELLE!
        '_send_email',
        '_send_whatsapp',
        '_build_payment_email_html',
        'get_channel_status'
    ]
    
    print("\n📋 Méthodes disponibles:")
    for method in methods:
        exists = hasattr(service, method)
        status = "✅" if exists else "❌"
        print(f"  {status} {method}")
    
    print("\n📊 Configuration:")
    print(f"  Email: {service.email_address or '❌ NON CONFIGURÉ'}")
    print(f"  Email Password: {'✅ Configuré' if service.email_password else '❌ NON CONFIGURÉ'}")
    print(f"  Twilio SID: {service.whatsapp_sid[:10] + '...' if service.whatsapp_sid else '❌ NON CONFIGURÉ'}")
    print(f"  Twilio Token: {'✅ Configuré' if service.whatsapp_token else '❌ NON CONFIGURÉ'}")
    
    status = service.get_channel_status()
    print("\n🔌 Statut des canaux:")
    print(f"  Email: {'✅ OPÉRATIONNEL' if status['email_configured'] else '❌ Non configuré'}")
    print(f"  WhatsApp: {'⚠️  Configuré (token possiblement invalide)' if status['whatsapp_configured'] else '❌ Non configuré'}")
    
    print("\n" + "=" * 60)
    print("✅ Vérification terminée!")
    print("=" * 60)
    
    if not status['email_configured']:
        print("\n⚠️  WARNING: Email non configuré - Ajoutez EMAIL_ADDRESS et EMAIL_PASSWORD dans .env")
    else:
        print("\n✅ Email configuré - Les notifications seront envoyées")
    
    if not status['whatsapp_configured']:
        print("ℹ️  INFO: WhatsApp non configuré (optionnel)")
    else:
        print("⚠️  WhatsApp configuré mais peut nécessiter correction du token")

if __name__ == "__main__":
    verify()
