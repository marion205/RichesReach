#!/usr/bin/env python3
"""
Django Test Configuration for RichesReach
========================================

This script sets up the Django test environment and runs comprehensive tests
for all new endpoints and features.

Usage: python run_django_tests.py
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def setup_django():
    """Setup Django for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
    
    # Set test database
    os.environ.setdefault('DATABASE_URL', 'postgresql://localhost/richesreach_test')
    
    django.setup()

def run_tests():
    """Run Django tests"""
    print("🚀 Starting Django Tests for RichesReach...")
    print("=" * 50)
    
    # Setup Django
    setup_django()
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Define test modules to run
    test_modules = [
        'core.tests',
        'core.test_social_trading',
        'core.test_pump_fun',
        'core.test_defi_yield',
    ]
    
    # Run tests
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
