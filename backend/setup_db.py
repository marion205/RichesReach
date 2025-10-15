#!/usr/bin/env python3
"""
Database setup script to create appuser and appdb
"""
import psycopg2
import sys
import os

def setup_database():
    # Connect as master user
    master_conn = psycopg2.connect(
        host="riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com",
        port=5432,
        user="richesreach",
        password="@Master22",
        sslmode="require"
    )
    
    master_conn.autocommit = True
    cursor = master_conn.cursor()
    
    try:
        # Create appuser role if it doesn't exist
        cursor.execute("""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'appuser') THEN
                CREATE ROLE appuser LOGIN PASSWORD 'AppUser2025Secure!';
              END IF;
            END$$;
        """)
        print("✅ Created appuser role")
        
        # Create appdb database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'appdb'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE appdb OWNER appuser TEMPLATE template1")
            print("✅ Created appdb database")
        else:
            print("✅ appdb database already exists")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser")
        print("✅ Granted privileges on appdb to appuser")
        
        # Test connection as appuser
        test_conn = psycopg2.connect(
            host="riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com",
            port=5432,
            user="appuser",
            password="AppUser2025Secure!",
            database="appdb",
            sslmode="require"
        )
        
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT version()")
        version = test_cursor.fetchone()[0]
        print(f"✅ Successfully connected as appuser: {version}")
        
        # Set up schema permissions
        test_cursor.execute("GRANT ALL ON SCHEMA public TO appuser")
        test_cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appuser")
        test_cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appuser")
        print("✅ Set up schema permissions")
        
        test_conn.close()
        print("🎉 Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        master_conn.close()

if __name__ == "__main__":
    setup_database()
