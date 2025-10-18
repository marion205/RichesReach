#!/usr/bin/env python3
"""
Create popular cryptocurrency data - Top 20 by market cap
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

def create_popular_crypto_data():
    """Create top 20 popular cryptocurrencies with current market data"""
    
    # Top 20 cryptocurrencies by market cap (as of late 2024)
    popular_cryptos = [
        # Tier 1 - Major cryptocurrencies
        {
            'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.001'), 'precision': 8, 'is_staking_available': False,
            'price_usd': Decimal('108659.00'), 'price_btc': Decimal('1.0'),
            'price_change_24h': Decimal('2500.00'), 'price_change_percentage_24h': Decimal('2.35')
        },
        {
            'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.01'), 'precision': 6, 'is_staking_available': True,
            'price_usd': Decimal('3800.00'), 'price_btc': Decimal('0.0349'),
            'price_change_24h': Decimal('150.00'), 'price_change_percentage_24h': Decimal('4.11')
        },
        {
            'symbol': 'USDT', 'name': 'Tether', 'coingecko_id': 'tether',
            'volatility_tier': 'LOW', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 2, 'is_staking_available': False,
            'price_usd': Decimal('1.00'), 'price_btc': Decimal('0.0000092'),
            'price_change_24h': Decimal('0.00'), 'price_change_percentage_24h': Decimal('0.00')
        },
        {
            'symbol': 'BNB', 'name': 'BNB', 'coingecko_id': 'binancecoin',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.01'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('650.00'), 'price_btc': Decimal('0.00598'),
            'price_change_24h': Decimal('15.50'), 'price_change_percentage_24h': Decimal('2.44')
        },
        {
            'symbol': 'SOL', 'name': 'Solana', 'coingecko_id': 'solana',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('200.00'), 'price_btc': Decimal('0.0018'),
            'price_change_24h': Decimal('8.50'), 'price_change_percentage_24h': Decimal('4.44')
        },
        
        # Tier 2 - Major altcoins
        {
            'symbol': 'USDC', 'name': 'USD Coin', 'coingecko_id': 'usd-coin',
            'volatility_tier': 'LOW', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 2, 'is_staking_available': False,
            'price_usd': Decimal('1.00'), 'price_btc': Decimal('0.0000092'),
            'price_change_24h': Decimal('0.00'), 'price_change_percentage_24h': Decimal('0.00')
        },
        {
            'symbol': 'XRP', 'name': 'XRP', 'coingecko_id': 'ripple',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': False,
            'price_usd': Decimal('0.62'), 'price_btc': Decimal('0.0000057'),
            'price_change_24h': Decimal('0.02'), 'price_change_percentage_24h': Decimal('3.33')
        },
        {
            'symbol': 'ADA', 'name': 'Cardano', 'coingecko_id': 'cardano',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('0.45'), 'price_btc': Decimal('0.0000041'),
            'price_change_24h': Decimal('0.02'), 'price_change_percentage_24h': Decimal('4.65')
        },
        {
            'symbol': 'AVAX', 'name': 'Avalanche', 'coingecko_id': 'avalanche-2',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('35.00'), 'price_btc': Decimal('0.00032'),
            'price_change_24h': Decimal('1.50'), 'price_change_percentage_24h': Decimal('4.48')
        },
        {
            'symbol': 'DOGE', 'name': 'Dogecoin', 'coingecko_id': 'dogecoin',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': False,
            'price_usd': Decimal('0.15'), 'price_btc': Decimal('0.0000014'),
            'price_change_24h': Decimal('0.01'), 'price_change_percentage_24h': Decimal('7.14')
        },
        
        # Tier 3 - Popular DeFi and Layer 2 tokens
        {
            'symbol': 'MATIC', 'name': 'Polygon', 'coingecko_id': 'matic-network',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('0.85'), 'price_btc': Decimal('0.0000078'),
            'price_change_24h': Decimal('0.04'), 'price_change_percentage_24h': Decimal('4.94')
        },
        {
            'symbol': 'DOT', 'name': 'Polkadot', 'coingecko_id': 'polkadot',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('7.50'), 'price_btc': Decimal('0.000069'),
            'price_change_24h': Decimal('0.35'), 'price_change_percentage_24h': Decimal('4.88')
        },
        {
            'symbol': 'LINK', 'name': 'Chainlink', 'coingecko_id': 'chainlink',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('14.50'), 'price_btc': Decimal('0.000133'),
            'price_change_24h': Decimal('0.65'), 'price_change_percentage_24h': Decimal('4.69')
        },
        {
            'symbol': 'UNI', 'name': 'Uniswap', 'coingecko_id': 'uniswap',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('6.80'), 'price_btc': Decimal('0.000062'),
            'price_change_24h': Decimal('0.30'), 'price_change_percentage_24h': Decimal('4.62')
        },
        {
            'symbol': 'LTC', 'name': 'Litecoin', 'coingecko_id': 'litecoin',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.01'), 'precision': 4, 'is_staking_available': False,
            'price_usd': Decimal('75.00'), 'price_btc': Decimal('0.00069'),
            'price_change_24h': Decimal('3.50'), 'price_change_percentage_24h': Decimal('4.89')
        },
        
        # Tier 4 - Emerging and popular tokens
        {
            'symbol': 'ATOM', 'name': 'Cosmos', 'coingecko_id': 'cosmos',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('8.50'), 'price_btc': Decimal('0.000078'),
            'price_change_24h': Decimal('0.40'), 'price_change_percentage_24h': Decimal('4.94')
        },
        {
            'symbol': 'ALGO', 'name': 'Algorand', 'coingecko_id': 'algorand',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('0.18'), 'price_btc': Decimal('0.0000017'),
            'price_change_24h': Decimal('0.01'), 'price_change_percentage_24h': Decimal('5.88')
        },
        {
            'symbol': 'VET', 'name': 'VeChain', 'coingecko_id': 'vechain',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('0.025'), 'price_btc': Decimal('0.00000023'),
            'price_change_24h': Decimal('0.001'), 'price_change_percentage_24h': Decimal('4.17')
        },
        {
            'symbol': 'FIL', 'name': 'Filecoin', 'coingecko_id': 'filecoin',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('0.1'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('4.20'), 'price_btc': Decimal('0.000039'),
            'price_change_24h': Decimal('0.20'), 'price_change_percentage_24h': Decimal('5.00')
        },
        {
            'symbol': 'TRX', 'name': 'TRON', 'coingecko_id': 'tron',
            'volatility_tier': 'HIGH', 'is_sec_compliant': False, 'regulatory_status': 'UNREGULATED',
            'min_trade_amount': Decimal('1.0'), 'precision': 4, 'is_staking_available': True,
            'price_usd': Decimal('0.12'), 'price_btc': Decimal('0.0000011'),
            'price_change_24h': Decimal('0.005'), 'price_change_percentage_24h': Decimal('4.35')
        }
    ]
    
    print(f"🚀 Creating {len(popular_cryptos)} popular cryptocurrencies...")
    
    created_count = 0
    updated_count = 0
    
    for crypto_data in popular_cryptos:
        # Create or update cryptocurrency
        crypto, created = Cryptocurrency.objects.get_or_create(
            symbol=crypto_data['symbol'],
            defaults={
                'name': crypto_data['name'],
                'coingecko_id': crypto_data['coingecko_id'],
                'is_active': True,
                'volatility_tier': crypto_data['volatility_tier'],
                'is_sec_compliant': crypto_data['is_sec_compliant'],
                'regulatory_status': crypto_data['regulatory_status'],
                'min_trade_amount': crypto_data['min_trade_amount'],
                'precision': crypto_data['precision'],
                'is_staking_available': crypto_data['is_staking_available']
            }
        )
        
        if created:
            print(f"✅ Created: {crypto.symbol} - {crypto.name}")
            created_count += 1
        else:
            print(f"🔄 Updated: {crypto.symbol} - {crypto.name}")
            updated_count += 1
        
        # Create or update price data
        price, price_created = CryptoPrice.objects.get_or_create(
            cryptocurrency=crypto,
            defaults={
                'price_usd': crypto_data['price_usd'],
                'price_btc': crypto_data['price_btc'],
                'volume_24h': Decimal('1000000000'),  # Mock volume
                'market_cap': Decimal('1000000000000'),  # Mock market cap
                'price_change_24h': crypto_data['price_change_24h'],
                'price_change_percentage_24h': crypto_data['price_change_percentage_24h'],
                'rsi_14': Decimal('55.0'),
                'volatility_7d': Decimal('0.15'),
                'volatility_30d': Decimal('0.25'),
                'momentum_score': Decimal('0.6'),
                'sentiment_score': Decimal('0.7')
            }
        )
        
        if price_created:
            print(f"   💰 Price: ${crypto_data['price_usd']} ({crypto_data['price_change_percentage_24h']:+.2f}%)")
        else:
            # Update existing price
            price.price_usd = crypto_data['price_usd']
            price.price_btc = crypto_data['price_btc']
            price.price_change_24h = crypto_data['price_change_24h']
            price.price_change_percentage_24h = crypto_data['price_change_percentage_24h']
            price.save()
            print(f"   💰 Updated price: ${crypto_data['price_usd']} ({crypto_data['price_change_percentage_24h']:+.2f}%)")
    
    print(f"\n🎉 Successfully processed {len(popular_cryptos)} cryptocurrencies!")
    print(f"   📊 Created: {created_count}")
    print(f"   🔄 Updated: {updated_count}")
    print(f"   💰 Total active cryptocurrencies: {Cryptocurrency.objects.filter(is_active=True).count()}")
    
    # Show some examples
    print(f"\n📈 Sample cryptocurrencies now available:")
    for crypto in Cryptocurrency.objects.filter(is_active=True).order_by('symbol')[:10]:
        try:
            price = CryptoPrice.objects.get(cryptocurrency=crypto)
            print(f"   {crypto.symbol}: ${price.price_usd} ({price.price_change_percentage_24h:+.2f}%)")
        except CryptoPrice.DoesNotExist:
            print(f"   {crypto.symbol}: No price data")

if __name__ == '__main__':
    create_popular_crypto_data()
