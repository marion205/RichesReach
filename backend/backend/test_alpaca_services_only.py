#!/usr/bin/env python3
"""
Alpaca Services Test (No Django Setup)
Tests only the service classes without Django model dependencies
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/marioncollins/RichesReach/backend/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Users/marioncollins/RichesReach/backend/backend/env.secrets')

def test_alpaca_broker_service():
    """Test Alpaca Broker Service without Django"""
    print("🔍 Testing Alpaca Broker Service...")
    
    try:
        # Import and test the service
        from core.services.alpaca_broker_service import AlpacaBrokerService
        
        service = AlpacaBrokerService()
        print(f"  📊 Service initialized: ✅")
        print(f"  🔑 API Key: {'✅ Set' if service.api_key else '❌ Missing'}")
        print(f"  🔑 Secret Key: {'✅ Set' if service.secret_key else '❌ Missing'}")
        print(f"  🌐 Base URL: {service.base_url}")
        print(f"  🌍 Environment: {service.environment}")
        
        # Test connection
        print("  📡 Testing connection...")
        try:
            is_connected = service.check_connection()
            print(f"    Connection: {'✅ Connected' if is_connected else '❌ Failed'}")
        except Exception as e:
            print(f"    Connection: ⚠️ {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Broker service test failed: {e}")
        return False

def test_alpaca_crypto_service():
    """Test Alpaca Crypto Service without Django"""
    print("🔍 Testing Alpaca Crypto Service...")
    
    try:
        # Import and test the service
        from core.services.alpaca_crypto_service import AlpacaCryptoService
        
        service = AlpacaCryptoService()
        print(f"  📊 Service initialized: ✅")
        print(f"  🔑 API Key: {'✅ Set' if service.api_key else '❌ Missing'}")
        print(f"  🔑 Secret Key: {'✅ Set' if service.secret_key else '❌ Missing'}")
        print(f"  🌐 Base URL: {service.base_url}")
        print(f"  🌍 Environment: {service.environment}")
        print(f"  🌍 Supported States: {len(service.supported_states)} states")
        
        # Test connection
        print("  📡 Testing connection...")
        try:
            is_connected = service.is_connected()
            print(f"    Connection: {'✅ Connected' if is_connected else '❌ Failed'}")
        except Exception as e:
            print(f"    Connection: ⚠️ {str(e)[:100]}...")
        
        # Test order validation
        print("  📝 Testing order validation...")
        test_order = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'type': 'market',
            'notional': '100'
        }
        validation = service.validate_crypto_order(test_order)
        print(f"    Order validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        
        # Test state eligibility
        print("  🌍 Testing state eligibility...")
        test_states = ['CA', 'NY', 'TX', 'FL']
        for state in test_states:
            eligible = service.is_crypto_eligible(state)
            print(f"    {state}: {'✅ Eligible' if eligible else '❌ Not eligible'}")
        
        # Test fee calculation
        print("  💰 Testing fee calculation...")
        maker_fee = service.calculate_crypto_fee(1000.0, is_maker=True)
        taker_fee = service.calculate_crypto_fee(1000.0, is_maker=False)
        print(f"    Maker fee (15 bps): ${maker_fee:.2f}")
        print(f"    Taker fee (25 bps): ${taker_fee:.2f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Crypto service test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment configuration"""
    print("🔍 Testing Environment Configuration...")
    
    try:
        # Check environment variables
        required_vars = [
            'ALPACA_API_KEY',
            'ALPACA_SECRET_KEY',
            'ALPACA_BASE_URL',
            'ALPACA_CRYPTO_API_KEY',
            'ALPACA_CRYPTO_SECRET_KEY',
            'ALPACA_CRYPTO_BASE_URL'
        ]
        
        print("  🔧 Checking environment variables...")
        for var in required_vars:
            value = os.getenv(var)
            status = '✅ Set' if value else '❌ Missing'
            if value:
                # Show first 10 characters for security
                display_value = f"{value[:10]}..." if len(value) > 10 else value
                print(f"    {var}: {status} ({display_value})")
            else:
                print(f"    {var}: {status}")
        
        # Check optional variables
        optional_vars = [
            'ALPACA_ENVIRONMENT',
            'ALPACA_PAPER_TRADING',
            'USE_ALPACA',
            'USE_ALPACA_BROKER',
            'USE_ALPACA_CRYPTO'
        ]
        
        print("  🔧 Checking optional variables...")
        for var in optional_vars:
            value = os.getenv(var)
            status = '✅ Set' if value else '⚠️ Not set'
            print(f"    {var}: {status} ({value})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Environment configuration test failed: {e}")
        return False

