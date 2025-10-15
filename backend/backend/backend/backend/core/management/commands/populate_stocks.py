from django.core.management.base import BaseCommand
from core.models import Stock


class Command(BaseCommand):
    help = 'Populate database with real stock data for ML/AI backend'

    def handle(self, *args, **options):
        # Real stock data that matches the ML/AI backend expectations
        real_stocks = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'current_price': 175.50,
                'market_cap': 2800000000000,
                'pe_ratio': 28.5,
                'dividend_yield': 0.44,
                'beginner_friendly_score': 90
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'current_price': 380.25,
                'market_cap': 2800000000000,
                'pe_ratio': 32.1,
                'dividend_yield': 0.68,
                'beginner_friendly_score': 85
            },
            {
                'symbol': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'sector': 'Automotive',
                'current_price': 250.75,
                'market_cap': 800000000000,
                'pe_ratio': 45.2,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 60
            },
            {
                'symbol': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'current_price': 450.30,
                'market_cap': 1100000000000,
                'pe_ratio': 65.8,
                'dividend_yield': 0.04,
                'beginner_friendly_score': 70
            },
            {
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'current_price': 140.85,
                'market_cap': 1800000000000,
                'pe_ratio': 24.3,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 80
            }
        ]
        
        # Clear existing stocks and add new ones
        Stock.objects.all().delete()
        
        for stock_data in real_stocks:
            Stock.objects.create(**stock_data)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {len(real_stocks)} real stocks'
            )
        )