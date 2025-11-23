"""
Management command to evaluate signal performance at different horizons.
Run this nightly (or every 30min/2hrs) to track how picks performed.

Usage:
    python manage.py evaluate_signal_performance --horizon 30m
    python manage.py evaluate_signal_performance --horizon 2h
    python manage.py evaluate_signal_performance --horizon EOD
    python manage.py evaluate_signal_performance --all
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging
import os
import aiohttp
import asyncio

from core.signal_performance_models import DayTradingSignal, SignalPerformance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Evaluate performance of day trading signals at specified horizons'

    def add_arguments(self, parser):
        parser.add_argument(
            '--horizon',
            type=str,
            choices=['30m', '2h', 'EOD', '1d', '2d'],
            help='Time horizon to evaluate (30m, 2h, EOD, 1d, 2d)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Evaluate all horizons'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be evaluated without saving'
        )

    def handle(self, *args, **options):
        horizon = options.get('horizon')
        evaluate_all = options.get('all', False)
        dry_run = options.get('dry_run', False)
        
        if not horizon and not evaluate_all:
            self.stdout.write(self.style.ERROR('Must specify --horizon or --all'))
            return
        
        horizons_to_evaluate = []
        if evaluate_all:
            horizons_to_evaluate = ['30m', '2h', 'EOD', '1d', '2d']
        else:
            horizons_to_evaluate = [horizon]
        
        for h in horizons_to_evaluate:
            self.stdout.write(self.style.SUCCESS(f'\n📊 Evaluating {h} horizon...'))
            count = self.evaluate_horizon(h, dry_run)
            self.stdout.write(self.style.SUCCESS(f'✅ Evaluated {count} signals for {h} horizon'))
    
    def evaluate_horizon(self, horizon, dry_run=False):
        """Evaluate signals for a specific time horizon"""
        now = timezone.now()
        
        # Calculate time window based on horizon
        if horizon == '30m':
            time_delta = timedelta(minutes=30)
            min_age = timedelta(minutes=25)  # Signals must be at least 25 min old
            max_age = timedelta(hours=2)  # But not older than 2 hours
        elif horizon == '2h':
            time_delta = timedelta(hours=2)
            min_age = timedelta(hours=1, minutes=50)
            max_age = timedelta(hours=4)
        elif horizon == 'EOD':
            # End of day - evaluate signals from today
            time_delta = timedelta(hours=6)  # Market close is ~6.5 hours after open
            min_age = timedelta(hours=5)
            max_age = timedelta(hours=8)
        elif horizon == '1d':
            time_delta = timedelta(days=1)
            min_age = timedelta(hours=20)
            max_age = timedelta(days=2)
        elif horizon == '2d':
            time_delta = timedelta(days=2)
            min_age = timedelta(days=1, hours=20)
            max_age = timedelta(days=3)
        else:
            return 0
        
        # Find signals that need evaluation
        cutoff_time = now - time_delta
        min_time = now - max_age
        max_time = now - min_age
        
        signals = DayTradingSignal.objects.filter(
            generated_at__gte=min_time,
            generated_at__lte=max_time
        ).exclude(
            performance__horizon=horizon  # Don't re-evaluate
        )
        
        count = 0
        for signal in signals:
            try:
                # Calculate time since signal
                age = now - signal.generated_at
                if age < min_age or age > max_age:
                    continue
                
                # Fetch current price
                current_price = asyncio.run(self.fetch_current_price(signal.symbol))
                if not current_price:
                    logger.warning(f"Could not fetch price for {signal.symbol}")
                    continue
                
                # Calculate PnL
                if signal.side == 'LONG':
                    pnl_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
                    pnl_dollars = (current_price - signal.entry_price) * signal.suggested_size_shares
                else:  # SHORT
                    pnl_pct = ((signal.entry_price - current_price) / signal.entry_price) * 100
                    pnl_dollars = (signal.entry_price - current_price) * signal.suggested_size_shares
                
                # Check if stop/targets hit
                hit_stop = False
                hit_target_1 = False
                hit_target_2 = False
                hit_time_stop = False
                
                if signal.side == 'LONG':
                    if current_price <= signal.stop_price:
                        hit_stop = True
                    if signal.target_prices and len(signal.target_prices) > 0:
                        if current_price >= signal.target_prices[0]:
                            hit_target_1 = True
                        if len(signal.target_prices) > 1 and current_price >= signal.target_prices[1]:
                            hit_target_2 = True
                else:  # SHORT
                    if current_price >= signal.stop_price:
                        hit_stop = True
                    if signal.target_prices and len(signal.target_prices) > 0:
                        if current_price <= signal.target_prices[0]:
                            hit_target_1 = True
                        if len(signal.target_prices) > 1 and current_price <= signal.target_prices[1]:
                            hit_target_2 = True
                
                # Check time stop
                if age.total_seconds() / 60 >= signal.time_stop_minutes:
                    hit_time_stop = True
                
                # Determine outcome
                if hit_stop:
                    outcome = 'STOP_HIT'
                elif hit_target_2:
                    outcome = 'TARGET_HIT'
                elif hit_target_1:
                    outcome = 'TARGET_HIT'
                elif pnl_pct > 0.1:
                    outcome = 'WIN'
                elif pnl_pct < -0.1:
                    outcome = 'LOSS'
                else:
                    outcome = 'BREAKEVEN'
                
                if not dry_run:
                    # Create or update performance record
                    perf, created = SignalPerformance.objects.update_or_create(
                        signal=signal,
                        horizon=horizon,
                        defaults={
                            'evaluated_at': now,
                            'price_at_horizon': current_price,
                            'pnl_dollars': pnl_dollars,
                            'pnl_percent': pnl_pct,
                            'hit_stop': hit_stop,
                            'hit_target_1': hit_target_1,
                            'hit_target_2': hit_target_2,
                            'hit_time_stop': hit_time_stop,
                            'outcome': outcome,
                        }
                    )
                    if created:
                        logger.debug(f"✅ Created {horizon} performance for {signal.symbol}")
                    else:
                        logger.debug(f"🔄 Updated {horizon} performance for {signal.symbol}")
                else:
                    self.stdout.write(
                        f"  {signal.symbol} {signal.side}: {pnl_pct:.2f}% ({outcome})"
                    )
                
                count += 1
            except Exception as e:
                logger.error(f"Error evaluating {signal.symbol} for {horizon}: {e}", exc_info=True)
                continue
        
        return count
    
    async def fetch_current_price(self, symbol):
        """Fetch current price from multiple providers"""
        # Try Polygon first
        polygon_key = os.getenv('POLYGON_API_KEY')
        if polygon_key:
            try:
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
                params = {'adjusted': 'true', 'apiKey': polygon_key}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get('results', [])
                            if results and len(results) > 0:
                                return float(results[0].get('c', 0))
            except:
                pass
        
        # Try Finnhub
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            try:
                url = "https://finnhub.io/api/v1/quote"
                params = {'symbol': symbol, 'token': finnhub_key}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                        if response.status == 200:
                            data = await response.json()
                            price = data.get('c', 0)
                            if price and price > 0:
                                return float(price)
            except:
                pass
        
        return None

