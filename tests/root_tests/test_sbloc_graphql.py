#!/usr/bin/env python3
"""
Test SBLOC GraphQL Queries and Mutations
Run this script to test SBLOC GraphQL functionality
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.sbloc_models import SBLOCBank, SBLOCSession
from core.schema import schema
from graphql import graphql_sync

User = get_user_model()

def test_sbloc_banks_query():
    """Test sblocBanks GraphQL query"""
    print("\n" + "="*60)
    print("Testing sblocBanks Query")
    print("="*60)
    
    # Create a test user
    user, created = User.objects.get_or_create(
        email='test@richesreach.com',
        defaults={'name': 'Test User', 'password': 'testpass123'}
    )
    
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
            notes
            regions
        }
    }
    """
    
    # Create a mock context with user
    class MockContext:
        def __init__(self, user):
            self.user = user
    
    context = MockContext(user)
    
    result = graphql_sync(schema, query, context_value=context)
    
    if result.errors:
        print(f"❌ Query errors: {result.errors}")
        return False
    
    print("✅ Query executed successfully")
    print(f"Banks returned: {len(result.data.get('sblocBanks', []))}")
    
    for bank in result.data.get('sblocBanks', []):
        print(f"  - {bank.get('name')}: APR {bank.get('minApr')}-{bank.get('maxApr')}, LTV {bank.get('minLtv')}-{bank.get('maxLtv')}")
    
    return True


def test_create_sbloc_session_mutation():
    """Test createSblocSession GraphQL mutation"""
    print("\n" + "="*60)
    print("Testing createSblocSession Mutation")
    print("="*60)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='test@richesreach.com',
        defaults={'name': 'Test User', 'password': 'testpass123'}
    )
    
    # Get a test bank
    bank = SBLOCBank.objects.filter(is_active=True).first()
    if not bank:
        print("❌ No active banks found. Please create banks first.")
        return False
    
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


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SBLOC GraphQL Tests")
    print("="*60)
    
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
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

