#!/usr/bin/env python3
"""
Test SBLOC GraphQL Queries and Mutations (Local SQLite)
This script uses SQLite for local testing without requiring production database access
"""
import os
import sys
import django
from pathlib import Path

# Setup Django with SQLite for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

# Temporarily use SQLite for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
os.environ['DB_NAME'] = ''  # Force SQLite fallback

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from core.sbloc_models import SBLOCBank, SBLOCSession
from core.schema import schema
from graphql import graphql_sync

User = get_user_model()

def setup_test_database():
    """Create SBLOC tables if they don't exist (for SQLite testing)"""
    with connection.cursor() as cursor:
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sbloc_banks'")
        if not cursor.fetchone():
            print("Creating SBLOC tables...")
            # Create sbloc_banks table
            cursor.execute("""
                CREATE TABLE sbloc_banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id VARCHAR(255) UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    logo_url VARCHAR(500),
                    min_apr DECIMAL(5,4),
                    max_apr DECIMAL(5,4),
                    min_ltv DECIMAL(5,4),
                    max_ltv DECIMAL(5,4),
                    notes TEXT,
                    regions TEXT NOT NULL DEFAULT '[]',
                    min_loan_usd INTEGER,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    priority INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            
            # Create sbloc_sessions table
            cursor.execute("""
                CREATE TABLE sbloc_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    bank_id INTEGER NOT NULL,
                    amount_usd INTEGER NOT NULL,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    application_url VARCHAR(500),
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    aggregator_response TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES core_user (id),
                    FOREIGN KEY (bank_id) REFERENCES sbloc_banks (id)
                )
            """)
            print("✅ SBLOC tables created")


def test_sbloc_banks_query():
    """Test sblocBanks GraphQL query"""
    print("\n" + "="*60)
    print("Testing sblocBanks Query")
    print("="*60)
    
    # Create a test user
    user, created = User.objects.get_or_create(
        email='test@richesreach.com',
        defaults={'name': 'Test User'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create some test banks
    bank1, _ = SBLOCBank.objects.get_or_create(
        name='Test Bank 1',
        defaults={
            'min_apr': 0.05,
            'max_apr': 0.08,
            'min_ltv': 0.5,
            'max_ltv': 0.7,
            'min_loan_usd': 10000,
            'is_active': True,
            'priority': 1,
        }
    )
    
    bank2, _ = SBLOCBank.objects.get_or_create(
        name='Test Bank 2',
        defaults={
            'min_apr': 0.06,
            'max_apr': 0.09,
            'min_ltv': 0.6,
            'max_ltv': 0.75,
            'min_loan_usd': 25000,
            'is_active': True,
            'priority': 2,
        }
    )
    
    print(f"Created test banks: {bank1.name}, {bank2.name}")
    
    # Test query
    query = """
    query {
        sblocBanks {
            id
            name
            logoUrl
            minApr
            maxApr
            minLtv
            maxLtv
            minLoanUsd
        }
    }
    """
    
    # Create a mock context with user
    class MockContext:
        def __init__(self, user):
            self.user = user
    
    context = MockContext(user)
    
    try:
        result = graphql_sync(schema, query, context_value=context)
        
        if result.errors:
            print(f"❌ Query errors: {result.errors}")
            return False
        
        print("✅ Query executed successfully")
        banks = result.data.get('sblocBanks', [])
        print(f"Banks returned: {len(banks)}")
        
        for bank in banks:
            print(f"  - {bank.get('name')}: APR {bank.get('minApr')}-{bank.get('maxApr')}, LTV {bank.get('minLtv')}-{bank.get('maxLtv')}")
        
        return True
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_sbloc_session_mutation():
    """Test createSblocSession GraphQL mutation"""
    print("\n" + "="*60)
    print("Testing createSblocSession Mutation")
    print("="*60)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='test@richesreach.com',
        defaults={'name': 'Test User'}
    )
    
    # Get a test bank
    bank = SBLOCBank.objects.filter(is_active=True).first()
    if not bank:
        print("❌ No active banks found. Creating one...")
        bank = SBLOCBank.objects.create(
            name='Test Bank',
            min_apr=0.05,
            max_apr=0.08,
            min_ltv=0.5,
            max_ltv=0.7,
            min_loan_usd=10000,
            is_active=True
        )
    
    print(f"Using bank: {bank.name} (ID: {bank.id})")
    
    # Test mutation
    mutation = """
    mutation CreateSession($bankId: ID!, $amountUsd: Int!) {
        createSblocSession(bankId: $bankId, amountUsd: $amountUsd) {
            success
            sessionId
            applicationUrl
            error
        }
    }
    """
    
    variables = {
        'bankId': str(bank.id),
        'amountUsd': 50000
    }
    
    # Create a mock context with user
    class MockContext:
        def __init__(self, user):
            self.user = user
    
    context = MockContext(user)
    
    try:
        result = graphql_sync(schema, mutation, variable_values=variables, context_value=context)
        
        if result.errors:
            print(f"❌ Mutation errors: {result.errors}")
            return False
        
        data = result.data.get('createSblocSession', {})
        
        if data.get('success'):
            print("✅ Mutation executed successfully")
            print(f"  Session ID: {data.get('sessionId')}")
            print(f"  Application URL: {data.get('applicationUrl')}")
            
            # Verify session was created in database
            session = SBLOCSession.objects.filter(session_id=data.get('sessionId')).first()
            if session:
                print(f"  ✅ Session saved to database: {session.id}")
            else:
                print(f"  ⚠️  Session not found in database")
        else:
            print(f"❌ Mutation failed: {data.get('error')}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error executing mutation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SBLOC GraphQL Tests (Local SQLite)")
    print("="*60)
    
    # Setup test database
    setup_test_database()
    
    # Test 1: Query
    test1_result = test_sbloc_banks_query()
    
    # Test 2: Mutation
    test2_result = test_create_sbloc_session_mutation()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"sblocBanks Query: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"createSblocSession Mutation: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed!")
        print("\n📝 Next Steps:")
        print("   1. Test via GraphQL endpoint: http://localhost:8000/graphql/")
        print("   2. See SBLOC_GRAPHQL_TEST_QUERIES.md for example queries")
        print("   3. Run migration on production database when accessible")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

