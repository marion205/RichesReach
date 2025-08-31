# core/management/commands/populate_stocks.py
from django.core.management.base import BaseCommand
from core.models import Stock
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with sample stocks for testing'

    def handle(self, *args, **options):
        # Sample stocks that are beginner-friendly
        sample_stocks = [
            {
                'symbol': 'META',
                'company_name': 'Meta Platforms, Inc.',
                'sector': 'Technology',
                'market_cap': 1200000000000,  # $1.2T
                'pe_ratio': Decimal('22.8'),
                'dividend_yield': Decimal('0.0'),
                'debt_ratio': Decimal('0.3'),
                'volatility': Decimal('1.8'),
                'beginner_friendly_score': 75
            },
            {
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'market_cap': 1800000000000,  # $1.8T
                'pe_ratio': Decimal('26.4'),
                'dividend_yield': Decimal('0.0'),
                'debt_ratio': Decimal('0.2'),
                'volatility': Decimal('1.5'),
                'beginner_friendly_score': 78
            },
            {
                'symbol': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'sector': 'Consumer Cyclical',
                'market_cap': 800000000000,  # $800B
                'pe_ratio': Decimal('45.2'),
                'dividend_yield': Decimal('0.0'),
                'debt_ratio': Decimal('0.8'),
                'volatility': Decimal('2.5'),
                'beginner_friendly_score': 65
            },
            {
                'symbol': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'market_cap': 2200000000000,  # $2.2T
                'pe_ratio': Decimal('35.1'),
                'dividend_yield': Decimal('0.1'),
                'debt_ratio': Decimal('0.4'),
                'volatility': Decimal('2.1'),
                'beginner_friendly_score': 70
            },
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'market_cap': 3000000000000,  # $3T
                'pe_ratio': Decimal('25.5'),
                'dividend_yield': Decimal('0.5'),
                'debt_ratio': Decimal('1.2'),
                'volatility': Decimal('1.1'),
                'beginner_friendly_score': 85
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'market_cap': 2800000000000,  # $2.8T
                'pe_ratio': Decimal('28.2'),
                'dividend_yield': Decimal('0.8'),
                'debt_ratio': Decimal('0.8'),
                'volatility': Decimal('1.0'),
                'beginner_friendly_score': 88
            },
            {
                'symbol': 'JNJ',
                'company_name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'market_cap': 400000000000,  # $400B
                'pe_ratio': Decimal('15.8'),
                'dividend_yield': Decimal('3.2'),
                'debt_ratio': Decimal('0.4'),
                'volatility': Decimal('0.7'),
                'beginner_friendly_score': 92
            },
            {
                'symbol': 'PG',
                'company_name': 'Procter & Gamble Co.',
                'sector': 'Consumer Defensive',
                'market_cap': 350000000000,  # $350B
                'pe_ratio': Decimal('22.1'),
                'dividend_yield': Decimal('2.8'),
                'debt_ratio': Decimal('0.6'),
                'volatility': Decimal('0.6'),
                'beginner_friendly_score': 90
            },
            {
                'symbol': 'KO',
                'company_name': 'The Coca-Cola Company',
                'sector': 'Consumer Defensive',
                'market_cap': 250000000000,  # $250B
                'pe_ratio': Decimal('24.5'),
                'dividend_yield': Decimal('3.1'),
                'debt_ratio': Decimal('1.8'),
                'volatility': Decimal('0.8'),
                'beginner_friendly_score': 87
            },
            {
                'symbol': 'V',
                'company_name': 'Visa Inc.',
                'sector': 'Financial Services',
                'market_cap': 500000000000,  # $500B
                'pe_ratio': Decimal('30.2'),
                'dividend_yield': Decimal('0.7'),
                'debt_ratio': Decimal('0.3'),
                'volatility': Decimal('1.2'),
                'beginner_friendly_score': 82
            },
            {
                'symbol': 'WMT',
                'company_name': 'Walmart Inc.',
                'sector': 'Consumer Defensive',
                'market_cap': 450000000000,  # $450B
                'pe_ratio': Decimal('18.9'),
                'dividend_yield': Decimal('1.6'),
                'debt_ratio': Decimal('0.7'),
                'volatility': Decimal('0.7'),
                'beginner_friendly_score': 89
            },
            {
                'symbol': 'HD',
                'company_name': 'The Home Depot, Inc.',
                'sector': 'Consumer Cyclical',
                'market_cap': 300000000000,  # $300B
                'pe_ratio': Decimal('20.1'),
                'dividend_yield': Decimal('2.4'),
                'debt_ratio': Decimal('1.1'),
                'volatility': Decimal('1.0'),
                'beginner_friendly_score': 84
            }
        ]

        created_count = 0
        updated_count = 0

        for stock_data in sample_stocks:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created stock: {stock.symbol} - {stock.company_name}')
                )
            else:
                # Update existing stock
                for key, value in stock_data.items():
                    if key != 'symbol':  # Don't update the symbol
                        setattr(stock, key, value)
                stock.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated stock: {stock.symbol} - {stock.company_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Stock population complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
