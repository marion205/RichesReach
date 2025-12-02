#!/usr/bin/env python3
"""
Standalone test script for Constellation AI API endpoints
Can be run directly to verify endpoints are working
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ENDPOINTS = {
    "life-events": f"{BASE_URL}/api/ai/life-events",
    "growth-projections": f"{BASE_URL}/api/ai/growth-projections",
    "shield-analysis": f"{BASE_URL}/api/ai/shield-analysis",
    "recommendations": f"{BASE_URL}/api/ai/recommendations"
}

def test_endpoint(name: str, url: str, data: Dict[str, Any]) -> bool:
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"Response keys: {list(result.keys())}")
            
            # Print summary based on endpoint type
            if name == "life-events":
                events = result.get("events", [])
                print(f"Events returned: {len(events)}")
                for event in events[:3]:  # Show first 3
                    print(f"  - {event.get('title')}: ${event.get('targetAmount', 0):,.0f} target")
            
            elif name == "growth-projections":
                projections = result.get("projections", [])
                print(f"Projections returned: {len(projections)}")
                scenarios = set(p.get("scenario") for p in projections)
                print(f"Scenarios: {', '.join(list(scenarios)[:5])}")
            
            elif name == "shield-analysis":
                strategies = result.get("recommendedStrategies", [])
                outlook = result.get("marketOutlook", {})
                print(f"Strategies: {len(strategies)}")
                print(f"Market Outlook: {outlook.get('sentiment', 'unknown')} ({outlook.get('confidence', 0)*100:.0f}% confidence)")
            
            elif name == "recommendations":
                recs = result.get("recommendations", [])
                print(f"Recommendations: {len(recs)}")
                for rec in recs[:3]:  # Show first 3
                    print(f"  - {rec.get('title')} (Priority {rec.get('priority')})")
            
            return True
        else:
            print(f"❌ FAILED")
            print(f"Error: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR")
        print(f"Could not connect to {BASE_URL}")
        print("Make sure the server is running: python main_server.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run all endpoint tests"""
    print("="*60)
    print("Constellation AI API Endpoint Tests")
    print("="*60)
    
    # Test data
    test_snapshot = {
        "netWorth": 100000,
        "cashflow": {
            "delta": 2000,
            "in": 5000,
            "out": 3000
        },
        "breakdown": {
            "bankBalance": 10000,
            "portfolioValue": 90000,
            "bankAccountsCount": 2
        },
        "positions": [
            {"symbol": "AAPL", "value": 45000, "shares": 300},
            {"symbol": "MSFT", "value": 45000, "shares": 150}
        ]
    }
    
    test_user_profile = {
        "age": 35,
        "incomeBracket": "middle",
        "riskTolerance": "moderate",
        "investmentGoals": ["retirement", "home"]
    }
    
    results = {}
    
    # Test 1: Life Events
    results["life-events"] = test_endpoint(
        "life-events",
        ENDPOINTS["life-events"],
        {
            "snapshot": test_snapshot,
            "userProfile": test_user_profile
        }
    )
    
    # Test 2: Growth Projections
    results["growth-projections"] = test_endpoint(
        "growth-projections",
        ENDPOINTS["growth-projections"],
        {
            "currentValue": test_snapshot["netWorth"],
            "monthlySurplus": test_snapshot["cashflow"]["delta"],
            "portfolioValue": test_snapshot["breakdown"]["portfolioValue"],
            "timeframes": [6, 12, 24, 36]
        }
    )
    
    # Test 3: Shield Analysis
    results["shield-analysis"] = test_endpoint(
        "shield-analysis",
        ENDPOINTS["shield-analysis"],
        {
            "portfolioValue": test_snapshot["breakdown"]["portfolioValue"],
            "bankBalance": test_snapshot["breakdown"]["bankBalance"],
            "positions": test_snapshot["positions"],
            "cashflow": test_snapshot["cashflow"]
        }
    )
    
    # Test 4: Recommendations
    results["recommendations"] = test_endpoint(
        "recommendations",
        ENDPOINTS["recommendations"],
        {
            "snapshot": test_snapshot,
            "userBehavior": {
                "recentActions": ["view_portfolio", "check_balance"],
                "preferences": {"risk_tolerance": "moderate"}
            }
        }
    )
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20s}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

