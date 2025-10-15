"""
Management command to backfill swing trading data and warm indexes
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from core.models import OHLCV, Signal
from core.swing_trading.indicators import calculate_all_indicators
from core.swing_trading.tasks import scan_symbol_for_signals

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill swing trading data and warm database indexes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'],
            help='Symbols to process (default: AAPL MSFT GOOGL TSLA AMZN)'
        )
        parser.add_argument(
            '--timeframes',
            nargs='+',
            default=['1d', '5m', '1h'],
            help='Timeframes to process (default: 1d 5m 1h)'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=365,
            help='Number of days back to process (default: 365)'
        )
        parser.add_argument(
            '--warm-indexes',
            action='store_true',
            help='Warm database indexes after backfill'
        )
        parser.add_argument(
            '--generate-signals',
            action='store_true',
            help='Generate signals after backfilling indicators'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        symbols = options['symbols']
        timeframes = options['timeframes']
        days_back = options['days_back']
        warm_indexes = options['warm_indexes']
        generate_signals = options['generate_signals']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting swing trading data backfill for {len(symbols)} symbols, '
                f'{len(timeframes)} timeframes, {days_back} days back'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            # Backfill indicators
            self.backfill_indicators(symbols, timeframes, days_back, dry_run)
            
            # Warm indexes if requested
            if warm_indexes:
                self.warm_indexes(dry_run)
            
            # Generate signals if requested
            if generate_signals:
                self.generate_signals(symbols, timeframes, dry_run)
            
            self.stdout.write(
                self.style.SUCCESS('Swing trading data backfill completed successfully!')
            )
            
        except Exception as e:
            logger.error(f'Error during backfill: {e}')
            raise CommandError(f'Backfill failed: {e}')

    def backfill_indicators(self, symbols, timeframes, days_back, dry_run):
        """Backfill technical indicators for OHLCV data"""
        
        self.stdout.write('Backfilling technical indicators...')
        
        start_date = timezone.now() - timedelta(days=days_back)
        
        for symbol in symbols:
            for timeframe in timeframes:
                self.stdout.write(f'Processing {symbol} {timeframe}...')
                
                if dry_run:
                    # Count records that would be processed
                    count = OHLCV.objects.filter(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp__gte=start_date
                    ).count()
                    self.stdout.write(f'  Would process {count} records')
                    continue
                
                # Get OHLCV data
                ohlcv_data = OHLCV.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp__gte=start_date
                ).order_by('timestamp')
                
                if not ohlcv_data.exists():
                    self.stdout.write(f'  No data found for {symbol} {timeframe}')
                    continue
                
                # Convert to DataFrame for indicator calculation
                import pandas as pd
                
                df_data = []
                for ohlcv in ohlcv_data:
                    df_data.append({
                        'timestamp': ohlcv.timestamp,
                        'open': float(ohlcv.open_price),
                        'high': float(ohlcv.high_price),
                        'low': float(ohlcv.low_price),
                        'close': float(ohlcv.close_price),
                        'volume': ohlcv.volume
                    })
                
                if len(df_data) < 50:
                    self.stdout.write(f'  Insufficient data for {symbol} {timeframe} ({len(df_data)} records)')
                    continue
                
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
                # Calculate indicators
                try:
                    df_with_indicators = calculate_all_indicators(df)
                    
                    # Update OHLCV records
                    updated_count = 0
                    for i, (timestamp, row) in enumerate(df_with_indicators.iterrows()):
                        try:
                            ohlcv = OHLCV.objects.get(
                                symbol=symbol,
                                timeframe=timeframe,
                                timestamp=timestamp
                            )
                            
                            # Update indicators
                            ohlcv.ema_12 = row.get('ema_12')
                            ohlcv.ema_26 = row.get('ema_26')
                            ohlcv.rsi_14 = row.get('rsi_14')
                            ohlcv.atr_14 = row.get('atr_14')
                            ohlcv.volume_sma_20 = row.get('volume_sma_20')
                            
                            ohlcv.save()
                            updated_count += 1
                            
                        except OHLCV.DoesNotExist:
                            continue
                        except Exception as e:
                            logger.warning(f'Error updating OHLCV {symbol} {timeframe} {timestamp}: {e}')
                            continue
                    
                    self.stdout.write(f'  Updated {updated_count} records with indicators')
                    
                except Exception as e:
                    logger.error(f'Error calculating indicators for {symbol} {timeframe}: {e}')
                    self.stdout.write(f'  Error: {e}')

    def warm_indexes(self, dry_run):
        """Warm database indexes for better query performance"""
        
        self.stdout.write('Warming database indexes...')
        
        if dry_run:
            self.stdout.write('  Would warm indexes for: signals, ohlcv, social interactions')
            return
        
        try:
            with connection.cursor() as cursor:
                # Check if we're on Postgres
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                if 'PostgreSQL' in version:
                    self.stdout.write('  Warming Postgres indexes...')
                    
                    # Warm signal indexes
                    cursor.execute("""
                        SELECT COUNT(*) FROM core_signal 
                        WHERE is_active = TRUE 
                        ORDER BY triggered_at DESC 
                        LIMIT 1000
                    """)
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM core_signal 
                        WHERE features @> '{"rsi": 25.0}' 
                        LIMIT 1000
                    """)
                    
                    # Warm OHLCV indexes
                    cursor.execute("""
                        SELECT COUNT(*) FROM core_ohlcv 
                        WHERE symbol = 'AAPL' 
                        AND timeframe = '1d' 
                        ORDER BY timestamp DESC 
                        LIMIT 1000
                    """)
                    
                    # Warm social interaction indexes
                    cursor.execute("""
                        SELECT COUNT(*) FROM core_signallike 
                        ORDER BY created_at DESC 
                        LIMIT 1000
                    """)
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM core_signalcomment 
                        ORDER BY created_at DESC 
                        LIMIT 1000
                    """)
                    
                    self.stdout.write('  Postgres indexes warmed successfully')
                    
                else:
                    self.stdout.write('  Non-Postgres database detected, skipping index warming')
                    
        except Exception as e:
            logger.error(f'Error warming indexes: {e}')
            self.stdout.write(f'  Warning: Could not warm indexes: {e}')

    def generate_signals(self, symbols, timeframes, dry_run):
        """Generate signals for processed symbols"""
        
        self.stdout.write('Generating signals...')
        
        for symbol in symbols:
            for timeframe in timeframes:
                if dry_run:
                    self.stdout.write(f'  Would generate signals for {symbol} {timeframe}')
                    continue
                
                try:
                    # Queue signal generation task
                    scan_symbol_for_signals.delay(symbol, timeframe)
                    self.stdout.write(f'  Queued signal generation for {symbol} {timeframe}')
                    
                except Exception as e:
                    logger.error(f'Error queuing signal generation for {symbol} {timeframe}: {e}')
                    self.stdout.write(f'  Error: {e}')

    def get_database_stats(self):
        """Get database statistics for monitoring"""
        
        stats = {}
        
        try:
            with connection.cursor() as cursor:
                # Count records in each table
                tables = ['core_ohlcv', 'core_signal', 'core_signallike', 'core_signalcomment']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = count
                
                # Get index usage stats (Postgres only)
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                if 'PostgreSQL' in version:
                    cursor.execute("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        WHERE schemaname = 'public' 
                        AND tablename LIKE 'core_%'
                        ORDER BY idx_scan DESC
                        LIMIT 10
                    """)
                    
                    index_stats = cursor.fetchall()
                    stats['index_usage'] = index_stats
                
        except Exception as e:
            logger.error(f'Error getting database stats: {e}')
            stats['error'] = str(e)
        
        return stats
