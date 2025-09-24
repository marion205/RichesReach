#!/usr/bin/env python3
"""
Create a simple test user by directly inserting into the database
"""
import sqlite3
import hashlib
import os

def create_test_user():
    """Create a test user directly in the database"""
    db_path = '/Users/marioncollins/RichesReach/backend/db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if core_user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_user'")
    if not cursor.fetchone():
        print("❌ core_user table not found")
        conn.close()
        return False
    
    # Get table schema
    cursor.execute("PRAGMA table_info(core_user)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Available columns: {columns}")
    
    # Check if user already exists
    cursor.execute("SELECT id FROM core_user WHERE email = ?", ('test@example.com',))
    if cursor.fetchone():
        print("✅ Test user already exists!")
        print("Email: test@example.com")
        print("Password: testpass123")
        conn.close()
        return True
    
    # Create user with available columns
    try:
        # Hash the password (Django's default hasher)
        password = 'testpass123'
        # Simple hash for testing (not production secure)
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()
        
        # Insert user with minimal required fields
        cursor.execute("""
            INSERT INTO core_user (email, password, is_active, is_staff, is_superuser, date_joined)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ('test@example.com', hashed_password, 1, 0, 0))
        
        conn.commit()
        print("✅ Test user created successfully!")
        print("Email: test@example.com")
        print("Password: testpass123")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    create_test_user()
