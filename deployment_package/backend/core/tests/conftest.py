"""
Pytest configuration for Django tests
"""
import os
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import call_command

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

# Configure Django
django.setup()

# Pytest fixtures can be added here
import pytest

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    """
    pass


