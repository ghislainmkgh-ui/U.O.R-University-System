# Twilio WhatsApp Integration Guide

## ⚠️ Security First

**NEVER hardcode credentials in code!** Always use environment variables.

### Setup `.env` File
Create `e:\SECRET FILES\MY_TFC\.env`:
```env
# Twilio WhatsApp
TWILIO_ACCOUNT_SID=AC_your_new_sid_here
TWILIO_AUTH_TOKEN=your_new_auth_token_here
TWILIO_WHATSAPP_FROM=+14155238886

# Email
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Never commit `.env` to Git!** Add to `.gitignore`:
```
.env
*.pyc
__pycache__/
```

---

## 📱 Two Methods for Sending WhatsApp

### Method 1: Standard Message (Current)
```python
from app.services.integration.notification_service import NotificationService

service = NotificationService()
service.send_access_code_notification(
    student_email='student@example.com',
    student_phone='+243XXXXXXXXX',
    student_name='John Doe',
    access_code='123456',
    code_type='full',
    expires_at='2025-09-15'
)
# Sends readable formatted message
```

**Pros**: 
- Simple, no pre-approval needed
- Flexible content

**Cons**:
- Less professional formatting
- Higher costs ($0.0147 - $0.0400 per message depending on region)

---

### Method 2: Content Templates (Advanced)
Pre-approved message templates with variables.

**Pros**:
- Professional formatting
- Lower costs per message ($0.0088 - $0.0176)
- Brand consistency
- Twilio reviews for compliance

**Cons**:
- Requires Twilio approval
- Setup time (2-48 hours)
- Limited to pre-approved content

#### Create Template in Twilio Console

1. Go to: https://console.twilio.com/develop/sms/content-builder
2. Create new template:

**Example: Access Code Template**
```
Hi {{1}}! 🎓

Your exam access code has been generated:

📝 Code: {{2}}
⏰ Valid: {{3}}
🔐 Keep this code safe!

Need help? Contact admin@uor.ac

- U.O.R System
```

Save template → Copy **Content SID** (e.g., `HXb5b62575e6e4ff6...`)

#### Send Using Template
```python
service.send_whatsapp_with_template(
    student_phone='+243123456789',
    template_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
    template_variables=['John Doe', '123456', 'All exam periods']
)
```

---

## 🔑 Complete Integration Example

### Step 1: Update Finance Service
```python
# In finance_service.py _issue_access_code_if_needed()

# Option A: Standard message (current)
self.notification_service.send_access_code_notification(
    student_email=student_email,
    student_phone=student_phone,
    student_name=student_name,
    access_code=access_code,
    code_type='full',
    expires_at=expiry_date
)

# Option B: Template-based (if you want)
if use_templates:  # config flag
    self.notification_service.send_whatsapp_with_template(
        student_phone=student_phone,
        template_sid=os.getenv('WHATSAPP_TEMPLATE_ACCESS_CODE'),
        template_variables=[student_name, access_code, validity_text]
    )
```

### Step 2: Create Custom Method in NotificationService
```python
def send_access_code_via_template(self, student_phone: str, 
                                  student_name: str, access_code: str,
                                  validity_text: str) -> bool:
    """Send access code using pre-approved Twilio template"""
    template_sid = os.getenv('WHATSAPP_TEMPLATE_ACCESS_CODE')
    return self.send_whatsapp_with_template(
        student_phone=student_phone,
        template_sid=template_sid,
        template_variables=[student_name, access_code, validity_text]
    )

def send_threshold_alert_via_template(self, student_phone: str,
                                      student_name: str, new_threshold: float) -> bool:
    """Send threshold change alert using template"""
    template_sid = os.getenv('WHATSAPP_TEMPLATE_THRESHOLD_ALERT')
    return self.send_whatsapp_with_template(
        student_phone=student_phone,
        template_sid=template_sid,
        template_variables=[student_name, f"{new_threshold:,.0f} FC"]
    )
