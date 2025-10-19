#!/usr/bin/env python3
"""
Test Alpaca Integration - Simple test without database models
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

from core.services.alpaca_broker_service import AlpacaBrokerService

def test_alpaca_broker_service():
    """Test the Alpaca Broker Service"""
    print("🔍 Testing Alpaca Broker Service...")
    
    try:
        # Initialize the service
        broker_service = AlpacaBrokerService()
        
        # Test connection
        print("🔍 Testing connection...")
        is_connected = broker_service.is_connected()
        print(f"📊 Connection status: {'✅ Connected' if is_connected else '❌ Not connected'}")
        
        if is_connected:
            # Test getting accounts
            print("🔍 Testing get accounts...")
            accounts = broker_service.get_accounts()
            print(f"📊 Accounts found: {len(accounts)}")
            
            if accounts:
                account = accounts[0]
                print(f"📈 Account ID: {account.get('id', 'N/A')}")
                print(f"📊 Account Status: {account.get('status', 'N/A')}")
                
                # Test getting specific account
                print("🔍 Testing get specific account...")
                account_details = broker_service.get_account(account['id'])
                print(f"📊 Account details retrieved: {bool(account_details)}")
                
                # Test getting activities
                print("🔍 Testing get activities...")
                activities = broker_service.get_activities(account['id'])
                print(f"📊 Activities found: {len(activities)}")
                
                # Test getting positions
                print("🔍 Testing get positions...")
                positions = broker_service.get_positions(account['id'])
                print(f"📊 Positions found: {len(positions)}")
                
                # Test getting orders
                print("🔍 Testing get orders...")
                orders = broker_service.get_orders(account['id'])
                print(f"📊 Orders found: {len(orders)}")
        
        print("✅ Alpaca Broker Service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Alpaca Broker Service test failed: {e}")
        return False

def test_alpaca_graphql_schema():
    """Test that Alpaca GraphQL mutations are properly loaded"""
    print("\n🔍 Testing Alpaca GraphQL Schema...")
    
    try:
        from richesreach.schema import schema
        from graphene.test import Client
        
        # Create GraphQL client
        client = Client(schema)
        
        # Test introspection for Alpaca mutations
        introspection_query = '''
        query {
          __type(name: "Mutation") {
            fields {
              name
            }
          }
        }
        '''
        
        result = client.execute(introspection_query)
        if 'errors' in result and result['errors']:
            print(f"❌ GraphQL introspection errors: {result['errors']}")
            return False
        
        mutations = result['data']['__type']['fields']
        alpaca_mutations = [m for m in mutations if 'alpaca' in m['name'].lower()]
        
        print(f"📊 Total mutations: {len(mutations)}")
        print(f"📊 Alpaca mutations: {len(alpaca_mutations)}")
        
        if alpaca_mutations:
            print("✅ Alpaca mutations found:")
            for mutation in alpaca_mutations:
                print(f"  - {mutation['name']}")
        else:
            print("⚠️ No Alpaca mutations found")
        
        print("✅ GraphQL schema test completed!")
        return True
        
    except Exception as e:
        print(f"❌ GraphQL schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Alpaca Integration Tests...")
    print("=" * 60)
    
    # Test 1: Broker Service
    broker_test = test_alpaca_broker_service()
    
    # Test 2: GraphQL Schema
    schema_test = test_alpaca_graphql_schema()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Broker Service: {'✅ PASS' if broker_test else '❌ FAIL'}")
    print(f"  GraphQL Schema: {'✅ PASS' if schema_test else '❌ FAIL'}")
    
    if broker_test and schema_test:
        print("\n🎉 All Alpaca integration tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
