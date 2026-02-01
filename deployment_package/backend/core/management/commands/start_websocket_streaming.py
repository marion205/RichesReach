"""
Start WebSocket Streaming Service
Initialize WebSocket connections for real-time price data streaming.
"""
import os
import sys
import django
import logging
import asyncio
from django.core.management.base import BaseCommand
from typing import List

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.websocket_streaming import get_websocket_service
from core.broker_models import BrokerAccount

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start WebSocket streaming service for real-time price data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            help='Stock symbols to stream (default: AAPL MSFT GOOGL TSLA NVDA)'
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['alpaca', 'polygon'],
            default='alpaca',
            help='WebSocket provider (alpaca or polygon)'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='API key (optional, will try to get from broker account)'
        )
        parser.add_argument(
            '--api-secret',
            type=str,
            help='API secret (optional, will try to get from broker account)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting WebSocket Streaming Service")
        self.stdout.write("=" * 60)
        
        symbols = options['symbols']
        provider = options['provider']
        
        self.stdout.write(f"\n📊 Streaming {len(symbols)} symbols via {provider}")
        self.stdout.write(f"   Symbols: {', '.join(symbols)}")
        
        # Get API credentials
        api_key = options.get('api_key')
        api_secret = options.get('api_secret')
        
        if not api_key or not api_secret:
            # Try to get from broker account
            try:
                broker_account = BrokerAccount.objects.filter(status='ACTIVE').first()
                if broker_account:
                    if provider == 'alpaca':
                        api_key = api_key or broker_account.api_key
                        api_secret = api_secret or broker_account.api_secret
                    elif provider == 'polygon':
                        # Polygon API key would be in environment or settings
                        api_key = api_key or os.getenv('POLYGON_API_KEY')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   ⚠️ Could not get credentials from broker account: {e}"))
        
        if not api_key:
            self.stdout.write(self.style.ERROR("   ❌ API key required. Set --api-key or configure broker account."))
            return
        
        if provider == 'alpaca' and not api_secret:
            self.stdout.write(self.style.ERROR("   ❌ API secret required for Alpaca. Set --api-secret or configure broker account."))
            return
        
        # Initialize WebSocket service
        ws_service = get_websocket_service()
        
        # Subscribe to price updates
        def price_callback(symbol: str, price_data: dict):
            """Callback for price updates"""
            price = price_data.get('price') or price_data.get('close')
            volume = price_data.get('volume', 0)
            timestamp = price_data.get('timestamp', 'N/A')
            self.stdout.write(f"   📈 {symbol}: ${price:.2f} (vol: {volume:,}) @ {timestamp}")
        
        for symbol in symbols:
            ws_service.subscribe(symbol, price_callback)
        
        self.stdout.write(self.style.SUCCESS(f"\n   ✅ Subscribed to {len(symbols)} symbols"))
        
        # Start streaming
        self.stdout.write(f"\n🔄 Starting {provider} WebSocket connection...")
        self.stdout.write("   (Press Ctrl+C to stop)")
        
        try:
            # Run async streaming
            if provider == 'alpaca':
                asyncio.run(ws_service.start_streaming(
                    symbols=symbols,
                    provider='alpaca',
                    api_key=api_key,
                    api_secret=api_secret
                ))
            elif provider == 'polygon':
                asyncio.run(ws_service.start_streaming(
                    symbols=symbols,
                    provider='polygon',
                    api_key=api_key
                ))
        except KeyboardInterrupt:
            self.stdout.write("\n\n⏹️  Stopping WebSocket streaming...")
            asyncio.run(ws_service.stop_streaming())
            self.stdout.write(self.style.SUCCESS("   ✅ Stopped"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n   ❌ Error: {e}"))
            import traceback
            logger.error(f"WebSocket streaming error: {traceback.format_exc()}")

