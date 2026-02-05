"""
Migration Helper Script
Run this after applying the SQL migration to set up initial data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.finance.academic_year_service import AcademicYearService
from app.services.student.student_service import StudentService
from app.services.finance.finance_service import FinanceService
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_default_academic_year():
    """Create the default academic year with exam periods"""
    academic_service = AcademicYearService()
    
    # Check if academic year already exists
    active_year = academic_service.get_active_year()
    if active_year:
        logger.info(f"Active academic year already exists: {active_year['year_name']}")
        return active_year['academic_year_id']
    
    # Create new academic year
    current_year = datetime.now().year
    year_name = f"{current_year}-{current_year + 1}"
    
    year_id = academic_service.create_year(
        year_name=year_name,
        threshold_amount=100000.00,  # 100,000 FC threshold
        final_fee=200000.00,         # 200,000 FC full fee
        partial_valid_days=30        # 30 days validity for partial payments
    )
    
    if year_id:
        logger.info(f"Created academic year: {year_name} (ID: {year_id})")
        
        # Add exam periods
        exam_periods = [
            {
                "name": "Session 1 - Janvier 2025",
                "start": datetime(2025, 1, 15),
                "end": datetime(2025, 1, 31)
            },
            {
                "name": "Session 2 - Juin 2025",
                "start": datetime(2025, 6, 1),
                "end": datetime(2025, 6, 30)
            },
            {
                "name": "Session 3 - Septembre 2025",
                "start": datetime(2025, 9, 1),
                "end": datetime(2025, 9, 15)
            }
        ]
        
        for period in exam_periods:
            academic_service.add_exam_period(
                academic_year_id=year_id,
                period_name=period["name"],
                start_date=period["start"],
                end_date=period["end"]
            )
            logger.info(f"Added exam period: {period['name']}")
        
        return year_id
    else:
        logger.error("Failed to create academic year")
        return None


def update_existing_finance_profiles(academic_year_id):
    """Link existing finance profiles to the academic year"""
    finance_service = FinanceService()
    
    logger.info("Updating existing finance profiles with academic year...")
    
    # This would require a direct database update
    from core.database.connection import DatabaseConnection
    db = DatabaseConnection()
    connection = db.get_connection()
    cursor = connection.cursor()
    
    try:
        # Update all finance_profiles without academic_year_id
        cursor.execute("""
            UPDATE finance_profile 
            SET academic_year_id = %s 
            WHERE academic_year_id IS NULL
        """, (academic_year_id,))
        
        affected = cursor.rowcount
        connection.commit()
        logger.info(f"Updated {affected} finance profiles with academic year ID {academic_year_id}")
        
    except Exception as e:
        logger.error(f"Error updating finance profiles: {e}")
        connection.rollback()
    finally:
        cursor.close()
        db.return_connection(connection)


def regenerate_access_codes():
    """Regenerate access codes for eligible students"""
    logger.info("Regenerating access codes for eligible students...")
    
    from core.database.connection import DatabaseConnection
    db = DatabaseConnection()
    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Find all eligible students without access codes
        cursor.execute("""
            SELECT s.student_id, s.firstname, s.lastname, s.email, s.phone_number,
                   fp.finance_id, fp.amount_paid, fp.threshold_required, fp.final_fee
            FROM student s
            JOIN finance_profile fp ON s.student_id = fp.student_id
            WHERE fp.is_eligible = TRUE 
              AND (fp.access_code IS NULL OR fp.access_code = '')
        """)
        
        eligible_students = cursor.fetchall()
        logger.info(f"Found {len(eligible_students)} eligible students without access codes")
        
        finance_service = FinanceService()
        
        for student in eligible_students:
            try:
                # Use the internal method to issue access code
                finance_service._issue_access_code_if_needed(
                    student_id=student['student_id'],
                    finance_id=student['finance_id'],
                    amount_paid=student['amount_paid'],
                    threshold_required=student['threshold_required'],
                    final_fee=student.get('final_fee'),
                    student_email=student['email'],
                    student_phone=student.get('phone_number'),
                    student_name=f"{student['firstname']} {student['lastname']}"
                )
                logger.info(f"Issued access code for: {student['firstname']} {student['lastname']}")
                
            except Exception as e:
                logger.error(f"Failed to issue code for student {student['student_id']}: {e}")
        
    except Exception as e:
        logger.error(f"Error regenerating access codes: {e}")
    finally:
        cursor.close()
        db.return_connection(connection)


def display_migration_status():
    """Display current migration status"""
    logger.info("\n" + "="*60)
    logger.info("MIGRATION STATUS")
    logger.info("="*60)
    
    from core.database.connection import DatabaseConnection
    db = DatabaseConnection()
    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Check tables existence
        cursor.execute("SHOW TABLES LIKE 'academic_year'")
        if cursor.fetchone():
            logger.info("✓ academic_year table exists")
        else:
            logger.warning("✗ academic_year table missing")
        
        cursor.execute("SHOW TABLES LIKE 'exam_period'")
        if cursor.fetchone():
            logger.info("✓ exam_period table exists")
        else:
            logger.warning("✗ exam_period table missing")
        
        cursor.execute("SHOW TABLES LIKE 'student_face_encoding'")
        if cursor.fetchone():
            logger.info("✓ student_face_encoding table exists")
        else:
            logger.warning("✗ student_face_encoding table missing")
        
        # Check new columns
        cursor.execute("SHOW COLUMNS FROM student LIKE 'phone_number'")
        if cursor.fetchone():
            logger.info("✓ student.phone_number column exists")
        else:
            logger.warning("✗ student.phone_number column missing")
        
        cursor.execute("SHOW COLUMNS FROM finance_profile LIKE 'access_code_type'")
        if cursor.fetchone():
            logger.info("✓ finance_profile.access_code_type column exists")
        else:
            logger.warning("✗ finance_profile.access_code_type column missing")
        
        # Count academic years
        cursor.execute("SELECT COUNT(*) as count FROM academic_year")
        result = cursor.fetchone()
        logger.info(f"\nAcademic years: {result['count']}")
        
        # Count exam periods
        cursor.execute("SELECT COUNT(*) as count FROM exam_period")
        result = cursor.fetchone()
        logger.info(f"Exam periods: {result['count']}")
        
        # Count students with access codes
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN access_code IS NOT NULL THEN 1 ELSE 0 END) as with_code,
                SUM(CASE WHEN access_code_type = 'full' THEN 1 ELSE 0 END) as full_codes,
                SUM(CASE WHEN access_code_type = 'partial' THEN 1 ELSE 0 END) as partial_codes
            FROM finance_profile
        """)
        result = cursor.fetchone()
        logger.info(f"\nFinance profiles:")
        logger.info(f"  Total: {result['total']}")
        logger.info(f"  With access codes: {result['with_code']}")
        logger.info(f"  Full access codes: {result['full_codes']}")
        logger.info(f"  Partial access codes: {result['partial_codes']}")
        
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
    finally:
        cursor.close()
        db.return_connection(connection)
    
    logger.info("="*60 + "\n")


