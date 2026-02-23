# ⚡ Quick Troubleshooting Checklist

Use this checklist to quickly diagnose and fix issues after the implementation.

---

## Pre-Testing Setup

- [ ] Did you restart the application after the update?
- [ ] Is there a `.env` file in the project root with Ultramsg credentials?
  - [ ] ULTRAMSG_INSTANCE_ID set (non-empty)?
  - [ ] ULTRAMSG_TOKEN set (non-empty)?
- [ ] Are logs being written to `logs/app.log`?
- [ ] Is the database connection working?

---

## Test 1: Payment Validation (No Fees) ✅

### Setup:
```
Create promotion with:
- fee_usd = 0
- threshold_amount = 0

Create student in that promotion with:
- Email: valid@example.com
- Phone: +237691234567
```

### Test Steps:
1. [ ] Open "Enregistrer un paiement"
2. [ ] Select the $0 fee student
3. [ ] Try to record $50 payment
4. [ ] Get error: "Aucun frais académique..."
5. [ ] Click OK to close error

### Verify:
- [ ] No payment record in database
- [ ] Logs show: `"Payment rejected: No active academic fees"`

### If Failed:
- [ ] Check student is in correct promotion
- [ ] Verify promotion.fee_usd = 0 in database
- [ ] Check logs for: "Payment recorded" (if present, validation not working)

---

## Test 2: Normal Payment (With Fees) ✅

### Setup:
```
Create promotion with:
- fee_usd = $500
- threshold_amount = $500

Create student in that promotion with:
- Email: student@example.com
- Phone: +237XXXXXXXXX (valid format)
- First & Last name configured
```

### Test Steps:
1. [ ] Open "Enregistrer un paiement"
2. [ ] Select the student with valid fees
3. [ ] Record payment of $100
4. [ ] See success confirmation
5. [ ] Payment shows in history

### Verify Logs:
- [ ] Find line: `"Payment recorded for student X"`
- [ ] Find line: `"Starting async notification for student X"`
- [ ] Find line: `"Email notification result: True/False"`
- [ ] Find line: `"Ultramsg API response: {...}"`

### If Failed:
- [ ] Check student email is not empty
- [ ] Check student phone is not empty
- [ ] Verify phone format starts with `+` and country code
- [ ] Check Ultramsg is configured: `Ultramsg: True` in init log

---

## Test 3: WhatsApp Delivery 📱

### If Email Sent But WhatsApp Not Arriving:

1. [ ] Check logs for: `"Ultramsg API response:"`
   
   - If response shows `'sent': 'true'` → ✅ API accepted, check:
     - Phone has WhatsApp installed
     - Message might be in spam/queue
     - Contact Ultramsg support
   
   - If response shows `'error': 'Invalid phone number'` → ❌ Fix:
     - Check phone format in database
     - Should be: `+237XXXXXXXXX` (+ then 12 digits for Cameroon)
     - Don't use: `237...`, `00237...`, `697...`
   
   - If response shows `'error': 'Unauthorized'` → ❌ Fix:
     - Update .env with correct ULTRAMSG_TOKEN
     - Restart application

   - If response shows `'error': 'Instance not found'` → ❌ Fix:
     - Check ULTRAMSG_INSTANCE_ID in .env
     - Verify instance still active on Ultramsg dashboard

### If No Ultramsg Log Entry At All:

1. [ ] Check app startup log: `"Ultramsg: True"` or `"Ultramsg: False"`?
   
   - If `Ultramsg: False` → Missing credentials:
     - Create .env file with ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN
     - Restart app
     - Re-test payment
   
   - If `Ultramsg: True` but no WhatsApp log → Check:
     - Is student phone NULL or empty?
     - Is email configured? (email sends first, then WhatsApp)
     - Check daemon thread error: `"Notification failed for..."`

---

## Test 4: Phone Number Debugging 📞

### What To Look For In Logs:

```
Good log:
"Sending WhatsApp - Original: +237691234567, Normalized: +237691234567"
(Both are identical)

Bad log:
"Sending WhatsApp - Original: 237691234567, Normalized: +237691234567"
(System added +, might be wrong country code)

Bad log:
"Sending WhatsApp - Original: +237 691 234 567, Normalized: +237691234567"
(System removed spaces, should work)
```

### Fix Phone Format:

Current Format → Correct Format:
- `697123456` → `+237697123456`
- `00237697123456` → `+237697123456`
- `+237 697 123 456` → `+237697123456` (system fixes this)
- `00237 697 123 456` → `+237697123456` (system fixes this)

---

## Test 5: Configuration Check 🔧

### Run Diagnostic Script:

```bash
cd "e:\SECRET FILES\MY_TFC"
python test_diagnostics.py
```

### Check Output Includes:

