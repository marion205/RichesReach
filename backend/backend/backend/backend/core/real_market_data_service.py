import logging
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class RealMarketDataService:
    """Service for fetching real market data from various APIs"""
    
    def __init__(self):
        self.alpha_vantage_key = None
        self.polygon_key = None
        self.finnhub_key = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RichesReach/1.0 (Financial Analysis App)'
        })
        
        # Rate limiting
        self.last_request_time = {}
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of settings-dependent attributes"""
        if not self._initialized:
            try:
                from django.conf import settings
                self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
                self.polygon_key = getattr(settings, 'POLYGON_API_KEY', None)
                self.finnhub_key = getattr(settings, 'FINNHUB_API_KEY', None)
                self._initialized = True
            except Exception as e:
                # Fallback to defaults if Django settings not available
                self._initialized = True
        self.min_request_interval = 0.1  # 100ms between requests
        
    def _rate_limit(self, api_name: str):
        """Simple rate limiting"""
        now = time.time()
        if api_name in self.last_request_time:
            elapsed = now - self.last_request_time[api_name]
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time[api_name] = time.time()
    
    def get_yahoo_finance_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Optional[Dict[str, Any]]:
        """Get data from Yahoo Finance using yfinance library"""
        self._ensure_initialized()
        try:
            self._rate_limit('yahoo')
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol} on Yahoo Finance")
                return None
            
            # Convert to our format
            data_points = []
            for date, row in hist.iterrows():
                data_points.append({
                    'timestamp': date.isoformat(),
                    'value': float(row['Close']),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': int(row['Volume']),
                })
            
            # Calculate additional metrics
            prices = [point['value'] for point in data_points]
            returns = np.diff(prices) / prices[:-1]
            
            return {
                'symbol': symbol,
                'dataPoints': data_points,
                'startValue': prices[0],
                'endValue': prices[-1],
                'totalReturn': prices[-1] - prices[0],
                'totalReturnPercent': ((prices[-1] - prices[0]) / prices[0]) * 100,
                'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
                'sharpeRatio': self._calculate_sharpe_ratio(returns),
                'maxDrawdown': self._calculate_max_drawdown(prices),
                'source': 'yahoo_finance'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def get_alpha_vantage_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get data from Alpha Vantage API"""
        self._ensure_initialized()
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            self._rate_limit('alpha_vantage')
            
            # Map timeframe to Alpha Vantage function
            function_map = {
                '1D': 'TIME_SERIES_INTRADAY',
                '1W': 'TIME_SERIES_DAILY',
                '1M': 'TIME_SERIES_DAILY',
                '3M': 'TIME_SERIES_DAILY',
                '1Y': 'TIME_SERIES_DAILY',
                'All': 'TIME_SERIES_DAILY'
            }
            
            function = function_map.get(timeframe, 'TIME_SERIES_DAILY')
            interval = '1min' if timeframe == '1D' else None
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'full' if timeframe in ['1Y', 'All'] else 'compact'
            }
            
            if interval:
                params['interval'] = interval
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return None
            
            # Extract time series data
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                logger.error(f"No time series data found for {symbol}")
                return None
            
            time_series = data[time_series_key]
            
            # Convert to our format
            data_points = []
            for timestamp, values in time_series.items():
                data_points.append({
                    'timestamp': timestamp,
                    'value': float(values['4. close']),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'volume': int(values['5. volume']),
                })
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x['timestamp'])
            
            # Calculate metrics
            prices = [point['value'] for point in data_points]
            returns = np.diff(prices) / prices[:-1]
            
            return {
                'symbol': symbol,
                'dataPoints': data_points,
                'startValue': prices[0],
                'endValue': prices[-1],
                'totalReturn': prices[-1] - prices[0],
                'totalReturnPercent': ((prices[-1] - prices[0]) / prices[0]) * 100,
                'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
                'sharpeRatio': self._calculate_sharpe_ratio(returns),
                'maxDrawdown': self._calculate_max_drawdown(prices),
                'source': 'alpha_vantage'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    def get_polygon_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get data from Polygon.io API"""
        self._ensure_initialized()
        if not self.polygon_key:
            logger.warning("Polygon API key not configured")
            return None
            
        try:
            self._rate_limit('polygon')
            
            # Map timeframe to Polygon timespan
            timespan_map = {
                '1D': ('minute', 1),
                '1W': ('day', 1),
                '1M': ('day', 1),
                '3M': ('day', 1),
                '1Y': ('day', 1),
                'All': ('day', 1)
            }
            
            timespan, multiplier = timespan_map.get(timeframe, ('day', 1))
            
            # Calculate date range
            end_date = datetime.now()
            if timeframe == '1D':
                start_date = end_date - timedelta(days=1)
            elif timeframe == '1W':
                start_date = end_date - timedelta(weeks=1)
            elif timeframe == '1M':
                start_date = end_date - timedelta(days=30)
            elif timeframe == '3M':
                start_date = end_date - timedelta(days=90)
            elif timeframe == '1Y':
                start_date = end_date - timedelta(days=365)
            else:  # All
                start_date = end_date - timedelta(days=365*5)
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'apikey': self.polygon_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Polygon API error for {symbol}: {data.get('message', 'Unknown error')}")
                return None
            
            results = data.get('results', [])
            if not results:
                logger.warning(f"No data found for {symbol} on Polygon")
                return None
            
            # Convert to our format
            data_points = []
            for result in results:
                timestamp = datetime.fromtimestamp(result['t'] / 1000)
                data_points.append({
                    'timestamp': timestamp.isoformat(),
                    'value': float(result['c']),  # close
                    'open': float(result['o']),
                    'high': float(result['h']),
                    'low': float(result['l']),
                    'volume': int(result['v']),
                })
            
            # Calculate metrics
            prices = [point['value'] for point in data_points]
            returns = np.diff(prices) / prices[:-1]
            
            return {
                'symbol': symbol,
                'dataPoints': data_points,
                'startValue': prices[0],
                'endValue': prices[-1],
                'totalReturn': prices[-1] - prices[0],
                'totalReturnPercent': ((prices[-1] - prices[0]) / prices[0]) * 100,
                'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
                'sharpeRatio': self._calculate_sharpe_ratio(returns),
                'maxDrawdown': self._calculate_max_drawdown(prices),
                'source': 'polygon'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Polygon data for {symbol}: {e}")
            return None
    
    def get_benchmark_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get benchmark data from the best available source"""
        self._ensure_initialized()
        # Try sources in order of preference
        sources = [
            ('yahoo', self.get_yahoo_finance_data),
            ('alpha_vantage', self.get_alpha_vantage_data),
            ('polygon', self.get_polygon_data),
        ]
        
        for source_name, source_func in sources:
            try:
                data = source_func(symbol, timeframe)
                if data:
                    logger.info(f"Successfully fetched {symbol} data from {source_name}")
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {source_name}: {e}")
                continue
        
        logger.error(f"Failed to fetch data for {symbol} from all sources")
        return None
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """Calculate maximum drawdown"""
        if len(prices) == 0:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100  # Return as percentage
    
    def calculate_beta(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate beta (portfolio volatility relative to benchmark)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 1.0
        
        portfolio_returns = np.array(portfolio_returns)
        benchmark_returns = np.array(benchmark_returns)
        
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    def calculate_correlation(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        return np.corrcoef(portfolio_returns, benchmark_returns)[0, 1]
    
    def calculate_alpha(self, portfolio_return: float, benchmark_return: float, risk_free_rate: float = 0.02) -> float:
        """Calculate alpha (excess return over benchmark)"""
        return portfolio_return - benchmark_return
    
    def calculate_tracking_error(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate tracking error (standard deviation of excess returns)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        excess_returns = np.array(portfolio_returns) - np.array(benchmark_returns)
        return np.std(excess_returns) * np.sqrt(252)  # Annualized
    
    def get_multiple_benchmarks(self, symbols: List[str], timeframe: str) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple benchmarks concurrently"""
        self._ensure_initialized()
        results = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(self.get_benchmark_data, symbol, timeframe): symbol 
                for symbol in symbols
            }
            
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=30)
                    if data:
                        results[symbol] = data
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
        
        return results

# Global instance
real_market_data_service = RealMarketDataService()
