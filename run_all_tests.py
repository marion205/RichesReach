#!/usr/bin/env python3
"""
Comprehensive test runner for all Phase 1, 2, and 3 features
Runs backend unit tests, mobile component tests, and API integration tests
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def run_command(command, description, cwd=None):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print(f"Working directory: {cwd or os.getcwd()}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print(f"❌ {description} - FAILED")
            print("Error:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    python_deps = ["pytest", "requests", "asyncio"]
    for dep in python_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} - installed")
        except ImportError:
            print(f"❌ {dep} - missing")
            return False
    
    # Check if test server is running
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Test server - running")
        else:
            print("⚠️  Test server - responding but not healthy")
    except:
        print("❌ Test server - not running")
        print("   Please start the test server: python3 test_server_minimal.py")
        return False
    
    return True


def run_backend_tests():
    """Run all backend unit tests"""
    print("\n🚀 Running Backend Unit Tests...")
    
    tests = [
        ("python3 -m pytest tests/test_phase1_backend.py -v", "Phase 1 Backend Tests"),
        ("python3 -m pytest tests/test_phase2_backend.py -v", "Phase 2 Backend Tests"),
        ("python3 -m pytest tests/test_phase3_backend.py -v", "Phase 3 Backend Tests"),
    ]
    
    results = []
    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))
    
    return results


def run_api_integration_tests():
    """Run API integration tests"""
    print("\n🌐 Running API Integration Tests...")
    
    tests = [
        ("python3 -m pytest tests/test_api_endpoints_integration.py::TestPhase1APIEndpoints -v", "Phase 1 API Tests"),
        ("python3 -m pytest tests/test_api_endpoints_integration.py::TestPhase2APIEndpoints -v", "Phase 2 API Tests"),
        ("python3 -m pytest tests/test_api_endpoints_integration.py::TestPhase3APIEndpoints -v", "Phase 3 API Tests"),
        ("python3 -m pytest tests/test_api_endpoints_integration.py::TestCrossPhaseIntegration -v", "Cross-Phase Integration Tests"),
    ]
    
    results = []
    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))
    
    return results


def run_mobile_tests():
    """Run mobile component tests"""
    print("\n📱 Running Mobile Component Tests...")
    
    mobile_dir = Path("mobile")
    if not mobile_dir.exists():
        print("❌ Mobile directory not found")
        return [("Mobile Tests", False)]
    
    # Check if package.json exists
    package_json = mobile_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found in mobile directory")
        return [("Mobile Tests", False)]
    
    # Install dependencies if needed
    print("📦 Installing mobile dependencies...")
    install_success = run_command("npm install", "Install Mobile Dependencies", cwd=mobile_dir)
    if not install_success:
        return [("Mobile Tests", False)]
    
    # Run mobile tests
    tests = [
        ("npm test -- --testPathPattern=test_phase1_components.test.tsx", "Phase 1 Mobile Tests"),
        ("npm test -- --testPathPattern=test_phase2_components.test.tsx", "Phase 2 Mobile Tests"),
        ("npm test -- --testPathPattern=test_phase3_components.test.tsx", "Phase 3 Mobile Tests"),
    ]
    
    results = []
    for command, description in tests:
        success = run_command(command, description, cwd=mobile_dir)
        results.append((description, success))
    
    return results


def generate_test_report(all_results):
    """Generate a comprehensive test report"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, success in all_results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Test Suites: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for description, success in all_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {status} - {description}")
    
    if failed_tests > 0:
        print(f"\n🔧 FAILED TESTS:")
        for description, success in all_results:
            if not success:
                print(f"   ❌ {description}")
    
    print(f"\n🎯 PHASE COVERAGE:")
    phases = {
        "Phase 1": ["Daily Voice Digest", "Momentum Missions", "Notifications", "Regime Monitoring"],
        "Phase 2": ["Wealth Circles", "Peer Progress", "Trade Simulator"],
        "Phase 3": ["Behavioral Analytics", "Dynamic Content", "Personalization"]
    }
    
    for phase, features in phases.items():
        print(f"   {phase}: {', '.join(features)}")
    
    print(f"\n📁 TEST FILES CREATED:")
    test_files = [
        "tests/test_phase1_backend.py",
        "tests/test_phase2_backend.py", 
        "tests/test_phase3_backend.py",
        "tests/test_api_endpoints_integration.py",
        "mobile/src/__tests__/test_phase1_components.test.tsx",
        "mobile/src/__tests__/test_phase2_components.test.tsx",
        "mobile/src/__tests__/test_phase3_components.test.tsx"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"   ✅ {test_file}")
        else:
            print(f"   ❌ {test_file}")
    
    return passed_tests == total_tests


def main():
    """Main test runner"""
    print("🧪 RICHESREACH COMPREHENSIVE TEST SUITE")
    print("Testing all Phase 1, 2, and 3 features")
    print("="*60)
    
    start_time = time.time()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    all_results = []
    
    # Run backend tests
    backend_results = run_backend_tests()
    all_results.extend(backend_results)
    
    # Run API integration tests
    api_results = run_api_integration_tests()
    all_results.extend(api_results)
    
    # Run mobile tests
    mobile_results = run_mobile_tests()
    all_results.extend(mobile_results)
    
    # Generate report
    end_time = time.time()
    duration = end_time - start_time
    
    success = generate_test_report(all_results)
    
    print(f"\n⏱️  Total execution time: {duration:.2f} seconds")
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Your implementation is solid.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED. Please review the failures above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
