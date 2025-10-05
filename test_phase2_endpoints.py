#!/usr/bin/env python3
"""
Test script for Phase 2 endpoints
"""

import requests
import json
import time

def test_endpoint(url, name):
    """Test a single endpoint"""
    try:
        print(f"Testing {name}...")
        response = requests.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ {name} - Success")
                return True
            except:
                print(f"  ✅ {name} - Success (non-JSON)")
                return True
        else:
            print(f"  ❌ {name} - Error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ {name} - Exception: {e}")
        return False

def main():
    """Test all Phase 2 endpoints"""
    base_url = "http://localhost:8007"
    
    endpoints = [
        (f"{base_url}/health/", "Basic Health Check"),
        (f"{base_url}/health/detailed/", "Detailed Health Check"),
        (f"{base_url}/metrics/", "Prometheus Metrics"),
        (f"{base_url}/phase2/streaming/status/", "Streaming Status"),
        (f"{base_url}/phase2/ml/models/", "ML Models"),
        (f"{base_url}/phase2/batch/status/", "AWS Batch Status"),
    ]
    
    print("🧪 Testing Phase 2 Endpoints...")
    print("=" * 50)
    
    results = []
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append((name, result))
        print()
    
    print("📊 Test Results Summary:")
    print("=" * 50)
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 endpoints are working!")
    else:
        print("⚠️ Some endpoints need attention")

if __name__ == "__main__":
    main()
