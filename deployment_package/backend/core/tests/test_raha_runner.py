"""
Test runner for RAHA tests
Run all RAHA-related tests
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

import unittest
from django.test.utils import get_runner
from django.conf import settings

def run_raha_tests():
    """Run all RAHA tests"""
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Discover and run RAHA tests
    test_suite = unittest.TestLoader().discover(
        start_dir=os.path.dirname(__file__),
        pattern='test_raha_*.py',
        top_level_dir=os.path.dirname(os.path.dirname(__file__))
    )
    
    failures = test_runner.run_tests(['core.tests.test_raha_services', 
                                      'core.tests.test_raha_graphql',
                                      'core.tests.test_raha_integration'])
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All RAHA tests passed!")

if __name__ == '__main__':
    run_raha_tests()

