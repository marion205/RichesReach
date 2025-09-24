"""
Django management command to update stocks with real-time data
"""
import asyncio
from django.core.management.base import BaseCommand, CommandError
from core.simple_realtime_service import simple_realtime_service
from core.models import Stock

class Command(BaseCommand):
    help = 'Update stocks with real-time data from APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Update specific stock symbol',
        )
        parser.add_argument(
            '--priority',
            action='store_true',
            help='Update only priority stocks',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all stocks',
        )

    def handle(self, *args, **options):
        if options['symbol']:
            self.update_single_stock(options['symbol'])
        elif options['priority']:
            self.update_priority_stocks()
        elif options['all']:
            self.update_all_stocks()
        else:
            raise CommandError('Please specify --symbol, --priority, or --all')

    def update_single_stock(self, symbol):
        """Update a single stock"""
        self.stdout.write(f'Updating {symbol}...')
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(simple_realtime_service.update_stock_in_database(symbol))
            loop.close()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {symbol}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to update {symbol}')
                )
        except Exception as e:
            raise CommandError(f'Error updating {symbol}: {e}')

    def update_priority_stocks(self):
        """Update priority stocks"""
        self.stdout.write('Updating priority stocks...')
        
        priority_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'JNJ', 'PG']
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(simple_realtime_service.update_priority_stocks(priority_symbols))
            loop.close()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Priority update complete: {results["updated"]}/{results["total"]} updated'
                )
            )
            
            if results['errors']:
                self.stdout.write(
                    self.style.WARNING(f'Errors: {results["errors"]}')
                )
                
        except Exception as e:
            raise CommandError(f'Error updating priority stocks: {e}')

    def update_all_stocks(self):
        """Update all stocks"""
        self.stdout.write('Updating all stocks...')
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(simple_realtime_service.update_all_stocks())
            loop.close()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'All stocks update complete: {results["updated"]}/{results["total"]} updated'
                )
            )
            
            if results['errors']:
                self.stdout.write(
                    self.style.WARNING(f'Errors: {results["errors"]}')
                )
                
        except Exception as e:
            raise CommandError(f'Error updating all stocks: {e}')
