#!/bin/bash
# Create a second test user for RichesReach

cd /Users/marioncollins/RichesReach/deployment_package/backend

echo "🔧 Creating second user account..."
echo ""

python3 manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# User 2 credentials
email = 'user2@test.com'
password = 'testpass123'
name = 'Test User 2'

# Check if user already exists
if User.objects.filter(email=email).exists():
    print(f"⚠️  User {email} already exists!")
    user = User.objects.get(email=email)
    print(f"   User ID: {user.id}")
    print(f"   Name: {user.name}")
else:
    # Create new user
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        is_active=True
    )
    print(f"✅ Created second user:")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.name}")
    print(f"   Password: {password}")
    print(f"   User ID: {user.id}")

# List all users
print(f"\n📋 All users ({User.objects.count()} total):")
for i, u in enumerate(User.objects.all().order_by('created_at'), 1):
    print(f"   {i}. {u.email} ({u.name})")

print(f"\n📱 Login credentials for second user:")
print(f"   Email: {email}")
print(f"   Password: {password}")
EOF

