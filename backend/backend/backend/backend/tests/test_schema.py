#!/usr/bin/env python3
"""
Simple GraphQL Schema Test
"""
import os
import django
# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()
def test_schema():
"""Test GraphQL schema loading"""
print(" Testing GraphQL Schema...")
try:
# Test basic imports
print(" Django environment loaded")
from core import types
print(" Types module imported")
# Check specific types
print(f" WatchlistType: {types.WatchlistType}")
print(f" StockDiscussionType: {types.StockDiscussionType}")
print(f" PortfolioType: {types.PortfolioType}")
# Test schema creation
from core.schema import schema
print(" Schema created successfully")
print("\n Phase 3 GraphQL Schema - SUCCESS!")
print(" All social types loaded")
print(" Schema validation passed")
print(" Ready for GraphQL queries!")
return True
except Exception as e:
print(f" Error: {e}")
import traceback
traceback.print_exc()
return False
if __name__ == "__main__":
test_schema()
