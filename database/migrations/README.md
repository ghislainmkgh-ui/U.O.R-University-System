# Database Migrations - Access Management Features

## Overview
This migration adds comprehensive access management features including:
- Academic year management with financial thresholds
- Exam period tracking
- Automatic password issuance based on payment threshold
- Password validity tracking (full vs partial payments)
- Multi-channel notifications (Email + WhatsApp)
- Multi-face enrollment support

## Files
- `add_access_management_features.sql` - Main SQL migration script
- `migration_helper.py` - Python helper to set up initial data

## Prerequisites
1. MySQL database running
2. Existing database schema (student, finance_profile tables)
3. Python environment with application dependencies installed
4. Database backup (recommended)

## Migration Steps

### Step 1: Backup Database
```bash
mysqldump -u [username] -p [database_name] > backup_before_migration.sql
```

### Step 2: Run SQL Migration
```bash
mysql -u [username] -p [database_name] < add_access_management_features.sql
```

Or using a MySQL client:
```sql
SOURCE /path/to/add_access_management_features.sql;
```

### Step 3: Run Python Migration Helper
```bash
cd database/migrations
python migration_helper.py
```

This helper script will:
- ✅ Create default academic year (2024-2025)
- ✅ Add 3 exam periods (Jan, June, Sept 2025)
- ✅ Link existing finance profiles to academic year
- ✅ Regenerate access codes for eligible students
- ✅ Display migration status

### Step 4: Configure Notification Services

#### Email (Already configured)
Verify in `config/settings.py`:
```python
EMAIL_SERVICE = 'gmail'
EMAIL_ADDRESS = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'
```

#### WhatsApp (New - requires setup)
1. Install Twilio SDK:
```bash
pip install twilio
```

2. Get Twilio credentials:
   - Sign up at https://www.twilio.com/
   - Get Account SID and Auth Token from console
   - Enable WhatsApp sandbox for testing
   - Get WhatsApp-enabled phone number

3. Update `config/settings.py`:
```python
WHATSAPP_ACCOUNT_SID = 'your_account_sid'
WHATSAPP_AUTH_TOKEN = 'your_auth_token'
WHATSAPP_FROM = '+1234567890'  # Your Twilio WhatsApp number
```

### Step 5: Update Student Phone Numbers
Add phone numbers for existing students:
```sql
UPDATE student 
SET phone_number = '+243XXXXXXXXX' 
WHERE student_id = ?;
```

## Database Schema Changes

### New Tables

#### `academic_year`
Manages academic years and financial settings:
- `academic_year_id` (PK)
- `year_name` (e.g., "2024-2025")
- `threshold_amount` - Financial threshold for access
- `final_fee` - Total fee for full year access
- `partial_valid_days` - Days partial payment codes remain valid
- `is_active` - Only one active year at a time

#### `exam_period`
Tracks exam periods within academic years:
- `exam_period_id` (PK)
- `academic_year_id` (FK)
- `period_name` (e.g., "Session 1 - Janvier 2025")
- `start_date`, `end_date`

#### `student_face_encoding`
Stores multiple face encodings per student:
- `encoding_id` (PK)
- `student_id` (FK)
- `face_encoding` (LONGBLOB - numpy array)
- `encoding_order` (1, 2, or 3)

### Modified Tables

#### `student`
- **New**: `phone_number VARCHAR(20)` - For WhatsApp notifications

#### `finance_profile`
- **New**: `academic_year_id INT` - Links to academic year
- **New**: `access_code_issued_at TIMESTAMP` - When code was generated
- **New**: `access_code_expires_at TIMESTAMP` - When code expires
- **New**: `access_code_type ENUM('full', 'partial')` - Code validity type
- **New**: `final_fee DECIMAL(15,2)` - Total fee for this student

## Business Logic

### Password Issuance Rules
1. **Threshold Reached**: When `amount_paid >= threshold_amount`
   - Automatic 6-digit numeric password generated
   - Password hashed and stored in `student.access_code`
   - Notification sent via Email + WhatsApp

