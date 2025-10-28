#!/usr/bin/env python3
"""
RichesReach API Endpoint Test Report - Simplified
================================================

Quick test report for all new RichesReach endpoints.
"""

import requests
import json
import time
from datetime import datetime

def test_endpoints():
    """Test all RichesReach endpoints and generate report"""
    base_url = "http://localhost:8001"
    session = requests.Session()
    results = []
    
    print("🚀 RichesReach API Endpoint Test Report")
    print("=" * 50)
    
    # Test server connectivity
    try:
        response = session.get(f"{base_url}/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Define test cases
    test_cases = [
        # Pump.fun Integration
        ("POST", "/api/pump-fun/launch/", {
            "name": "TestFrog", "symbol": "TFROG", "description": "Test meme",
            "template": "wealth-frog", "cultural_theme": "BIPOC Wealth Building"
        }, 201, "Launch meme coin"),
        
        ("GET", "/api/pump-fun/bonding-curve/0x1234567890abcdef/", None, 200, "Get bonding curve"),
        
        ("POST", "/api/pump-fun/trade/", {
            "contract_address": "0x1234567890abcdef", "amount": 100.0, "trade_type": "buy"
        }, 200, "Execute trade"),
        
        # DeFi Yield Farming
        ("GET", "/api/defi/pools/", None, 200, "Get yield pools"),
        ("GET", "/api/defi/pools/?chain=ethereum", None, 200, "Get yield pools for chain"),
        
        ("POST", "/api/defi/stake/", {
            "pool_id": "test-pool-123", "amount": 50.0, "user_address": "0x1234567890abcdef"
        }, 200, "Stake tokens"),
        
        ("POST", "/api/defi/unstake/", {
            "pool_id": "test-pool-123", "amount": 25.0, "user_address": "0x1234567890abcdef"
        }, 200, "Unstake tokens"),
        
        ("GET", "/api/defi/stakes/0x1234567890abcdef/", None, 200, "Get user stakes"),
        
        # Social Trading
        ("GET", "/api/social/feed", None, 200, "Get social feed"),
        ("GET", "/api/social/meme-templates", None, 200, "Get meme templates"),
        
        ("POST", "/api/social/launch-meme", {
            "user_id": "test-user-123",
            "meme_data": {
                "name": "SocialFrog", "template": "wealth-frog",
                "description": "Social trading test meme", "cultural_theme": "BIPOC Wealth Building"
            }
        }, 201, "Launch meme via social trading"),
        
        ("POST", "/api/social/voice-command", {
            "command": "launch meme", "user_id": "test-user-123",
            "parameters": {"name": "VoiceFrog", "template": "frog"}
        }, 200, "Process voice command"),
        
        ("POST", "/api/social/create-raid", {
            "user_id": "test-user-123", "meme_id": "test-meme-123", "amount": 100.0
        }, 201, "Create trading raid"),
        
        ("POST", "/api/social/join-raid", {
            "user_id": "test-user-123", "raid_id": "test-raid-123", "amount": 50.0
        }, 200, "Join trading raid"),
        
        ("POST", "/api/social/stake-yield", {
            "meme_id": "test-meme-123", "amount": 50.0, "user_address": "0x1234567890abcdef"
        }, 200, "Stake meme yield"),
        
        ("GET", "/api/social/meme-analytics", None, 200, "Get meme analytics"),
        ("GET", "/api/social/leaderboard", None, 200, "Get leaderboard"),
        ("GET", "/api/social/health", None, 200, "Social trading health"),
        
        # Core System
        ("GET", "/api/market/quotes/", None, 200, "Get market quotes"),
        ("GET", "/api/portfolio/", None, 200, "Get portfolio data"),
        
        # Error Handling
        ("POST", "/api/pump-fun/launch/", "invalid json", 400, "Handle invalid JSON"),
        ("POST", "/api/pump-fun/launch/", {"name": "Test"}, 400, "Handle missing fields"),
        ("GET", "/api/non-existent/", None, 404, "Handle non-existent endpoint"),
    ]
    
    # Run tests
    successful = 0
    failed = 0
    
    for method, endpoint, data, expected_status, description in test_cases:
        try:
            start_time = time.time()
            
            if method == "GET":
                response = session.get(f"{base_url}{endpoint}", timeout=10)
            elif method == "POST":
                headers = {'Content-Type': 'application/json'}
                if isinstance(data, str):
                    response = session.post(f"{base_url}{endpoint}", data=data, headers=headers, timeout=10)
                else:
                    response = session.post(f"{base_url}{endpoint}", json=data, headers=headers, timeout=10)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == expected_status
            status_emoji = "✅" if success else "❌"
            
            print(f"{status_emoji} {method} {endpoint} - {response.status_code} ({response_time:.3f}s)")
            print(f"   {description}")
            
            if success:
                successful += 1
            else:
                failed += 1
                print(f"   Expected: {expected_status}, Got: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {method} {endpoint} - ERROR ({str(e)})")
            print(f"   {description}")
            failed += 1
    
    # Summary
    total = successful + failed
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 Excellent! All endpoints are working well.")
    elif success_rate >= 80:
        print("\n✅ Good! Most endpoints are working. Review failed tests.")
    elif success_rate >= 70:
        print("\n⚠️ Fair. Some endpoints need attention.")
    else:
        print("\n❌ Poor. Many endpoints need fixes.")
    
    print("\n💡 Next Steps:")
    print("   1. Fix any failed endpoints")
    print("   2. Add authentication for protected endpoints")
    print("   3. Implement real service integrations")
    print("   4. Add comprehensive error handling")
    print("   5. Set up monitoring and alerting")
    
    return success_rate >= 80

if __name__ == '__main__':
    import sys
    success = test_endpoints()
    sys.exit(0 if success else 1)
