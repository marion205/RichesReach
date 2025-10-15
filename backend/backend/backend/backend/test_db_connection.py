#!/usr/bin/env python3
"""
Test AWS PostgreSQL Database Connection
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_aws')

# Setup Django
django.setup()

from django.db import connection
from core.models import User

def test_database_connection():
    """Test the database connection"""
    print("🔍 Testing AWS PostgreSQL Database Connection")
    print("=" * 50)
    
    try:
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Basic database connection successful")
        
        # Test Django ORM
        user_count = User.objects.count()
        print(f"✅ Django ORM working - Found {user_count} users in database")
        
        # Test creating a test user
        test_user, created = User.objects.get_or_create(
            email="test@example.com",
            defaults={
                "name": "Test User",
                "password": "testpass123"
            }
        )
        
        if created:
            print("✅ Test user created successfully")
        else:
            print("✅ Test user already exists")
        
        print("\n🎉 Database connection test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your AWS RDS endpoint is correct")
        print("2. Verify your database credentials")
        print("3. Ensure your security groups allow connections")
        print("4. Check if the database is running")
        return False

if __name__ == "__main__":
    test_database_connection()

