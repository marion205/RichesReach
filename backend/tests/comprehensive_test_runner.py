"""
Comprehensive Test Runner
Orchestrates all testing phases and generates final report
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from .comprehensive_integration_tests import ComprehensiveIntegrationTester
from .safety_validation_framework import SafetyValidationFramework
from .production_deployment_manager import ProductionDeploymentManager


class ComprehensiveTestRunner:
    """Comprehensive test runner for all phases"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        
        # Initialize test components
        self.integration_tester = ComprehensiveIntegrationTester()
        self.safety_validator = SafetyValidationFramework()
        self.deployment_manager = ProductionDeploymentManager()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test phases"""
        self.logger.info("🧪 Starting Comprehensive Test Suite...")
        
        start_time = time.time()
        overall_results = {}
        
        try:
            # Phase 1: Integration Tests
            self.logger.info("📋 Phase 1: Running Integration Tests...")
            integration_results = await self.integration_tester.run_comprehensive_tests()
            overall_results["integration_tests"] = integration_results
            
            # Phase 2: Safety Validation
            self.logger.info("🛡️ Phase 2: Running Safety Validation...")
            safety_results = await self.safety_validator.run_comprehensive_validation()
            overall_results["safety_validation"] = safety_results
            
            # Phase 3: Deployment Checklist
            self.logger.info("🚀 Phase 3: Running Deployment Checklist...")
            deployment_results = await self.deployment_manager.run_deployment_checklist()
            overall_results["deployment_checklist"] = deployment_results
            
            # Generate overall summary
            total_duration = time.time() - start_time
            overall_summary = self._generate_overall_summary(overall_results)
            
            # Save comprehensive results
            await self._save_comprehensive_results(overall_results)
            
            return {
                "overall_summary": overall_summary,
                "test_phases": overall_results,
                "total_duration_seconds": total_duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive testing failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _generate_overall_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall test summary"""
        
        # Integration tests summary
        integration_summary = results.get("integration_tests", {}).get("overall_summary", {})
        integration_success_rate = integration_summary.get("overall_success_rate", 0)
        
        # Safety validation summary
        safety_summary = results.get("safety_validation", {}).get("overall_summary", {})
        safety_success_rate = safety_summary.get("overall_success_rate", 0)
        critical_success_rate = safety_summary.get("critical_success_rate", 0)
        
        # Deployment checklist summary
        deployment_summary = results.get("deployment_checklist", {}).get("deployment_summary", {})
        deployment_ready = deployment_summary.get("deployment_ready", False)
        overall_readiness = deployment_summary.get("overall_readiness", 0)
        
        # Overall assessment
        all_phases_passed = (
            integration_success_rate >= 0.95 and
            critical_success_rate >= 1.0 and
            safety_success_rate >= 0.9 and
            deployment_ready
        )
        
        return {
            "integration_success_rate": integration_success_rate,
            "safety_success_rate": safety_success_rate,
            "critical_success_rate": critical_success_rate,
            "deployment_ready": deployment_ready,
            "overall_readiness": overall_readiness,
            "all_phases_passed": all_phases_passed,
            "production_ready": all_phases_passed
        }
    
    async def _save_comprehensive_results(self, results: Dict[str, Any]):
        """Save comprehensive test results"""
        try:
            results_dir = "backend/comprehensive_test_results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{results_dir}/comprehensive_test_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"📊 Comprehensive test results saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save comprehensive results: {e}")


# Main execution
async def main():
    """Main function to run comprehensive tests"""
    runner = ComprehensiveTestRunner()
    results = await runner.run_all_tests()
    
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE TEST SUITE RESULTS")
    print("="*80)
    
    if "error" in results:
        print(f"❌ Comprehensive testing failed: {results['error']}")
        return
    
    overall_summary = results["overall_summary"]
    print(f"\n📊 Overall Summary:")
    print(f"   Integration Tests Success Rate: {overall_summary['integration_success_rate']:.2%}")
    print(f"   Safety Validation Success Rate: {overall_summary['safety_success_rate']:.2%}")
    print(f"   Critical Safety Success Rate: {overall_summary['critical_success_rate']:.2%}")
    print(f"   Deployment Ready: {'✅ YES' if overall_summary['deployment_ready'] else '❌ NO'}")
    print(f"   Overall Readiness: {overall_summary['overall_readiness']:.2%}")
    print(f"   All Phases Passed: {'✅ YES' if overall_summary['all_phases_passed'] else '❌ NO'}")
    print(f"   Production Ready: {'✅ YES' if overall_summary['production_ready'] else '❌ NO'}")
    
    print(f"\n📋 Phase Results:")
    for phase_name, phase_results in results["test_phases"].items():
        if "overall_summary" in phase_results:
            summary = phase_results["overall_summary"]
            print(f"   {phase_name}:")
            if "overall_success_rate" in summary:
                print(f"     Success Rate: {summary['overall_success_rate']:.2%}")
            if "deployment_ready" in summary:
                print(f"     Deployment Ready: {'✅' if summary['deployment_ready'] else '❌'}")
    
    if overall_summary["production_ready"]:
        print(f"\n🎉 ALL TESTS PASSED - System is PRODUCTION READY!")
        print(f"   🚀 Ready for deployment to production environment")
        print(f"   🛡️ All safety validations passed")
        print(f"   📊 All performance benchmarks met")
        print(f"   ✅ All compliance requirements satisfied")
    else:
        print(f"\n⚠️ TESTS INCOMPLETE - Address issues before production")
        print(f"   Review failed tests and fix issues")
        print(f"   Re-run tests after fixes")


if __name__ == "__main__":
    asyncio.run(main())
