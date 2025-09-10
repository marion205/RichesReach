#!/usr/bin/env python3
"""
Run the enhanced authentication migration
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def run_migration():
    """Run the enhanced authentication migration"""
    print("Running Enhanced Authentication Migration")
    print("=" * 45)
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()
    
    try:
        # Run the migration
        print("Applying migration 0014_enhance_user_security...")
        execute_from_command_line(['manage.py', 'migrate', 'core'])
        print("Migration completed successfully!")
        
        # Show migration status
        print("\n Migration Status:")
        execute_from_command_line(['manage.py', 'showmigrations', 'core'])
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n Enhanced authentication system is ready!")
        print("You can now test the authentication features.")
    else:
        print("\n Migration failed. Please check the error messages above.")
        sys.exit(1)
