#!/usr/bin/env python3
"""
Test Alpaca Crypto Integration
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

from core.services.alpaca_crypto_service import AlpacaCryptoService

def test_alpaca_crypto_service():
    """Test the Alpaca Crypto Service"""
    print("🔍 Testing Alpaca Crypto Service...")
    
    try:
        # Initialize the service
        crypto_service = AlpacaCryptoService()
        
        # Test connection
        print("🔍 Testing connection...")
        is_connected = crypto_service.is_connected()
        print(f"📊 Connection status: {'✅ Connected' if is_connected else '❌ Not connected'}")
        
        if is_connected:
            # Test getting crypto assets
            print("🔍 Testing get crypto assets...")
            assets = crypto_service.get_crypto_assets()
            print(f"📊 Crypto assets found: {len(assets)}")
            
            if assets:
                # Show first few assets
                print("📈 Available crypto pairs:")
                for asset in assets[:10]:  # Show first 10
                    symbol = asset.get('symbol', 'N/A')
                    tradable = asset.get('tradable', False)
                    print(f"  - {symbol} (Tradable: {'✅' if tradable else '❌'})")
                
                # Test getting crypto account
                print("🔍 Testing get crypto account...")
                account = crypto_service.get_crypto_account()
                print(f"📊 Crypto account retrieved: {bool(account)}")
                
                # Test getting positions
                print("🔍 Testing get crypto positions...")
                positions = crypto_service.get_crypto_positions()
                print(f"📊 Crypto positions found: {len(positions)}")
                
                # Test getting orders
                print("🔍 Testing get crypto orders...")
                orders = crypto_service.get_crypto_orders()
                print(f"📊 Crypto orders found: {len(orders)}")
                
                # Test getting activities
                print("🔍 Testing get crypto activities...")
                activities = crypto_service.get_crypto_activities()
                print(f"📊 Crypto activities found: {len(activities)}")
                
                # Test state eligibility
                print("🔍 Testing state eligibility...")
                test_states = ['CA', 'NY', 'TX', 'FL']
                for state in test_states:
                    eligible = crypto_service.is_crypto_eligible(state)
                    print(f"  - {state}: {'✅ Eligible' if eligible else '❌ Not eligible'}")
                
                # Test supported pairs
                print("🔍 Testing supported crypto pairs...")
                pairs = crypto_service.get_supported_crypto_pairs()
                print(f"📊 Supported pairs: {len(pairs)}")
                if pairs:
                    print("📈 Sample pairs:")
                    for pair in pairs[:5]:  # Show first 5
                        print(f"  - {pair}")
        
        print("✅ Alpaca Crypto Service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Alpaca Crypto Service test failed: {e}")
        return False

def test_crypto_order_validation():
    """Test crypto order validation"""
    print("\n🔍 Testing Crypto Order Validation...")
    
    try:
        crypto_service = AlpacaCryptoService()
        
        # Test valid order
        valid_order = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'type': 'market',
            'notional': '100'
        }
        
        validation = crypto_service.validate_crypto_order(valid_order)
        print(f"📊 Valid order test: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
        if not validation['valid']:
            print(f"  Errors: {validation['errors']}")
        
        # Test invalid order (missing required field)
        invalid_order = {
            'symbol': 'BTC/USD',
            'side': 'buy'
            # Missing 'type' field
        }
        
        validation = crypto_service.validate_crypto_order(invalid_order)
        print(f"📊 Invalid order test: {'✅ PASS' if not validation['valid'] else '❌ FAIL'}")
        if not validation['valid']:
            print(f"  Errors: {validation['errors']}")
        
        # Test fee calculation
        print("🔍 Testing fee calculation...")
        order_value = 1000.0
        maker_fee = crypto_service.calculate_crypto_fee(order_value, is_maker=True)
        taker_fee = crypto_service.calculate_crypto_fee(order_value, is_maker=False)
        print(f"📊 Maker fee (15 bps): ${maker_fee:.2f}")
        print(f"📊 Taker fee (25 bps): ${taker_fee:.2f}")
        
        print("✅ Crypto order validation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Crypto order validation test failed: {e}")
        return False

def test_crypto_graphql_schema():
    """Test that Crypto GraphQL mutations are properly loaded"""
    print("\n🔍 Testing Crypto GraphQL Schema...")
    
    try:
        from richesreach.schema import schema
        from graphene.test import Client
        
        # Create GraphQL client
        client = Client(schema)
        
        # Test introspection for Crypto mutations
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
        crypto_mutations = [m for m in mutations if 'crypto' in m['name'].lower()]
        
        print(f"📊 Total mutations: {len(mutations)}")
        print(f"📊 Crypto mutations: {len(crypto_mutations)}")
        
        if crypto_mutations:
            print("✅ Crypto mutations found:")
            for mutation in crypto_mutations:
                print(f"  - {mutation['name']}")
        else:
            print("⚠️ No Crypto mutations found")
        
        print("✅ Crypto GraphQL schema test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Crypto GraphQL schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Alpaca Crypto Integration Tests...")
    print("=" * 60)
    
    # Test 1: Crypto Service
    crypto_test = test_alpaca_crypto_service()
    
    # Test 2: Order Validation
    validation_test = test_crypto_order_validation()
    
    # Test 3: GraphQL Schema
    schema_test = test_crypto_graphql_schema()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Crypto Service: {'✅ PASS' if crypto_test else '❌ FAIL'}")
    print(f"  Order Validation: {'✅ PASS' if validation_test else '❌ FAIL'}")
    print(f"  GraphQL Schema: {'✅ PASS' if schema_test else '❌ FAIL'}")
    
    if crypto_test and validation_test and schema_test:
        print("\n🎉 All Alpaca Crypto integration tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
