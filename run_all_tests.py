#!/usr/bin/env python3
"""
RichesReach Comprehensive Test Runner
Executes all unit tests for HFT, Voice AI, Mobile Features, and AI capabilities
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_test_file(test_file, description):
    """Run a specific test file and return success status"""
    print(f"\n🧪 Running {description}...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED ({duration:.1f}s)")
            return True
        else:
            print(f"❌ {description} FAILED ({duration:.1f}s)")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} TIMED OUT (300s)")
        return False
    except Exception as e:
        print(f"💥 {description} ERROR: {e}")
        return False

def check_server_running():
    """Check if the test server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_test_server():
    """Start the test server if not running"""
    if check_server_running():
        print("✅ Test server is already running")
        return True
        
    print("🚀 Starting test server...")
    
    try:
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "test_server_minimal.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if check_server_running():
                print("✅ Test server started successfully")
                return True
                
        print("❌ Test server failed to start")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"💥 Failed to start test server: {e}")
        return False

def run_all_tests():
    """Run all comprehensive tests"""
    print("🚀 RICHESREACH COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Testing HFT Engine, Voice AI, Mobile Features, and AI Capabilities")
    print("=" * 80)
    
    # Check if test server is running
    if not start_test_server():
        print("❌ Cannot run tests without test server")
        return False
    
    # Define test files and descriptions
    test_files = [
        ("test_comprehensive_unit_tests.py", "Comprehensive Unit Tests"),
        ("test_hft_performance.py", "HFT Performance Tests"),
        ("test_all_endpoints.py", "Endpoint Integration Tests")
    ]
    
    # Track results
    results = []
    total_start_time = time.time()
    
    # Run each test file
    for test_file, description in test_files:
        if Path(test_file).exists():
            success = run_test_file(test_file, description)
            results.append((description, success))
        else:
            print(f"⚠️  {test_file} not found, skipping {description}")
            results.append((description, False))
    
    # Calculate summary
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    passed_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total duration: {total_duration:.1f}s")
    
    print("\n📋 DETAILED RESULTS:")
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} - {description}")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! RichesReach is ready for production!")
        print("🚀 HFT Engine: ✅ Operational")
        print("🎤 Voice AI: ✅ Operational") 
        print("📱 Mobile Features: ✅ Operational")
        print("🧠 AI Features: ✅ Operational")
        print("⚡ Performance: ✅ Excellent")
    elif success_rate >= 80:
        print(f"\n⚠️  {success_rate:.1f}% tests passed. Minor issues detected.")
    else:
        print(f"\n❌ Only {success_rate:.1f}% tests passed. Major issues detected.")
    
    return success_rate >= 80

def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality"""
    print("🔥 QUICK SMOKE TEST")
    print("-" * 40)
    
    try:
        import requests
        
        # Test basic endpoints
        endpoints = [
            ("/health", "Health Check"),
            ("/api/hft/performance/", "HFT Performance"),
            ("/api/voice-ai/voices/", "Voice AI"),
            ("/api/regime-detection/current-regime/", "AI Regime Detection"),
            ("/api/mobile/gesture-trade/", "Mobile Gestures")
        ]
        
        passed = 0
        for endpoint, description in endpoints:
            try:
                if endpoint == "/api/mobile/gesture-trade/":
                    # POST endpoint
                    response = requests.post(
                        f"http://localhost:8000{endpoint}",
                        json={"symbol": "AAPL", "gesture_type": "swipe_right"},
                        timeout=5
                    )
                else:
                    # GET endpoint
                    response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {description}")
                    passed += 1
                else:
                    print(f"❌ {description} (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ {description} (Error: {e})")
        
        success_rate = (passed / len(endpoints)) * 100
        print(f"\nSmoke test: {passed}/{len(endpoints)} passed ({success_rate:.1f}%)")
        
        return success_rate >= 80
        
    except ImportError:
        print("❌ requests library not available for smoke test")
        return False

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        success = run_quick_smoke_test()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)