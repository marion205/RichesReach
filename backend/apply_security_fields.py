#!/usr/bin/env python3
"""
Directly apply security fields to User model
This bypasses GraphQL schema issues by directly modifying the database
"""

import os
import sys
import django
from django.db import connection

def apply_security_fields():
    """Apply security fields directly to the database"""
    print("🔐 Applying Enhanced Authentication Security Fields")
    print("=" * 55)
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()
    
    try:
        with connection.cursor() as cursor:
            # Check if fields already exist
            cursor.execute("PRAGMA table_info(core_user)")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📊 Current User table columns: {columns}")
            
            # Add security fields if they don't exist
            security_fields = [
                ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                ('locked_until', 'DATETIME NULL'),
                ('last_login_ip', 'VARCHAR(39) NULL'),
                ('email_verified', 'BOOLEAN DEFAULT 0'),
                ('two_factor_enabled', 'BOOLEAN DEFAULT 0'),
                ('two_factor_secret', 'VARCHAR(32) DEFAULT ""'),
                ('created_at', 'DATETIME NULL'),
                ('updated_at', 'DATETIME NULL'),
            ]
            
            for field_name, field_type in security_fields:
                if field_name not in columns:
                    print(f"➕ Adding field: {field_name}")
                    cursor.execute(f"ALTER TABLE core_user ADD COLUMN {field_name} {field_type}")
                else:
                    print(f"✅ Field already exists: {field_name}")
            
            # Create indexes for performance
            indexes = [
                ('idx_user_email_verified', 'core_user', 'email_verified'),
                ('idx_user_locked_until', 'core_user', 'locked_until'),
                ('idx_user_created_at', 'core_user', 'created_at'),
            ]
            
            for index_name, table_name, column_name in indexes:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
                    print(f"📈 Created index: {index_name}")
                except Exception as e:
                    print(f"⚠️ Index {index_name} may already exist: {e}")
            
            # Update existing users to have email_verified = True (for existing users)
            cursor.execute("UPDATE core_user SET email_verified = 1 WHERE email_verified IS NULL")
            updated_rows = cursor.rowcount
            print(f"🔄 Updated {updated_rows} existing users to have verified emails")
            
        print("\n✅ Security fields applied successfully!")
        
        # Verify the changes
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(core_user)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"\n📋 Updated User table columns: {columns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply security fields: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_fields():
    """Test that the security fields are working"""
    print("\n🧪 Testing Security Fields")
    print("=" * 30)
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Test creating a user with security fields
        test_email = "security_test@example.com"
        
        # Clean up any existing test user
        User.objects.filter(email=test_email).delete()
        
        # Create test user
        user = User.objects.create_user(
            email=test_email,
            name="Security Test User",
            password="TestPassword123!"
        )
        
        # Test security fields
        print(f"✅ User created: {user.email}")
        print(f"✅ Failed login attempts: {user.failed_login_attempts}")
        print(f"✅ Email verified: {user.email_verified}")
        print(f"✅ Two factor enabled: {user.two_factor_enabled}")
        print(f"✅ Created at: {user.created_at}")
        print(f"✅ Updated at: {user.updated_at}")
        
        # Test security methods
        print(f"✅ Is locked: {user.is_locked()}")
        
        # Clean up
        user.delete()
        print("✅ Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Security fields test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Enhanced Authentication Database Setup")
    print("=" * 45)
    
    # Apply security fields
    success = apply_security_fields()
    
    if success:
        # Test the fields
        test_success = test_security_fields()
        
        if test_success:
            print("\n🎉 Enhanced authentication database setup complete!")
            print("✅ All security fields are working correctly")
            print("\n📋 Next steps:")
            print("1. Configure email settings: python setup_email_config.py")
            print("2. Test authentication: python test_enhanced_auth.py")
        else:
            print("\n⚠️ Security fields applied but tests failed")
            print("Please check the error messages above")
    else:
        print("\n❌ Failed to apply security fields")
        print("Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
