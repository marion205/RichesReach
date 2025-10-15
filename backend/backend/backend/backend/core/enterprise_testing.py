"""
Enterprise Testing Framework
Comprehensive testing utilities for enterprise-level quality assurance
"""
import unittest
import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
import logging

from .enterprise_config import config
from .enterprise_exceptions import EnterpriseException, ErrorCode
from .enterprise_logging import get_enterprise_logger


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class EnterpriseTestCase(TestCase):
    """Base test case for enterprise-level testing"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logger = get_enterprise_logger('test')
        cls.test_start_time = time.time()
        cls.logger.info(f"Starting test class: {cls.__name__}")
    
    @classmethod
    def tearDownClass(cls):
        test_duration = time.time() - cls.test_start_time
        cls.logger.info(f"Completed test class: {cls.__name__} in {test_duration:.3f}s")
        super().tearDownClass()
    
    def setUp(self):
        super().setUp()
        self.test_start_time = time.time()
        self.logger.info(f"Starting test: {self._testMethodName}")
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        test_duration = time.time() - self.test_start_time
        self.logger.info(f"Completed test: {self._testMethodName} in {test_duration:.3f}s")
        super().tearDown()
    
    def assertEnterpriseException(
        self,
        callable_obj: Callable,
        expected_error_code: ErrorCode,
        *args,
        **kwargs
    ):
        """Assert that a callable raises an EnterpriseException with specific error code"""
        with self.assertRaises(EnterpriseException) as context:
            callable_obj(*args, **kwargs)
        
        self.assertEqual(context.exception.error_code, expected_error_code)
    
    def assertPerformanceWithinLimit(
        self,
        callable_obj: Callable,
        max_execution_time: float,
        *args,
        **kwargs
    ):
        """Assert that a callable executes within time limit"""
        start_time = time.time()
        result = callable_obj(*args, **kwargs)
        execution_time = time.time() - start_time
        
        self.assertLessEqual(
            execution_time,
            max_execution_time,
            f"Execution time {execution_time:.3f}s exceeded limit {max_execution_time}s"
        )
        
        return result
    
    def assertDataIntegrity(self, data: Dict[str, Any], required_fields: List[str]):
        """Assert data integrity"""
        for field in required_fields:
            self.assertIn(field, data, f"Required field '{field}' missing from data")
            self.assertIsNotNone(data[field], f"Required field '{field}' is None")
    
    def create_test_user(self, username: str = "testuser", **kwargs) -> User:
        """Create test user"""
        user_data = {
            'username': username,
            'email': f"{username}@test.com",
            'password': 'testpass123',
            **kwargs
        }
        
        user = User.objects.create_user(**user_data)
        self.logger.info(f"Created test user: {username}")
        return user
    
    def mock_api_response(self, data: Dict[str, Any], status_code: int = 200):
        """Mock API response"""
        mock_response = Mock()
        mock_response.json.return_value = data
        mock_response.status_code = status_code
        mock_response.text = json.dumps(data)
        return mock_response


class EnterpriseAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    """Base async test case for enterprise-level testing"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logger = get_enterprise_logger('async_test')
        cls.test_start_time = time.time()
        cls.logger.info(f"Starting async test class: {cls.__name__}")
    
    @classmethod
    def tearDownClass(cls):
        test_duration = time.time() - cls.test_start_time
        cls.logger.info(f"Completed async test class: {cls.__name__} in {test_duration:.3f}s")
        super().tearDownClass()
    
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.test_start_time = time.time()
        self.logger.info(f"Starting async test: {self._testMethodName}")
    
    async def asyncTearDown(self):
        test_duration = time.time() - self.test_start_time
        self.logger.info(f"Completed async test: {self._testMethodName} in {test_duration:.3f}s")
        await super().asyncTearDown()
    
    async def assertAsyncPerformanceWithinLimit(
        self,
        coro,
        max_execution_time: float,
        *args,
        **kwargs
    ):
        """Assert that an async callable executes within time limit"""
        start_time = time.time()
        result = await coro(*args, **kwargs)
        execution_time = time.time() - start_time
        
        self.assertLessEqual(
            execution_time,
            max_execution_time,
            f"Async execution time {execution_time:.3f}s exceeded limit {max_execution_time}s"
        )
        
        return result


class PerformanceTestMixin:
    """Mixin for performance testing"""
    
    def assert_response_time(self, response, max_time: float):
        """Assert response time is within limit"""
        if hasattr(response, 'elapsed'):
            self.assertLessEqual(
                response.elapsed.total_seconds(),
                max_time,
                f"Response time {response.elapsed.total_seconds():.3f}s exceeded limit {max_time}s"
            )
    
    def measure_execution_time(self, func: Callable, *args, **kwargs) -> float:
        """Measure function execution time"""
        start_time = time.time()
        func(*args, **kwargs)
        return time.time() - start_time
    
    async def measure_async_execution_time(self, coro, *args, **kwargs) -> float:
        """Measure async function execution time"""
        start_time = time.time()
        await coro(*args, **kwargs)
        return time.time() - start_time


