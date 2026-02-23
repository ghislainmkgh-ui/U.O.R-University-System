# Payment & WhatsApp Notifications - Diagnostic Guide

## Summary of Changes

### 1. Payment Validation
✅ **FIXED**: Payments are now rejected when a promotion has no academic fees defined (final_fee ≤ 0)

**Three-layer validation**:
- UI Level: `admin_dashboard.py` - Immediate user feedback
- Service Level: `finance_service.py` - Backend safety net
- Message: "Aucun frais académique n'est défini pour cette promotion..."

**Expected Behavior**:
```
User tries to pay for student in promotion with $0 fees
↓
UI check triggers: final_fee <= 0 detected
↓
Error dialog shown: "Aucun frais académique..."
↓
Service layer also checks: payment never reaches database
```

### 2. WhatsApp Notification Diagnostics
⚠️ **DIAGNOSED**: Comprehensive logging added to trace failure points

**New Logging Points** (in order of execution):
1. **App Startup** (`notification_service.py` `__init__`):
   ```
   "NotificationService initialized - Email: True/False, Ultramsg: True/False"
   "Ultramsg not fully configured - Instance: True/False, Token: True/False"
   ```

2. **Before Payment** (`enter_payment_dialog`):
   ```
   "Payment notification call initiated for student_id: X"
   ```

3. **Async Thread Start** (`finance_service.py` `_notify_async`):
   ```
   "Starting async notification for student X"
   ```

4. **Notification Service Entry** (`notification_service.py` `send_payment_notification`):
   ```
   "Sending payment notification to email@example.com / +237XX123456"
   ```

5. **Email Send** (`notification_service.py` `_send_email`):
   ```
   "Email notification result: True/False"
   ```

6. **WhatsApp Send** (`notification_service.py` `_send_whatsapp`):
   ```
   "Sending WhatsApp - Original: +237XX123456, Normalized: +237XX123456, Instance: instance_id_here"
   "Ultramsg API response: {'sent': 'true'/'false', 'error': '...', ...}"
   ```

7. **Final Result** (`finance_service.py` `_notify_async`):
   ```
   "Notification sent successfully for student X"
   OR
   "Notification failed for student X - Email: email@example.com, Phone: +237XX123456"
   ```

---

## Troubleshooting Checklist

### ❌ Problem: WhatsApp Not Arriving

**Step 1: Check Ultramsg Configuration**

Look for this log line at app startup:
```
NotificationService initialized - Email: ..., Ultramsg: True
```

- If you see `Ultramsg: False`, then:
  - Ultramsg credentials are NOT configured
  - Create `.env` file in project root with:
    ```
    ULTRAMSG_INSTANCE_ID=your_instance_id_here
    ULTRAMSG_TOKEN=your_api_token_here
    ```

**Step 2: Verify Phone Number Format**

Look for this log line when sending WhatsApp:
```
Sending WhatsApp - Original: +237691234567, Normalized: +237691234567
```

- Original phone should match database value
- Normalized should start with `+` and contain only digits
- If normalization is different, phone in database might be incorrect format

**Step 3: Check Ultramsg API Response**

Look for this log line:
```
Ultramsg API response: {'sent': 'true', 'result': 'Message queued'}
```

**Possible API responses**:
- ✅ `{'sent': 'true', 'result': '...'}` → Message sent successfully
- ❌ `{'error': 'Invalid phone number', ...}` → Phone format wrong
- ❌ `{'error': 'Unauthorized', ...}` → Token expired or invalid
- ❌ `{'error': 'Instance not found', ...}` → Instance ID wrong
- ❌ `{'error': 'Quota exceeded', ...}` → API quota used up
- ❌ `{'sent': 'false', 'message': '...'}` → Generic failure

**Step 4: Check Network**

Look for this error log:
```
WhatsApp API network error via Ultramsg: RequestException: ...
```

If you see network errors:
- Check internet connectivity
- Check firewall/proxy settings
- Verify Ultramsg API domain is not blocked: `api.ultramsg.com`

---

## Test Plan

### Test 1: Payment Validation (No Fees)

```
1. Create a new promotion with fee_usd = 0 and threshold_amount = 0
2. Create/select a student in that promotion
3. Try to record a payment ($50)
4. Expected: Error dialog appears - "Aucun frais académique..."
5. Expected logs:
   - "Payment rejected... No active academic fees (final_fee=0)"
   - No payment record created in database
```

### Test 2: Payment Validation (With Valid Fees)

```
1. Create a promotion with fee_usd = 500 and threshold_amount = 500
2. Create/select a student in that promotion
3. Record payment ($100)
4. Expected: Payment succeeds
5. Expected logs:
   - "Payment recorded for student X"
   - "Sending payment notification to email/ phone"
   - "Email notification result: True"
   - "WhatsApp notification result: True"
```

### Test 3: Overpayment Prevention

```
1. Student has paid $300 of $500 fee (remaining: $200)
2. Try to pay $300
3. Expected: Overpayment error
4. Expected logs:
   - "Payment rejected: Amount $300 exceeds remaining $200"
   - No payment recorded
```

### Test 4: WhatsApp Delivery

```
1. Complete Test 2 (valid payment with fees)
2. Check application logs for:
   - Ultramsg configuration status at startup
   - Phone number normalization
   - API response (sent: true/false)
3. If API response shows 'sent: true' but message doesn't arrive:
   - Issue might be Ultramsg API going to spam/queue
   - Check Ultramsg dashboard to see message status
4. If API response shows error:
   - See "Possible API responses" above to diagnose
```

---

## Log File Locations

Application logs are written to:
```
e:\SECRET FILES\MY_TFC\logs\
```

