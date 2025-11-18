# Email Configuration Guide

**Date**: November 10, 2024

---

## Current Email Configuration

**Status**: Placeholder values detected

**Current Settings**:
- `EMAIL_HOST_USER=your-email@gmail.com` (placeholder)
- `EMAIL_HOST_PASSWORD=your-app-specific-password` (placeholder)

---

## Options for Email Configuration

### Option 1: Gmail (Quick Setup)

**Pros**: Easy to set up, free  
**Cons**: 500 emails/day limit, not ideal for production

**Steps**:

1. **Enable 2-Factor Authentication** on your Gmail account

2. **Generate App-Specific Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "RichesReach Production"
   - Copy the 16-character password

3. **Update .env**:
```bash
cd deployment_package/backend

# Edit .env and update:
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-actual-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=noreply@richesreach.com
```

4. **Test Email**:
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'RichesReach Test',
    'Email configuration test.',
    'noreply@richesreach.com',
    ['your-test-email@example.com'],
    fail_silently=False,
)
```

5. **Redeploy** (if needed):
```bash
cd ../..
./deploy_backend.sh
```

---

### Option 2: AWS SES (Recommended for Production)

**Pros**: Scalable, production-ready, cost-effective  
**Cons**: Requires AWS setup

**Steps**:

1. **Verify Email Domain in SES**:
   - Go to AWS Console → SES → Verified identities
   - Add and verify `richesreach.com` domain
   - Or verify individual email addresses

2. **Create SMTP Credentials**:
   - Go to SES → SMTP Settings
   - Click "Create SMTP credentials"
   - Save the username and password

3. **Request Production Access** (if needed):
   - SES starts in sandbox mode
   - Request production access to send to any email
   - Usually approved within 24 hours

4. **Update .env**:
```bash
cd deployment_package/backend

# Edit .env and update:
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=YOUR_SES_SMTP_USERNAME
EMAIL_HOST_PASSWORD=YOUR_SES_SMTP_PASSWORD
DEFAULT_FROM_EMAIL=noreply@richesreach.com
```

5. **Test Email** (same as Gmail test above)

6. **Redeploy**:
```bash
cd ../..
./deploy_backend.sh
```

---

### Option 3: Skip Email (For Now)

**If you don't need email right now**:
- Keep placeholder values
- No action needed
- Can update later when needed

---

## Testing Email Configuration

### Quick Test

```bash
cd deployment_package/backend
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Check configuration
print(f"Email host: {settings.EMAIL_HOST}")
print(f"Email port: {settings.EMAIL_PORT}")
print(f"Email user: {settings.EMAIL_HOST_USER}")

# Send test email
try:
    send_mail(
        'RichesReach Test Email',
        'This is a test email from RichesReach production.',
        settings.DEFAULT_FROM_EMAIL,
        ['your-email@example.com'],
        fail_silently=False,
    )
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Email failed: {e}")
```

### Verify Email Received
- Check inbox
- Check spam folder
- Verify sender is correct

---

## Troubleshooting

### Gmail Issues

**"Username and Password not accepted"**:
- Make sure you're using an app-specific password, not your regular password
- Verify 2FA is enabled
- Check that "Less secure app access" is not needed (use app password instead)

**"Daily sending quota exceeded"**:
- Gmail limit: 500 emails/day
- Consider switching to AWS SES for higher limits

### AWS SES Issues

**"Email address not verified"**:
- Verify the sender email in SES
- Or verify the domain

**"Account is in sandbox mode"**:
- Request production access in SES
- Or only send to verified email addresses

**"SMTP credentials invalid"**:
- Regenerate SMTP credentials
- Make sure you're using the correct region

---

## Recommendation

**For Development/Testing**: Gmail (quick setup)  
**For Production**: AWS SES (scalable, professional)

**If Not Needed Now**: Skip and update later

---

## Next Steps After Email Configuration

1. ✅ Test email sending
2. ✅ Verify email received
3. ✅ Redeploy if needed
4. ✅ Run final testing checklist

---

**Status**: Ready to configure email or skip for now

