#!/usr/bin/env python
"""
Database Migration Script: SQLite to PostgreSQL
Run this script to migrate your data from SQLite to PostgreSQL
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connections
from django.core.management.commands import dumpdata, loaddata
import subprocess
import tempfile

def backup_sqlite_data():
    """Backup current SQLite data to JSON"""
    print("📦 Backing up SQLite data...")
    
    # Create temporary file for data dump
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    # Dump data from SQLite
    try:
        # Switch to SQLite temporarily for backup
        os.environ['DJANGO_SETTINGS_MODULE'] = 'richesreach.settings'
        django.setup()
        
        # Dump all data
        subprocess.run([
            'python', 'manage.py', 'dumpdata', 
            '--natural-foreign', '--natural-primary',
            '--indent', '2',
            '--output', temp_file
        ], check=True)
        
        print(f"✅ Data backed up to: {temp_file}")
        return temp_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error backing up data: {e}")
        return None

def setup_postgres_database():
    """Set up PostgreSQL database and run migrations"""
    print("🗄️ Setting up PostgreSQL database...")
    
    # Switch back to production settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'richesreach.settings_production'
    django.setup()
    
    try:
        # Create migrations
        print("📝 Creating migrations...")
        subprocess.run(['python', 'manage.py', 'makemigrations'], check=True)
        
        # Run migrations
        print("🚀 Running migrations...")
        subprocess.run(['python', 'manage.py', 'migrate'], check=True)
        
        print("✅ PostgreSQL database set up successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        return False

def restore_data_to_postgres(backup_file):
    """Restore data from backup to PostgreSQL"""
    if not backup_file or not os.path.exists(backup_file):
        print("❌ No backup file found")
        return False
    
    print("🔄 Restoring data to PostgreSQL...")
    
    try:
        # Load data into PostgreSQL
        subprocess.run([
            'python', 'manage.py', 'loaddata', backup_file
        ], check=True)
        
        print("✅ Data restored successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error restoring data: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    print("🔍 Verifying migration...")
    
    try:
        from django.db import connection
        from core.models import User, Stock, Portfolio
        
        with connection.cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('core_user', 'core_stock', 'core_portfolio')
            """)
            tables = cursor.fetchall()
            
            if len(tables) >= 3:
                print("✅ All tables created successfully")
            else:
                print(f"⚠️ Only {len(tables)} tables found")
            
            # Check data counts
            user_count = User.objects.count()
            stock_count = Stock.objects.count()
            portfolio_count = Portfolio.objects.count()
            
            print(f"📊 Data counts:")
            print(f"   Users: {user_count}")
            print(f"   Stocks: {stock_count}")
            print(f"   Portfolios: {portfolio_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 Starting SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Step 1: Backup SQLite data
    backup_file = backup_sqlite_data()
    if not backup_file:
        print("❌ Migration failed: Could not backup SQLite data")
        return False
    
    # Step 2: Set up PostgreSQL
    if not setup_postgres_database():
        print("❌ Migration failed: Could not set up PostgreSQL")
        return False
    
    # Step 3: Restore data
    if not restore_data_to_postgres(backup_file):
        print("❌ Migration failed: Could not restore data")
        return False
    
    # Step 4: Verify migration
    if not verify_migration():
        print("⚠️ Migration completed but verification failed")
        return False
    
    # Cleanup
    try:
        os.unlink(backup_file)
        print(f"🧹 Cleaned up temporary file: {backup_file}")
    except:
        pass
    
    print("=" * 50)
    print("🎉 Migration completed successfully!")
    print("✅ Your app is now running on PostgreSQL")
    print("🔧 Remember to update your environment variables")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
