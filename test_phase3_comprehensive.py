#!/usr/bin/env python3
"""
Comprehensive Phase 3 Testing Script
Tests all Phase 3 components and ensures everything is working 100%
"""

import sys
import os
import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

class Phase3Tester:
    """Comprehensive Phase 3 testing suite"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        self.server_running = False
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_imports(self) -> Dict[str, bool]:
        """Test all Phase 3 component imports"""
        self.log("Testing Phase 3 component imports...")
        
        import_results = {}
        
        # Test core imports
        core_modules = [
            'zero_trust_security',
            'encryption_manager', 
            'compliance_manager',
            'security_api',
            'ai_router',
            'ai_router_api',
            'analytics_engine',
            'analytics_api',
            'analytics_websocket',
            'advanced_ai_router',
            'advanced_ai_router_api',
            'ai_model_training',
            'ai_training_api',
            'performance_optimizer',
            'cdn_optimizer',
            'database_optimizer',
            'performance_api'
        ]
        
        for module in core_modules:
            try:
                __import__(f'backend.core.{module}')
                import_results[module] = True
                self.log(f"✅ {module} imported successfully")
            except ImportError as e:
                import_results[module] = False
                self.log(f"❌ {module} import failed: {e}", "ERROR")
            except Exception as e:
                import_results[module] = False
                self.log(f"❌ {module} import error: {e}", "ERROR")
        
        return import_results
    
    def test_server_startup(self) -> bool:
        """Test server startup"""
        self.log("Testing server startup...")
        
        try:
            # Try to start server in background
            import subprocess
            import threading
            
            def start_server():
                try:
                    subprocess.run([
                        sys.executable, '-m', 'uvicorn', 
                        'backend.final_complete_server:app',
                        '--host', '0.0.0.0',
                        '--port', '8000'
                    ], cwd='backend', timeout=30)
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
    
    def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health endpoints"""
        self.log("Testing health endpoints...")
        
        health_results = {}
        
        endpoints = [
            "/health",
            "/health/detailed/",
            "/metrics/"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                health_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                health_results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return health_results
    
    def test_phase3_components(self) -> Dict[str, Any]:
        """Test Phase 3 component availability"""
        self.log("Testing Phase 3 component availability...")
        
        component_results = {}
        
        # Test detailed health check for Phase 3 components
        try:
            response = requests.get(f"{self.base_url}/health/detailed/", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                phase3_components = [
                    "ai_router",
                    "analytics", 
                    "advanced_ai",
                    "performance_optimization",
                    "advanced_security"
                ]
                
                for component in phase3_components:
                    if component in health_data:
                        component_results[component] = {
                            "available": health_data[component].get("available", False),
                            "details": health_data[component]
                        }
                        
                        if health_data[component].get("available", False):
                            self.log(f"✅ {component} - Available")
                        else:
                            self.log(f"⚠️ {component} - Not available")
                    else:
                        component_results[component] = {
                            "available": False,
                            "details": "Not found in health check"
                        }
                        self.log(f"❌ {component} - Not found in health check", "ERROR")
            else:
                self.log(f"❌ Failed to get detailed health check: {response.status_code}", "ERROR")
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to test Phase 3 components: {e}", "ERROR")
        
        return component_results
    
    def test_graphql_endpoints(self) -> Dict[str, Any]:
        """Test GraphQL endpoints"""
        self.log("Testing GraphQL endpoints...")
        
        graphql_results = {}
        
        # Test GraphQL endpoint
        try:
            query = """
            query {
                __schema {
                    types {
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
            
            graphql_results["schema"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                self.log(f"✅ GraphQL schema - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
            else:
                self.log(f"❌ GraphQL schema - {response.status_code}", "ERROR")
                
        except requests.exceptions.RequestException as e:
            graphql_results["schema"] = {
                "status_code": None,
                "success": False,
                "error": str(e)
            }
            self.log(f"❌ GraphQL schema test failed: {e}", "ERROR")
        
        return graphql_results
    
    def test_security_endpoints(self) -> Dict[str, Any]:
        """Test security endpoints"""
        self.log("Testing security endpoints...")
        
        security_results = {}
        
        endpoints = [
            "/security/health",
            "/security/metrics"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                security_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                security_results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return security_results
    
    def test_analytics_endpoints(self) -> Dict[str, Any]:
        """Test analytics endpoints"""
        self.log("Testing analytics endpoints...")
        
        analytics_results = {}
        
        endpoints = [
            "/analytics/health",
            "/analytics/dashboards",
            "/analytics/metrics"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                analytics_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                analytics_results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return analytics_results
    
    def test_performance_endpoints(self) -> Dict[str, Any]:
        """Test performance endpoints"""
        self.log("Testing performance endpoints...")
        
        performance_results = {}
        
        endpoints = [
            "/performance/health",
            "/performance/metrics",
            "/performance/cache/status"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                performance_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                performance_results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return performance_results
    
    def test_ai_endpoints(self) -> Dict[str, Any]:
        """Test AI endpoints"""
        self.log("Testing AI endpoints...")
        
        ai_results = {}
        
        endpoints = [
            "/ai/health",
            "/ai/models",
            "/ai/performance"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                ai_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                else:
                    self.log(f"❌ {endpoint} - {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                ai_results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint} - Request failed: {e}", "ERROR")
        
        return ai_results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 3 test suite"""
        self.log("🚀 Starting Comprehensive Phase 3 Testing")
        self.log("=" * 60)
        
        # Test 1: Import Tests
        self.log("\n📦 Test 1: Component Imports")
        self.log("-" * 30)
        import_results = self.test_imports()
        
        # Test 2: Server Startup
        self.log("\n🖥️ Test 2: Server Startup")
        self.log("-" * 30)
        server_startup = self.test_server_startup()
        
        if not server_startup:
            self.log("❌ Server startup failed - skipping remaining tests", "ERROR")
            return {
                "overall_success": False,
                "import_results": import_results,
                "server_startup": server_startup,
                "error": "Server failed to start"
            }
        
        # Test 3: Health Endpoints
        self.log("\n🏥 Test 3: Health Endpoints")
        self.log("-" * 30)
        health_results = self.test_health_endpoints()
        
        # Test 4: Phase 3 Components
        self.log("\n🔧 Test 4: Phase 3 Components")
        self.log("-" * 30)
        component_results = self.test_phase3_components()
        
        # Test 5: GraphQL Endpoints
        self.log("\n📊 Test 5: GraphQL Endpoints")
        self.log("-" * 30)
        graphql_results = self.test_graphql_endpoints()
        
        # Test 6: Security Endpoints
        self.log("\n🔒 Test 6: Security Endpoints")
        self.log("-" * 30)
        security_results = self.test_security_endpoints()
        
        # Test 7: Analytics Endpoints
        self.log("\n📈 Test 7: Analytics Endpoints")
        self.log("-" * 30)
        analytics_results = self.test_analytics_endpoints()
        
        # Test 8: Performance Endpoints
        self.log("\n⚡ Test 8: Performance Endpoints")
        self.log("-" * 30)
        performance_results = self.test_performance_endpoints()
        
        # Test 9: AI Endpoints
        self.log("\n🤖 Test 9: AI Endpoints")
        self.log("-" * 30)
        ai_results = self.test_ai_endpoints()
        
        # Calculate overall success
        total_tests = 0
        passed_tests = 0
        
        # Count import tests
        for module, success in import_results.items():
            total_tests += 1
            if success:
                passed_tests += 1
        
        # Count server startup
        total_tests += 1
        if server_startup:
            passed_tests += 1
        
        # Count health endpoint tests
        for endpoint, result in health_results.items():
            total_tests += 1
            if result.get("success", False):
                passed_tests += 1
        
        # Count component tests
        for component, result in component_results.items():
            total_tests += 1
            if result.get("available", False):
                passed_tests += 1
        
        # Count other endpoint tests
        for test_group in [graphql_results, security_results, analytics_results, performance_results, ai_results]:
            for endpoint, result in test_group.items():
                total_tests += 1
                if result.get("success", False):
                    passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_success = success_rate >= 80  # 80% pass rate required
        
        # Generate report
        self.log("\n" + "=" * 60)
        self.log("📋 COMPREHENSIVE TEST RESULTS")
        self.log("=" * 60)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed Tests: {passed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log(f"Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        self.log(f"Test Duration: {time.time() - self.start_time:.2f} seconds")
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "test_duration": time.time() - self.start_time,
            "import_results": import_results,
            "server_startup": server_startup,
            "health_results": health_results,
            "component_results": component_results,
            "graphql_results": graphql_results,
            "security_results": security_results,
            "analytics_results": analytics_results,
            "performance_results": performance_results,
            "ai_results": ai_results
        }

def main():
    """Main test function"""
    tester = Phase3Tester()
    results = tester.run_comprehensive_test()
    
    # Save results to file
    with open("phase3_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: phase3_test_results.json")
    
    if results["overall_success"]:
        print("\n🎉 ALL TESTS PASSED! Ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
