"""
Industry-Standard Real-Time Stock Data Service
Integrates multiple data sources with intelligent fallbacks and caching
"""

import os
import json
import requests
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@dataclass
class StockQuote:
    """Real-time stock quote with comprehensive data"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    pe_ratio: float
    dividend_yield: float
    high_52_week: float
    low_52_week: float
    timestamp: datetime
    source: str

@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""
    rsi: float
    macd: float
    sma_20: float
    sma_50: float
    bollinger_upper: float
    bollinger_lower: float
    volume_sma: float
    volatility: float

class RealTimeStockService:
    """Industry-standard real-time stock data service"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_key = os.getenv('FINNHUB_KEY')
        self.polygon_key = os.getenv('POLYGON_KEY')
        self.yahoo_finance_enabled = True
        
        self.cache_timeout = 300  # 5 minutes for real-time data
        self.rate_limits = {
            'alpha_vantage': {'calls': 0, 'max_per_minute': 5},
            'finnhub': {'calls': 0, 'max_per_minute': 60},
            'polygon': {'calls': 0, 'max_per_minute': 5}
        }
        
        # Fallback order for data sources
        self.data_sources = ['finnhub', 'alpha_vantage', 'polygon', 'yahoo_finance']
    
    async def get_real_time_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get real-time stock quote with intelligent fallback"""
        cache_key = f"quote_{symbol}"
        cached_quote = cache.get(cache_key)
        
        if cached_quote:
            return StockQuote(**cached_quote)
        
        for source in self.data_sources:
            try:
                if source == 'finnhub' and self.finnhub_key:
                    quote = await self._get_finnhub_quote(symbol)
                elif source == 'alpha_vantage' and self.alpha_vantage_key:
                    quote = await self._get_alpha_vantage_quote(symbol)
                elif source == 'polygon' and self.polygon_key:
                    quote = await self._get_polygon_quote(symbol)
                elif source == 'yahoo_finance':
                    quote = await self._get_yahoo_finance_quote(symbol)
                else:
                    continue
                
                if quote:
                    # Cache the quote
                    cache.set(cache_key, quote.__dict__, self.cache_timeout)
                    return quote
                    
            except Exception as e:
                logger.warning(f"Failed to get quote from {source} for {symbol}: {e}")
                continue
        
        return None
    
    async def _get_finnhub_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Finnhub API"""
        if not self._check_rate_limit('finnhub'):
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://finnhub.io/api/v1/quote"
                params = {
                    'symbol': symbol,
                    'token': self.finnhub_key
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Get additional company info
                        company_info = await self._get_finnhub_company_info(symbol, session)
                        
                        return StockQuote(
                            symbol=symbol,
                            price=data.get('c', 0),
                            change=data.get('d', 0),
                            change_percent=data.get('dp', 0),
                            volume=data.get('v', 0),
                            market_cap=company_info.get('marketCapitalization', 0),
                            pe_ratio=company_info.get('pe', 0),
                            dividend_yield=company_info.get('dividendYield', 0),
                            high_52_week=data.get('h', 0),
                            low_52_week=data.get('l', 0),
                            timestamp=datetime.now(),
                            source='finnhub'
                        )
        except Exception as e:
            logger.error(f"Finnhub API error for {symbol}: {e}")
            return None
    
    async def _get_finnhub_company_info(self, symbol: str, session: aiohttp.ClientSession) -> Dict:
        """Get company info from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2"
            params = {'symbol': symbol, 'token': self.finnhub_key}
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return {}
    
    async def _get_alpha_vantage_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Alpha Vantage API"""
        if not self._check_rate_limit('alpha_vantage'):
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote_data = data.get('Global Quote', {})
                        
                        if quote_data:
                            return StockQuote(
                                symbol=symbol,
                                price=float(quote_data.get('05. price', 0)),
                                change=float(quote_data.get('09. change', 0)),
                                change_percent=float(quote_data.get('10. change percent', '0%').replace('%', '')),
                                volume=int(quote_data.get('06. volume', 0)),
                                market_cap=0,  # Not available in this endpoint
                                pe_ratio=0,
                                dividend_yield=0,
                                high_52_week=float(quote_data.get('03. high', 0)),
                                low_52_week=float(quote_data.get('04. low', 0)),
                                timestamp=datetime.now(),
                                source='alpha_vantage'
                            )
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None
    
    async def _get_polygon_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Polygon API"""
        if not self._check_rate_limit('polygon'):
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.polygon.io/v1/last_quote/stocks/{symbol}"
                params = {'apikey': self.polygon_key}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote_data = data.get('results', {})
                        
                        if quote_data:
                            return StockQuote(
                                symbol=symbol,
                                price=quote_data.get('P', 0),
                                change=0,  # Not available in this endpoint
                                change_percent=0,
                                volume=0,
                                market_cap=0,
                                pe_ratio=0,
                                dividend_yield=0,
                                high_52_week=0,
                                low_52_week=0,
                                timestamp=datetime.now(),
                                source='polygon'
                            )
        except Exception as e:
            logger.error(f"Polygon API error for {symbol}: {e}")
            return None
    
    async def _get_yahoo_finance_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Yahoo Finance (web scraping fallback)"""
        try:
            # This would implement Yahoo Finance scraping
            # For now, return None to avoid complexity
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits for a data source"""
        now = datetime.now()
        minute_key = f"rate_limit_{source}_{now.strftime('%Y%m%d%H%M')}"
        
        current_calls = cache.get(minute_key, 0)
        max_calls = self.rate_limits[source]['max_per_minute']
        
        if current_calls >= max_calls:
            return False
        
        cache.set(minute_key, current_calls + 1, 60)  # 1 minute TTL
        return True
    
    async def get_technical_indicators(self, symbol: str, period: int = 20) -> Optional[TechnicalIndicators]:
        """Calculate technical indicators for a stock"""
        cache_key = f"indicators_{symbol}_{period}"
        cached_indicators = cache.get(cache_key)
        
        if cached_indicators:
            return TechnicalIndicators(**cached_indicators)
        
        try:
            # Get historical data
            historical_data = await self.get_historical_data(symbol, period * 2)
            if historical_data is None or historical_data.empty:
                return None
            
            # Calculate indicators
            indicators = self._calculate_technical_indicators(historical_data, period)
            
            # Cache the indicators
            cache.set(cache_key, indicators.__dict__, self.cache_timeout)
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get historical stock data"""
        cache_key = f"historical_{symbol}_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return pd.DataFrame(cached_data)
        
        for source in self.data_sources:
            try:
                if source == 'finnhub' and self.finnhub_key:
                    data = await self._get_finnhub_historical(symbol, days)
                elif source == 'alpha_vantage' and self.alpha_vantage_key:
                    data = await self._get_alpha_vantage_historical(symbol, days)
                else:
                    continue
                
                if data is not None and not data.empty:
                    # Cache the data
                    cache.set(cache_key, data.to_dict('records'), self.cache_timeout)
                    return data
                    
            except Exception as e:
                logger.warning(f"Failed to get historical data from {source} for {symbol}: {e}")
                continue
        
        return None
    
    async def _get_finnhub_historical(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Get historical data from Finnhub"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            async with aiohttp.ClientSession() as session:
                url = f"https://finnhub.io/api/v1/stock/candle"
                params = {
                    'symbol': symbol,
                    'resolution': 'D',
                    'from': int(start_date.timestamp()),
                    'to': int(end_date.timestamp()),
                    'token': self.finnhub_key
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('s') == 'ok':
                            df = pd.DataFrame({
                                'timestamp': data['t'],
                                'open': data['o'],
                                'high': data['h'],
                                'low': data['l'],
                                'close': data['c'],
                                'volume': data['v']
                            })
                            
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                            df.set_index('timestamp', inplace=True)
                            return df
        except Exception as e:
            logger.error(f"Finnhub historical data error for {symbol}: {e}")
            return None
    
    async def _get_alpha_vantage_historical(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Get historical data from Alpha Vantage"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key,
                    'outputsize': 'compact'
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        time_series = data.get('Time Series (Daily)', {})
                        
                        if time_series:
                            df = pd.DataFrame.from_dict(time_series, orient='index')
                            df.index = pd.to_datetime(df.index)
                            df.columns = ['open', 'high', 'low', 'close', 'volume']
                            df = df.astype(float)
                            df = df.sort_index().tail(days)
                            return df
        except Exception as e:
            logger.error(f"Alpha Vantage historical data error for {symbol}: {e}")
            return None
    
    def _calculate_technical_indicators(self, df: pd.DataFrame, period: int) -> TechnicalIndicators:
        """Calculate technical indicators from historical data"""
        try:
            # RSI
            rsi = self._calculate_rsi(df['close'], 14)
            
            # MACD
            macd = self._calculate_macd(df['close'])
            
            # Simple Moving Averages
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1]
            
            # Bollinger Bands
            bb_upper, bb_lower = self._calculate_bollinger_bands(df['close'], 20)
            
            # Volume SMA
            volume_sma = df['volume'].rolling(20).mean().iloc[-1]
            
            # Volatility (annualized)
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            
            return TechnicalIndicators(
                rsi=rsi,
                macd=macd,
                sma_20=sma_20,
                sma_50=sma_50,
                bollinger_upper=bb_upper,
                bollinger_lower=bb_lower,
                volume_sma=volume_sma,
                volatility=volatility
            )
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators(0, 0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def _calculate_macd(self, prices: pd.Series) -> float:
        """Calculate MACD indicator"""
        try:
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            return macd.iloc[-1] if not macd.empty and not pd.isna(macd.iloc[-1]) else 0
        except:
            return 0
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(period).mean()
            std = prices.rolling(period).std()
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            return upper.iloc[-1], lower.iloc[-1]
        except:
            return 0, 0
    
    async def get_market_status(self) -> Dict:
        """Get overall market status"""
        try:
            # This would check market hours, major indices, etc.
            return {
                'market_open': True,
                'last_updated': datetime.now().isoformat(),
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {'market_open': False, 'status': 'error'}

# Global instance
real_time_service = RealTimeStockService()
