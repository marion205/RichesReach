# core/management/commands/test_advanced_stock_service.py
from django.core.management.base import BaseCommand
from django.conf import settings
from core.stock_service import advanced_stock_service, stock_cache, rate_limiter
import time
import json

class Command(BaseCommand):
    help = 'Test the advanced stock service with caching and rate limiting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL'],
            help='Stock symbols to test'
        )
        parser.add_argument(
            '--test-cache',
            action='store_true',
            help='Test caching functionality'
        )
        parser.add_argument(
            '--test-rate-limit',
            action='store_true',
            help='Test rate limiting'
        )
        parser.add_argument(
            '--test-batch',
            action='store_true',
            help='Test batch processing'
        )

    def handle(self, *args, **options):
        symbols = options['symbols']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Testing Advanced Stock Service with symbols: {", ".join(symbols)}')
        )
        
        # Test basic functionality
        self.test_basic_functionality(symbols[0])
        
        if options['test_cache']:
            self.test_caching(symbols[0])
        
        if options['test_rate_limit']:
            self.test_rate_limiting()
        
        if options['test_batch']:
            self.test_batch_processing(symbols)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Advanced Stock Service testing completed!')
        )

    def test_basic_functionality(self, symbol):
        """Test basic stock service functionality"""
        self.stdout.write(f'\n📊 Testing basic functionality for {symbol}...')
        
        try:
            # Test quote data
            quote_data = advanced_stock_service.get_stock_quote(symbol)
            if quote_data:
                self.stdout.write(f'✅ Quote data retrieved successfully')
                if 'Global Quote' in quote_data:
                    quote = quote_data['Global Quote']
                    self.stdout.write(f'   Price: ${quote.get("05. price", "N/A")}')
                    self.stdout.write(f'   Change: {quote.get("09. change", "N/A")} ({quote.get("10. change percent", "N/A")})')
            else:
                self.stdout.write(f'❌ Failed to retrieve quote data')
            
            # Test company overview
            overview_data = advanced_stock_service.get_company_overview(symbol)
            if overview_data:
                self.stdout.write(f'✅ Company overview retrieved successfully')
                self.stdout.write(f'   Company: {overview_data.get("Name", "N/A")}')
                self.stdout.write(f'   Sector: {overview_data.get("Sector", "N/A")}')
                self.stdout.write(f'   Market Cap: ${overview_data.get("MarketCapitalization", "N/A")}')
            else:
                self.stdout.write(f'❌ Failed to retrieve company overview')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing basic functionality: {e}')
            )

    def test_caching(self, symbol):
        """Test caching functionality"""
        self.stdout.write(f'\n💾 Testing caching for {symbol}...')
        
        try:
            # First request (should cache)
            start_time = time.time()
            quote_data_1 = advanced_stock_service.get_stock_quote(symbol)
            first_request_time = time.time() - start_time
            
            # Second request (should use cache)
            start_time = time.time()
            quote_data_2 = advanced_stock_service.get_stock_quote(symbol)
            second_request_time = time.time() - start_time
            
            if quote_data_1 and quote_data_2:
                self.stdout.write(f'✅ Caching test completed')
                self.stdout.write(f'   First request: {first_request_time:.3f}s')
                self.stdout.write(f'   Second request: {second_request_time:.3f}s')
                self.stdout.write(f'   Cache speedup: {first_request_time/second_request_time:.1f}x')
                
                # Test cache invalidation
                if stock_cache.invalidate('QUOTE_DATA', symbol):
                    self.stdout.write(f'✅ Cache invalidation successful')
                else:
                    self.stdout.write(f'❌ Cache invalidation failed')
            else:
                self.stdout.write(f'❌ Caching test failed - no data retrieved')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing caching: {e}')
            )

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        self.stdout.write(f'\n⏱️ Testing rate limiting...')
        
        try:
            # Check current rate limit status
            rate_info = rate_limiter.check_rate_limit()
            self.stdout.write(f'📊 Current rate limit status: {rate_info.status.value}')
            self.stdout.write(f'   Remaining requests: {rate_info.remaining_requests}')
            self.stdout.write(f'   Reset time: {rate_info.reset_time}')
            
            if rate_info.retry_after:
                self.stdout.write(f'   Retry after: {rate_info.retry_after}s')
            
            # Test rate limit increment
            if rate_limiter.increment_usage():
                self.stdout.write(f'✅ Rate limit usage incremented')
                
                # Check updated status
                updated_rate_info = rate_limiter.check_rate_limit()
                self.stdout.write(f'📊 Updated rate limit status: {updated_rate_info.status.value}')
                self.stdout.write(f'   Remaining requests: {updated_rate_info.remaining_requests}')
            else:
                self.stdout.write(f'❌ Failed to increment rate limit usage')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing rate limiting: {e}')
            )

    def test_batch_processing(self, symbols):
        """Test batch processing functionality"""
        self.stdout.write(f'\n🔄 Testing batch processing for {len(symbols)} symbols...')
        
        try:
            start_time = time.time()
            results = advanced_stock_service.batch_analyze_stocks(symbols)
            batch_time = time.time() - start_time
            
            self.stdout.write(f'✅ Batch processing completed in {batch_time:.2f}s')
            
            for symbol, result in results.items():
                if 'error' in result:
                    self.stdout.write(f'   ❌ {symbol}: {result["error"]}')
                else:
                    self.stdout.write(f'   ✅ {symbol}: Analysis completed')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing batch processing: {e}')
            )

    def display_cache_stats(self):
        """Display cache statistics"""
        try:
            # Get cache keys
            all_keys = stock_cache.redis_client.keys("stock:*")
            rate_limit_keys = stock_cache.redis_client.keys("rate_limit:*")
            
            self.stdout.write(f'\n📊 Cache Statistics:')
            self.stdout.write(f'   Stock data keys: {len(all_keys)}')
            self.stdout.write(f'   Rate limit keys: {len(rate_limit_keys)}')
            
            # Show some sample keys
            if all_keys:
                self.stdout.write(f'   Sample stock keys: {all_keys[:3]}')
            if rate_limit_keys:
                self.stdout.write(f'   Sample rate limit keys: {rate_limit_keys[:3]}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error displaying cache stats: {e}')
            )
