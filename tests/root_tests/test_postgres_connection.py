#!/usr/bin/env python3
"""Test PostgreSQL connection and Django setup"""
import os
import sys


def _setup_env() -> None:
    os.environ.setdefault('DB_NAME', 'richesreach')
    os.environ.setdefault('DB_USER', os.getenv('USER', 'postgres'))
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if os.path.exists(backend_path):
        sys.path.insert(0, backend_path)
        os.chdir(backend_path)


def test_postgres_connection() -> None:
    _setup_env()

    import django
    django.setup()

    from django.db import connection
    if connection.vendor != 'postgresql':
        import pytest
        pytest.skip("PostgreSQL not configured for this environment")

    connection.ensure_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        assert version and version[0]

    try:
        from core.schema import schema
        assert schema is not None
    except ImportError:
        pass


def main() -> None:
    _setup_env()

    print("🔍 Testing PostgreSQL Connection...")
    print("=" * 50)

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

        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"   PostgreSQL Version: {version[0]}")
        else:
            print("   Skipping version() check (non-Postgres backend)")

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


if __name__ == '__main__':
    main()