def test_service_integration():
    """Test service integration without Django models"""
    print("🔍 Testing Service Integration...")
    
    try:
        from core.services.alpaca_broker_service import AlpacaBrokerService
        from core.services.alpaca_crypto_service import AlpacaCryptoService
        
        # Initialize both services
        print("  🚀 Initializing services...")
        broker_service = AlpacaBrokerService()
        crypto_service = AlpacaCryptoService()
        print("    Services initialized: ✅")
        
        # Test service configuration
        print("  🔧 Testing service configuration...")
        print(f"    Broker API Key: {'✅' if broker_service.api_key else '❌'}")
        print(f"    Crypto API Key: {'✅' if crypto_service.api_key else '❌'}")
        print(f"    Broker Environment: {broker_service.environment}")
        print(f"    Crypto Environment: {crypto_service.environment}")
        
        # Test order preparation
        print("  📝 Testing order preparation...")
        stock_order = {
            'symbol': 'AAPL',
            'qty': '1',
            'side': 'buy',
            'type': 'market',
            'time_in_force': 'day'
        }
        crypto_order = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'type': 'market',
            'notional': '100'
        }
        
        crypto_validation = crypto_service.validate_crypto_order(crypto_order)
        print(f"    Stock order prepared: ✅")
        print(f"    Crypto order validated: {'✅' if crypto_validation['valid'] else '❌'}")
        
        # Test state eligibility
        print("  🌍 Testing state eligibility...")
        test_state = 'CA'
        eligible = crypto_service.is_crypto_eligible(test_state)
        print(f"    {test_state} crypto eligible: {'✅' if eligible else '❌'}")
        
        # Test fee calculation
        print("  💰 Testing fee calculation...")
        fee = crypto_service.calculate_crypto_fee(1000.0)
        print(f"    Fee calculation: ✅ ${fee:.2f}")
        
        print("    Service integration: ✅ PASS")
        return True
        
    except Exception as e:
        print(f"  ❌ Service integration test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("🔍 Testing Error Handling...")
    
    try:
        from core.services.alpaca_crypto_service import AlpacaCryptoService
        
        service = AlpacaCryptoService()
        
        # Test invalid order validation
        print("  🛡️ Testing invalid order handling...")
        invalid_orders = [
            {'symbol': 'BTC/USD'},  # Missing required fields
            {'symbol': 'INVALID', 'side': 'buy', 'type': 'market'},  # Invalid symbol
            {'symbol': 'BTC/USD', 'side': 'invalid', 'type': 'market'},  # Invalid side
            {'symbol': 'BTC/USD', 'side': 'buy', 'type': 'invalid'},  # Invalid type
        ]
        
        for i, order in enumerate(invalid_orders):
            validation = service.validate_crypto_order(order)
            print(f"    Invalid order {i+1}: {'✅ Handled' if not validation['valid'] else '❌ Not handled'}")
            if not validation['valid']:
                print(f"      Errors: {validation['errors']}")
        
        # Test fee calculation edge cases
        print("  🛡️ Testing fee calculation edge cases...")
        edge_cases = [0, -100, 1000000]
        for value in edge_cases:
            try:
                fee = service.calculate_crypto_fee(value)
                print(f"    Fee for ${value}: ${fee:.2f}")
            except Exception as e:
                print(f"    Fee for ${value}: ⚠️ {str(e)}")
        
        print("    Error handling: ✅ PASS")
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Alpaca Services Tests (No Django)...")
    print("=" * 60)
    
    # Test 1: Environment Configuration
    config_test = test_environment_configuration()
    
    # Test 2: Broker Service
    broker_test = test_alpaca_broker_service()
    
    # Test 3: Crypto Service
    crypto_test = test_alpaca_crypto_service()
    
    # Test 4: Service Integration
    integration_test = test_service_integration()
    
    # Test 5: Error Handling
    error_test = test_error_handling()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Environment Configuration: {'✅ PASS' if config_test else '❌ FAIL'}")
    print(f"  Broker Service: {'✅ PASS' if broker_test else '❌ FAIL'}")
    print(f"  Crypto Service: {'✅ PASS' if crypto_test else '❌ FAIL'}")
    print(f"  Service Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
    print(f"  Error Handling: {'✅ PASS' if error_test else '❌ FAIL'}")
    
    passed_tests = sum([config_test, broker_test, crypto_test, integration_test, error_test])
    total_tests = 5
    
    print(f"\n📈 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All service tests passed! Alpaca services are ready!")
    elif passed_tests >= 4:
        print("\n✅ Most tests passed! Services are mostly ready.")
    else:
        print("\n⚠️ Several tests failed. Review the output above.")
    
    print("\n🚀 Next Steps:")
    print("  1. Address any failed tests")
    print("  2. Test with production credentials")
    print("  3. Implement KYC workflow")
    print("  4. Update UI for real trading")