2. **Full Payment** (`amount_paid >= final_fee`):
   - `access_code_type = 'full'`
   - Valid throughout all exam periods of the academic year
   - Not affected by threshold changes

3. **Partial Payment** (`threshold_amount <= amount_paid < final_fee`):
   - `access_code_type = 'partial'`
   - Valid for `partial_valid_days` (default: 30 days)
   - **Invalidated immediately** when threshold is updated

### Threshold Update Behavior
When admin updates `academic_year.threshold_amount`:
1. All partial payment codes are invalidated
2. All students are notified via Email + WhatsApp
3. Students must make new payment to get new code
4. Full payment codes remain valid

### Code Validity Check
Access controller checks:
```python
if code_type == 'full':
    # Check if current date is within any exam period
    valid = is_within_exam_period(current_date)
else:  # partial
    # Check if code hasn't expired
    valid = current_datetime < access_code_expires_at
```

## Testing

### Test Academic Year Setup
```python
from app.services.finance.academic_year_service import AcademicYearService

service = AcademicYearService()
year = service.get_active_year()
print(f"Active year: {year['year_name']}")
print(f"Threshold: {year['threshold_amount']}")
```

### Test Password Issuance
```python
from app.services.finance.finance_service import FinanceService

service = FinanceService()
# Make a payment that reaches threshold
service.record_payment(
    student_id=1,
    amount=100000.00,
    payment_method='Cash'
)
# Check if access code was issued automatically
```

### Test Notification
```python
from app.services.integration.notification_service import NotificationService

service = NotificationService()
service.send_access_code_notification(
    student_email='student@example.com',
    student_phone='+243123456789',
    student_name='John Doe',
    access_code='123456',
    code_type='full',
    expires_at='2025-09-15'
)
```

### Test Threshold Update
```python
from app.services.finance.finance_service import FinanceService

service = FinanceService()
service.update_financial_thresholds(
    academic_year_id=1,
    new_threshold=150000.00,
    new_final_fee=250000.00
)
# All partial codes should be invalidated and students notified
```

## Rollback

⚠️ **WARNING**: Rollback will delete all new data (academic years, exam periods, etc.)

To rollback, uncomment and run the rollback script at the end of `add_access_management_features.sql`:
```sql
-- Execute the commented rollback script
```

## Troubleshooting

### Migration Fails: "Table already exists"
Safe to ignore if re-running migration. Script uses `IF NOT EXISTS` clauses.

### "WhatsApp service not configured" warnings
Normal if Twilio credentials not set. Email notifications will still work.

### "Twilio library not installed"
Run: `pip install twilio`

### No access codes generated after migration
Run: `python migration_helper.py` to regenerate codes for eligible students

### Students not notified of threshold change
Check:
1. Email credentials configured in `config/settings.py`
2. Student email addresses valid
3. Student phone numbers populated (for WhatsApp)
4. Application logs for notification errors

## Next Steps

1. **Install Dependencies**:
   ```bash
   pip install twilio
   ```

2. **Configure Services**:
   - Add Twilio credentials to `config/settings.py`
   - Test email delivery
   - Test WhatsApp delivery in Twilio sandbox

3. **Populate Data**:
   - Add phone numbers for all students
   - Create additional exam periods if needed
   - Adjust threshold/final fee amounts

4. **UI Development**:
   - Academic year management page (create years, exam periods)
   - Threshold update interface with notification preview
   - Multi-face enrollment dialog (3 photos per student)
   - Student phone number management

5. **Production Readiness**:
   - Upgrade Twilio from sandbox to production
   - Configure proper error handling and retry logic
   - Set up monitoring for notification delivery
   - Create admin dashboard for access code management

## Support

For issues or questions:
1. Check application logs: `logs/application.log`
2. Verify database schema: `SHOW COLUMNS FROM [table_name]`
3. Test notification services individually
4. Review migration_helper.py output

## Migration History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2025 | Initial access management features |

---

**Author**: System Administrator  
**Last Updated**: 2025
