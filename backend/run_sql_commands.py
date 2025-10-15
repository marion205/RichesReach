#!/usr/bin/env python3
"""
Script to run SQL commands to create appuser and appdb
"""
import psycopg2
import os
import sys

def run_sql_commands():
    try:
        # Connect as master user to create appuser and appdb
        print("Connecting to RDS as master user...")
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            database='postgres',  # Connect to postgres database first
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to RDS successfully")
        
        # SQL 1: Create/sync appuser role
        print("Running SQL 1: Create/sync appuser role...")
        cursor.execute("""
            DO $$ 
            BEGIN 
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='appuser') THEN 
                CREATE ROLE appuser LOGIN PASSWORD 'AppPass2025Simple';
              ELSE 
                ALTER ROLE appuser WITH LOGIN PASSWORD 'AppPass2025Simple';
              END IF; 
              ALTER ROLE appuser SET search_path = public;
            END $$;
        """)
        print("✅ SQL 1 completed: appuser role created/updated")
        
        # SQL 2: Create appdb database
        print("Running SQL 2: Create appdb database...")
        cursor.execute("""
            DO $$ BEGIN 
              IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='appdb') THEN 
                CREATE DATABASE "appdb" OWNER appuser; 
              END IF; 
            END $$;
        """)
        print("✅ SQL 2 completed: appdb database created")
        
        # Close connection to postgres
        conn.close()
        
        # SQL 3: Connect to appdb and grant permissions
        print("Running SQL 3: Grant permissions on appdb...")
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            database='appdb',  # Connect to appdb
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("""
            ALTER SCHEMA public OWNER TO appuser;
            GRANT CONNECT ON DATABASE appdb TO appuser;
            GRANT USAGE, CREATE ON SCHEMA public TO appuser;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appuser;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appuser;
            REVOKE CREATE ON SCHEMA public FROM PUBLIC;
        """)
        print("✅ SQL 3 completed: Permissions granted on appdb")
        
        # Test connection as appuser
        print("Testing connection as appuser...")
        conn.close()
        test_conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT'),
            user='appuser',
            password='AppPass2025Simple',
            database='appdb',
            sslmode='require'
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT current_user, current_database()")
        result = test_cursor.fetchone()
        print(f"✅ Test connection successful: {result}")
        test_conn.close()
        
        print("\n🎉 All SQL commands completed successfully!")
        print("The appuser and appdb are now ready for the application.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_sql_commands()
