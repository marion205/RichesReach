#!/usr/bin/env python3
import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_endpoints():
    client = Client()
    
    print("Testing Django server endpoints...")
    
    # Test health endpoint
    try:
        response = client.get('/defi/health/')
        print(f"Health endpoint: {response.status_code} - {response.content}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test aave user data endpoint
    try:
        response = client.get('/defi/aave-user-data/?address=0x0000000000000000000000000000000000000001')
        print(f"AAVE user data endpoint: {response.status_code} - {response.content}")
    except Exception as e:
        print(f"AAVE user data endpoint error: {e}")
    
    # Test validation endpoint
    try:
        response = client.post('/defi/validate-transaction/', 
                              {'type': 'borrow', 
                               'wallet_address': '0x0000000000000000000000000000000000000001',
                               'data': {'symbol': 'USDC', 'amountHuman': '100', 'rateMode': 2}},
                              content_type='application/json')
        print(f"Validation endpoint: {response.status_code} - {response.content}")
    except Exception as e:
        print(f"Validation endpoint error: {e}")

if __name__ == '__main__':
    test_endpoints()
