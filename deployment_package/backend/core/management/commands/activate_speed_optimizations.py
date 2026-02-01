"""
Activate Speed Optimizations
Start WebSocket streaming and check optimization status.
"""
from django.core.management.base import BaseCommand
from core.speed_optimization_service import get_speed_optimization_service
import asyncio
import os


class Command(BaseCommand):
    help = 'Activate speed optimizations (WebSocket streaming, model optimization)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            help='Symbols to stream via WebSocket (default: AAPL MSFT GOOGL TSLA NVDA)'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check status, do not activate WebSocket'
        )

    def handle(self, *args, **options):
        symbols = options['symbols']
        check_only = options['check_only']
        
        self.stdout.write("🚀 Speed Optimization Service")
        self.stdout.write("=" * 60)
        
        service = get_speed_optimization_service()
        
        # Show current status
        status = service.get_optimization_status()
        
        self.stdout.write("\n📊 Current Status:")
        self.stdout.write(f"   WebSocket Active: {'✅' if status['websocket_active'] else '❌'}")
        self.stdout.write(f"   Model Optimized: {'✅' if status['model_optimized'] else '❌'}")
        self.stdout.write(f"   Target Latency: {status['latency_target_ms']}ms")
        self.stdout.write(f"   Current Avg Latency: {status['current_avg_latency_ms']:.1f}ms")
        self.stdout.write(f"   Below Target: {status['below_target_percent']:.1f}%")
        
        # Show latency stats
        latency_stats = service.get_latency_stats()
        if latency_stats.get('count', 0) > 0:
            self.stdout.write("\n📈 Latency Statistics:")
            self.stdout.write(f"   Count: {latency_stats['count']}")
            self.stdout.write(f"   Avg: {latency_stats['avg_ms']:.1f}ms")
            self.stdout.write(f"   Median: {latency_stats['median_ms']:.1f}ms")
            self.stdout.write(f"   P95: {latency_stats['p95_ms']:.1f}ms")
            self.stdout.write(f"   P99: {latency_stats['p99_ms']:.1f}ms")
            self.stdout.write(f"   Min: {latency_stats['min_ms']:.1f}ms")
            self.stdout.write(f"   Max: {latency_stats['max_ms']:.1f}ms")
        
        # Show recommendations
        recommendations = status['recommendations']
        if recommendations:
            self.stdout.write("\n💡 Recommendations:")
            for rec in recommendations:
                self.stdout.write(f"   • {rec}")
        
        # Activate WebSocket if requested
        if not check_only and not status['websocket_active']:
            self.stdout.write(f"\n🔌 Activating WebSocket streaming for {len(symbols)} symbols...")
            
            # Check for API credentials
            api_key = os.getenv('ALPACA_API_KEY')
            api_secret = os.getenv('ALPACA_API_SECRET')
            
            if not api_key or not api_secret:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  ALPACA_API_KEY and ALPACA_API_SECRET not found in environment"
                    )
                )
                self.stdout.write("   Set these environment variables to enable WebSocket streaming")
                return
            
            # Start WebSocket streaming
            try:
                loop = asyncio.get_event_loop()
                success = loop.run_until_complete(
                    service.start_websocket_streaming(symbols, api_key, api_secret)
                )
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ WebSocket streaming activated for {len(symbols)} symbols"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR("❌ Failed to activate WebSocket streaming")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error activating WebSocket: {e}")
                )
        elif check_only:
            self.stdout.write("\nℹ️  Use without --check-only to activate WebSocket streaming")
        
        self.stdout.write("\n" + "=" * 60)

