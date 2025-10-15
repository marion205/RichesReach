"""
Django management command to seed initial cryptocurrency data
"""

from django.core.management.base import BaseCommand
from core.crypto_models import Cryptocurrency


class Command(BaseCommand):
    help = 'Seed initial cryptocurrency data'

    def handle(self, *args, **options):
        # Top 20 cryptocurrencies by market cap
        crypto_data = [
            {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'coingecko_id': 'bitcoin',
                'is_staking_available': False,
                'min_trade_amount': 0.0001,
                'precision': 8,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'coingecko_id': 'ethereum',
                'is_staking_available': True,
                'min_trade_amount': 0.001,
                'precision': 6,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'SOL',
                'name': 'Solana',
                'coingecko_id': 'solana',
                'is_staking_available': True,
                'min_trade_amount': 0.01,
                'precision': 4,
                'volatility_tier': 'EXTREME',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'ADA',
                'name': 'Cardano',
                'coingecko_id': 'cardano',
                'is_staking_available': True,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'DOT',
                'name': 'Polkadot',
                'coingecko_id': 'polkadot',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'MATIC',
                'name': 'Polygon',
                'coingecko_id': 'matic-network',
                'is_staking_available': True,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'AVAX',
                'name': 'Avalanche',
                'coingecko_id': 'avalanche-2',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'LINK',
                'name': 'Chainlink',
                'coingecko_id': 'chainlink',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'UNI',
                'name': 'Uniswap',
                'coingecko_id': 'uniswap',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'LTC',
                'name': 'Litecoin',
                'coingecko_id': 'litecoin',
                'is_staking_available': False,
                'min_trade_amount': 0.01,
                'precision': 4,
                'volatility_tier': 'MEDIUM',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'BCH',
                'name': 'Bitcoin Cash',
                'coingecko_id': 'bitcoin-cash',
                'is_staking_available': False,
                'min_trade_amount': 0.01,
                'precision': 4,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'XRP',
                'name': 'XRP',
                'coingecko_id': 'ripple',
                'is_staking_available': False,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'ATOM',
                'name': 'Cosmos',
                'coingecko_id': 'cosmos',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'NEAR',
                'name': 'NEAR Protocol',
                'coingecko_id': 'near',
                'is_staking_available': True,
                'min_trade_amount': 0.1,
                'precision': 3,
                'volatility_tier': 'EXTREME',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'ALGO',
                'name': 'Algorand',
                'coingecko_id': 'algorand',
                'is_staking_available': True,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'HIGH',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'FTM',
                'name': 'Fantom',
                'coingecko_id': 'fantom',
                'is_staking_available': True,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'EXTREME',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'MANA',
                'name': 'Decentraland',
                'coingecko_id': 'decentraland',
                'is_staking_available': False,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'EXTREME',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'SAND',
                'name': 'The Sandbox',
                'coingecko_id': 'the-sandbox',
                'is_staking_available': False,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'EXTREME',
                'is_sec_compliant': False,
                'regulatory_status': 'UNKNOWN'
            },
            {
                'symbol': 'USDC',
                'name': 'USD Coin',
                'coingecko_id': 'usd-coin',
                'is_staking_available': True,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'LOW',
                'is_sec_compliant': True,
                'regulatory_status': 'STABLE_COIN'
            },
            {
                'symbol': 'USDT',
                'name': 'Tether',
                'coingecko_id': 'tether',
                'is_staking_available': False,
                'min_trade_amount': 1.0,
                'precision': 2,
                'volatility_tier': 'LOW',
                'is_sec_compliant': False,
                'regulatory_status': 'STABLE_COIN'
            }
        ]

        created_count = 0
        updated_count = 0

        for crypto_info in crypto_data:
            crypto, created = Cryptocurrency.objects.get_or_create(
                symbol=crypto_info['symbol'],
                defaults=crypto_info
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created {crypto.symbol} - {crypto.name}')
                )
            else:
                # Update existing record
                for key, value in crypto_info.items():
                    setattr(crypto, key, value)
                crypto.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated {crypto.symbol} - {crypto.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(crypto_data)} cryptocurrencies: '
                f'{created_count} created, {updated_count} updated'
            )
        )
