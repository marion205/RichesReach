"""
Collect Training Data for Hybrid LSTM + XGBoost
Bulk collection of historical price data and alternative data for training.
"""
import os
import sys
import django
import logging
from django.core.management.base import BaseCommand
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import aiohttp
import time
from pathlib import Path

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Collect historical training data for hybrid LSTM + XGBoost model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=None,
            help='Stock symbols to collect (default: core 50 stocks)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=730,  # 2 years
            help='Days of historical data to collect'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='training_data',
            help='Output directory for collected data'
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['alpaca', 'polygon', 'yfinance'],
            default='yfinance',
            help='Data provider to use'
        )
        parser.add_argument(
            '--include-alt-data',
            action='store_true',
            help='Also collect alternative data (options, earnings, insider, sentiment)'
        )
        parser.add_argument(
            '--rate-limit',
            type=float,
            default=0.5,
            help='Rate limit delay between requests (seconds)'
        )

    def handle(self, *args, **options):
        self.stdout.write("📊 Starting Training Data Collection")
        self.stdout.write("=" * 60)
        
        # Get symbols
        if options['symbols']:
            symbols = options['symbols']
        else:
            symbols = self._get_core_stocks()
        
        self.stdout.write(f"\n📈 Collecting data for {len(symbols)} symbols")
        self.stdout.write(f"   Time period: {options['days']} days")
        self.stdout.write(f"   Provider: {options['provider']}")
        self.stdout.write(f"   Output: {options['output_dir']}")
        
        # Create output directories
        output_dir = Path(options['output_dir'])
        price_dir = output_dir / 'price_data'
        alt_dir = output_dir / 'alternative_data'
        price_dir.mkdir(parents=True, exist_ok=True)
        alt_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect data
        successful = 0
        failed = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.stdout.write(f"\n[{i}/{len(symbols)}] Collecting {symbol}...")
                
                # Collect price data
                price_data = self._collect_price_data(
                    symbol,
                    days=options['days'],
                    provider=options['provider']
                )
                
                if price_data is not None and len(price_data) > 0:
                    # Save price data
                    price_file = price_dir / f"{symbol}_1min_{datetime.now().strftime('%Y%m%d')}.csv"
                    price_data.to_csv(price_file)
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Price data: {len(price_data)} bars saved"))
                    successful += 1
                    
                    # Collect alternative data if requested
                    if options['include_alt_data']:
                        alt_data = asyncio.run(
                            self._collect_alternative_data(symbol)
                        )
                        if alt_data:
                            alt_file = alt_dir / f"{symbol}_alt_{datetime.now().strftime('%Y%m%d')}.json"
                            import json
                            with open(alt_file, 'w') as f:
                                json.dump(alt_data, f, indent=2, default=str)
                            self.stdout.write(self.style.SUCCESS(f"   ✅ Alternative data saved"))
                else:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ No price data collected for {symbol}"))
                    failed += 1
                
                # Rate limiting
                if i < len(symbols):
                    time.sleep(options['rate_limit'])
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error collecting {symbol}: {e}"))
                failed += 1
                continue
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 Collection Summary:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Successful: {successful}/{len(symbols)}"))
        if failed > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Failed: {failed}/{len(symbols)}"))
        
        self.stdout.write(f"\n📁 Data saved to: {output_dir.absolute()}")
        self.stdout.write(self.style.SUCCESS("\n✅ Data collection complete!"))
    
    def _get_core_stocks(self) -> list:
        """Get core 50 stocks for training"""
        return [
            # Technology (15)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD',
            'INTC', 'CRM', 'ORCL', 'ADBE', 'NFLX', 'PYPL', 'SQ',
            # Finance (10)
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'COF', 'SCHW', 'BLK',
            # Healthcare (8)
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY',
            # Consumer (7)
            'WMT', 'HD', 'MCD', 'SBUX', 'NKE', 'TGT', 'LOW',
            # Industrial (5)
            'BA', 'CAT', 'GE', 'HON', 'RTX',
            # Energy (3)
            'XOM', 'CVX', 'SLB',
            # Other (2)
            'V', 'MA'
        ]
    
    def _collect_price_data(
        self,
        symbol: str,
        days: int,
        provider: str
    ) -> pd.DataFrame:
        """Collect price data from specified provider"""
        try:
            if provider == 'yfinance':
                return self._collect_yfinance(symbol, days)
            elif provider == 'alpaca':
                return self._collect_alpaca(symbol, days)
            elif provider == 'polygon':
                return self._collect_polygon(symbol, days)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            logger.error(f"Error collecting price data for {symbol}: {e}")
            return None
    
    def _collect_yfinance(self, symbol: str, days: int) -> pd.DataFrame:
        """Collect from yfinance"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            
            # Get 1-minute data (yfinance limits to 7 days, so we'll use daily and resample)
            # For full 1-min data, need to use multiple calls or different provider
            period = f"{days}d"
            
            # Try intraday first (limited to recent data)
            try:
                hist = ticker.history(period='5d', interval='1m')
                if not hist.empty:
                    return hist[['Open', 'High', 'Low', 'Close', 'Volume']]
            except:
                pass
            
            # Fallback to daily (can resample later)
            hist = ticker.history(period=period, interval='1d')
            if hist.empty:
                return None
            
            return hist[['Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            logger.error(f"yfinance error for {symbol}: {e}")
            return None
    
    def _collect_alpaca(self, symbol: str, days: int) -> pd.DataFrame:
        """Collect from Alpaca API"""
        try:
            from .alpaca_trading_service import AlpacaTradingService
            from .broker_models import BrokerAccount
            
            # Get broker account
            broker_account = BrokerAccount.objects.filter(status='ACTIVE').first()
            if not broker_account or not broker_account.access_token:
                logger.warning("Alpaca credentials not available")
                return None
            
            # Use Alpaca API
            import requests
            headers = {
                'APCA-API-KEY-ID': broker_account.api_key or '',
                'APCA-API-SECRET-KEY': broker_account.api_secret or '',
            }
            
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
            params = {
                'timeframe': '1Min',
                'start': (datetime.now() - timedelta(days=days)).isoformat(),
                'limit': 10000
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                bars = data.get('bars', [])
                
                if bars:
                    df = pd.DataFrame(bars)
                    df['timestamp'] = pd.to_datetime(df['t'])
                    df = df.set_index('timestamp')
                    df = df[['o', 'h', 'l', 'c', 'v']]
                    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    return df
            
            return None
            
        except Exception as e:
            logger.error(f"Alpaca error for {symbol}: {e}")
            return None
    
    def _collect_polygon(self, symbol: str, days: int) -> pd.DataFrame:
        """Collect from Polygon.io API"""
        try:
            import os
            api_key = os.getenv('POLYGON_API_KEY')
            if not api_key:
                logger.warning("Polygon API key not configured")
                return None
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start_date}/{datetime.now().strftime('%Y-%m-%d')}"
            params = {'apiKey': api_key, 'adjusted': 'true', 'sort': 'asc'}
            
            import requests
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    df = pd.DataFrame(results)
                    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
                    df = df.set_index('timestamp')
                    df = df[['o', 'h', 'l', 'c', 'v']]
                    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    return df
            
            return None
            
        except Exception as e:
            logger.error(f"Polygon error for {symbol}: {e}")
            return None
    
    async def _collect_alternative_data(self, symbol: str) -> dict:
        """Collect alternative data (options, earnings, insider, sentiment)"""
        try:
            from .hybrid_ml_predictor import HybridMLPredictor
            
            predictor = HybridMLPredictor()
            
            # Get all alternative features
            options_feat = await predictor.options_features.get_options_features(symbol)
            earnings_feat = await predictor.earnings_insider.get_earnings_features(symbol)
            insider_feat = await predictor.earnings_insider.get_insider_features(symbol)
            
            # Get social sentiment
            try:
                from .deep_social_sentiment_service import get_deep_social_sentiment_service
                social_service = get_deep_social_sentiment_service()
                social_data = await social_service.get_comprehensive_sentiment(symbol, hours_back=24)
                social_feat = {
                    'sentiment_score': social_data.sentiment_score,
                    'volume': social_data.volume,
                    'engagement': social_data.engagement_score
                }
            except:
                social_feat = {}
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'options': options_feat,
                'earnings': earnings_feat,
                'insider': insider_feat,
                'social': social_feat
            }
            
        except Exception as e:
            logger.error(f"Error collecting alternative data for {symbol}: {e}")
            return {}

