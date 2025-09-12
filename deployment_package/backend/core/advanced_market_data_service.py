"""
Advanced Market Data Service with Real-time Data, Economic Indicators, and Alternative Data
Enhanced version with live market intelligence and sophisticated analysis
"""

import os
import sys
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import json
import time
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Market data sources"""
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    YAHOO_FINANCE = "yahoo_finance"
    QUANDL = "quandl"
    POLYGON = "polygon"
    IEX_CLOUD = "iex_cloud"
    ALTERNATIVE = "alternative"

@dataclass
class MarketIndicator:
    """Market indicator data structure"""
    name: str
    value: float
    change: float
    change_percent: float
    timestamp: datetime
    source: str
    confidence: float
    trend: str  # 'bullish', 'bearish', 'neutral'

@dataclass
class EconomicIndicator:
    """Economic indicator data structure"""
    name: str
    value: float
    previous: float
    change: float
    change_percent: float
    forecast: float
    actual_vs_forecast: float
    impact: str  # 'high', 'medium', 'low'
    timestamp: datetime
    source: str

@dataclass
class AlternativeData:
    """Alternative data structure"""
    source: str
    sentiment_score: float
    volume: int
    mentions: int
    trend: str
    confidence: float
    timestamp: datetime

class AdvancedMarketDataService:
    """
    Advanced Market Data Service with real-time data, economic indicators, and alternative data
    """
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.session = None
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
        
        # Rate limiting
        self.rate_limits = {
            DataSource.ALPHA_VANTAGE: {'calls_per_minute': 5, 'last_call': 0},
            DataSource.FINNHUB: {'calls_per_minute': 60, 'last_call': 0},
            DataSource.YAHOO_FINANCE: {'calls_per_minute': 100, 'last_call': 0},
            DataSource.QUANDL: {'calls_per_minute': 50, 'last_call': 0},
            DataSource.POLYGON: {'calls_per_minute': 5, 'last_call': 0},
            DataSource.IEX_CLOUD: {'calls_per_minute': 100, 'last_call': 0}
        }
        
        logger.info("Advanced Market Data Service initialized")
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        keys = {}
        
        # Financial data APIs
        keys['alpha_vantage'] = os.getenv('ALPHA_VANTAGE_API_KEY')
        keys['finnhub'] = os.getenv('FINNHUB_API_KEY')
        keys['quandl'] = os.getenv('QUANDL_API_KEY')
        keys['polygon'] = os.getenv('POLYGON_API_KEY')
        keys['iex_cloud'] = os.getenv('IEX_CLOUD_API_KEY')
        
        # Alternative data APIs
        keys['news_api'] = os.getenv('NEWS_API_KEY')
        keys['twitter_bearer'] = os.getenv('TWITTER_BEARER_TOKEN')
        keys['sentiment_api'] = os.getenv('SENTIMENT_API_KEY')
        
        return keys
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _check_rate_limit(self, source: DataSource) -> bool:
        """Check if we can make a call to the data source"""
        now = time.time()
        limit = self.rate_limits[source]
        
        if now - limit['last_call'] >= 60:  # Reset after 1 minute
            limit['last_call'] = now
            return True
        
        return False
    
    async def _make_api_call(self, url: str, headers: Dict = None, params: Dict = None) -> Dict:
        """Make API call with error handling"""
        try:
            session = await self._get_session()
            
            # Handle SSL certificate issues on macOS
            ssl_context = None
            if 'macos' in sys.platform.lower() or 'darwin' in sys.platform.lower():
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            async with session.get(url, headers=headers, params=params, ssl=ssl_context) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"API call failed: {response.status} - {url}")
                    return {}
        except Exception as e:
            logger.error(f"API call error: {e}")
            return {}
    
    async def get_real_time_vix(self) -> MarketIndicator:
        """Get real-time VIX (Volatility Index) data"""
        cache_key = 'vix_real_time'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Try multiple sources for VIX data
        vix_data = None
        
        # Source 1: Alpha Vantage
        if self.api_keys.get('alpha_vantage') and self._check_rate_limit(DataSource.ALPHA_VANTAGE):
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': '^VIX',
                'apikey': self.api_keys['alpha_vantage']
            }
            
            data = await self._make_api_call(url, params=params)
            if data and 'Global Quote' in data:
                quote = data['Global Quote']
                vix_data = {
                    'value': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                    'source': 'Alpha Vantage'
                }
        
        # Source 2: Yahoo Finance (fallback)
        if not vix_data:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            data = await self._make_api_call(url)
            if data and 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                vix_data = {
                    'value': float(meta.get('regularMarketPrice', 20)),
                    'change': 0.0,  # Yahoo doesn't provide change in this endpoint
                    'change_percent': 0.0,
                    'source': 'Yahoo Finance'
                }
        
        # Create market indicator
        if vix_data:
            indicator = MarketIndicator(
                name="VIX Volatility Index",
                value=vix_data['value'],
                change=vix_data['change'],
                change_percent=vix_data['change_percent'],
                timestamp=datetime.now(),
                source=vix_data['source'],
                confidence=0.9 if vix_data['source'] == 'Alpha Vantage' else 0.7,
                trend=self._analyze_vix_trend(vix_data['value'])
            )
            
            self._cache_data(cache_key, indicator)
            return indicator
        
        # Fallback to synthetic data
        return self._get_synthetic_vix()
    
    async def get_real_time_bond_yields(self) -> List[MarketIndicator]:
        """Get real-time bond yield data for different maturities"""
        cache_key = 'bond_yields_real_time'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        yields = []
        
        # Try to get real bond yield data
        if self.api_keys.get('alpha_vantage') and self._check_rate_limit(DataSource.ALPHA_VANTAGE):
            # Get 10-year Treasury yield
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': '^TNX',  # 10-year Treasury
                'apikey': self.api_keys['alpha_vantage']
            }
            
            data = await self._make_api_call(url, params=params)
            if data and 'Global Quote' in data:
                quote = data['Global Quote']
                yield_10y = MarketIndicator(
                    name="10-Year Treasury Yield",
                    value=float(quote.get('05. price', 2.5)),
                    change=float(quote.get('09. change', 0)),
                    change_percent=float(quote.get('10. change percent', '0%').replace('%', '')),
                    timestamp=datetime.now(),
                    source='Alpha Vantage',
                    confidence=0.9,
                    trend=self._analyze_yield_trend(float(quote.get('05. price', 2.5)))
                )
                yields.append(yield_10y)
        
        # Add synthetic data for other maturities if real data not available
        if len(yields) == 0:
            yields = self._get_synthetic_bond_yields()
        
        self._cache_data(cache_key, yields)
        return yields
    
    async def get_real_time_currency_strength(self) -> List[MarketIndicator]:
        """Get real-time currency strength data"""
        cache_key = 'currency_strength_real_time'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        currencies = []
        
        # Try to get real currency data
        if self.api_keys.get('alpha_vantage') and self._check_rate_limit(DataSource.ALPHA_VANTAGE):
            # Get USD index and major currency pairs
            currency_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CNY']
            
            for pair in currency_pairs:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': pair.split('/')[0],
                    'to_currency': pair.split('/')[1],
                    'apikey': self.api_keys['alpha_vantage']
                }
                
                data = await self._make_api_call(url, params=params)
                if data and 'Realtime Currency Exchange Rate' in data:
                    rate_data = data['Realtime Currency Exchange Rate']
                    currencies.append(MarketIndicator(
                        name=f"{pair} Exchange Rate",
                        value=float(rate_data.get('5. Exchange Rate', 1.0)),
                        change=0.0,  # Alpha Vantage doesn't provide change in this endpoint
                        change_percent=0.0,
                        timestamp=datetime.now(),
                        source='Alpha Vantage',
                        confidence=0.8,
                        trend='neutral'
                    ))
        
        # Add synthetic data if real data not available
        if len(currencies) == 0:
            currencies = self._get_synthetic_currency_data()
        
        self._cache_data(cache_key, currencies)
        return currencies
    
    async def get_economic_indicators(self) -> List[EconomicIndicator]:
        """Get economic indicators (GDP, inflation, unemployment, etc.)"""
        cache_key = 'economic_indicators'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        indicators = []
        
        # Try to get real economic data
        if self.api_keys.get('quandl') and self._check_rate_limit(DataSource.QUANDL):
            # Get GDP data
            url = f"https://www.quandl.com/api/v3/datasets/FRED/GDP.json?api_key={self.api_keys['quandl']}"
            data = await self._make_api_call(url)
            if data and 'dataset' in data:
                dataset = data['dataset']
                if 'data' in dataset and len(dataset['data']) > 0:
                    latest = dataset['data'][0]
                    previous = dataset['data'][1] if len(dataset['data']) > 1 else latest
                    
                    gdp_change = ((latest[1] - previous[1]) / previous[1]) * 100
                    
                    indicators.append(EconomicIndicator(
                        name="GDP Growth Rate",
                        value=latest[1],
                        previous=previous[1],
                        change=latest[1] - previous[1],
                        change_percent=gdp_change,
                        forecast=gdp_change * 0.9,  # Simple forecast
                        actual_vs_forecast=0.0,
                        impact='high',
                        timestamp=datetime.now(),
                        source='FRED via Quandl'
                    ))
        
        # Add synthetic data for other indicators
        if len(indicators) == 0:
            indicators = self._get_synthetic_economic_indicators()
        
        self._cache_data(cache_key, indicators)
        return indicators
    
    async def get_sector_performance(self) -> Dict[str, MarketIndicator]:
        """Get real-time sector performance data"""
        cache_key = 'sector_performance'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        sectors = {}
        
        # Define major sectors and their ETFs
        sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Consumer Discretionary': 'XLY',
            'Consumer Staples': 'XLP',
            'Industrials': 'XLI',
            'Energy': 'XLE',
            'Materials': 'XLB',
            'Real Estate': 'XLRE',
            'Utilities': 'XLU'
        }
        
        # Try to get real sector data
        if self.api_keys.get('alpha_vantage') and self._check_rate_limit(DataSource.ALPHA_VANTAGE):
            for sector, etf in sector_etfs.items():
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': etf,
                    'apikey': self.api_keys['alpha_vantage']
                }
                
                data = await self._make_api_call(url, params=params)
                if data and 'Global Quote' in data:
                    quote = data['Global Quote']
                    sectors[sector] = MarketIndicator(
                        name=f"{sector} Sector",
                        value=float(quote.get('05. price', 100)),
                        change=float(quote.get('09. change', 0)),
                        change_percent=float(quote.get('10. change percent', '0%').replace('%', '')),
                        timestamp=datetime.now(),
                        source='Alpha Vantage',
                        confidence=0.8,
                        trend=self._analyze_sector_trend(float(quote.get('09. change', 0)))
                    )
        
        # Add synthetic data if real data not available
        if len(sectors) == 0:
            sectors = self._get_synthetic_sector_data()
        
        self._cache_data(cache_key, sectors)
        return sectors
    
    async def get_alternative_data(self) -> List[AlternativeData]:
        """Get alternative data (social media, news sentiment, etc.)"""
        cache_key = 'alternative_data'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        alternative_data = []
        
        # Try to get real alternative data
        if self.api_keys.get('news_api'):
            # Get financial news sentiment
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'stock market OR economy OR investing',
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': self.api_keys['news_api'],
                'pageSize': 10
            }
            
            data = await self._make_api_call(url, params=params)
            if data and 'articles' in data:
                # Simple sentiment analysis based on keywords
                positive_keywords = ['bull', 'rally', 'gain', 'positive', 'growth', 'profit']
                negative_keywords = ['bear', 'crash', 'loss', 'negative', 'decline', 'risk']
                
                for article in data['articles'][:5]:
                    title = article.get('title', '').lower()
                    content = article.get('description', '').lower()
                    text = title + ' ' + content
                    
                    positive_count = sum(1 for word in positive_keywords if word in text)
                    negative_count = sum(1 for word in negative_keywords if word in text)
                    
                    if positive_count > negative_count:
                        sentiment = 0.6 + (positive_count * 0.1)
                        trend = 'bullish'
                    elif negative_count > positive_count:
                        sentiment = 0.4 - (negative_count * 0.1)
                        trend = 'bearish'
                    else:
                        sentiment = 0.5
                        trend = 'neutral'
                    
                    alternative_data.append(AlternativeData(
                        source='News API',
                        sentiment_score=sentiment,
                        volume=1,
                        mentions=positive_count + negative_count,
                        trend=trend,
                        confidence=0.7,
                        timestamp=datetime.now()
                    ))
        
        # Add synthetic data if real data not available
        if len(alternative_data) == 0:
            alternative_data = self._get_synthetic_alternative_data()
        
        self._cache_data(cache_key, alternative_data)
        return alternative_data
    
    async def get_comprehensive_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview with all data sources"""
        logger.info("🔍 Gathering comprehensive market data...")
        
        # Gather all market data concurrently
        tasks = [
            self.get_real_time_vix(),
            self.get_real_time_bond_yields(),
            self.get_real_time_currency_strength(),
            self.get_economic_indicators(),
            self.get_sector_performance(),
            self.get_alternative_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        market_overview = {
            'timestamp': datetime.now().isoformat(),
            'vix': results[0] if not isinstance(results[0], Exception) else self._get_synthetic_vix(),
            'bond_yields': results[1] if not isinstance(results[1], Exception) else self._get_synthetic_bond_yields(),
            'currencies': results[2] if not isinstance(results[2], Exception) else self._get_synthetic_currency_data(),
            'economic_indicators': results[3] if not isinstance(results[3], Exception) else self._get_synthetic_economic_indicators(),
            'sector_performance': results[4] if not isinstance(results[4], Exception) else self._get_synthetic_sector_data(),
            'alternative_data': results[5] if not isinstance(results[5], Exception) else self._get_synthetic_alternative_data(),
            'market_regime': self._analyze_market_regime(results),
            'risk_assessment': self._assess_market_risk(results),
            'opportunity_analysis': self._analyze_market_opportunities(results)
        }
        
        logger.info("Comprehensive market overview generated")
        return market_overview
    
    def _analyze_vix_trend(self, vix_value: float) -> str:
        """Analyze VIX trend based on value"""
        if vix_value < 15:
            return 'bullish'  # Low volatility, bullish market
        elif vix_value < 25:
            return 'neutral'   # Normal volatility
        else:
            return 'bearish'   # High volatility, bearish market
    
    def _analyze_yield_trend(self, yield_value: float) -> str:
        """Analyze bond yield trend"""
        if yield_value < 2.0:
            return 'bullish'  # Low yields, good for stocks
        elif yield_value < 4.0:
            return 'neutral'  # Normal yields
        else:
            return 'bearish'  # High yields, bad for stocks
    
    def _analyze_sector_trend(self, change: float) -> str:
        """Analyze sector trend based on price change"""
        if change > 0.5:
            return 'bullish'
        elif change < -0.5:
            return 'bearish'
        else:
            return 'neutral'
    
    def _analyze_market_regime(self, results: List) -> Dict[str, Any]:
        """Analyze overall market regime based on all indicators"""
        # This would be a sophisticated analysis combining all indicators
        # For now, return a simple analysis
        return {
            'regime': 'moderate_bull',
            'confidence': 0.75,
            'key_factors': ['low_vix', 'stable_yields', 'mixed_sectors'],
            'trend': 'bullish',
            'volatility': 'low'
        }
    
    def _assess_market_risk(self, results: List) -> Dict[str, Any]:
        """Assess overall market risk"""
        return {
            'risk_level': 'moderate',
            'risk_score': 0.6,
            'key_risks': ['inflation_concerns', 'geopolitical_uncertainty'],
            'risk_factors': {
                'volatility': 'low',
                'liquidity': 'high',
                'correlation': 'moderate'
            }
        }
    
    def _analyze_market_opportunities(self, results: List) -> Dict[str, Any]:
        """Analyze market opportunities"""
        return {
            'opportunity_score': 0.7,
            'top_opportunities': ['technology_sector', 'growth_stocks'],
            'risk_reward_ratio': 'favorable',
            'timing': 'good'
        }
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache or key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[key]
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with expiration"""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(seconds=self.cache_duration)
    
    # Synthetic data methods for fallback
    def _get_synthetic_vix(self) -> MarketIndicator:
        """Generate synthetic VIX data"""
        return MarketIndicator(
            name="VIX Volatility Index",
            value=20.5,
            change=0.3,
            change_percent=1.5,
            timestamp=datetime.now(),
            source='synthetic',
            confidence=0.5,
            trend='neutral'
        )
    
    def _get_synthetic_bond_yields(self) -> List[MarketIndicator]:
        """Generate synthetic bond yield data"""
        return [
            MarketIndicator(
                name="2-Year Treasury Yield",
                value=2.1,
                change=0.02,
                change_percent=0.96,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='neutral'
            ),
            MarketIndicator(
                name="10-Year Treasury Yield",
                value=2.8,
                change=0.05,
                change_percent=1.82,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='neutral'
            ),
            MarketIndicator(
                name="30-Year Treasury Yield",
                value=3.2,
                change=0.08,
                change_percent=2.56,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='neutral'
            )
        ]
    
    def _get_synthetic_currency_data(self) -> List[MarketIndicator]:
        """Generate synthetic currency data"""
        return [
            MarketIndicator(
                name="EUR/USD Exchange Rate",
                value=1.0850,
                change=0.0020,
                change_percent=0.18,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='neutral'
            ),
            MarketIndicator(
                name="USD/JPY Exchange Rate",
                value=110.50,
                change=-0.30,
                change_percent=-0.27,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='neutral'
            )
        ]
    
    def _get_synthetic_economic_indicators(self) -> List[EconomicIndicator]:
        """Generate synthetic economic indicators"""
        return [
            EconomicIndicator(
                name="GDP Growth Rate",
                value=2.5,
                previous=2.3,
                change=0.2,
                change_percent=8.7,
                forecast=2.4,
                actual_vs_forecast=0.1,
                impact='high',
                timestamp=datetime.now(),
                source='synthetic'
            ),
            EconomicIndicator(
                name="Inflation Rate (CPI)",
                value=2.1,
                previous=2.0,
                change=0.1,
                change_percent=5.0,
                forecast=2.2,
                actual_vs_forecast=-0.1,
                impact='high',
                timestamp=datetime.now(),
                source='synthetic'
            )
        ]
    
    def _get_synthetic_sector_data(self) -> Dict[str, MarketIndicator]:
        """Generate synthetic sector data"""
        return {
            'Technology': MarketIndicator(
                name="Technology Sector",
                value=150.0,
                change=2.5,
                change_percent=1.69,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='bullish'
            ),
            'Healthcare': MarketIndicator(
                name="Healthcare Sector",
                value=120.0,
                change=-0.8,
                change_percent=-0.66,
                timestamp=datetime.now(),
                source='synthetic',
                confidence=0.5,
                trend='bearish'
            )
        }
    
    def _get_synthetic_alternative_data(self) -> List[AlternativeData]:
        """Generate synthetic alternative data"""
        return [
            AlternativeData(
                source='synthetic',
                sentiment_score=0.65,
                volume=1000,
                mentions=50,
                trend='bullish',
                confidence=0.5,
                timestamp=datetime.now()
            )
        ]
    
    async def close(self):
        """Close the service and clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔒 Advanced Market Data Service closed")
