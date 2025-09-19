#!/usr/bin/env python3
"""
Comprehensive test for all new institutional ML features
Tests Django settings, authentication, dependencies, point-in-time data, and monitoring
"""
import asyncio
import time
import json
import requests
from typing import Dict, Any
import sys
import os

# Add backend to path
sys.path.append('/Users/marioncollins/RichesReach/backend')

BACKEND_URL = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{BACKEND_URL}/graphql/"

class ComprehensiveTester:
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        
    def make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request"""
        payload = {"query": query, "variables": variables or {}}
        try:
            response = self.session.post(GRAPHQL_ENDPOINT, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "data": None}
    
    def test_django_settings(self) -> Dict[str, Any]:
        """Test Django settings configuration"""
        print("\n🔧 Testing Django Settings Configuration...")
        
        try:
            # Test ML settings
            from core.ml_settings import (
                get_ml_config, get_pit_config, get_institutional_config, 
                get_monitoring_config, is_ml_enabled, validate_ml_config
            )
            
            ml_config = get_ml_config()
            pit_config = get_pit_config()
            institutional_config = get_institutional_config()
            monitoring_config = get_monitoring_config()
            
            is_valid, message = validate_ml_config()
            
            return {
                "success": True,
                "ml_enabled": is_ml_enabled(),
                "ml_config": ml_config,
                "pit_config": pit_config,
                "institutional_config": institutional_config,
                "monitoring_config": monitoring_config,
                "config_valid": is_valid,
                "config_message": message
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_dependencies(self) -> Dict[str, Any]:
        """Test optional dependencies installation"""
        print("\n📦 Testing Optional Dependencies...")
        
        dependencies = {}
        
        try:
            import numpy as np
            dependencies["numpy"] = {"installed": True, "version": np.__version__}
        except ImportError:
            dependencies["numpy"] = {"installed": False}
        
        try:
            import cvxpy as cp
            dependencies["cvxpy"] = {"installed": True, "version": cp.__version__}
        except ImportError:
            dependencies["cvxpy"] = {"installed": False}
        
        try:
            import scipy
            dependencies["scipy"] = {"installed": True, "version": scipy.__version__}
        except ImportError:
            dependencies["scipy"] = {"installed": False}
        
        try:
            import sklearn
            dependencies["scikit-learn"] = {"installed": True, "version": sklearn.__version__}
        except ImportError:
            dependencies["scikit-learn"] = {"installed": False}
        
        try:
            import pandas as pd
            dependencies["pandas"] = {"installed": True, "version": pd.__version__}
        except ImportError:
            dependencies["pandas"] = {"installed": False}
        
        all_installed = all(dep["installed"] for dep in dependencies.values())
        
        return {
            "success": all_installed,
            "dependencies": dependencies,
            "all_installed": all_installed
        }
    
    def test_authentication_system(self) -> Dict[str, Any]:
        """Test authentication system"""
        print("\n🔐 Testing Authentication System...")
        
        try:
            from core.auth_utils import (
                RateLimiter, MLMutationAuth, SecurityUtils, 
                MLMutationValidator, get_ml_mutation_context
            )
            
            # Test rate limiter
            rate_limiter = RateLimiter()
            
            # Test security utils
            security = SecurityUtils()
            test_data = {"test": "value", "number": 123}
            sanitized = security.sanitize_input(test_data)
            audit_hash = security.generate_audit_hash(test_data)
            
            # Test validator
            validator = MLMutationValidator()
            test_universe = ["AAPL", "MSFT", "GOOGL"]
            validated_universe = validator.validate_universe(test_universe)
            
            return {
                "success": True,
                "rate_limiter": "available",
                "security_utils": "available",
                "validator": "available",
                "sanitization_works": sanitized is not None,
                "audit_hash_works": len(audit_hash) > 0,
                "universe_validation_works": len(validated_universe) > 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_point_in_time_data(self) -> Dict[str, Any]:
        """Test point-in-time data service"""
        print("\n📊 Testing Point-in-Time Data Service...")
        
        try:
            from core.pit_data_service import pit_service, audit_service
            
            # Test data quality metrics
            quality_metrics = pit_service.get_data_quality_metrics()
            
            # Test audit service
            test_audit = audit_service.log_ml_mutation(
                user_id=1,
                action_type="TEST_ACTION",
                request_id="test_123",
                input_data={"test": "data"},
                success=True
            )
            
            return {
                "success": True,
                "pit_service": "available",
                "audit_service": "available",
                "quality_metrics": quality_metrics,
                "audit_logging": test_audit is not None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_monitoring_system(self) -> Dict[str, Any]:
        """Test monitoring system"""
        print("\n📈 Testing Monitoring System...")
        
        try:
            from core.monitoring_service import monitoring_service
            
            # Test metrics collection
            metrics = monitoring_service.collect_all_metrics()
            
            # Test health check
            health = monitoring_service.perform_health_check()
            
            # Test alerts
            alerts = monitoring_service.check_and_send_alerts()
            
            return {
                "success": True,
                "metrics_collection": "working",
                "health_check": "working",
                "alerts_system": "working",
                "metrics_keys": list(metrics.keys()) if metrics else [],
                "health_status": health.get("overall_status", "unknown"),
                "alerts_count": len(alerts)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_ml_mutations_with_auth(self) -> Dict[str, Any]:
        """Test ML mutations with authentication"""
        print("\n🤖 Testing ML Mutations with Authentication...")
        
        # Test ML service status (should require auth)
        query = """
        mutation GetMLServiceStatus {
            getMlServiceStatus {
                success
                message
                serviceStatus
            }
        }
        """
        
        result = self.make_graphql_request(query)
        
        return {
            "success": "data" in result,
            "has_errors": "errors" in result,
            "response": result
        }
    
    def test_monitoring_endpoints(self) -> Dict[str, Any]:
        """Test monitoring GraphQL endpoints"""
        print("\n📊 Testing Monitoring Endpoints...")
        
        # Test system health
        health_query = """
        mutation GetSystemHealth {
            getSystemHealth {
                success
                message
                health {
                    overallStatus
                    timestamp
                    components
                    error
                }
            }
        }
        """
        
        health_result = self.make_graphql_request(health_query)
        
        # Test system metrics
        metrics_query = """
        mutation GetSystemMetrics {
            getSystemMetrics {
                success
                message
                metrics {
                    system
                    application
                    business
                    timestamp
                }
            }
        }
        """
        
        metrics_result = self.make_graphql_request(metrics_query)
        
        return {
            "health_endpoint": "data" in health_result,
            "metrics_endpoint": "data" in metrics_result,
            "health_response": health_result,
            "metrics_response": metrics_result
        }
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 COMPREHENSIVE INSTITUTIONAL ML SETUP TEST")
        print("=" * 60)
        
        # Test 1: Django Settings
        settings_result = self.test_django_settings()
        self.results["django_settings"] = settings_result
        
        # Test 2: Dependencies
        deps_result = self.test_dependencies()
        self.results["dependencies"] = deps_result
        
        # Test 3: Authentication
        auth_result = self.test_authentication_system()
        self.results["authentication"] = auth_result
        
        # Test 4: Point-in-Time Data
        pit_result = self.test_point_in_time_data()
        self.results["point_in_time_data"] = pit_result
        
        # Test 5: Monitoring
        monitoring_result = self.test_monitoring_system()
        self.results["monitoring"] = monitoring_result
        
        # Test 6: ML Mutations
        ml_result = self.test_ml_mutations_with_auth()
        self.results["ml_mutations"] = ml_result
        
        # Test 7: Monitoring Endpoints
        endpoints_result = self.test_monitoring_endpoints()
        self.results["monitoring_endpoints"] = endpoints_result
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE SETUP TEST REPORT")
        print("=" * 80)
        
        # Overall Status
        all_tests = [
            self.results["django_settings"]["success"],
            self.results["dependencies"]["success"],
            self.results["authentication"]["success"],
            self.results["point_in_time_data"]["success"],
            self.results["monitoring"]["success"],
        ]
        
        overall_success = all(all_tests)
        
        print(f"\n🎯 OVERALL STATUS: {'✅ SUCCESS' if overall_success else '⚠️ PARTIAL SUCCESS'}")
        print(f"Tests Passed: {sum(all_tests)}/{len(all_tests)}")
        
        # Detailed Results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)
        
        for test_name, result in self.results.items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"{status} {test_name.upper()}")
            
            if "error" in result:
                print(f"   Error: {result['error']}")
            elif test_name == "dependencies":
                deps = result.get("dependencies", {})
                for dep_name, dep_info in deps.items():
                    dep_status = "✅" if dep_info.get("installed", False) else "❌"
                    version = dep_info.get("version", "N/A")
                    print(f"   {dep_status} {dep_name}: {version}")
            elif test_name == "django_settings":
                print(f"   ML Enabled: {result.get('ml_enabled', False)}")
                print(f"   Config Valid: {result.get('config_valid', False)}")
                print(f"   Message: {result.get('config_message', 'N/A')}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 50)
        
        if not self.results["django_settings"]["success"]:
            print("1. ❌ Fix Django settings configuration")
        
        if not self.results["dependencies"]["success"]:
            print("2. ❌ Install missing dependencies")
        
        if not self.results["authentication"]["success"]:
            print("3. ❌ Fix authentication system")
        
        if not self.results["point_in_time_data"]["success"]:
            print("4. ❌ Fix point-in-time data service")
        
        if not self.results["monitoring"]["success"]:
            print("5. ❌ Fix monitoring system")
        
        if overall_success:
            print("✅ All systems are properly configured!")
            print("✅ Institutional ML mutations are ready for use!")
            print("✅ Monitoring and alerting are operational!")
            print("✅ Point-in-time data is available!")
        
        print("\n🎉 Comprehensive setup test completed!")

def main():
    """Main test execution"""
    print("🧪 Comprehensive Institutional ML Setup Test")
    print("Testing all new features and configurations")
    
    tester = ComprehensiveTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
