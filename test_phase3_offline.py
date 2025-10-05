#!/usr/bin/env python3
"""
Phase 3 Offline Testing Suite
Tests Phase 3 components without requiring a running server
"""

import sys
import os
import importlib
import traceback
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3OfflineTester:
    """Offline testing for Phase 3 components"""
    
    def __init__(self):
        self.test_results = []
        self.backend_path = "backend/backend"
    
    def add_sys_path(self):
        """Add backend path to sys.path for imports"""
        if os.path.exists(self.backend_path):
            sys.path.insert(0, self.backend_path)
    
    def test_import(self, module_name: str, description: str) -> Dict[str, Any]:
        """Test if a module can be imported"""
        try:
            self.add_sys_path()
            module = importlib.import_module(module_name)
            return {
                "test": description,
                "status": "PASS",
                "message": f"Successfully imported {module_name}",
                "module": module
            }
        except Exception as e:
            return {
                "test": description,
                "status": "FAIL",
                "message": f"Failed to import {module_name}: {str(e)}",
                "error": str(e)
            }
    
    def test_file_exists(self, file_path: str, description: str) -> Dict[str, Any]:
        """Test if a file exists"""
        try:
            if os.path.exists(file_path):
                return {
                    "test": description,
                    "status": "PASS",
                    "message": f"File exists: {file_path}",
                    "file_path": file_path
                }
            else:
                return {
                    "test": description,
                    "status": "FAIL",
                    "message": f"File not found: {file_path}",
                    "file_path": file_path
                }
        except Exception as e:
            return {
                "test": description,
                "status": "FAIL",
                "message": f"Error checking file {file_path}: {str(e)}",
                "error": str(e)
            }
    
    def test_phase3_components(self) -> List[Dict[str, Any]]:
        """Test all Phase 3 components"""
        logger.info("🧪 Starting Phase 3 Offline Tests")
        logger.info("=" * 50)
        
        tests = []
        
        # Test Phase 3 core files
        tests.append(self.test_file_exists("backend/backend/core/ai_router.py", "AI Router Core"))
        tests.append(self.test_file_exists("backend/backend/core/ai_router_api.py", "AI Router API"))
        tests.append(self.test_file_exists("backend/backend/core/analytics_engine.py", "Analytics Engine"))
        tests.append(self.test_file_exists("backend/backend/core/analytics_api.py", "Analytics API"))
        tests.append(self.test_file_exists("backend/backend/core/analytics_websocket.py", "Analytics WebSocket"))
        tests.append(self.test_file_exists("backend/backend/core/advanced_ai_router.py", "Advanced AI Router"))
        tests.append(self.test_file_exists("backend/backend/core/advanced_ai_router_api.py", "Advanced AI Router API"))
        tests.append(self.test_file_exists("backend/backend/core/ai_model_training.py", "AI Model Training"))
        tests.append(self.test_file_exists("backend/backend/core/ai_training_api.py", "AI Training API"))
        tests.append(self.test_file_exists("backend/backend/core/performance_optimizer.py", "Performance Optimizer"))
        tests.append(self.test_file_exists("backend/backend/core/cdn_optimizer.py", "CDN Optimizer"))
        tests.append(self.test_file_exists("backend/backend/core/database_optimizer.py", "Database Optimizer"))
        tests.append(self.test_file_exists("backend/backend/core/performance_api.py", "Performance API"))
        
        # Test deployment files
        tests.append(self.test_file_exists("deploy_phase3.sh", "Phase 3 Deployment Script"))
        tests.append(self.test_file_exists("test_phase3.py", "Phase 3 Test Suite"))
        tests.append(self.test_file_exists("phase3_config.py", "Phase 3 Configuration Manager"))
        tests.append(self.test_file_exists("health_check_phase3.py", "Phase 3 Health Check"))
        tests.append(self.test_file_exists("phase3.env.template", "Phase 3 Environment Template"))
        
        # Test documentation files
        tests.append(self.test_file_exists("PHASE_3_ARCHITECTURE_UPGRADE.md", "Phase 3 Architecture Documentation"))
        tests.append(self.test_file_exists("ADVANCED_AI_INTEGRATION.md", "Advanced AI Integration Documentation"))
        tests.append(self.test_file_exists("PERFORMANCE_OPTIMIZATION.md", "Performance Optimization Documentation"))
        
        # Test imports (these might fail due to dependencies, but we can check the structure)
        try:
            tests.append(self.test_import("core.ai_router", "AI Router Import"))
        except:
            tests.append({
                "test": "AI Router Import",
                "status": "SKIP",
                "message": "AI Router import skipped (dependencies not available)"
            })
        
        try:
            tests.append(self.test_import("core.analytics_engine", "Analytics Engine Import"))
        except:
            tests.append({
                "test": "Analytics Engine Import",
                "status": "SKIP",
                "message": "Analytics Engine import skipped (dependencies not available)"
            })
        
        try:
            tests.append(self.test_import("core.performance_optimizer", "Performance Optimizer Import"))
        except:
            tests.append({
                "test": "Performance Optimizer Import",
                "status": "SKIP",
                "message": "Performance Optimizer import skipped (dependencies not available)"
            })
        
        return tests
    
    def print_results(self, tests: List[Dict[str, Any]]):
        """Print test results"""
        passed = len([t for t in tests if t["status"] == "PASS"])
        failed = len([t for t in tests if t["status"] == "FAIL"])
        skipped = len([t for t in tests if t["status"] == "SKIP"])
        total = len(tests)
        
        logger.info("")
        logger.info("📊 Test Results Summary")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        if failed > 0:
            logger.info("")
            logger.info("❌ Failed Tests:")
            for test in tests:
                if test["status"] == "FAIL":
                    logger.info(f"  - {test['test']}: {test['message']}")
        
        # Show skipped tests
        if skipped > 0:
            logger.info("")
            logger.info("⏭️  Skipped Tests:")
            for test in tests:
                if test["status"] == "SKIP":
                    logger.info(f"  - {test['test']}: {test['message']}")
        
        logger.info("")
        if failed == 0:
            logger.info("🎉 All Phase 3 components are properly structured!")
        else:
            logger.info(f"⚠️  {failed} tests failed. Please check the missing files.")
        
        return failed == 0

def main():
    """Main test runner"""
    tester = Phase3OfflineTester()
    tests = tester.test_phase3_components()
    success = tester.print_results(tests)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
