#!/usr/bin/env python
"""
Directly create IncomeProfile table using SQL
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.db import connection

def create_income_profile_table():
    """Create IncomeProfile table directly"""
    try:
        with connection.cursor() as cursor:
            # Check if table already exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='core_incomeprofile'
            """)
            
            if cursor.fetchone():
                print("✅ IncomeProfile table already exists!")
                return True
            
            # Create the table
            cursor.execute("""
                CREATE TABLE core_incomeprofile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    income_bracket VARCHAR(50) NOT NULL,
                    age INTEGER NOT NULL,
                    investment_goals TEXT NOT NULL,
                    risk_tolerance VARCHAR(20) NOT NULL,
                    investment_horizon VARCHAR(20) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL UNIQUE,
                    FOREIGN KEY (user_id) REFERENCES core_user (id)
                )
            """)
            
            print("✅ IncomeProfile table created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create IncomeProfile table: {e}")
        return False

if __name__ == "__main__":
    success = create_income_profile_table()
    sys.exit(0 if success else 1)
