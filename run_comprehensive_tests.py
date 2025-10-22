#!/usr/bin/env python3
"""
Comprehensive test runner for RichesReach AI platform.
Runs all backend and mobile tests with detailed reporting.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

class TestRunner:
    """Comprehensive test runner for the RichesReach AI platform."""
    
    def __init__(self, verbose: bool = False, coverage: bool = True):
        self.verbose = verbose
        self.coverage = coverage
        self.results = {
            "backend": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "mobile": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "performance": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "total_time": 0
        }
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: List[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if self.verbose:
            self.log(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {' '.join(command)}", "ERROR")
            return subprocess.CompletedProcess(command, 1, "", "Timeout")
        except Exception as e:
            self.log(f"Error running command: {e}", "ERROR")
            return subprocess.CompletedProcess(command, 1, "", str(e))
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        self.log("Checking dependencies...")
        
        # Check Python dependencies
        python_deps = ["pytest", "pytest-asyncio", "pytest-cov", "httpx"]
        for dep in python_deps:
            result = self.run_command([sys.executable, "-c", f"import {dep}"])
            if result.returncode != 0:
                self.log(f"Missing Python dependency: {dep}", "ERROR")
                return False
        
        # Check Node.js dependencies
        if os.path.exists("mobile/package.json"):
            result = self.run_command(["npm", "list", "--depth=0"], cwd="mobile")
            if result.returncode != 0:
                self.log("Missing Node.js dependencies", "ERROR")
                return False
        
        self.log("All dependencies are installed")
        return True
    
    def run_backend_tests(self) -> bool:
        """Run all backend tests."""
        self.log("Running backend tests...")
        
        # Unit tests
        unit_tests = [
            "tests/unit/test_ai_services_comprehensive.py",
            "tests/unit/test_phase_services_comprehensive.py"
        ]
        
        # Integration tests
        integration_tests = [
            "tests/integration/test_api_endpoints_comprehensive.py",
            "tests/test_api_endpoints_integration.py"
        ]
        
        # Phase-specific tests
        phase_tests = [
            "tests/test_phase1_backend.py",
            "tests/test_phase2_backend.py", 
            "tests/test_phase3_backend.py"
        ]
        
        all_tests = unit_tests + integration_tests + phase_tests
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        if self.coverage:
            cmd.extend(["--cov=backend", "--cov-report=html", "--cov-report=term"])
        
        if self.verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short", "--strict-markers"])
        cmd.extend(all_tests)
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            self.log("Backend tests passed")
            self.results["backend"]["passed"] += 1
        else:
            self.log(f"Backend tests failed: {result.stderr}", "ERROR")
            self.results["backend"]["failed"] += 1
            self.results["backend"]["errors"].append(result.stderr)
        
        return result.returncode == 0
    
    def run_mobile_tests(self) -> bool:
        """Run all mobile tests."""
        self.log("Running mobile tests...")
        
        if not os.path.exists("mobile"):
            self.log("Mobile directory not found, skipping mobile tests")
            return True
        
        # Change to mobile directory
        os.chdir("mobile")
        
        try:
            # Run Jest tests
            cmd = ["npm", "test", "--", "--coverage", "--watchAll=false"]
            
            if self.verbose:
                cmd.append("--verbose")
            
            result = self.run_command(cmd)
            
            if result.returncode == 0:
                self.log("Mobile tests passed")
                self.results["mobile"]["passed"] += 1
            else:
                self.log(f"Mobile tests failed: {result.stderr}", "ERROR")
                self.results["mobile"]["failed"] += 1
                self.results["mobile"]["errors"].append(result.stderr)
            
            return result.returncode == 0
        
        finally:
            # Change back to root directory
            os.chdir("..")
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self.log("Running integration tests...")
        
        # Start test server
        self.log("Starting test server...")
        server_process = subprocess.Popen(
            [sys.executable, "test_server_minimal.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Run integration tests
            cmd = [sys.executable, "-m", "pytest", "tests/integration/", "-v"]
            result = self.run_command(cmd)
            
            if result.returncode == 0:
                self.log("Integration tests passed")
                self.results["integration"]["passed"] += 1
            else:
                self.log(f"Integration tests failed: {result.stderr}", "ERROR")
                self.results["integration"]["failed"] += 1
                self.results["integration"]["errors"].append(result.stderr)
            
            return result.returncode == 0
        
        finally:
            # Stop test server
            server_process.terminate()
            server_process.wait()
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        self.log("Running performance tests...")
        
        # Run performance tests with pytest markers
        cmd = [sys.executable, "-m", "pytest", "-m", "performance", "-v"]
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            self.log("Performance tests passed")
            self.results["performance"]["passed"] += 1
        else:
            self.log(f"Performance tests failed: {result.stderr}", "ERROR")
            self.results["performance"]["failed"] += 1
            self.results["performance"]["errors"].append(result.stderr)
        
        return result.returncode == 0
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        self.results["total_time"] = time.time() - self.start_time
        
        total_passed = sum(category["passed"] for category in self.results.values() if isinstance(category, dict))
        total_failed = sum(category["failed"] for category in self.results.values() if isinstance(category, dict))
        total_skipped = sum(category["skipped"] for category in self.results.values() if isinstance(category, dict))
        
        report = {
            "summary": {
                "total_tests": total_passed + total_failed + total_skipped,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "success_rate": (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0,
                "total_time": self.results["total_time"]
            },
            "categories": self.results,
            "coverage": self.get_coverage_info(),
            "recommendations": self.generate_recommendations()
        }
        
        return report
    
    def get_coverage_info(self) -> Dict[str, Any]:
        """Get test coverage information."""
        coverage_info = {
            "backend": {"percentage": 0, "lines_covered": 0, "total_lines": 0},
            "mobile": {"percentage": 0, "lines_covered": 0, "total_lines": 0}
        }
        
        # Try to read coverage reports
        if os.path.exists("htmlcov/index.html"):
            # Parse HTML coverage report if available
            pass
        
        if os.path.exists("mobile/coverage/lcov.info"):
            # Parse mobile coverage report if available
            pass
        
        return coverage_info
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if self.results["backend"]["failed"] > 0:
            recommendations.append("Fix failing backend tests before deployment")
        
        if self.results["mobile"]["failed"] > 0:
            recommendations.append("Fix failing mobile tests before deployment")
        
        if self.results["integration"]["failed"] > 0:
            recommendations.append("Fix integration test failures")
        
        if self.results["performance"]["failed"] > 0:
            recommendations.append("Address performance test failures")
        
        total_failed = sum(category["failed"] for category in self.results.values() if isinstance(category, dict))
        if total_failed == 0:
            recommendations.append("All tests passed! Ready for deployment.")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = "test_report.json"):
        """Save test report to file."""
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Test report saved to {filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary."""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("🧪 RICHESREACH AI - COMPREHENSIVE TEST SUMMARY")
        print("="*60)
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Time: {summary['total_time']:.2f}s")
        print("="*60)
        
        # Category breakdown
        print("\n📋 CATEGORY BREAKDOWN:")
        for category, results in report["categories"].items():
            if isinstance(results, dict) and "passed" in results:
                print(f"  {category.upper()}: {results['passed']} passed, {results['failed']} failed")
        
        # Recommendations
        if report["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        
        print("="*60)
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        self.log("Starting comprehensive test suite...")
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("Dependency check failed", "ERROR")
            return False
        
        # Run all test categories
        success = True
        
        success &= self.run_backend_tests()
        success &= self.run_mobile_tests()
        success &= self.run_integration_tests()
        success &= self.run_performance_tests()
        
        # Generate and save report
        report = self.generate_report()
        self.save_report(report)
        self.print_summary(report)
        
        return success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for RichesReach AI")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--mobile-only", action="store_true", help="Run only mobile tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose, coverage=not args.no_coverage)
    
    if args.backend_only:
        success = runner.run_backend_tests()
    elif args.mobile_only:
        success = runner.run_mobile_tests()
    elif args.integration_only:
        success = runner.run_integration_tests()
    elif args.performance_only:
        success = runner.run_performance_tests()
    else:
        success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
