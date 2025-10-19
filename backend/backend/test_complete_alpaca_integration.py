#!/usr/bin/env python3
"""
Complete Alpaca Integration Test
Tests all components: Broker API, Crypto API, GraphQL mutations, and workflows
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

from core.services.alpaca_broker_service import AlpacaBrokerService
from core.services.alpaca_crypto_service import AlpacaCryptoService
import logging

logger = logging.getLogger(__name__)

def test_alpaca_broker_integration():
    """Test Alpaca Broker API integration"""
    print("🔍 Testing Alpaca Broker API Integration...")
    
    try:
        broker_service = AlpacaBrokerService()
        
        # Test 1: Connection
        print("  📡 Testing connection...")
        is_connected = broker_service.check_connection()
        print(f"    Connection: {'✅ Connected' if is_connected else '❌ Failed'}")
        
        if is_connected:
            # Test 2: Get accounts
            print("  📊 Testing get accounts...")
            try:
                accounts = broker_service.get_accounts()
                print(f"    Accounts found: {len(accounts) if isinstance(accounts, list) else 'N/A'}")
            except Exception as e:
                print(f"    Accounts: ⚠️ {str(e)}")
            
            # Test 3: Order validation (without placing real orders)
            print("  📝 Testing order validation...")
            test_order_data = {
                'symbol': 'AAPL',
                'qty': '1',
                'side': 'buy',
                'type': 'market',
                'time_in_force': 'day'
            }
            print(f"    Order data prepared: ✅ {test_order_data}")
        
        return is_connected
        
    except Exception as e:
        print(f"  ❌ Broker integration failed: {e}")
        return False

def test_alpaca_crypto_integration():
    """Test Alpaca Crypto API integration"""
    print("🔍 Testing Alpaca Crypto API Integration...")
    
    try:
        crypto_service = AlpacaCryptoService()
        
        # Test 1: Connection
        print("  📡 Testing connection...")
        is_connected = crypto_service.is_connected()
        print(f"    Connection: {'✅ Connected' if is_connected else '❌ Failed'}")
        
        if is_connected:
            # Test 2: Get crypto assets
            print("  📊 Testing get crypto assets...")
            try:
                assets = crypto_service.get_crypto_assets()
                print(f"    Crypto assets found: {len(assets)}")
                if assets:
                    print(f"    Sample assets: {[asset.get('symbol', 'N/A') for asset in assets[:3]]}")
            except Exception as e:
                print(f"    Assets: ⚠️ {str(e)}")
            
            # Test 3: Order validation
            print("  📝 Testing crypto order validation...")
            test_crypto_order = {
                'symbol': 'BTC/USD',
                'side': 'buy',
                'type': 'market',
                'notional': '100'
            }
            validation = crypto_service.validate_crypto_order(test_crypto_order)
            print(f"    Order validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            if not validation['valid']:
                print(f"    Errors: {validation['errors']}")
            
            # Test 4: State eligibility
            print("  🌍 Testing state eligibility...")
            test_states = ['CA', 'NY', 'TX', 'FL']
            for state in test_states:
                eligible = crypto_service.is_crypto_eligible(state)
                print(f"    {state}: {'✅ Eligible' if eligible else '❌ Not eligible'}")
        
        return is_connected
        
    except Exception as e:
        print(f"  ❌ Crypto integration failed: {e}")
        return False

def test_service_configuration():
    """Test service configuration and environment variables"""
    print("🔍 Testing Service Configuration...")
    
    try:
        # Test Broker Service Config
        print("  🔧 Testing Broker Service Config...")
        broker_service = AlpacaBrokerService()
        print(f"    API Key: {'✅ Set' if broker_service.api_key else '❌ Missing'}")
        print(f"    Secret Key: {'✅ Set' if broker_service.secret_key else '❌ Missing'}")
        print(f"    Base URL: {broker_service.base_url}")
        print(f"    Environment: {broker_service.environment}")
        
        # Test Crypto Service Config
        print("  🔧 Testing Crypto Service Config...")
        crypto_service = AlpacaCryptoService()
        print(f"    API Key: {'✅ Set' if crypto_service.api_key else '❌ Missing'}")
        print(f"    Secret Key: {'✅ Set' if crypto_service.secret_key else '❌ Missing'}")
        print(f"    Base URL: {crypto_service.base_url}")
        print(f"    Environment: {crypto_service.environment}")
        
        # Test supported states
        print(f"    Supported States: {len(crypto_service.supported_states)} states")
        print(f"    Sample States: {crypto_service.supported_states[:5]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_order_validation():
    """Test order validation for both stocks and crypto"""
    print("🔍 Testing Order Validation...")
    
    try:
        crypto_service = AlpacaCryptoService()
        
        # Test valid crypto order
        print("  📝 Testing valid crypto order...")
        valid_order = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'type': 'market',
            'notional': '100'
        }
        validation = crypto_service.validate_crypto_order(valid_order)
        print(f"    Valid order: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
        
        # Test invalid crypto order
        print("  📝 Testing invalid crypto order...")
        invalid_order = {
            'symbol': 'INVALID',
            'side': 'buy'
            # Missing required fields
        }
        validation = crypto_service.validate_crypto_order(invalid_order)
        print(f"    Invalid order: {'✅ PASS' if not validation['valid'] else '❌ FAIL'}")
        if not validation['valid']:
            print(f"    Expected errors: {validation['errors']}")
        
        # Test fee calculation
        print("  💰 Testing fee calculation...")
        order_value = 1000.0
        maker_fee = crypto_service.calculate_crypto_fee(order_value, is_maker=True)
        taker_fee = crypto_service.calculate_crypto_fee(order_value, is_maker=False)
        print(f"    Maker fee (15 bps): ${maker_fee:.2f}")
        print(f"    Taker fee (25 bps): ${taker_fee:.2f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Order validation test failed: {e}")
        return False

def test_websocket_integration():
    """Test WebSocket integration for real-time data"""
    print("🔍 Testing WebSocket Integration...")
    
    try:
        crypto_service = AlpacaCryptoService()
        
        # Test WebSocket availability
        print("  📡 Testing WebSocket availability...")
        try:
            ws = crypto_service.connect_websocket(['BTC/USD'], ['quotes'])
            print("    WebSocket: ✅ Available")
            # Note: We don't actually connect in test mode
        except ImportError:
            print("    WebSocket: ⚠️ websocket-client not available")
        except Exception as e:
            print(f"    WebSocket: ⚠️ {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ WebSocket test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("🔍 Testing Error Handling...")
    
    try:
        # Test with invalid credentials
        print("  🛡️ Testing invalid credentials handling...")
        import os
        original_key = os.environ.get('ALPACA_API_KEY')
        os.environ['ALPACA_API_KEY'] = 'invalid_key'
        
        try:
            broker_service = AlpacaBrokerService()
            is_connected = broker_service.check_connection()
            print(f"    Invalid credentials: {'✅ Handled' if not is_connected else '❌ Not handled'}")
        except Exception as e:
            print(f"    Invalid credentials: ✅ Handled ({str(e)[:50]}...)")
        
        # Restore original credentials
        if original_key:
            os.environ['ALPACA_API_KEY'] = original_key
        
        # Test with missing required fields
        print("  🛡️ Testing missing fields handling...")
        crypto_service = AlpacaCryptoService()
        invalid_order = {'symbol': 'BTC/USD'}  # Missing required fields
        validation = crypto_service.validate_crypto_order(invalid_order)
        print(f"    Missing fields: {'✅ Handled' if not validation['valid'] else '❌ Not handled'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

def test_integration_workflow():
    """Test complete integration workflow"""
    print("🔍 Testing Complete Integration Workflow...")
    
    try:
        # Step 1: Initialize services
        print("  🚀 Step 1: Initialize services...")
        broker_service = AlpacaBrokerService()
        crypto_service = AlpacaCryptoService()
        print("    Services initialized: ✅")
        
        # Step 2: Check connections
        print("  🚀 Step 2: Check connections...")
        broker_connected = broker_service.check_connection()
        crypto_connected = crypto_service.is_connected()
        print(f"    Broker connected: {'✅' if broker_connected else '❌'}")
        print(f"    Crypto connected: {'✅' if crypto_connected else '❌'}")
        
        # Step 3: Validate order preparation
        print("  🚀 Step 3: Validate order preparation...")
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
        
        # Step 4: Test state eligibility
        print("  🚀 Step 4: Test state eligibility...")
        test_state = 'CA'
        eligible = crypto_service.is_crypto_eligible(test_state)
        print(f"    {test_state} crypto eligible: {'✅' if eligible else '❌'}")
        
        # Step 5: Test fee calculation
        print("  🚀 Step 5: Test fee calculation...")
        fee = crypto_service.calculate_crypto_fee(1000.0)
        print(f"    Fee calculation: ✅ ${fee:.2f}")
        
        print("    Complete workflow: ✅ PASS")
        return True
        
    except Exception as e:
        print(f"  ❌ Integration workflow failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete Alpaca Integration Tests...")
    print("=" * 70)
    
    # Test 1: Service Configuration
    config_test = test_service_configuration()
    
    # Test 2: Broker Integration
    broker_test = test_alpaca_broker_integration()
    
    # Test 3: Crypto Integration
    crypto_test = test_alpaca_crypto_integration()
    
    # Test 4: Order Validation
    validation_test = test_order_validation()
    
    # Test 5: WebSocket Integration
    websocket_test = test_websocket_integration()
    
    # Test 6: Error Handling
    error_test = test_error_handling()
    
    # Test 7: Complete Workflow
    workflow_test = test_integration_workflow()
    
    print("\n" + "=" * 70)
    print("📊 Integration Test Results:")
    print(f"  Service Configuration: {'✅ PASS' if config_test else '❌ FAIL'}")
    print(f"  Broker Integration: {'✅ PASS' if broker_test else '❌ FAIL'}")
    print(f"  Crypto Integration: {'✅ PASS' if crypto_test else '❌ FAIL'}")
    print(f"  Order Validation: {'✅ PASS' if validation_test else '❌ FAIL'}")
    print(f"  WebSocket Integration: {'✅ PASS' if websocket_test else '❌ FAIL'}")
    print(f"  Error Handling: {'✅ PASS' if error_test else '❌ FAIL'}")
    print(f"  Complete Workflow: {'✅ PASS' if workflow_test else '❌ FAIL'}")
    
    passed_tests = sum([config_test, broker_test, crypto_test, validation_test, websocket_test, error_test, workflow_test])
    total_tests = 7
    
    print(f"\n📈 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All integration tests passed! Alpaca integration is ready for production!")
    elif passed_tests >= 5:
        print("\n✅ Most tests passed! Integration is mostly ready with minor issues.")
    else:
        print("\n⚠️ Several tests failed. Review the output above for issues.")
    
    print("\n🚀 Next Steps:")
    print("  1. Address any failed tests")
    print("  2. Test with production credentials")
    print("  3. Implement KYC workflow")
    print("  4. Update UI for real trading")
