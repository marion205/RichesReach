#!/usr/bin/env python3
"""
Test script to verify all GenAI routes are accessible and working
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8124"

def test_endpoint(endpoint: str, payload: Dict[str, Any], expected_status: int = 200) -> bool:
    """Test a single endpoint"""
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
        if response.status_code == expected_status:
            print(f"✅ {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {endpoint} - Status: {response.status_code}, Expected: {expected_status}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - Error: {e}")
        return False

def main():
    print("🧪 Testing GenAI Routes...")
    print("=" * 50)
    
    # Test data
    test_user_id = "test-user-123"
    
    # Test endpoints
    endpoints = [
        # Tutor endpoints
        ("/tutor/ask", {
            "user_id": test_user_id,
            "question": "What is a stock?"
        }),
        ("/tutor/explain", {
            "user_id": test_user_id,
            "concept": "dollar cost averaging"
        }),
        ("/tutor/quiz", {
            "user_id": test_user_id,
            "topic": "Options Basics",
            "difficulty": "beginner",
            "num_questions": 2
        }),
        ("/tutor/module", {
            "user_id": test_user_id,
            "topic": "Risk Management",
            "difficulty": "beginner"
        }),
        ("/tutor/market-commentary", {
            "user_id": test_user_id,
            "horizon": "daily",
            "tone": "neutral"
        }),
        
        # Assistant endpoint
        ("/assistant/query", {
            "user_id": test_user_id,
            "prompt": "Explain compound interest"
        }),
        
        # Coach endpoints
        ("/coach/advise", {
            "user_id": test_user_id,
            "goal": "Grow capital steadily",
            "risk_tolerance": "medium",
            "horizon": "medium"
        }),
        ("/coach/strategy", {
            "user_id": test_user_id,
            "objective": "income",
            "market_view": "neutral"
        }),
    ]
    
    # Test each endpoint
    passed = 0
    total = len(endpoints)
    
    for endpoint, payload in endpoints:
        if test_endpoint(endpoint, payload):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 All GenAI routes are working!")
        return 0
    else:
        print("⚠️  Some routes failed. Check the backend server.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
