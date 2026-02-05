"""
Test Script - Notification System
Verify Email and WhatsApp notifications work correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.integration.notification_service import NotificationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_email_notification():
    """Test email notification"""
    print("\n" + "="*60)
    print("TEST 1: Email Notification")
    print("="*60)
    
    service = NotificationService()
    
    # Test data
    student_email = input("Enter test email address: ").strip()
    if not student_email:
        print("❌ No email provided. Skipping test.")
        return False
    
    # Send test access code notification
    result = service.send_access_code_notification(
        student_email=student_email,
        student_phone=None,  # Skip WhatsApp
        student_name="Test Student",
        access_code="123456",
        code_type="full",
        expires_at="2025-09-15"
    )
    
    if result:
        print("✅ Email sent successfully!")
        print(f"   Check inbox: {student_email}")
        return True
    else:
        print("❌ Email failed to send. Check logs and credentials.")
        return False


def test_whatsapp_notification():
    """Test WhatsApp notification"""
    print("\n" + "="*60)
    print("TEST 2: WhatsApp Notification")
    print("="*60)
    
    service = NotificationService()
    
    # Check if WhatsApp is configured
    if not service.whatsapp_sid or not service.whatsapp_token:
        print("⚠️  WhatsApp not configured in config/settings.py")
        print("   Add WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN, WHATSAPP_FROM")
        return False
    
    # Test data
    student_phone = input("Enter test phone number (format: +243XXXXXXXXX): ").strip()
    if not student_phone:
        print("❌ No phone number provided. Skipping test.")
        return False
    
    # Validate format
    if not student_phone.startswith('+'):
        print("❌ Phone number must start with + (example: +243123456789)")
        return False
    
    # Send test access code notification
    result = service.send_access_code_notification(
        student_email=None,  # Skip email
        student_phone=student_phone,
        student_name="Test Student",
        access_code="123456",
        code_type="full",
        expires_at="2025-09-15"
    )
    
    if result:
        print("✅ WhatsApp sent successfully!")
        print(f"   Check WhatsApp: {student_phone}")
        return True
    else:
        print("❌ WhatsApp failed to send. Check logs, credentials, and Twilio sandbox.")
        return False


def test_threshold_change_notification():
    """Test threshold change notification (dual channel)"""
    print("\n" + "="*60)
    print("TEST 3: Threshold Change Notification (Email + WhatsApp)")
    print("="*60)
    
    service = NotificationService()
    
    student_email = input("Enter test email address: ").strip()
    student_phone = input("Enter test phone number (or leave empty): ").strip()
    
    if not student_email and not student_phone:
        print("❌ At least one contact method required. Skipping test.")
        return False
    
    # Validate phone format if provided
    if student_phone and not student_phone.startswith('+'):
        print("⚠️  Phone number should start with + (example: +243123456789)")
        student_phone = None
    
    # Send test threshold change notification
    result = service.send_threshold_change_notification(
        student_email=student_email or None,
        student_phone=student_phone or None,
        student_name="Test Student",
        old_threshold=100000.00,
        new_threshold=150000.00
    )
    
    if result:
        print("✅ Threshold change notification sent!")
        if student_email:
            print(f"   Email: {student_email}")
        if student_phone:
            print(f"   WhatsApp: {student_phone}")
        return True
    else:
        print("❌ Notification failed to send. Check logs.")
        return False


def test_configuration():
    """Test notification service configuration"""
    print("\n" + "="*60)
    print("CONFIGURATION CHECK")
    print("="*60)
    
    service = NotificationService()
    
    # Email config
    print("\n[EMAIL]")
    if service.email_address and service.email_password:
        print(f"✅ Email configured: {service.email_address}")
    else:
        print("❌ Email not configured in config/settings.py")
        print("   Required: EMAIL_ADDRESS, EMAIL_PASSWORD")
    
    # WhatsApp config
    print("\n[WHATSAPP]")
    if service.whatsapp_sid and service.whatsapp_token and service.whatsapp_from:
        print(f"✅ WhatsApp configured")
        print(f"   Account SID: {service.whatsapp_sid[:10]}...")
        print(f"   From: {service.whatsapp_from}")
    else:
        print("⚠️  WhatsApp not configured")
        print("   Optional: WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN, WHATSAPP_FROM")
    
    # Twilio library
    print("\n[DEPENDENCIES]")
    try:
        import twilio
        print(f"✅ Twilio library installed (v{twilio.__version__})")
    except ImportError:
        print("❌ Twilio library not installed")
        print("   Install with: pip install twilio")


def main():
    """Run notification tests"""
    print("\n" + "="*60)
    print("NOTIFICATION SYSTEM TEST SUITE")
    print("="*60)
    print("\nThis script tests the multi-channel notification system.")
    print("Make sure you have configured:")
    print("  - Email credentials (Gmail)")
    print("  - WhatsApp credentials (Twilio)")
    print("\nPress Ctrl+C to cancel at any time.")
    print("="*60)
    
    # Configuration check
    test_configuration()
    
    # Menu
    while True:
        print("\n" + "="*60)
        print("TEST MENU")
        print("="*60)
        print("1. Test Email Notification")
        print("2. Test WhatsApp Notification")
        print("3. Test Threshold Change (Email + WhatsApp)")
        print("4. Re-check Configuration")
        print("5. Exit")
        print("="*60)
        
        choice = input("Select test (1-5): ").strip()
        
        if choice == '1':
            test_email_notification()
        elif choice == '2':
            test_whatsapp_notification()
        elif choice == '3':
            test_threshold_change_notification()
        elif choice == '4':
            test_configuration()
        elif choice == '5':
            print("\nExiting test suite. Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("For production deployment:")
    print("1. Ensure both email and WhatsApp are configured")
    print("2. Test with real student data")
    print("3. Monitor logs/application.log for errors")
    print("4. Set up Twilio production credentials (not sandbox)")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user. Goodbye!")
    except Exception as e:
        logger.error(f"Test suite error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        print("Check logs for details.")
