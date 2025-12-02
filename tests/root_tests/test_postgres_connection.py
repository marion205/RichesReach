#!/usr/bin/env python3
"""Test PostgreSQL connection and Django setup"""
import os
import sys

# Set environment variables
os.environ.setdefault('DB_NAME', 'richesreach')
os.environ.setdefault('DB_USER', os.getenv('USER', 'postgres'))
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

print("🔍 Testing PostgreSQL Connection...")
print("=" * 50)

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
if os.path.exists(backend_path):
    sys.path.insert(0, backend_path)
    os.chdir(backend_path)

try:
    import django
    django.setup()
    print("✅ Django initialized successfully")
    
    from django.db import connection
    connection.ensure_connection()
    db_info = connection.get_connection_params()
    
    print(f"✅ Database Connection Successful!")
    print(f"   Database: {db_info.get('database', 'unknown')}")
    print(f"   Host: {db_info.get('host', 'unknown')}")
    print(f"   Port: {db_info.get('port', 'unknown')}")
    print(f"   User: {db_info.get('user', 'unknown')}")
    
    # Test a simple query
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   PostgreSQL Version: {version[0]}")
    
    # Try to import GraphQL schema
    try:
        from core.schema import schema
        print("✅ GraphQL schema imported successfully")
        print(f"   Schema type: {type(schema)}")
    except ImportError as e:
        print(f"⚠️  Could not import GraphQL schema: {e}")
        print("   This is okay if schema.py doesn't exist yet")
    
    print("\n✅ All tests passed! Server is ready to use PostgreSQL.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

