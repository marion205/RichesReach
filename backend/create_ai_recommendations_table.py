#!/usr/bin/env python
"""
Create AIPortfolioRecommendation table directly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.db import connection

def create_ai_recommendations_table():
    """Create AIPortfolioRecommendation table directly"""
    try:
        with connection.cursor() as cursor:
            # Check if table already exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='core_aiportfoliorecommendation'
            """)
            
            if cursor.fetchone():
                print("✅ AIPortfolioRecommendation table already exists!")
                return True
            
            # Create the table
            cursor.execute("""
                CREATE TABLE core_aiportfoliorecommendation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    risk_profile VARCHAR(20) NOT NULL,
                    portfolio_allocation TEXT NOT NULL,
                    recommended_stocks TEXT NOT NULL,
                    expected_portfolio_return DECIMAL(5,2),
                    risk_assessment TEXT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES core_user (id)
                )
            """)
            
            print("✅ AIPortfolioRecommendation table created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create AIPortfolioRecommendation table: {e}")
        return False

if __name__ == "__main__":
    success = create_ai_recommendations_table()
    sys.exit(0 if success else 1)