def main():
    """Main migration helper"""
    print("\n" + "="*60)
    print("MIGRATION HELPER - Access Management Features")
    print("="*60 + "\n")
    
    print("This script will:")
    print("1. Check migration status")
    print("2. Create default academic year (2024-2025)")
    print("3. Add exam periods (3 sessions)")
    print("4. Link existing finance profiles to academic year")
    print("5. Regenerate access codes for eligible students")
    print("\nMake sure you have run the SQL migration first!")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    # Step 1: Check status
    display_migration_status()
    
    # Step 2: Create academic year
    print("\n[1/4] Creating academic year...")
    academic_year_id = create_default_academic_year()
    
    if not academic_year_id:
        print("Failed to create academic year. Exiting.")
        return
    
    # Step 3: Update existing finance profiles
    print("\n[2/4] Updating existing finance profiles...")
    update_existing_finance_profiles(academic_year_id)
    
    # Step 4: Regenerate access codes
    print("\n[3/4] Regenerating access codes...")
    regenerate_access_codes()
    
    # Step 5: Display final status
    print("\n[4/4] Final status check...")
    display_migration_status()
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Install Twilio: pip install twilio")
    print("2. Configure WHATSAPP_* settings in config/settings.py")
    print("3. Update student phone numbers in the database")
    print("4. Test notification system")
    print("5. Implement multi-face enrollment UI")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
