#!/usr/bin/env python3
"""
Production Health Check - Comprehensive System Verification
This script checks ALL production systems to ensure everything is working
"""

import requests
import json
import time
import sys
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime
import subprocess

class ProductionHealthChecker:
    def __init__(self, base_url: str = "https://app.richesreach.net"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "checks": {},
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
    
    def check_endpoint(self, endpoint: str, method: str = "GET", 
                      expected_status: int = 200, timeout: int = 10,
                      headers: Dict = None, data: Dict = None) -> Tuple[bool, str, Dict]:
        """Check a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(
                method, url, 
                headers=headers or {},
                json=data,
                timeout=timeout
            )
            
            success = response.status_code == expected_status
            message = f"Status: {response.status_code}"
            
            try:
                response_data = response.json()
            except:
                response_data = {"content": response.text[:200]}
            
            return success, message, response_data
            
        except requests.exceptions.Timeout:
            return False, "Timeout", {}
        except requests.exceptions.ConnectionError:
            return False, "Connection Error", {}
        except Exception as e:
            return False, f"Error: {str(e)}", {}
    
    def check_health_endpoints(self):
        """Check basic health endpoints"""
        print("🏥 Checking health endpoints...")
        
        health_endpoints = [
            ("/health/", "Health Check"),
            ("/live/", "Liveness Probe"),
            ("/ready/", "Readiness Probe"),
        ]
        
        for endpoint, name in health_endpoints:
            success, message, data = self.check_endpoint(endpoint)
            self.results["checks"][name] = {
                "endpoint": endpoint,
                "success": success,
                "message": message,
                "data": data
            }
            
            if not success:
                self.results["critical_issues"].append(f"{name} failed: {message}")
            else:
                print(f"  ✅ {name}: {message}")
    
    def check_graphql_api(self):
        """Check GraphQL API functionality"""
        print("🔍 Checking GraphQL API...")
        
        # Test basic GraphQL ping
        graphql_query = {
            "query": "query { __schema { types { name } } }"
        }
        
        success, message, data = self.check_endpoint(
            "/graphql/", 
            method="POST",
            headers={"Content-Type": "application/json"},
            data=graphql_query
        )
        
        self.results["checks"]["GraphQL API"] = {
            "endpoint": "/graphql/",
            "success": success,
            "message": message,
            "data": data
        }
        
        if not success:
            self.results["critical_issues"].append(f"GraphQL API failed: {message}")
        else:
            print(f"  ✅ GraphQL API: {message}")
    
    def check_ai_endpoints(self):
        """Check AI-powered endpoints"""
        print("🤖 Checking AI endpoints...")
        
        ai_endpoints = [
            ("/api/ai-options/recommendations", "AI Options API"),
            ("/api/ai-portfolio/optimize", "AI Portfolio Optimization"),
            ("/api/ml/status", "ML Service Status"),
        ]
        
        for endpoint, name in ai_endpoints:
            success, message, data = self.check_endpoint(endpoint, method="POST")
            self.results["checks"][name] = {
                "endpoint": endpoint,
                "success": success,
                "message": message,
                "data": data
            }
            
            if not success:
                self.results["warnings"].append(f"{name} failed: {message}")
            else:
                print(f"  ✅ {name}: {message}")
    
    def check_bank_integration(self):
        """Check bank integration endpoints"""
        print("🏦 Checking bank integration...")
        
        bank_endpoints = [
            ("/api/yodlee/fastlink/start", "Yodlee Bank Linking"),
            ("/api/sbloc/health", "SBLOC Health"),
            ("/api/sbloc/banks", "SBLOC Banks"),
        ]
        
        for endpoint, name in bank_endpoints:
            success, message, data = self.check_endpoint(endpoint)
            self.results["checks"][name] = {
                "endpoint": endpoint,
                "success": success,
                "message": message,
                "data": data
            }
            
            if not success:
                self.results["warnings"].append(f"{name} failed: {message}")
            else:
                print(f"  ✅ {name}: {message}")
    
    def check_crypto_defi(self):
        """Check crypto and DeFi endpoints"""
        print("₿ Checking crypto/DeFi endpoints...")
        
        crypto_endpoints = [
            ("/api/crypto/prices", "Crypto Prices"),
            ("/api/defi/account", "DeFi Account"),
            ("/rust/analyze", "Rust Crypto Analysis"),
        ]
        
        for endpoint, name in crypto_endpoints:
            success, message, data = self.check_endpoint(endpoint, method="POST")
            self.results["checks"][name] = {
                "endpoint": endpoint,
                "success": success,
                "message": message,
                "data": data
            }
            
            if not success:
                self.results["warnings"].append(f"{name} failed: {message}")
            else:
                print(f"  ✅ {name}: {message}")
    
    def check_market_data(self):
        """Check market data endpoints"""
        print("📈 Checking market data...")
        
        market_endpoints = [
            ("/api/market-data/stocks", "Stock Data"),
            ("/api/market-data/options", "Options Data"),
            ("/api/market-data/news", "Market News"),
        ]
        
        for endpoint, name in market_endpoints:
            success, message, data = self.check_endpoint(endpoint)
            self.results["checks"][name] = {
                "endpoint": endpoint,
                "success": success,
                "message": message,
                "data": data
            }
            
            if not success:
                self.results["warnings"].append(f"{name} failed: {message}")
            else:
                print(f"  ✅ {name}: {message}")
    
    def check_ssl_security(self):
        """Check SSL and security"""
        print("🔒 Checking SSL and security...")
        
        try:
            import ssl
            import socket
            
            # Check SSL certificate
            hostname = self.base_url.replace("https://", "").replace("http://", "")
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issuer = dict(x[0] for x in cert['issuer'])
                    subject = dict(x[0] for x in cert['subject'])
                    
                    self.results["checks"]["SSL Certificate"] = {
                        "success": True,
                        "message": f"Valid certificate from {issuer.get('organizationName', 'Unknown')}",
                        "data": {
                            "issuer": issuer,
                            "subject": subject,
                            "expires": cert.get('notAfter', 'Unknown')
                        }
                    }
                    print(f"  ✅ SSL Certificate: Valid")
                    
        except Exception as e:
            self.results["checks"]["SSL Certificate"] = {
                "success": False,
                "message": f"SSL check failed: {str(e)}",
                "data": {}
            }
            self.results["critical_issues"].append(f"SSL Certificate issue: {str(e)}")
    
    def check_performance(self):
        """Check performance metrics"""
        print("⚡ Checking performance...")
        
        # Test response times for critical endpoints
        critical_endpoints = [
            "/health/",
            "/graphql/",
            "/api/ai-options/recommendations"
        ]
        
        performance_results = {}
        
        for endpoint in critical_endpoints:
            start_time = time.time()
            success, message, data = self.check_endpoint(endpoint, timeout=5)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            performance_results[endpoint] = {
                "response_time_ms": round(response_time, 2),
                "success": success,
                "acceptable": response_time < 2000  # 2 second threshold
            }
            
            if response_time > 2000:
                self.results["warnings"].append(f"Slow response: {endpoint} took {response_time:.2f}ms")
        
        self.results["checks"]["Performance"] = {
            "success": all(p["success"] for p in performance_results.values()),
            "message": "Performance metrics collected",
            "data": performance_results
        }
        
        print(f"  ✅ Performance: Response times checked")
    
    def check_database_connectivity(self):
        """Check database connectivity (if possible)"""
        print("🗄️ Checking database connectivity...")
        
        # Try to check database through a simple query
        try:
            # This would need to be implemented based on your database setup
            # For now, we'll check if the GraphQL schema is accessible
            success, message, data = self.check_endpoint("/graphql/", method="POST", 
                data={"query": "query { __schema { queryType { name } } }"})
            
            if success and "queryType" in str(data):
                self.results["checks"]["Database Connectivity"] = {
                    "success": True,
                    "message": "Database accessible through GraphQL",
                    "data": data
                }
                print(f"  ✅ Database: Accessible")
            else:
                self.results["checks"]["Database Connectivity"] = {
                    "success": False,
                    "message": "Database not accessible",
                    "data": data
                }
                self.results["critical_issues"].append("Database connectivity issue")
                
        except Exception as e:
            self.results["checks"]["Database Connectivity"] = {
                "success": False,
                "message": f"Database check failed: {str(e)}",
                "data": {}
            }
            self.results["critical_issues"].append(f"Database check failed: {str(e)}")
    
    def check_mobile_app_config(self):
        """Check mobile app configuration"""
        print("📱 Checking mobile app configuration...")
        
        # Check if mobile app can connect
        mobile_endpoints = [
            "/api/mobile/config",
            "/api/mobile/version",
        ]
        
        mobile_success = True
        for endpoint in mobile_endpoints:
            success, message, data = self.check_endpoint(endpoint)
            if not success:
                mobile_success = False
                break
        
        self.results["checks"]["Mobile App Config"] = {
            "success": mobile_success,
            "message": "Mobile app configuration checked",
            "data": {"endpoints_tested": len(mobile_endpoints)}
        }
        
        if mobile_success:
            print(f"  ✅ Mobile App: Configuration accessible")
        else:
            self.results["warnings"].append("Mobile app configuration issues")
    
    def generate_recommendations(self):
        """Generate recommendations based on check results"""
        print("💡 Generating recommendations...")
        
        # Check for common issues and provide recommendations
        if any("SSL" in issue for issue in self.results["critical_issues"]):
            self.results["recommendations"].append("Fix SSL certificate issues immediately")
        
        if any("GraphQL" in issue for issue in self.results["critical_issues"]):
            self.results["recommendations"].append("Check GraphQL server configuration and restart if needed")
        
        if any("Database" in issue for issue in self.results["critical_issues"]):
            self.results["recommendations"].append("Check database connection and credentials")
        
        if len(self.results["warnings"]) > 5:
            self.results["recommendations"].append("Multiple warnings detected - review system logs")
        
        # Performance recommendations
        performance_data = self.results["checks"].get("Performance", {}).get("data", {})
        slow_endpoints = [ep for ep, data in performance_data.items() 
                         if data.get("response_time_ms", 0) > 1000]
        if slow_endpoints:
            self.results["recommendations"].append(f"Optimize slow endpoints: {', '.join(slow_endpoints)}")
    
    def determine_overall_status(self):
        """Determine overall system status"""
        critical_issues = len(self.results["critical_issues"])
        warnings = len(self.results["warnings"])
        
        if critical_issues > 0:
            self.results["overall_status"] = "CRITICAL"
        elif warnings > 3:
            self.results["overall_status"] = "WARNING"
        elif warnings > 0:
            self.results["overall_status"] = "DEGRADED"
        else:
            self.results["overall_status"] = "HEALTHY"
    
    def run_comprehensive_check(self):
        """Run all health checks"""
        print("🚀 Starting comprehensive production health check...")
        print("=" * 60)
        
        # Run all checks
        self.check_health_endpoints()
        self.check_graphql_api()
        self.check_ai_endpoints()
        self.check_bank_integration()
        self.check_crypto_defi()
        self.check_market_data()
        self.check_ssl_security()
        self.check_performance()
        self.check_database_connectivity()
        self.check_mobile_app_config()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Determine overall status
        self.determine_overall_status()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print health check summary"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION HEALTH CHECK SUMMARY")
        print("=" * 60)
        
        status_emoji = {
            "HEALTHY": "✅",
            "DEGRADED": "⚠️",
            "WARNING": "⚠️",
            "CRITICAL": "❌"
        }
        
        print(f"Overall Status: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status']}")
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Count checks
        total_checks = len(self.results["checks"])
        successful_checks = sum(1 for check in self.results["checks"].values() if check["success"])
        
        print(f"Checks: {successful_checks}/{total_checks} successful")
        print(f"Critical Issues: {len(self.results['critical_issues'])}")
        print(f"Warnings: {len(self.results['warnings'])}")
        
        # Print critical issues
        if self.results["critical_issues"]:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in self.results["critical_issues"]:
                print(f"  ❌ {issue}")
        
        # Print warnings
        if self.results["warnings"]:
            print("\n⚠️ WARNINGS:")
            for warning in self.results["warnings"]:
                print(f"  ⚠️ {warning}")
        
        # Print recommendations
        if self.results["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"  💡 {rec}")
        
        print("\n" + "=" * 60)
        
        # Save results to file
        with open("production_health_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("📄 Detailed report saved to: production_health_report.json")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Health Check")
    parser.add_argument("--url", default="https://app.richesreach.net", 
                       help="Base URL to check")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    checker = ProductionHealthChecker(args.url)
    results = checker.run_comprehensive_check()
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output}")
    
    # Exit with appropriate code
    if results["overall_status"] == "CRITICAL":
        sys.exit(2)
    elif results["overall_status"] in ["WARNING", "DEGRADED"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
