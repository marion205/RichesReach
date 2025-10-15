#!/usr/bin/env python3
"""
Market Data Loader for RichesReach
Fetches real market data from free APIs and loads it into the database
"""

import os
import sys
import django
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
import time
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import OHLCV
from core.swing_trading.indicators import TechnicalIndicators

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataLoader:
    """Load real market data from various free APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.ti = TechnicalIndicators()
        
    def fetch_yahoo_finance_data(self, symbol, period='1y', interval='1d'):
        """Fetch data from Yahoo Finance (free API)"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': int((datetime.now() - timedelta(days=365)).timestamp()),
                'period2': int(datetime.now().timestamp()),
                'interval': interval,
                'includePrePost': 'false',
                'events': 'div,split'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or not data['chart']['result']:
                logger.warning(f"No data found for {symbol}")
                return None
                
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            
            # Convert to DataFrame
            df_data = []
            for i, timestamp in enumerate(timestamps):
                if (quotes['open'][i] is not None and 
                    quotes['high'][i] is not None and 
                    quotes['low'][i] is not None and 
                    quotes['close'][i] is not None and 
                    quotes['volume'][i] is not None):
                    
                    df_data.append({
                        'timestamp': datetime.fromtimestamp(timestamp),
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i],
                        'close': quotes['close'][i],
                        'volume': quotes['volume'][i]
                    })
            
            if not df_data:
                logger.warning(f"No valid data found for {symbol}")
                return None
                
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def fetch_alpha_vantage_data(self, symbol, api_key=None):
        """Fetch data from Alpha Vantage (requires free API key)"""
        if not api_key:
            logger.warning("Alpha Vantage API key not provided, skipping...")
            return None
            
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': api_key,
                'outputsize': 'full'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                logger.warning(f"No data found for {symbol} from Alpha Vantage")
                return None
                
            time_series = data['Time Series (Daily)']
            
            # Convert to DataFrame
            df_data = []
            for date_str, values in time_series.items():
                df_data.append({
                    'timestamp': datetime.strptime(date_str, '%Y-%m-%d'),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Fetched {len(df)} records for {symbol} from Alpha Vantage")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for the data"""
        try:
            # Calculate indicators
            df['ema_12'] = self.ti.ema(df['close'], 12)
            df['ema_26'] = self.ti.ema(df['close'], 26)
            df['rsi_14'] = self.ti.rsi(df['close'], 14)
            df['atr_14'] = self.ti.atr(df, 14)
            df['volume_sma_20'] = self.ti.sma(df['volume'], 20)
            
            # Handle NaN values
            df = df.fillna(0)
            
            logger.info("Technical indicators calculated successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def save_to_database(self, df, symbol, timeframe='1d'):
        """Save DataFrame to database"""
        try:
            records_created = 0
            records_updated = 0
            
            for timestamp, row in df.iterrows():
                # Create or update OHLCV record
                ohlcv, created = OHLCV.objects.update_or_create(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    defaults={
                        'open_price': Decimal(str(round(row['open'], 2))),
                        'high_price': Decimal(str(round(row['high'], 2))),
                        'low_price': Decimal(str(round(row['low'], 2))),
                        'close_price': Decimal(str(round(row['close'], 2))),
                        'volume': int(row['volume']),
                        'ema_12': Decimal(str(round(row['ema_12'], 2))) if row['ema_12'] > 0 else None,
                        'ema_26': Decimal(str(round(row['ema_26'], 2))) if row['ema_26'] > 0 else None,
                        'rsi_14': Decimal(str(round(row['rsi_14'], 2))) if row['rsi_14'] > 0 else None,
                        'atr_14': Decimal(str(round(row['atr_14'], 2))) if row['atr_14'] > 0 else None,
                        'volume_sma_20': int(row['volume_sma_20']) if row['volume_sma_20'] > 0 else None,
                    }
                )
                
                if created:
                    records_created += 1
                else:
                    records_updated += 1
            
            logger.info(f"Saved {symbol} {timeframe}: {records_created} created, {records_updated} updated")
            return records_created + records_updated
            
        except Exception as e:
            logger.error(f"Error saving {symbol} to database: {e}")
            return 0
    
    def load_symbol_data(self, symbol, timeframe='1d', api_key=None):
        """Load data for a specific symbol"""
        logger.info(f"Loading data for {symbol} {timeframe}...")
        
        # Try Yahoo Finance first (free)
        df = self.fetch_yahoo_finance_data(symbol, interval=timeframe)
        
        # If Yahoo Finance fails, try Alpha Vantage (requires API key)
        if df is None and api_key:
            logger.info(f"Trying Alpha Vantage for {symbol}...")
            df = self.fetch_alpha_vantage_data(symbol, api_key)
        
        if df is None:
            logger.error(f"Failed to fetch data for {symbol}")
            return False
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Save to database
        records_saved = self.save_to_database(df, symbol, timeframe)
        
        if records_saved > 0:
            logger.info(f"Successfully loaded {records_saved} records for {symbol} {timeframe}")
            return True
        else:
            logger.error(f"Failed to save data for {symbol}")
            return False
    
    def load_multiple_symbols(self, symbols, timeframes=['1d'], api_key=None):
        """Load data for multiple symbols"""
        logger.info(f"Loading data for {len(symbols)} symbols...")
        
        results = {}
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    success = self.load_symbol_data(symbol, timeframe, api_key)
                    results[f"{symbol}_{timeframe}"] = success
                    
                    # Rate limiting - be respectful to free APIs
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error loading {symbol} {timeframe}: {e}")
                    results[f"{symbol}_{timeframe}"] = False
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"Data loading complete: {successful}/{total} successful")
        return results

def main():
    """Main function to load market data"""
    print("📊 Market Data Loader for RichesReach")
    print("=" * 50)
    
    # Get API key from environment or user input
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("💡 Alpha Vantage API key not found in environment variables")
        print("   You can get a free API key at: https://www.alphavantage.co/support/#api-key")
        print("   Set ALPHA_VANTAGE_API_KEY environment variable for more data sources")
        print()
    
    # Symbols to load
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
    timeframes = ['1d']  # Can add '5m', '1h' etc. for more granular data
    
    # Create loader and load data
    loader = MarketDataLoader()
    results = loader.load_multiple_symbols(symbols, timeframes, api_key)
    
    # Print summary
    print("\n📈 Data Loading Summary:")
    print("-" * 30)
    for key, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {key}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n🎯 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful > 0:
        print("\n🚀 Market data loaded successfully!")
        print("   You can now:")
        print("   - Run backtests with real data")
        print("   - Train ML models")
        print("   - Generate trading signals")
        print("   - Use the management command to update indicators")
    else:
        print("\n❌ No data was loaded successfully")
        print("   Check your internet connection and API keys")

if __name__ == "__main__":
    main()