- [ ] ✅ "Ultramsg configured" OR ❌ "Ultramsg NOT configured"
- [ ] Phone normalization tests pass
- [ ] Test promotions found (one with $0 fees, one with fees > $0)
- [ ] Email service status
- [ ] No critical errors

### If Errors Appear:

1. [ ] Read each error message
2. [ ] Cross-reference with `DIAGNOSTICS_GUIDE.md`
3. [ ] Follow recommended actions

---

## Quick Fix Reference

| Issue | Fix | Verify |
|-------|-----|--------|
| Payment accepted with $0 fees | Restart app, test again | Logs show rejection |
| "Ultramsg not configured" | Create .env with credentials | `Ultramsg: True` in init log |
| "Invalid phone number" error | Fix format to +COUNTRYCODE | Check logs for normalized format |
| Email sends but no WhatsApp | Check Ultramsg response in logs | Look for 'sent': true/false |
| Payment never recorded | Check `Payment rejected` logs | Verify fee validation working |
| No logs being written | Check `logs/` directory exists | Create manually if needed |

---

## Emergency Debug Commands

### View Recent Logs (Windows PowerShell):

```powershell
# Show last 50 lines of log
Get-Content logs\app.log -Tail 50

# Follow logs in real-time
Get-Content logs\app.log -Tail 50 -Wait

# Search for payment errors
Select-String logs\app.log -Pattern "Payment|rejected|payment"

# Search for WhatsApp issues
Select-String logs\app.log -Pattern "WhatsApp|Ultramsg|notification"
```

### Check Database Payment Record:

```sql
-- Show recent payments
SELECT * FROM paiement ORDER BY date_paiement DESC LIMIT 10;

-- Check promotion fees
SELECT id, name, fee_usd FROM promotion WHERE fee_usd = 0 LIMIT 5;

-- Check student phone format
SELECT matricule_etudiant, email, phone_number FROM etudiant LIMIT 10;
```

### Reset for Testing:

```sql
-- Delete test payment (careful!)
DELETE FROM paiement WHERE matricule_etudiant = 'TEST001';

-- Update student email/phone
UPDATE etudiant SET email = 'test@example.com', phone_number = '+237691234567' WHERE matricule_etudiant = 'TEST001';
```

---

## When to Check What

| Symptom | Check First | Then Check | Finally |
|---------|-------------|-----------|---------|
| Payment rejected | Promotion.fee_usd | Logs for rejection reason | Database for payment |
| No error, payment not saved | Service layer logs | Database payment table | UI error dialog |
| WhatsApp not sent | Ultramsg init status | Phone format | API response in logs |
| Email sent, WhatsApp failed | Phone number (NULL?) | Ultramsg credentials | API response |
| Nothing happens | Database connection | Logs written at all | Application running |

---

## Quick Decision Tree

```
Does payment fail with error?
├─ YES: Check error type
│  ├─ "Aucun frais académique..." → Correct! Validation working ✅
│  ├─ "Le montant saisi dépasse..." → Correct! Overpayment blocked ✅
│  └─ Other error → See DIAGNOSTICS_GUIDE.md
│
└─ NO: Check logs
   ├─ "Payment recorded" found? → Payment saved ✅
   ├─ "Payment rejected" found? → Expected when no fees ✅
   └─ Nothing found? → Logs not writing or app not running ❌

Does WhatsApp log entry appear?
├─ YES: Check API response
│  ├─ 'sent': 'true' → API accepted ✅ (check Ultramsg dashboard)
│  ├─ 'error': found → API rejected ❌ (see error message)
│  └─ 'sent': 'false' → API refused ❌ (check API response)
│
└─ NO: Check config
   ├─ Ultramsg: True? → Check phone number format
   ├─ Ultramsg: False? → Add credentials to .env
   └─ No notification log? → Check email first
```

---

## Success Indicators 🎉

You know everything is working when:

- ✅ Payment with $0 fees shows clear error
- ✅ Payment with valid fees succeeds
- ✅ Email notification arrives
- ✅ Logs show: `"Ultramsg API response: {'sent': 'true'}"`
- ✅ WhatsApp message arrives to phone
- ✅ All events logged in app.log with timestamps

---

## Emergency Contacts / Resources

- 📖 **Main Guide**: DIAGNOSTICS_GUIDE.md
- 📖 **Code Reference**: CODE_CHANGES_REFERENCE.md
- 📖 **Implementation Details**: IMPLEMENTATION_FIXES_PAYMENT_WHATSAPP.md
- 🧪 **Test Script**: test_diagnostics.py
- 📊 **Logs Location**: logs/app.log
- 🌐 **Ultramsg Dashboard**: https://app.ultramsg.com/

---

**Last Updated**: After implementation
**Status**: Ready for Testing
**Next Step**: Run Test 1 and 2 from this checklist
