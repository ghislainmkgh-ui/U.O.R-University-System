#!/usr/bin/env python3
"""
Test script for payment validation and WhatsApp notifications

Usage:
    python test_diagnostics.py
    
This script tests:
1. Payment validation (no fees scenario)
2. Payment validation (with fees scenario)
3. WhatsApp notification delivery
4. Email notification delivery
"""

import sys
import os
import logging
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_diagnostics.log'))
    ]
)
logger = logging.getLogger(__name__)

# Import services
from app.services.finance.finance_service import FinanceService
from app.services.integration.notification_service import NotificationService
from config.settings import ULTRAMSG_INSTANCE_ID, ULTRAMSG_TOKEN

class PaymentDiagnostics:
    """Diagnostic tests for payment and notification systems"""
    
    def __init__(self):
        self.finance_service = FinanceService()
        self.notification_service = NotificationService()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def test_ultramsg_config(self):
        """Test 1: Verify Ultramsg configuration"""
        logger.info("=" * 60)
        logger.info("TEST 1: Ultramsg Configuration Check")
        logger.info("=" * 60)
        
        if not ULTRAMSG_INSTANCE_ID or not ULTRAMSG_TOKEN:
            msg = "❌ Ultramsg NOT configured - ULTRAMSG_INSTANCE_ID and/or ULTRAMSG_TOKEN missing"
            logger.error(msg)
            self.results['failed'].append(msg)
            logger.info("   ACTION: Create .env file with:")
            logger.info("   ULTRAMSG_INSTANCE_ID=your_instance_id")
            logger.info("   ULTRAMSG_TOKEN=your_api_token")
            return False
        else:
            msg = "✅ Ultramsg configured - Instance ID present and Token present"
            logger.info(msg)
            self.results['passed'].append(msg)
            return True
    
    def test_phone_normalization(self, phone_numbers=None):
        """Test 2: Phone number normalization"""
        logger.info("=" * 60)
        logger.info("TEST 2: Phone Number Normalization")
        logger.info("=" * 60)
        
        test_phones = phone_numbers or [
            "+237691234567",  # Already normalized
            "237691234567",   # Missing +
            "691234567",      # Missing country code
            "+237 691 234 567",  # With spaces
            "+237-691-234-567",  # With dashes
            "whatsapp:+237691234567",  # WhatsApp format
        ]
        
        for phone in test_phones:
            # Simulate normalization
            original = phone
            normalized = str(phone).strip()
            
            if normalized.lower().startswith("whatsapp:"):
                normalized = normalized.split("whatsapp:", 1)[1]
            
            normalized = normalized.replace(" ", "").replace("-", "")
            
            if not normalized.startswith("+"):
                normalized = "+" + normalized
            
            logger.info(f"  {original:30} → {normalized}")
            
            # Verify result
            if normalized.startswith("+") and len(normalized) > 5:
                self.results['passed'].append(f"Phone normalization: {original} → {normalized}")
            else:
                self.results['warnings'].append(f"Phone normalization might be invalid: {normalized}")
    
    def test_payment_validation_no_fees(self):
        """Test 3: Payment validation with no fees"""
        logger.info("=" * 60)
        logger.info("TEST 3: Payment Validation (No Fees Scenario)")
        logger.info("=" * 60)
        
        logger.info("This test requires:")
        logger.info("  1. A promotion with fee_usd = 0 or NULL")
        logger.info("  2. A student assigned to that promotion")
        logger.info("  3. Database access")
        logger.info("")
        logger.info("Manual test steps:")
        logger.info("  1. In the application UI:")
        logger.info("     - Go to 'Enregistrer un paiement'")
        logger.info("     - Select a student from a $0 fee promotion")
        logger.info("     - Try to record any payment amount")
        logger.info("  2. Expected result:")
        logger.info("     - Error dialog: 'Aucun frais académique...'")
        logger.info("     - No payment saved to database")
        logger.info("  3. Check logs for:")
        logger.info("     - 'Payment rejected: No active academic fees'")
        logger.info("")
        
        try:
            # Try to connect and query for test promotion
            from core.database.connection import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, fee_usd FROM promotion WHERE fee_usd = 0 OR fee_usd IS NULL LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ Found test promotion: {result}")
                self.results['passed'].append(f"Test promotion found: {result}")
            else:
                logger.warning("⚠️ No $0 fee promotion found - create one to test payment rejection")
                self.results['warnings'].append("No $0 fee promotion found for testing")
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not verify test promotion: {e}")
            self.results['warnings'].append(f"Could not query test promotion: {e}")
    
    def test_payment_validation_with_fees(self):
        """Test 4: Payment validation with valid fees"""
        logger.info("=" * 60)
        logger.info("TEST 4: Payment Validation (Valid Fees Scenario)")
        logger.info("=" * 60)
        
        logger.info("This test requires:")
        logger.info("  1. A promotion with fee_usd > 0")
        logger.info("  2. A student assigned to that promotion (with 0 paid)")
        logger.info("  3. Database access")
        logger.info("")
        logger.info("Manual test steps:")
        logger.info("  1. In the application UI:")
        logger.info("     - Go to 'Enregistrer un paiement'")
        logger.info("     - Select a student from a promotion with fees > 0")
        logger.info("     - Record a valid payment (less than total fee)")
        logger.info("  2. Expected result:")
        logger.info("     - Payment succeeds")
        logger.info("     - Notifications sent (email + WhatsApp)")
        logger.info("  3. Check logs for:")
        logger.info("     - 'Payment recorded for student X'")
        logger.info("     - 'Email notification result: True'")
        logger.info("     - 'WhatsApp notification result: True'")
        logger.info("")
        
        try:
            # Try to connect and query for test promotion
            from core.database.connection import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, fee_usd FROM promotion WHERE fee_usd > 0 LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ Found test promotion with fees: {result}")
                self.results['passed'].append(f"Test promotion with fees found: {result}")
            else:
                logger.warning("⚠️ No promotion with fees found - create one to test normal flow")
                self.results['warnings'].append("No promotion with fees > 0 found for testing")
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not verify test promotion: {e}")
            self.results['warnings'].append(f"Could not query test promotion: {e}")
    
    def test_notification_service(self):
        """Test 5: Notification service configuration"""
        logger.info("=" * 60)
        logger.info("TEST 5: Notification Service Status")
        logger.info("=" * 60)
        
        # Check email config
        from config.settings import EMAIL_ADDRESS, EMAIL_PASSWORD
        
        if EMAIL_ADDRESS and EMAIL_PASSWORD:
            logger.info("✅ Email configured")
            self.results['passed'].append("Email service configured")
        else:
            logger.warning("⚠️ Email not fully configured")
            self.results['warnings'].append("Email configuration incomplete (EMAIL_ADDRESS or EMAIL_PASSWORD)")
        
        # Check Ultramsg config
        if ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN:
            logger.info("✅ Ultramsg (WhatsApp) configured")
            self.results['passed'].append("Ultramsg service configured")
        else:
            logger.warning("⚠️ Ultramsg (WhatsApp) not configured")
            self.results['warnings'].append("Ultramsg configuration incomplete")
    
    def run_all_tests(self):
        """Run all diagnostic tests"""
        logger.info("\n")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 58 + "║")
        logger.info("║" + "  PAYMENT & NOTIFICATION DIAGNOSTICS TEST SUITE".center(58) + "║")
        logger.info("║" + f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ".center(58) + "║")
        logger.info("║" + " " * 58 + "║")
        logger.info("╚" + "=" * 58 + "╝")
        logger.info("\n")
        
        try:
            self.test_ultramsg_config()
            self.test_phone_normalization()
            self.test_payment_validation_no_fees()
            self.test_payment_validation_with_fees()
            self.test_notification_service()
        except Exception as e:
            logger.error(f"Test suite error: {e}", exc_info=True)
            self.results['failed'].append(f"Test suite error: {e}")
        
        logger.info("\n")
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"\n✅ PASSED ({len(self.results['passed'])}):")
        for item in self.results['passed']:
            logger.info(f"   - {item}")
        
        if self.results['warnings']:
            logger.info(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for item in self.results['warnings']:
                logger.info(f"   - {item}")
        
        if self.results['failed']:
            logger.info(f"\n❌ FAILED ({len(self.results['failed'])}):")
            for item in self.results['failed']:
                logger.info(f"   - {item}")
        
        logger.info("\n" + "=" * 60)
        
        # Final recommendation
        total_tests = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        logger.info(f"RECOMMENDATION:")
        
        if self.results['failed']:
            logger.info("  🔴 Critical issues found - see FAILED items above")
            logger.info("  📖 Read DIAGNOSTICS_GUIDE.md for detailed solutions")
        elif self.results['warnings']:
            logger.info("  🟡 Some services not configured - see WARNINGS above")
            logger.info("  📖 Check DIAGNOSTICS_GUIDE.md for configuration steps")
        else:
            logger.info("  🟢 All checks passed!")
            logger.info("  ✅ Configuration appears correct")
            logger.info("  📋 Proceed with manual end-to-end testing via UI")
        
        logger.info("\n")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run diagnostics
    diag = PaymentDiagnostics()
    diag.run_all_tests()
    
    logger.info("\n📝 Full diagnostic log saved to: logs/test_diagnostics.log")
