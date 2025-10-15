#!/usr/bin/env python3
"""
Test script to verify stock data is working
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

# Test the mock data function
from core.graphql.queries import get_mock_advanced_screening_results

print("🧪 Testing stock data...")

try:
    # Get mock data
    mock_data = get_mock_advanced_screening_results()
    print(f"✅ Mock data retrieved: {len(mock_data)} stocks")
    
    # Show first few stocks
    for i, stock in enumerate(mock_data[:3]):
        print(f"  {i+1}. {stock.get('symbol', 'N/A')} - {stock.get('company_name', 'N/A')} - ${stock.get('current_price', 0)}")
    
    # Test GraphQL resolver
    from core.schema import BaseQuery
    query = BaseQuery()
    
    # Test stocks resolver
    stocks = query.resolve_stocks(None, limit=5)
    print(f"✅ GraphQL stocks resolver: {len(stocks)} stocks returned")
    
    for i, stock in enumerate(stocks[:3]):
        print(f"  {i+1}. {stock.symbol} - {stock.companyName} - ${stock.currentPrice}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Test complete")
