#!/usr/bin/env python3
"""
Test Alpaca-Integrated GraphQL Mutations
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

from graphene.test import Client
from richesreach.schema import schema

def test_place_stock_order():
    """Test PlaceStockOrder mutation with Alpaca integration"""
    print("🔍 Testing PlaceStockOrder mutation...")
    
    client = Client(schema)
    
    # Test mutation
    mutation = '''
    mutation PlaceStockOrder($symbol: String!, $side: String!, $quantity: Int!, $orderType: String!) {
        placeStockOrder(
            symbol: $symbol
            side: $side
            quantity: $quantity
            orderType: $orderType
        ) {
            success
            message
            orderId
        }
    }
    '''
    
    variables = {
        'symbol': 'AAPL',
        'side': 'BUY',
        'quantity': 10,
        'orderType': 'MARKET'
    }
    
    try:
        result = client.execute(mutation, variables=variables)
        print(f"📊 PlaceStockOrder result: {result}")
        
        if 'errors' in result and result['errors']:
            print(f"❌ Errors: {result['errors']}")
            return False
        else:
            print("✅ PlaceStockOrder mutation executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ PlaceStockOrder test failed: {e}")
        return False

def test_execute_crypto_trade():
    """Test ExecuteCryptoTrade mutation with Alpaca integration"""
    print("🔍 Testing ExecuteCryptoTrade mutation...")
    
    client = Client(schema)
    
    # Test mutation
    mutation = '''
    mutation ExecuteCryptoTrade($symbol: String!, $tradeType: String!, $quantity: Float!, $orderType: String!) {
        executeCryptoTrade(
            symbol: $symbol
            tradeType: $tradeType
            quantity: $quantity
            orderType: $orderType
        ) {
            ok
            trade {
                id
                tradeType
                quantity
                pricePerUnit
                status
            }
            error {
                code
                message
            }
        }
    }
    '''
    
    variables = {
        'symbol': 'BTC/USD',
        'tradeType': 'BUY',
        'quantity': 0.001,
        'orderType': 'MARKET'
    }
    
    try:
        result = client.execute(mutation, variables=variables)
        print(f"📊 ExecuteCryptoTrade result: {result}")
        
        if 'errors' in result and result['errors']:
            print(f"❌ Errors: {result['errors']}")
            return False
        else:
            print("✅ ExecuteCryptoTrade mutation executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ ExecuteCryptoTrade test failed: {e}")
        return False

def test_generate_ai_recommendations():
    """Test GenerateAIRecommendations mutation with Alpaca integration"""
    print("🔍 Testing GenerateAIRecommendations mutation...")
    
    client = Client(schema)
    
    # Test mutation
    mutation = '''
    mutation GenerateAIRecommendations {
        generateAIRecommendations {
            success
            message
            recommendations {
                id
                symbol
                companyName
                recommendationType
                confidenceScore
                targetPrice
                currentPrice
                reasoning
                riskLevel
                timeHorizon
            }
        }
    }
    '''
    
    try:
        result = client.execute(mutation)
        print(f"📊 GenerateAIRecommendations result: {result}")
        
        if 'errors' in result and result['errors']:
            print(f"❌ Errors: {result['errors']}")
            return False
        else:
            print("✅ GenerateAIRecommendations mutation executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ GenerateAIRecommendations test failed: {e}")
        return False

def test_alpaca_crypto_mutations():
    """Test new Alpaca Crypto mutations"""
    print("🔍 Testing Alpaca Crypto mutations...")
    
    client = Client(schema)
    
    # Test get crypto assets
    mutation = '''
    mutation GetCryptoAssets {
        getCryptoAssets {
            success
            message
            assets {
                symbol
                name
                status
                tradable
                fractionable
            }
        }
    }
    '''
    
    try:
        result = client.execute(mutation)
        print(f"📊 GetCryptoAssets result: {result}")
        
        if 'errors' in result and result['errors']:
            print(f"❌ Errors: {result['errors']}")
            return False
        else:
            print("✅ GetCryptoAssets mutation executed successfully")
            return True
            
    except Exception as e:
        print(f"❌ GetCryptoAssets test failed: {e}")
        return False

def test_schema_introspection():
    """Test that all mutations are properly loaded in the schema"""
    print("🔍 Testing schema introspection...")
    
    client = Client(schema)
    
    introspection_query = '''
    query {
        __type(name: "Mutation") {
            fields {
                name
                description
            }
        }
    }
    '''
    
    try:
        result = client.execute(introspection_query)
        
        if 'errors' in result and result['errors']:
            print(f"❌ Introspection errors: {result['errors']}")
            return False
        
        mutations = result['data']['__type']['fields']
        mutation_names = [m['name'] for m in mutations]
        
        # Check for key mutations
        required_mutations = [
            'placeStockOrder',
            'executeCryptoTrade', 
            'generateAIRecommendations',
            'createCryptoOrder',
            'getCryptoAssets',
            'syncCryptoData'
        ]
        
        found_mutations = [name for name in required_mutations if name in mutation_names]
        
        print(f"📊 Total mutations: {len(mutations)}")
        print(f"📊 Required mutations found: {len(found_mutations)}/{len(required_mutations)}")
        
        for mutation in found_mutations:
            print(f"  ✅ {mutation}")
        
        missing_mutations = [name for name in required_mutations if name not in mutation_names]
        for mutation in missing_mutations:
            print(f"  ❌ {mutation}")
        
        return len(found_mutations) == len(required_mutations)
        
    except Exception as e:
        print(f"❌ Schema introspection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Alpaca-Integrated Mutations Tests...")
    print("=" * 60)
    
    # Test 1: Schema Introspection
    schema_test = test_schema_introspection()
    
    # Test 2: Place Stock Order
    stock_order_test = test_place_stock_order()
    
    # Test 3: Execute Crypto Trade
    crypto_trade_test = test_execute_crypto_trade()
    
    # Test 4: Generate AI Recommendations
    ai_recommendations_test = test_generate_ai_recommendations()
    
    # Test 5: Alpaca Crypto Mutations
    crypto_mutations_test = test_alpaca_crypto_mutations()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Schema Introspection: {'✅ PASS' if schema_test else '❌ FAIL'}")
    print(f"  Place Stock Order: {'✅ PASS' if stock_order_test else '❌ FAIL'}")
    print(f"  Execute Crypto Trade: {'✅ PASS' if crypto_trade_test else '❌ FAIL'}")
    print(f"  Generate AI Recommendations: {'✅ PASS' if ai_recommendations_test else '❌ FAIL'}")
    print(f"  Alpaca Crypto Mutations: {'✅ PASS' if crypto_mutations_test else '❌ FAIL'}")
    
    if all([schema_test, stock_order_test, crypto_trade_test, ai_recommendations_test, crypto_mutations_test]):
        print("\n🎉 All Alpaca-integrated mutation tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
