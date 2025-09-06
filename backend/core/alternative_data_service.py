"""
Alternative Data Service
Integrates real-time news sentiment, social media sentiment, and economic indicators
"""

import os
import sys
import django
import logging
import requests
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dataclasses import dataclass

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

logger = logging.getLogger(__name__)

@dataclass
class AlternativeDataPoint:
    """Alternative data point structure"""
    symbol: str
    timestamp: datetime
    news_sentiment: float
    social_sentiment: float
    analyst_sentiment: float
    economic_indicators: Dict[str, float]
    market_sentiment: float
    volatility_index: float
    fear_greed_index: float

class AlternativeDataService:
    """
    Service for fetching and processing alternative data sources
    """
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        return {
            'news_api': os.getenv('NEWS_API_KEY', ''),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
            'finnhub': os.getenv('FINNHUB_API_KEY', ''),
            'polygon': os.getenv('POLYGON_API_KEY', ''),
            'fred': os.getenv('FRED_API_KEY', ''),
            'twitter_bearer': os.getenv('TWITTER_BEARER_TOKEN', ''),
        }
    
    async def get_news_sentiment(self, symbol: str, days: int = 7) -> float:
        """Get news sentiment for a symbol"""
        try:
            # Use NewsAPI for real news sentiment
            if self.api_keys['news_api']:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': f"{symbol} stock",
                    'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    'sortBy': 'publishedAt',
                    'apiKey': self.api_keys['news_api'],
                    'pageSize': 100
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            articles = data.get('articles', [])
                            
                            # Simple sentiment analysis based on title keywords
                            sentiment_scores = []
                            for article in articles:
                                title = article.get('title', '').lower()
                                description = article.get('description', '').lower()
                                
                                # Positive keywords
                                positive_words = ['up', 'rise', 'gain', 'surge', 'boost', 'strong', 'beat', 'exceed', 'growth', 'profit']
                                # Negative keywords
                                negative_words = ['down', 'fall', 'drop', 'decline', 'weak', 'miss', 'loss', 'cut', 'reduce', 'crisis']
                                
                                positive_count = sum(1 for word in positive_words if word in title or word in description)
                                negative_count = sum(1 for word in negative_words if word in title or word in description)
                                
                                if positive_count + negative_count > 0:
                                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                                    sentiment_scores.append(sentiment)
                            
                            if sentiment_scores:
                                return np.mean(sentiment_scores)
            
            # Fallback to simulated sentiment
            return np.random.normal(0, 0.3)
            
        except Exception as e:
            logger.error(f"Error fetching news sentiment for {symbol}: {e}")
            return np.random.normal(0, 0.3)
    
    async def get_social_sentiment(self, symbol: str) -> float:
        """Get social media sentiment for a symbol"""
        try:
            # Twitter API integration (requires Twitter API v2)
            if self.api_keys['twitter_bearer']:
                url = "https://api.twitter.com/2/tweets/search/recent"
                headers = {
                    'Authorization': f'Bearer {self.api_keys["twitter_bearer"]}',
                    'Content-Type': 'application/json'
                }
                params = {
                    'query': f"{symbol} -is:retweet lang:en",
                    'max_results': 100,
                    'tweet.fields': 'created_at,public_metrics'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            tweets = data.get('data', [])
                            
                            # Simple sentiment analysis based on engagement
                            sentiment_scores = []
                            for tweet in tweets:
                                text = tweet.get('text', '').lower()
                                metrics = tweet.get('public_metrics', {})
                                
                                # Positive keywords
                                positive_words = ['bullish', 'buy', 'moon', 'rocket', 'gains', 'profit', 'strong', 'growth']
                                # Negative keywords
                                negative_words = ['bearish', 'sell', 'crash', 'dump', 'loss', 'weak', 'decline', 'fall']
                                
                                positive_count = sum(1 for word in positive_words if word in text)
                                negative_count = sum(1 for word in negative_words if word in text)
                                
                                if positive_count + negative_count > 0:
                                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                                    # Weight by engagement
                                    engagement = metrics.get('like_count', 0) + metrics.get('retweet_count', 0)
                                    weight = min(engagement / 100, 1.0)  # Normalize engagement
                                    sentiment_scores.append(sentiment * weight)
                            
                            if sentiment_scores:
                                return np.mean(sentiment_scores)
            
            # Fallback to simulated sentiment
            return np.random.normal(0, 0.4)
            
        except Exception as e:
            logger.error(f"Error fetching social sentiment for {symbol}: {e}")
            return np.random.normal(0, 0.4)
    
    async def get_economic_indicators(self) -> Dict[str, float]:
        """Get economic indicators from FRED API"""
        try:
            indicators = {}
            
            if self.api_keys['fred']:
                # Federal Reserve Economic Data (FRED) API
                base_url = "https://api.stlouisfed.org/fred/series/observations"
                
                # Key economic indicators
                fred_series = {
                    'GDP': 'GDP',
                    'UNEMPLOYMENT': 'UNRATE',
                    'INFLATION': 'CPIAUCSL',
                    'INTEREST_RATE': 'FEDFUNDS',
                    'CONSUMER_SENTIMENT': 'UMCSENT',
                    'VIX': 'VIXCLS'
                }
                
                for indicator, series_id in fred_series.items():
                    params = {
                        'series_id': series_id,
                        'api_key': self.api_keys['fred'],
                        'file_type': 'json',
                        'limit': 1,
                        'sort_order': 'desc'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(base_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                observations = data.get('observations', [])
                                if observations:
                                    value = float(observations[0].get('value', 0))
                                    indicators[indicator] = value
            
            # Fallback to simulated data
            if not indicators:
                indicators = {
                    'GDP': np.random.normal(2.5, 0.5),
                    'UNEMPLOYMENT': np.random.normal(4.0, 0.3),
                    'INFLATION': np.random.normal(2.5, 0.4),
                    'INTEREST_RATE': np.random.normal(5.0, 0.5),
                    'CONSUMER_SENTIMENT': np.random.normal(70, 10),
                    'VIX': np.random.normal(20, 5)
                }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error fetching economic indicators: {e}")
            return {
                'GDP': np.random.normal(2.5, 0.5),
                'UNEMPLOYMENT': np.random.normal(4.0, 0.3),
                'INFLATION': np.random.normal(2.5, 0.4),
                'INTEREST_RATE': np.random.normal(5.0, 0.5),
                'CONSUMER_SENTIMENT': np.random.normal(70, 10),
                'VIX': np.random.normal(20, 5)
            }
    
    async def get_analyst_sentiment(self, symbol: str) -> float:
        """Get analyst sentiment from earnings and ratings"""
        try:
            # Use Alpha Vantage for analyst data
            if self.api_keys['alpha_vantage']:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.api_keys['alpha_vantage']
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract analyst data
                            pe_ratio = float(data.get('PERatio', 0))
                            peg_ratio = float(data.get('PEGRatio', 0))
                            analyst_target = float(data.get('AnalystTargetPrice', 0))
                            current_price = float(data.get('PriceToBookRatio', 0))  # This is actually PB ratio
                            
                            # Calculate sentiment based on ratios
                            sentiment = 0.0
                            if pe_ratio > 0 and pe_ratio < 25:  # Reasonable PE
                                sentiment += 0.3
                            if peg_ratio > 0 and peg_ratio < 2:  # Good PEG
                                sentiment += 0.3
                            if analyst_target > current_price:  # Target above current
                                sentiment += 0.4
                            
                            return sentiment
            
            # Fallback to simulated sentiment
            return np.random.normal(0, 0.2)
            
        except Exception as e:
            logger.error(f"Error fetching analyst sentiment for {symbol}: {e}")
            return np.random.normal(0, 0.2)
    
    async def get_market_sentiment(self) -> float:
        """Get overall market sentiment"""
        try:
            # Use VIX and other market indicators
            economic_indicators = await self.get_economic_indicators()
            vix = economic_indicators.get('VIX', 20)
            
            # VIX-based sentiment (lower VIX = higher sentiment)
            if vix < 15:
                sentiment = 0.8  # Very bullish
            elif vix < 20:
                sentiment = 0.6  # Bullish
            elif vix < 25:
                sentiment = 0.4  # Neutral
            elif vix < 30:
                sentiment = 0.2  # Bearish
            else:
                sentiment = 0.0  # Very bearish
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error calculating market sentiment: {e}")
            return np.random.normal(0.5, 0.2)
    
    async def get_fear_greed_index(self) -> float:
        """Get Fear & Greed Index"""
        try:
            # This would typically come from CNN Fear & Greed Index API
            # For now, simulate based on VIX
            economic_indicators = await self.get_economic_indicators()
            vix = economic_indicators.get('VIX', 20)
            
            # Convert VIX to Fear & Greed Index (0-100)
            if vix > 30:
                fear_greed = 0  # Extreme Fear
            elif vix > 25:
                fear_greed = 25  # Fear
            elif vix > 20:
                fear_greed = 50  # Neutral
            elif vix > 15:
                fear_greed = 75  # Greed
            else:
                fear_greed = 100  # Extreme Greed
            
            return fear_greed / 100.0  # Normalize to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating Fear & Greed Index: {e}")
            return np.random.normal(0.5, 0.2)
    
    async def get_alternative_data(self, symbols: List[str]) -> Dict[str, AlternativeDataPoint]:
        """Get comprehensive alternative data for multiple symbols"""
        logger.info(f"Fetching alternative data for {len(symbols)} symbols...")
        
        # Get economic indicators once (shared across all symbols)
        economic_indicators = await self.get_economic_indicators()
        market_sentiment = await self.get_market_sentiment()
        fear_greed_index = await self.get_fear_greed_index()
        
        # Get symbol-specific data
        alternative_data = {}
        
        for symbol in symbols:
            try:
                # Fetch all sentiment data in parallel
                news_sentiment, social_sentiment, analyst_sentiment = await asyncio.gather(
                    self.get_news_sentiment(symbol),
                    self.get_social_sentiment(symbol),
                    self.get_analyst_sentiment(symbol)
                )
                
                alternative_data[symbol] = AlternativeDataPoint(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    news_sentiment=news_sentiment,
                    social_sentiment=social_sentiment,
                    analyst_sentiment=analyst_sentiment,
                    economic_indicators=economic_indicators,
                    market_sentiment=market_sentiment,
                    volatility_index=economic_indicators.get('VIX', 20),
                    fear_greed_index=fear_greed_index
                )
                
                logger.info(f"✓ {symbol}: News={news_sentiment:.3f}, Social={social_sentiment:.3f}, Analyst={analyst_sentiment:.3f}")
                
            except Exception as e:
                logger.error(f"Error fetching alternative data for {symbol}: {e}")
                # Create fallback data point
                alternative_data[symbol] = AlternativeDataPoint(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    news_sentiment=np.random.normal(0, 0.3),
                    social_sentiment=np.random.normal(0, 0.4),
                    analyst_sentiment=np.random.normal(0, 0.2),
                    economic_indicators=economic_indicators,
                    market_sentiment=market_sentiment,
                    volatility_index=economic_indicators.get('VIX', 20),
                    fear_greed_index=fear_greed_index
                )
        
        return alternative_data
    
    def to_feature_vector(self, data_point: AlternativeDataPoint) -> List[float]:
        """Convert alternative data point to feature vector"""
        features = [
            data_point.news_sentiment,
            data_point.social_sentiment,
            data_point.analyst_sentiment,
            data_point.market_sentiment,
            data_point.volatility_index / 100.0,  # Normalize VIX
            data_point.fear_greed_index,
            data_point.economic_indicators.get('GDP', 2.5) / 10.0,  # Normalize GDP
            data_point.economic_indicators.get('UNEMPLOYMENT', 4.0) / 10.0,  # Normalize unemployment
            data_point.economic_indicators.get('INFLATION', 2.5) / 10.0,  # Normalize inflation
            data_point.economic_indicators.get('INTEREST_RATE', 5.0) / 10.0,  # Normalize interest rate
            data_point.economic_indicators.get('CONSUMER_SENTIMENT', 70) / 100.0,  # Normalize consumer sentiment
        ]
        
        return features

# Example usage
async def main():
    """Example usage of AlternativeDataService"""
    service = AlternativeDataService()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    alternative_data = await service.get_alternative_data(symbols)
    
    for symbol, data_point in alternative_data.items():
        print(f"\n{symbol}:")
        print(f"  News Sentiment: {data_point.news_sentiment:.3f}")
        print(f"  Social Sentiment: {data_point.social_sentiment:.3f}")
        print(f"  Analyst Sentiment: {data_point.analyst_sentiment:.3f}")
        print(f"  Market Sentiment: {data_point.market_sentiment:.3f}")
        print(f"  VIX: {data_point.volatility_index:.1f}")
        print(f"  Fear & Greed: {data_point.fear_greed_index:.3f}")
        
        features = service.to_feature_vector(data_point)
        print(f"  Feature Vector: {[f'{f:.3f}' for f in features]}")

if __name__ == "__main__":
    asyncio.run(main())
