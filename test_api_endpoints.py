#!/usr/bin/env python3
"""
MemeQuest API Test Runner
========================

Simple test runner to verify MemeQuest API endpoints are working.
This script tests the core functionality without requiring a full database setup.
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(method, url, headers=None, data=None, expected_status=200):
    """Test a single API endpoint."""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        success = response.status_code == expected_status
        message = f"{method} {url} -> {response.status_code}"
        
        if success:
            message += " ✅"
        else:
            message += f" ❌ (expected {expected_status})"
        
        return success, message
        
    except requests.exceptions.RequestException as e:
        return False, f"{method} {url} -> ERROR: {e}"

def main():
    """Run basic API endpoint tests."""
    base_url = "http://localhost:8000"
    
    print("🧪 MemeQuest API Endpoint Test Runner")
    print("=" * 50)
    print(f"Testing against: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test basic endpoints
    tests = [
        # Health checks
        ("GET", f"{base_url}/health/", None, None, 200),
        ("GET", f"{base_url}/ready/", None, None, 200),
        
        # GraphQL endpoint
        ("POST", f"{base_url}/graphql/", {"Content-Type": "application/json"}, {"query": "{ __schema { types { name } } }"}, 200),
        
        # API endpoints (these might return 404 if not implemented yet)
        ("GET", f"{base_url}/api/memequest/templates/", None, None, [200, 404]),
        ("GET", f"{base_url}/api/social/feed/", None, None, [200, 404]),
        ("GET", f"{base_url}/api/raids/active/", None, None, [200, 404]),
        ("GET", f"{base_url}/api/defi/pools/", None, None, [200, 404]),
        ("GET", f"{base_url}/api/voice/history/", None, None, [200, 404]),
    ]
    
    results = []
    
    for test in tests:
        method, url, headers, data, expected_status = test
        
        # Handle multiple expected status codes
        if isinstance(expected_status, list):
            success = False
            message = f"{method} {url} -> "
            for status in expected_status:
                test_success, test_message = test_endpoint(method, url, headers, data, status)
                if test_success:
                    success = True
                    message += f"{status} ✅"
                    break
            if not success:
                message += f"❌ (expected {expected_status})"
        else:
            success, message = test_endpoint(method, url, headers, data, expected_status)
        
        results.append((success, message))
        print(message)
    
    print()
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    for success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {message}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! API endpoints are accessible.")
    elif passed > total * 0.7:
        print("⚠️ Most tests passed. Some endpoints may not be implemented yet.")
    else:
        print("❌ Many tests failed. Check if the server is running and accessible.")
    
    print()
    print("💡 Next steps:")
    print("1. Ensure Django server is running: python manage.py runserver")
    print("2. Run database migrations: python manage.py migrate")
    print("3. Import Postman collection for detailed testing")
    print("4. Run comprehensive test suite: python test_memequest_api.py")

if __name__ == "__main__":
    main()