**To view real-time logs** (Windows PowerShell):
```powershell
# Follow logs as they're written
Get-Content -Path "e:\SECRET FILES\MY_TFC\logs\app.log" -Tail 20 -Wait

# Or search for specific errors
Select-String -Path "e:\SECRET FILES\MY_TFC\logs\*.log" -Pattern "WhatsApp|notification|payment"
```

---

## Common Issues & Fixes

### Issue 1: "Ultramsg WhatsApp service not configured"

**Cause**: `ULTRAMSG_INSTANCE_ID` or `ULTRAMSG_TOKEN` environment variables not set

**Fix**:
1. Create `.env` file in project root:
   ```
   ULTRAMSG_INSTANCE_ID=1234567890abcdef1234567890abcdef
   ULTRAMSG_TOKEN=your_ultramsg_api_token_here
   ```
2. Restart the application
3. Check logs for: `Ultramsg WhatsApp service configured`

### Issue 2: "Invalid phone number"

**Cause**: Phone in database not in international format

**Examples**:
- ❌ `697123456` → ✅ `+237697123456`
- ❌ `00237697123456` → ✅ `+237697123456`
- ❌ `237-697-123-456` → ✅ `+237697123456`

**Fix**:
1. Check phone format in database (should be `+COUNTRYCODEPHONENUMBER`)
2. Format can be corrected in student_dao imports or data entry validation

### Issue 3: "Message queued but not delivered"

**Cause**: Ultramsg API accepted message but WhatsApp delivery slow or failed

**Debug**:
1. Check Ultramsg dashboard for message status
2. Verify phone has WhatsApp installed
3. Verify phone number is correct
4. Check if message goes to spam

### Issue 4: "Payment validation not rejecting $0 fees"

**Cause**: Either cached code or condition not triggering

**Debug**:
1. Check logs for: `"Payment rejected: No active academic fees"`
2. If not found, restart application completely
3. Verify promotion.fee_usd is actually 0 in database
4. Check SQL query result: `SELECT fee_usd FROM promotion WHERE id = X`

---

## Email vs WhatsApp Status

**Test both channels independently**:

```
Looking at logs, you should see:
- Email notification result: True/False
- WhatsApp notification result: True/False

If only Email is True:
  → Email infrastructure working, WhatsApp config issue
  
If only WhatsApp is True:
  → WhatsApp infrastructure working, Email config issue
  
If both False:
  → Async thread might be terminated before completing
  → Check app logs for notification thread errors
```

---

## Next Debugging Steps (If Issues Persist)

### 1. Verify Environment Variables

Windows PowerShell:
```powershell
# Show environment variables
Get-ChildItem Env: | Where-Object {$_.Name -like "ULTRAMSG*" -or $_.Name -like "EMAIL*"}

# Alternatively, check .env file
Get-Content ".env" | Select-String "ULTRAMSG|EMAIL"
```

### 2. Test Ultramsg API Directly

```powershell
# Test Ultramsg API connectivity
$response = Invoke-WebRequest -Uri "https://api.ultramsg.com/instance_id/messages/chat" `
  -Method Post `
  -Body @{
    token = "your_token"
    to = "+237XXXXXXXXX"
    body = "Test message"
  }
Write-Output $response.Content
```

### 3. Check Database Payment Records

```sql
-- Verify payment was recorded
SELECT * FROM paiement WHERE matricule_etudiant = 'XXX' ORDER BY date_paiement DESC;

-- Check if fee_usd is 0
SELECT fee_usd, threshold_amount FROM promotion WHERE id = X;

-- Check if promotion properly linked to student
SELECT p.matricule_etudiant, p.promotion_id, pr.fee_usd 
FROM etudiant p 
JOIN promotion pr ON p.promotion_id = pr.id 
WHERE p.matricule_etudiant = 'XXX';
```

### 4. Enable Debug Mode

In `config/settings.py`, set:
```python
DEBUG = True  # or set DEBUG=True in .env
LOG_LEVEL = "DEBUG"  # Shows all debug logs
```

---

## Expected Log Flow (Success Case)

```
[APP START]
INFO: NotificationService initialized - Email: True, Ultramsg: True

[USER RECORDS PAYMENT]
INFO: Payment notification call initiated for student_id: 12345
INFO: Starting async notification for student 12345
INFO: Sending payment notification to student@email.com / +237691234567
INFO: Email notification result: True
INFO: Sending WhatsApp - Original: +237691234567, Normalized: +237691234567, Instance: abc123def456
INFO: Ultramsg API response: {'sent': 'true', 'result': 'Message queued'}
INFO: Notification sent successfully for student 12345
INFO: Payment notification overall result: True (email: True, whatsapp: True)
```

## Expected Log Flow (Failure: No Fees)

```
[USER TRIES TO RECORD PAYMENT FOR PROMOTION WITH $0 FEES]
INFO: Attempting to record payment for student: 12345
WARNING: Payment rejected for student 12345: No active academic fees (final_fee=0)
[No async thread started, UI shows error, database unchanged]
```

---

## Summary Table

| Check | Success Log | Problem Log |
|-------|-------------|-------------|
| **Init** | `Ultramsg: True` | `Ultramsg: False` |
| **Phone** | `Normalized: +237...` | `Normalized: 237...` (no +) |
| **API** | `'sent': 'true'` | `'sent': 'false'` or error |
| **Payment** | Payment recorded | `Payment rejected...` |
| **Email** | `Email result: True` | `Email result: False` |
| **WhatsApp** | `WhatsApp result: True` | `WhatsApp result: False` |

---

**Last Updated**: After implementing comprehensive logging enhancements
**Status**: Ready for end-to-end testing