class SecurityTestMixin:
    """Mixin for security testing"""
    
    def assert_no_sql_injection(self, endpoint: str, malicious_input: str):
        """Assert endpoint is protected against SQL injection"""
        client = Client()
        response = client.post(endpoint, {'input': malicious_input})
        
        # Should not return 500 error (which might indicate SQL injection)
        self.assertNotEqual(response.status_code, 500)
        
        # Should handle malicious input gracefully
        self.assertIn(response.status_code, [200, 400, 401, 403, 422])
    
    def assert_authentication_required(self, endpoint: str, method: str = 'GET'):
        """Assert endpoint requires authentication"""
        client = Client()
        
        if method.upper() == 'GET':
            response = client.get(endpoint)
        elif method.upper() == 'POST':
            response = client.post(endpoint)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        self.assertIn(response.status_code, [401, 403])
    
    def assert_csrf_protection(self, endpoint: str):
        """Assert endpoint has CSRF protection"""
        client = Client(enforce_csrf_checks=True)
        response = client.post(endpoint, {})
        
        # Should return 403 Forbidden due to CSRF protection
        self.assertEqual(response.status_code, 403)


class DataIntegrityTestMixin:
    """Mixin for data integrity testing"""
    
    def assert_required_fields(self, data: Dict[str, Any], required_fields: List[str]):
        """Assert all required fields are present"""
        for field in required_fields:
            self.assertIn(field, data, f"Required field '{field}' missing")
            self.assertIsNotNone(data[field], f"Required field '{field}' is None")
    
    def assert_data_types(self, data: Dict[str, Any], field_types: Dict[str, type]):
        """Assert data types are correct"""
        for field, expected_type in field_types.items():
            if field in data:
                self.assertIsInstance(
                    data[field],
                    expected_type,
                    f"Field '{field}' should be {expected_type.__name__}, got {type(data[field]).__name__}"
                )
    
    def assert_data_validation(self, validator_func: Callable, valid_data: Dict[str, Any], invalid_data: Dict[str, Any]):
        """Assert data validation works correctly"""
        # Valid data should pass
        try:
            validator_func(valid_data)
        except Exception as e:
            self.fail(f"Valid data failed validation: {e}")
        
        # Invalid data should fail
        with self.assertRaises(Exception):
            validator_func(invalid_data)


class APITestMixin:
    """Mixin for API testing"""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.api_base_url = '/api/v1'
    
    def assert_api_response_format(self, response, expected_fields: List[str] = None):
        """Assert API response has correct format"""
        self.assertEqual(response.status_code, 200)
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
        
        self.assertIn('success', data)
        self.assertIn('data', data)
        
        if expected_fields:
            for field in expected_fields:
                self.assertIn(field, data['data'], f"Expected field '{field}' missing from response")
    
    def assert_api_error_format(self, response, expected_status_code: int = 400):
        """Assert API error response has correct format"""
        self.assertEqual(response.status_code, expected_status_code)
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.fail("Error response is not valid JSON")
        
        self.assertIn('success', data)
        self.assertIn('error', data)
        self.assertFalse(data['success'])
    
    def make_authenticated_request(self, method: str, url: str, user: User = None, **kwargs):
        """Make authenticated API request"""
        if user:
            self.client.force_login(user)
        
        if method.upper() == 'GET':
            return self.client.get(url, **kwargs)
        elif method.upper() == 'POST':
            return self.client.post(url, **kwargs)
        elif method.upper() == 'PUT':
            return self.client.put(url, **kwargs)
        elif method.upper() == 'DELETE':
            return self.client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")


class TestSuite:
    """Test suite management"""
    
    def __init__(self, name: str):
        self.name = name
        self.tests: List[TestResult] = []
        self.logger = get_enterprise_logger('test_suite')
    
    def add_test_result(self, result: TestResult):
        """Add test result to suite"""
        self.tests.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test suite summary"""
        total_tests = len(self.tests)
        passed_tests = sum(1 for test in self.tests if test.passed)
        failed_tests = total_tests - passed_tests
        
        total_time = sum(test.execution_time for test in self.tests)
        
        return {
            'suite_name': self.name,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_execution_time': total_time,
            'average_execution_time': total_time / total_tests if total_tests > 0 else 0
        }
    
    def generate_report(self) -> str:
        """Generate test suite report"""
        summary = self.get_summary()
        
        report = f"""
Test Suite Report: {summary['suite_name']}
========================================
Total Tests: {summary['total_tests']}
Passed: {summary['passed_tests']}
Failed: {summary['failed_tests']}
Success Rate: {summary['success_rate']:.2f}%
Total Execution Time: {summary['total_execution_time']:.3f}s
Average Execution Time: {summary['average_execution_time']:.3f}s

Failed Tests:
"""
        
        for test in self.tests:
            if not test.passed:
                report += f"- {test.test_name}: {test.error_message}\n"
        
        return report


def run_enterprise_tests(test_classes: List[Type[unittest.TestCase]]) -> TestSuite:
    """Run enterprise test suite"""
    suite = TestSuite("Enterprise Test Suite")
    logger = get_enterprise_logger('test_runner')
    
    logger.info(f"Starting enterprise test suite with {len(test_classes)} test classes")
    
    for test_class in test_classes:
        logger.info(f"Running test class: {test_class.__name__}")
        
        # Create test suite for this class
        test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        # Record results
        for test_case in test_suite:
            test_name = f"{test_class.__name__}.{test_case._testMethodName}"
            
            # Find corresponding result
            test_result = None
            for test_result_obj in result.failures + result.errors:
                if test_result_obj[0]._testMethodName == test_case._testMethodName:
                    test_result = TestResult(
                        test_name=test_name,
                        passed=False,
                        execution_time=0,  # Would need to measure this
                        error_message=str(test_result_obj[1])
                    )
                    break
            
            if not test_result:
                test_result = TestResult(
                    test_name=test_name,
                    passed=True,
                    execution_time=0  # Would need to measure this
                )
            
            suite.add_test_result(test_result)
    
    logger.info("Enterprise test suite completed")
    logger.info(suite.generate_report())
    
    return suite
