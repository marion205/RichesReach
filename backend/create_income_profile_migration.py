#!/usr/bin/env python
"""
Create IncomeProfile migration and handle Watchlist issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from core.models import Stock

def create_sample_stock():
    """Create a sample stock if none exist"""
    if not Stock.objects.exists():
        print("Creating sample stock for migration...")
        Stock.objects.create(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,  # 3 trillion
            current_price=150.00
        )
        print("Sample stock created: AAPL")

def run_migration():
    """Run the migration with proper handling"""
    try:
        # Create sample stock first
        create_sample_stock()
        
        # Run makemigrations
        print("Creating migration...")
        execute_from_command_line(['manage.py', 'makemigrations', 'core'])
        
        # Run migrate
        print("Applying migration...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
