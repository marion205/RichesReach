#!/usr/bin/env python3
"""
Configure AWS PostgreSQL Database Connection
"""
import os
import sys
from pathlib import Path

def configure_aws_database():
    """Configure AWS PostgreSQL database connection"""
    print("🔧 AWS PostgreSQL Database Configuration")
    print("=" * 50)
    
    # Get database details from user
    print("\n📊 Please provide your AWS RDS PostgreSQL details:")
    
    db_host = input("RDS Endpoint (e.g., richesreach-db.xxxxxxxxx.us-east-1.rds.amazonaws.com): ").strip()
    db_name = input("Database Name [richesreach_prod]: ").strip() or "richesreach_prod"
    db_user = input("Database User [postgres]: ").strip() or "postgres"
    db_password = input("Database Password: ").strip()
    
    if not db_host or not db_password:
        print("❌ Database host and password are required")
        return False
    
    # Update the settings file
    settings_file = Path(__file__).parent / "richesreach" / "settings_aws.py"
    
    if not settings_file.exists():
        print(f"❌ Settings file not found: {settings_file}")
        return False
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Update database configuration
    content = content.replace(
        "DB_NAME = os.getenv('DB_NAME')",
        f"DB_NAME = os.getenv('DB_NAME', '{db_name}')"
    )
    content = content.replace(
        "DB_USER = os.getenv('DB_USER')",
        f"DB_USER = os.getenv('DB_USER', '{db_user}')"
    )
    content = content.replace(
        "DB_PASSWORD = os.getenv('DB_PASSWORD')",
        f"DB_PASSWORD = os.getenv('DB_PASSWORD', '{db_password}')"
    )
    content = content.replace(
        "DB_HOST = os.getenv('DB_HOST')",
        f"DB_HOST = os.getenv('DB_HOST', '{db_host}')"
    )
    
    # Write updated settings
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Database configuration updated in {settings_file}")
    
    # Set environment variables for current session
    os.environ['DB_NAME'] = db_name
    os.environ['DB_USER'] = db_user
    os.environ['DB_PASSWORD'] = db_password
    os.environ['DB_HOST'] = db_host
    os.environ['DB_PORT'] = '5432'
    
    print("\n🚀 Database configuration completed!")
    print("\n📋 Next steps:")
    print("1. Test the database connection:")
    print("   python3 test_db_connection.py")
    print("2. Run database migrations:")
    print("   DJANGO_SETTINGS_MODULE=richesreach.settings_aws python3 manage.py migrate")
    print("3. Start the production server:")
    print("   python3 aws_production_server.py")
    
    return True

if __name__ == "__main__":
    configure_aws_database()

