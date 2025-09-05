# 🔐 Enhanced Authentication Setup Guide

## 🎯 **Quick Setup (5 minutes)**

### **Step 1: Configure Email Settings**
```bash
cd backend
python setup_email_config.py
```

### **Step 2: Run Database Migration**
```bash
python run_migration.py
```

### **Step 3: Test Authentication Features**
```bash
python test_enhanced_auth.py
```

---

## 📧 **Email Configuration Details**

### **Gmail Setup (Recommended)**
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password:**
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password (not your regular Gmail password)

### **Manual .env Configuration**
If the setup script doesn't work, manually edit `backend/.env`:

```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@richesreach.com
FRONTEND_URL=http://localhost:3000
```

### **Other Email Providers**
- **Outlook/Hotmail:** `smtp-mail.outlook.com:587`
- **Yahoo:** `smtp.mail.yahoo.com:587`
- **Custom SMTP:** Use your provider's settings

---

## 🗄️ **Database Migration**

The migration adds these security fields to your User model:

```python
# Security Fields
failed_login_attempts = models.IntegerField(default=0)
locked_until = models.DateTimeField(null=True, blank=True)
last_login_ip = models.GenericIPAddressField(null=True, blank=True)
email_verified = models.BooleanField(default=False)

# 2FA Ready
two_factor_enabled = models.BooleanField(default=False)
two_factor_secret = models.CharField(max_length=32, blank=True)

# Timestamps
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

---

## 🧪 **Testing Features**

The test suite covers:

### **✅ Security Features**
- **Password Strength Validation** - Tests weak/strong passwords
- **Rate Limiting** - Tests IP-based rate limiting
- **Account Lockout** - Tests failed attempt lockout
- **Secure Token Generation** - Tests token security

### **✅ Authentication Features**
- **Enhanced Signup** - Tests new user registration
- **Enhanced Login** - Tests secure login with rate limiting
- **Password Reset** - Tests forgot password flow
- **Change Password** - Tests password change functionality
- **Email Verification** - Tests email verification system

### **✅ User Experience**
- **Clear Error Messages** - Tests user-friendly error handling
- **Email Notifications** - Tests email sending
- **Account Recovery** - Tests account recovery options

---

## 🚀 **New GraphQL Mutations**

### **Enhanced Authentication**
```graphql
# Enhanced Login with Security
mutation Login($email: String!, $password: String!) {
  enhancedTokenAuth(email: $email, password: $password) {
    token
    user { id email name }
    success
    message
  }
}

# Password Reset
mutation ForgotPassword($email: String!) {
  forgotPassword(email: $email) {
    success
    message
  }
}

# Change Password
mutation ChangePassword($currentPassword: String!, $newPassword: String!) {
  changePassword(currentPassword: $currentPassword, newPassword: $newPassword) {
    success
    message
  }
}

# Email Verification
mutation VerifyEmail($token: String!) {
  verifyEmail(token: $token) {
    success
    message
  }
}
```

---

## 🔒 **Security Features**

### **Rate Limiting**
- **Login:** 5 attempts per 15 minutes
- **Signup:** 3 attempts per 15 minutes
- **Password Reset:** 3 attempts per hour

### **Account Protection**
- **Lockout:** 30 minutes after 5 failed attempts
- **IP Tracking:** Records login IP addresses
- **Suspicious Activity:** Blocks suspicious requests

### **Password Security**
- **Minimum Length:** 8 characters
- **Complexity:** Mixed case, numbers, special characters
- **Common Patterns:** Blocks common weak patterns

---

## 📱 **Frontend Integration**

### **Enhanced Login Screen**
```typescript
// Use the new enhanced login mutation
const LOGIN = gql`
  mutation Login($email: String!, $password: String!) {
    enhancedTokenAuth(email: $email, password: $password) {
      token
      user { id email name }
      success
      message
    }
  }
`;
```

### **Password Strength Indicator**
```typescript
import PasswordStrengthIndicator from '../components/PasswordStrengthIndicator';

// In your signup form
<PasswordStrengthIndicator password={password} />
```

### **Forgot Password Flow**
```typescript
// Use the forgot password mutation
const FORGOT_PASSWORD = gql`
  mutation ForgotPassword($email: String!) {
    forgotPassword(email: $email) {
      success
      message
    }
  }
`;
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Email Not Sending**
```bash
# Check email configuration
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()
from django.core.mail import send_mail
from django.conf import settings
print(f'Email backend: {settings.EMAIL_BACKEND}')
print(f'Email host: {settings.EMAIL_HOST}')
print(f'Email user: {settings.EMAIL_HOST_USER}')
"
```

#### **Migration Issues**
```bash
# Check migration status
python manage.py showmigrations core

# Reset migrations if needed
python manage.py migrate core zero
python manage.py migrate core
```

#### **GraphQL Errors**
```bash
# Test GraphQL endpoint
curl -X POST http://127.0.0.1:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { fields { name } } } }"}'
```

---

## 🎉 **Success Checklist**

- [ ] Email configuration working
- [ ] Database migration applied
- [ ] All tests passing
- [ ] Enhanced login working
- [ ] Password reset working
- [ ] Rate limiting active
- [ ] Account lockout working
- [ ] Frontend integration complete

---

## 📞 **Support**

If you encounter any issues:

1. **Check the logs** in your terminal
2. **Run the test suite** to identify specific problems
3. **Verify email configuration** with the setup script
4. **Check Django settings** for any configuration issues

Your enhanced authentication system is now enterprise-grade and ready for production! 🚀
