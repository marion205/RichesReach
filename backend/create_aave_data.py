#!/usr/bin/env python3
"""
Create sample AAVE reserves and data for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.crypto_models import Cryptocurrency, LendingReserve
from decimal import Decimal

def create_sample_data():
    print("Creating sample AAVE data...")
    
    # Create cryptocurrencies if they don't exist
    usdc, created = Cryptocurrency.objects.get_or_create(
        symbol='USDC',
        defaults={
            'name': 'USD Coin',
            'is_active': True,
            'decimals': 6
        }
    )
    print(f"USDC: {'created' if created else 'exists'}")
    
    weth, created = Cryptocurrency.objects.get_or_create(
        symbol='WETH',
        defaults={
            'name': 'Wrapped Ether',
            'is_active': True,
            'decimals': 18
        }
    )
    print(f"WETH: {'created' if created else 'exists'}")
    
    usdt, created = Cryptocurrency.objects.get_or_create(
        symbol='USDT',
        defaults={
            'name': 'Tether USD',
            'is_active': True,
            'decimals': 6
        }
    )
    print(f"USDT: {'created' if created else 'exists'}")
    
    # Create lending reserves
    reserves_data = [
        {
            'cryptocurrency': usdc,
            'ltv': Decimal('0.85'),  # 85%
            'liquidation_threshold': Decimal('0.90'),  # 90%
            'can_be_collateral': True,
            'supply_apy': Decimal('0.032'),  # 3.2%
            'variable_borrow_apy': Decimal('0.045'),  # 4.5%
            'stable_borrow_apy': Decimal('0.055'),  # 5.5%
            'is_active': True
        },
        {
            'cryptocurrency': weth,
            'ltv': Decimal('0.80'),  # 80%
            'liquidation_threshold': Decimal('0.85'),  # 85%
            'can_be_collateral': True,
            'supply_apy': Decimal('0.015'),  # 1.5%
            'variable_borrow_apy': Decimal('0.025'),  # 2.5%
            'stable_borrow_apy': Decimal('0.035'),  # 3.5%
            'is_active': True
        },
        {
            'cryptocurrency': usdt,
            'ltv': Decimal('0.80'),  # 80%
            'liquidation_threshold': Decimal('0.85'),  # 85%
            'can_be_collateral': True,
            'supply_apy': Decimal('0.028'),  # 2.8%
            'variable_borrow_apy': Decimal('0.040'),  # 4.0%
            'stable_borrow_apy': Decimal('0.050'),  # 5.0%
            'is_active': True
        }
    ]
    
    for data in reserves_data:
        reserve, created = LendingReserve.objects.get_or_create(
            cryptocurrency=data['cryptocurrency'],
            defaults=data
        )
        print(f"Reserve {data['cryptocurrency'].symbol}: {'created' if created else 'exists'}")
    
    print("Sample AAVE data created successfully!")

if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
