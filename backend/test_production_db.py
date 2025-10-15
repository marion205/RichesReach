#!/usr/bin/env python3
"""
Test Production Database Connection
"""
import os
import psycopg2
from urllib.parse import urlparse

def test_production_db():
    """Test production database connection"""
    print("🔍 Testing Production Database Connection...")
    
    # Production database URL from your secret file
    db_url = "postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres"
    
    try:
        # Parse the database URL
        parsed = urlparse(db_url)
        
        print(f"Host: {parsed.hostname}")
        print(f"Port: {parsed.port}")
        print(f"Database: {parsed.path[1:]}")
        print(f"User: {parsed.username}")
        
        # Test connection
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Test table access
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables in database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_production_db()
    exit(0 if success else 1)
