#!/usr/bin/env python3
"""
Create sample crypto data for testing
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev_real')
django.setup()

from django.contrib.auth import get_user_model
from core.crypto_models import CryptoPortfolio, CryptoHolding, Cryptocurrency, CryptoPrice
from decimal import Decimal

User = get_user_model()

def create_sample_crypto_data():
    """Create sample crypto data for testing"""
    
    # Get or create test user
    try:
        user = User.objects.get(username='test')
        print(f"✅ Using existing test user: {user.username}")
    except User.DoesNotExist:
        try:
            user = User.objects.get(email='test@example.com')
            print(f"✅ Using existing test user by email: {user.email}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='test',
                email='test@example.com',
                password='password123',
                first_name='Test',
                last_name='User'
            )
            print(f"✅ Created test user: {user.username}")
    
    # Create sample cryptocurrencies
    cryptocurrencies = [
        {
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'coingecko_id': 'bitcoin',
            'is_active': True,
            'volatility_tier': 'HIGH',
            'is_sec_compliant': False,
            'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.001'),
            'precision': 8,
            'is_staking_available': False
        },
        {
            'symbol': 'ETH',
            'name': 'Ethereum',
            'coingecko_id': 'ethereum',
            'is_active': True,
            'volatility_tier': 'HIGH',
            'is_sec_compliant': False,
            'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.01'),
            'precision': 6,
            'is_staking_available': True
        },
        {
            'symbol': 'SOL',
            'name': 'Solana',
            'coingecko_id': 'solana',
            'is_active': True,
            'volatility_tier': 'HIGH',
            'is_sec_compliant': False,
            'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'),
            'precision': 4,
            'is_staking_available': True
        }
    ]
    
    created_cryptos = []
    for crypto_data in cryptocurrencies:
        crypto, created = Cryptocurrency.objects.get_or_create(
            symbol=crypto_data['symbol'],
            defaults=crypto_data
        )
        if created:
            print(f"✅ Created cryptocurrency: {crypto.symbol}")
        else:
            print(f"✅ Using existing cryptocurrency: {crypto.symbol}")
        created_cryptos.append(crypto)
    
    # Create sample crypto prices
    prices = [
        {'symbol': 'BTC', 'price_usd': Decimal('35000.00'), 'price_btc': Decimal('1.0')},
        {'symbol': 'ETH', 'price_usd': Decimal('2500.00'), 'price_btc': Decimal('0.0714')},
        {'symbol': 'SOL', 'price_usd': Decimal('60.00'), 'price_btc': Decimal('0.0017')},
    ]
    
    for price_data in prices:
        crypto = next(c for c in created_cryptos if c.symbol == price_data['symbol'])
        price, created = CryptoPrice.objects.get_or_create(
            cryptocurrency=crypto,
            defaults={
                'price_usd': price_data['price_usd'],
                'price_btc': price_data['price_btc'],
                'volume_24h': Decimal('1000000000'),
                'market_cap': Decimal('1000000000000'),
                'price_change_24h': Decimal('500.00'),
                'price_change_percentage_24h': Decimal('1.5'),
                'rsi_14': Decimal('55.0'),
                'volatility_7d': Decimal('0.15'),
                'volatility_30d': Decimal('0.25'),
                'momentum_score': Decimal('0.6'),
                'sentiment_score': Decimal('0.7')
            }
        )
        if created:
            print(f"✅ Created price for {crypto.symbol}: ${price.price_usd}")
        else:
            print(f"✅ Using existing price for {crypto.symbol}: ${price.price_usd}")
    
    # Create or update crypto portfolio
    portfolio, created = CryptoPortfolio.objects.get_or_create(
        user=user,
        defaults={
            'total_value_usd': Decimal('12547.50'),
            'total_cost_basis': Decimal('11300.00'),
            'total_pnl': Decimal('1247.50'),
            'total_pnl_percentage': Decimal('11.05'),
            'portfolio_volatility': Decimal('0.15'),
            'sharpe_ratio': Decimal('1.8'),
            'max_drawdown': Decimal('8.2'),
            'diversification_score': Decimal('75.0'),
            'top_holding_percentage': Decimal('40.0')
        }
    )
    if created:
        print(f"✅ Created crypto portfolio for {user.username}")
    else:
        print(f"✅ Using existing crypto portfolio for {user.username}")
    
    # Create sample holdings
    holdings_data = [
        {
            'symbol': 'BTC',
            'quantity': Decimal('0.25'),
            'average_cost': Decimal('32000.00'),
            'current_price': Decimal('35000.00'),
            'current_value': Decimal('8750.00'),
            'unrealized_pnl': Decimal('750.00'),
            'unrealized_pnl_percentage': Decimal('8.5'),
            'staked_quantity': Decimal('0.0'),
            'staking_rewards': Decimal('0.0'),
            'staking_apy': None,
            'is_collateralized': False,
            'collateral_value': Decimal('0.0'),
            'loan_amount': Decimal('0.0')
        },
        {
            'symbol': 'ETH',
            'quantity': Decimal('2.5'),
            'average_cost': Decimal('2200.00'),
            'current_price': Decimal('2500.00'),
            'current_value': Decimal('6250.00'),
            'unrealized_pnl': Decimal('750.00'),
            'unrealized_pnl_percentage': Decimal('12.3'),
            'staked_quantity': Decimal('1.0'),
            'staking_rewards': Decimal('0.05'),
            'staking_apy': Decimal('5.0'),
            'is_collateralized': True,
            'collateral_value': Decimal('2500.00'),
            'loan_amount': Decimal('1500.00')
        },
        {
            'symbol': 'SOL',
            'quantity': Decimal('15.0'),
            'average_cost': Decimal('65.00'),
            'current_price': Decimal('60.00'),
            'current_value': Decimal('900.00'),
            'unrealized_pnl': Decimal('-75.00'),
            'unrealized_pnl_percentage': Decimal('-2.1'),
            'staked_quantity': Decimal('10.0'),
            'staking_rewards': Decimal('0.5'),
            'staking_apy': Decimal('7.0'),
            'is_collateralized': False,
            'collateral_value': Decimal('0.0'),
            'loan_amount': Decimal('0.0')
        }
    ]
    
    # Clear existing holdings
    CryptoHolding.objects.filter(portfolio=portfolio).delete()
    
    for holding_data in holdings_data:
        crypto = next(c for c in created_cryptos if c.symbol == holding_data['symbol'])
        holding = CryptoHolding.objects.create(
            portfolio=portfolio,
            cryptocurrency=crypto,
            quantity=holding_data['quantity'],
            average_cost=holding_data['average_cost'],
            current_price=holding_data['current_price'],
            current_value=holding_data['current_value'],
            unrealized_pnl=holding_data['unrealized_pnl'],
            unrealized_pnl_percentage=holding_data['unrealized_pnl_percentage'],
            staked_quantity=holding_data['staked_quantity'],
            staking_rewards=holding_data['staking_rewards'],
            staking_apy=holding_data['staking_apy'],
            is_collateralized=holding_data['is_collateralized'],
            collateral_value=holding_data['collateral_value'],
            loan_amount=holding_data['loan_amount']
        )
        print(f"✅ Created holding: {holding.quantity} {crypto.symbol} = ${holding.current_value}")
    
    print(f"\n🎉 Sample crypto data created successfully!")
    print(f"   User: {user.username} ({user.email})")
    print(f"   Portfolio Value: ${portfolio.total_value_usd}")
    print(f"   Holdings: {CryptoHolding.objects.filter(portfolio=portfolio).count()}")
    print(f"   Cryptocurrencies: {Cryptocurrency.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    create_sample_crypto_data()