```

---

## 💰 Cost Comparison

| Service | Per Message | Notes |
|---------|------------|-------|
| **Standard WhatsApp** | $0.0147-$0.0400 | No approval needed |
| **Template Messages** | $0.0088-$0.0176 | 40-60% cheaper, needs approval |
| **SMS** | $0.0075-$0.0200 | Text messages (no media) |

**Example**: 1000 access codes per month
- Standard API: $20-40/month
- Templates: $10-18/month
- **Savings: 50%+**

---

## 🧪 Testing Templates

### Step 1: Create Simple Template
Content:
```
Hi {{1}}!

Your code: {{2}}

Thanks,
U.O.R
```

### Step 2: Test Sending
```python
from app.services.integration.notification_service import NotificationService

service = NotificationService()
success = service.send_whatsapp_with_template(
    student_phone='+243XXXXXXXXX',
    template_sid='HXb5b62575e6e4ff...',  # Your template SID
    template_variables=['John', '123456']
)

if success:
    print("✅ Template message sent!")
else:
    print("❌ Template message failed")
```

---

## 🔒 Best Practices

### 1. Environment Variables
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', '')
WHATSAPP_TEMPLATE_ACCESS_CODE = os.getenv('WHATSAPP_TEMPLATE_ACCESS_CODE', '')
WHATSAPP_TEMPLATE_THRESHOLD_ALERT = os.getenv('WHATSAPP_TEMPLATE_THRESHOLD_ALERT', '')
```

### 2. Validate Before Sending
```python
# Check credentials exist before sending
if not self.whatsapp_sid:
    logger.error("WhatsApp not configured - skipping send")
    return False

# Validate phone number format
if not student_phone.startswith('+'):
    logger.error(f"Invalid phone format: {student_phone}")
    return False
```

### 3. Implement Retry Logic
```python
import time

def send_with_retry(self, phone, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = self._send_whatsapp(phone, message)
            if result:
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
    return False
```

### 4. Log Everything
```python
import json
from datetime import datetime

def _log_message(self, phone, message_type, success):
    """Log all messages sent for audit trail"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'phone': phone,
        'type': message_type,
        'success': success
    }
    with open('logs/whatsapp_delivery.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

---

## 📊 Status Check

```python
from twilio.rest import Client
import os

# Initialize
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Check account balance
account = client.api.accounts(account_sid).fetch()
print(f"Account Status: {account.status}")
print(f"Account Type: {account.type}")

# Check message logs
messages = client.messages.list(limit=5)
for message in messages:
    print(f"SID: {message.sid}")
    print(f"Status: {message.status}")  # sent, delivered, failed, etc.
    print(f"Date Sent: {message.date_sent}")
    print(f"Error Code: {message.error_code}")
```

---

## ❌ Common Errors & Solutions

### Error: `Invalid content SID`
**Cause**: Template SID doesn't exist or is misspelled
**Solution**: Copy exact SID from Twilio console, verify in `.env`

### Error: `Invalid `from` parameter`
**Cause**: Using wrong WhatsApp number
**Solution**: Use Twilio-provided sandbox number or production approved number

### Error: `Invalid `to` parameter`
**Cause**: Recipient hasn't joined sandbox (if using sandbox)
**Solution**: From your verified phone, send WhatsApp message to Twilio: `join [code]`

### Error: `Authentication Token was invalid`
**Cause**: Old token copied or credentials exposed
**Solution**: Regenerate token in Twilio console, update `.env`

### Error: `Insufficient account balance`
**Cause**: Out of Twilio credits
**Solution**: Add payment method at https://console.twilio.com/billing/overview

---

## 🚀 Deployment Checklist

- [ ] Credentials in `.env` (NOT in code)
- [ ] `.env` added to `.gitignore`
- [ ] Twilio account created and verified
- [ ] WhatsApp number acquired (sandbox or production)
- [ ] Test message sent successfully
- [ ] Production templates created (if using)
- [ ] Rate limiting configured
- [ ] Error handling in place
- [ ] Logging enabled
- [ ] Monitoring setup
- [ ] Documented in team wiki

---

**Current Implementation**: Standard WhatsApp API (Method 1)  
**To Switch to Templates**: Update `.env` with template SIDs and call `send_whatsapp_with_template()`
