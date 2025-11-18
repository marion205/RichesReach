# Create Test User - Quick Guide

## ✅ Correct Path

**From project root** (not from `mobile/` directory):

```bash
cd /Users/marioncollins/RichesReach/deployment_package/backend
python3 manage.py shell
```

## 🚀 Quick User Creation

### Option 1: Using Python Shell

```bash
cd /Users/marioncollins/RichesReach/deployment_package/backend
python3 manage.py shell
```

Then in the shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user
user = User.objects.create_user(
    email='test@example.com',
    password='testpass123',
    name='Test User'
)
print(f"✅ Created user: {user.email}")
```

### Option 2: One-Liner Command

```bash
cd /Users/marioncollins/RichesReach/deployment_package/backend
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user(
    email='test@example.com',
    password='testpass123',
    name='Test User'
)
print(f'✅ Created user: {user.email}')
"
```

### Option 3: Using Django Management Command

If you have a custom command:
```bash
cd /Users/marioncollins/RichesReach/deployment_package/backend
python3 manage.py createsuperuser
# Follow prompts
```

---

## 🔍 Check Existing Users

```bash
cd /Users/marioncollins/RichesReach/deployment_package/backend
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Users: {User.objects.count()}')
for u in User.objects.all()[:5]:
    print(f'  - {u.email}')
"
```

---

## 📱 Test Login Credentials

After creating user:
- **Email**: `test@example.com`
- **Password**: `testpass123`

Use these in the mobile app login screen.

---

## ⚠️ Common Mistakes

**Wrong**: Starting from `mobile/` directory
```bash
cd mobile
cd deployment_package/backend  # ❌ Won't work
```

**Correct**: Starting from project root
```bash
cd /Users/marioncollins/RichesReach
cd deployment_package/backend  # ✅ Works
```

---

## 🎯 Quick Reference

**Project Root**: `/Users/marioncollins/RichesReach`  
**Backend Path**: `deployment_package/backend`  
**Full Path**: `/Users/marioncollins/RichesReach/deployment_package/backend`

**Always start from project root!**

