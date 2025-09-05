#!/usr/bin/env python
"""
Create a simple migration for IncomeProfile only
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

def run_simple_migration():
    """Create and apply migration for IncomeProfile only"""
    try:
        # Create migration for IncomeProfile
        print("Creating IncomeProfile migration...")
        execute_from_command_line(['manage.py', 'makemigrations', 'core', '--name', 'add_income_profile'])
        
        # Apply migration
        print("Applying migration...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_migration()
    sys.exit(0 if success else 1)
