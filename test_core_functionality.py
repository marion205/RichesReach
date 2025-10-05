#!/usr/bin/env python3
"""
Core Functionality Test - Simplified Phase 3 Testing
Tests core functionality without complex dependencies
"""

import sys
import os
import requests
import time
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

class CoreTester:
    """Simplified core functionality tester"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.server_running = False
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_server_startup(self) -> bool:
        """Test server startup"""
        self.log("Testing server startup...")
        
        try:
            # Try to start server
            import subprocess
            import threading
            
            def start_server():
                try:
                    subprocess.run([
                        sys.executable, '-m', 'uvicorn', 
                        'backend.final_complete_server:app',
                        '--host', '0.0.0.0',
                        '--port', '8000'
                    ], cwd='.', timeout=30)
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    self.log(f"Server startup error: {e}", "ERROR")
            
            # Start server in background
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            for i in range(30):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        self.server_running = True
                        self.log("✅ Server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            self.log("❌ Server failed to start within 30 seconds", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Server startup test failed: {e}", "ERROR")
            return False
    
    def test_basic_endpoints(self) -> dict:
        """Test basic endpoints"""
        self.log("Testing basic endpoints...")
        
        results = {}
        endpoints = [
            "/health",
            "/metrics/",
            "/debug/scoring_info"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return results
    
    def test_graphql_basic(self) -> dict:
        """Test basic GraphQL functionality"""
        self.log("Testing GraphQL basic functionality...")
        
        try:
            # Test GraphQL introspection
            query = """
            query {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """
            
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                self.log(f"✅ GraphQL introspection - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
            else:
                self.log(f"❌ GraphQL introspection - {response.status_code}", "ERROR")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ GraphQL test failed: {e}", "ERROR")
            return {
                "status_code": None,
                "success": False,
                "error": str(e)
            }
    
    def test_stock_data(self) -> dict:
        """Test stock data endpoints"""
        self.log("Testing stock data endpoints...")
        
        try:
            # Test stocks query
            query = """
            query {
                stocks(limit: 5) {
                    symbol
                    name
                    currentPrice
                }
            }
            """
            
            response = requests.post(
                f"{self.base_url}/graphql",
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "stocks" in data["data"]:
                    self.log(f"✅ Stock data query - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"⚠️ Stock data query returned unexpected format", "WARNING")
            else:
                self.log(f"❌ Stock data query - {response.status_code}", "ERROR")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Stock data test failed: {e}", "ERROR")
            return {
                "status_code": None,
                "success": False,
                "error": str(e)
            }
    
    def run_core_test(self) -> dict:
        """Run core functionality test"""
        self.log("🚀 Starting Core Functionality Test")
        self.log("=" * 50)
        
        # Test 1: Server Startup
        self.log("\n🖥️ Test 1: Server Startup")
        self.log("-" * 30)
        server_startup = self.test_server_startup()
        
        if not server_startup:
            self.log("❌ Server startup failed - skipping remaining tests", "ERROR")
            return {
                "overall_success": False,
                "server_startup": server_startup,
                "error": "Server failed to start"
            }
        
        # Test 2: Basic Endpoints
        self.log("\n🏥 Test 2: Basic Endpoints")
        self.log("-" * 30)
        basic_results = self.test_basic_endpoints()
        
        # Test 3: GraphQL Basic
        self.log("\n📊 Test 3: GraphQL Basic")
        self.log("-" * 30)
        graphql_results = self.test_graphql_basic()
        
        # Test 4: Stock Data
        self.log("\n📈 Test 4: Stock Data")
        self.log("-" * 30)
        stock_results = self.test_stock_data()
        
        # Calculate success rate
        total_tests = 1 + len(basic_results) + 2  # server + endpoints + graphql + stock
        passed_tests = 0
        
        if server_startup:
            passed_tests += 1
        
        for endpoint, result in basic_results.items():
            if result.get("success", False):
                passed_tests += 1
        
        if graphql_results.get("success", False):
            passed_tests += 1
        
        if stock_results.get("success", False):
            passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_success = success_rate >= 70  # 70% pass rate required
        
        # Generate report
        self.log("\n" + "=" * 50)
        self.log("📋 CORE FUNCTIONALITY TEST RESULTS")
        self.log("=" * 50)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed Tests: {passed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log(f"Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "server_startup": server_startup,
            "basic_results": basic_results,
            "graphql_results": graphql_results,
            "stock_results": stock_results
        }

def main():
    """Main test function"""
    tester = CoreTester()
    results = tester.run_core_test()
    
    # Save results to file
    with open("core_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: core_test_results.json")
    
    if results["overall_success"]:
        print("\n🎉 CORE FUNCTIONALITY TESTS PASSED! Ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ CORE FUNCTIONALITY TESTS FAILED! Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
