"""
Real-Time Sentiment Analysis Engine
Social media sentiment analysis for trading signals
"""

import asyncio
import logging
import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp
import json

# For sentiment analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    # Fallback sentiment analysis
    class SentimentIntensityAnalyzer:
        def polarity_scores(self, text):
            return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}


@dataclass
class SentimentData:
    """Sentiment data structure"""
    symbol: str
    timestamp: datetime
    
    # Sentiment scores
    overall_sentiment: float  # -1 to 1
    confidence: float  # 0 to 1
    
    # Source-specific sentiment
    twitter_sentiment: float
    reddit_sentiment: float
    news_sentiment: float
    
    # Sentiment breakdown
    positive_count: int
    negative_count: int
    neutral_count: int
    
    # Volume metrics
    mention_volume: int
    engagement_score: float
    
    # Trend analysis
    sentiment_trend: str  # "BULLISH", "BEARISH", "NEUTRAL", "VOLATILE"
    momentum_score: float  # -1 to 1
    
    # Catalyst detection
    catalyst_detected: bool
    catalyst_type: str  # "EARNINGS", "NEWS", "SOCIAL", "TECHNICAL"
    catalyst_strength: float  # 0 to 1


class SentimentEngine:
    """Real-time sentiment analysis engine for trading signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Sentiment cache
        self.sentiment_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Sentiment thresholds
        self.sentiment_thresholds = {
            "BULLISH": 0.3,
            "BEARISH": -0.3,
            "NEUTRAL_LOW": -0.1,
            "NEUTRAL_HIGH": 0.1
        }
        
        # Catalyst keywords
        self.catalyst_keywords = {
            "EARNINGS": ["earnings", "eps", "revenue", "profit", "guidance", "beat", "miss"],
            "NEWS": ["announcement", "partnership", "acquisition", "merger", "launch", "breakthrough"],
            "SOCIAL": ["viral", "trending", "meme", "squeeze", "diamond hands", "hodl"],
            "TECHNICAL": ["breakout", "resistance", "support", "volume", "pattern", "signal"]
        }
    
    async def analyze_sentiment(self, symbol: str) -> SentimentData:
        """Analyze sentiment for a specific symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.sentiment_cache:
                cached_data, timestamp = self.sentiment_cache[cache_key]
                if datetime.now() - timestamp < self.cache_duration:
                    return cached_data
            
            # Get sentiment data from multiple sources
            twitter_data = await self._get_twitter_sentiment(symbol)
            reddit_data = await self._get_reddit_sentiment(symbol)
            news_data = await self._get_news_sentiment(symbol)
            
            # Combine sentiment scores
            overall_sentiment = self._combine_sentiment_scores(
                twitter_data, reddit_data, news_data
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(twitter_data, reddit_data, news_data)
            
            # Detect sentiment trend
            sentiment_trend = self._detect_sentiment_trend(symbol, overall_sentiment)
            
            # Calculate momentum
            momentum_score = self._calculate_momentum(symbol, overall_sentiment)
            
            # Detect catalysts
            catalyst_info = self._detect_catalysts(symbol, twitter_data, reddit_data, news_data)
            
            # Create sentiment data object
            sentiment_data = SentimentData(
                symbol=symbol,
                timestamp=datetime.now(),
                overall_sentiment=overall_sentiment,
                confidence=confidence,
                twitter_sentiment=twitter_data["sentiment"],
                reddit_sentiment=reddit_data["sentiment"],
                news_sentiment=news_data["sentiment"],
                positive_count=twitter_data["positive"] + reddit_data["positive"] + news_data["positive"],
                negative_count=twitter_data["negative"] + reddit_data["negative"] + news_data["negative"],
                neutral_count=twitter_data["neutral"] + reddit_data["neutral"] + news_data["neutral"],
                mention_volume=twitter_data["volume"] + reddit_data["volume"] + news_data["volume"],
                engagement_score=self._calculate_engagement_score(twitter_data, reddit_data, news_data),
                sentiment_trend=sentiment_trend,
                momentum_score=momentum_score,
                catalyst_detected=catalyst_info["detected"],
                catalyst_type=catalyst_info["type"],
                catalyst_strength=catalyst_info["strength"]
            )
            
            # Cache the result
            self.sentiment_cache[cache_key] = (sentiment_data, datetime.now())
            
            # Clean old cache entries
            self._clean_cache()
            
            self.logger.info(f"Sentiment analysis completed for {symbol}: {overall_sentiment:.3f}")
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment for {symbol}: {e}")
            return self._get_default_sentiment(symbol)
    
    async def _get_twitter_sentiment(self, symbol: str) -> Dict:
        """Get Twitter sentiment data (mock implementation)"""
        try:
            # In production, this would use Twitter API or web scraping
            # For now, simulate Twitter sentiment
            
            # Simulate Twitter data
            tweets = [
                f"{symbol} looking bullish today!",
                f"Just bought more {symbol} shares",
                f"{symbol} earnings beat expectations",
                f"{symbol} stock is overvalued",
                f"Selling {symbol} before it drops more"
            ]
            
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for tweet in tweets:
                scores = self.analyzer.polarity_scores(tweet)
                sentiments.append(scores["compound"])
                
                if scores["compound"] > 0.1:
                    positive_count += 1
                elif scores["compound"] < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            return {
                "sentiment": avg_sentiment,
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "volume": len(tweets),
                "engagement": np.random.uniform(0.5, 1.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Twitter sentiment: {e}")
            return self._get_default_source_data()
    
    async def _get_reddit_sentiment(self, symbol: str) -> Dict:
        """Get Reddit sentiment data (mock implementation)"""
        try:
            # In production, this would use Reddit API
            # For now, simulate Reddit sentiment
            
            # Simulate Reddit posts
            posts = [
                f"DD: {symbol} is undervalued",
                f"{symbol} to the moon!",
                f"Bear case for {symbol}",
                f"{symbol} earnings call was disappointing",
                f"Technical analysis: {symbol} breakout incoming"
            ]
            
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for post in posts:
                scores = self.analyzer.polarity_scores(post)
                sentiments.append(scores["compound"])
                
                if scores["compound"] > 0.1:
                    positive_count += 1
                elif scores["compound"] < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            return {
                "sentiment": avg_sentiment,
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "volume": len(posts),
                "engagement": np.random.uniform(0.3, 0.8)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Reddit sentiment: {e}")
            return self._get_default_source_data()
    
    async def _get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment data (mock implementation)"""
        try:
            # In production, this would use news APIs
            # For now, simulate news sentiment
            
            # Simulate news headlines
            headlines = [
                f"{symbol} reports strong quarterly earnings",
                f"{symbol} stock rises on positive outlook",
                f"{symbol} faces regulatory challenges",
                f"{symbol} announces new product launch",
                f"{symbol} stock falls on disappointing guidance"
            ]
            
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for headline in headlines:
                scores = self.analyzer.polarity_scores(headline)
                sentiments.append(scores["compound"])
                
                if scores["compound"] > 0.1:
                    positive_count += 1
                elif scores["compound"] < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            return {
                "sentiment": avg_sentiment,
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "volume": len(headlines),
                "engagement": np.random.uniform(0.7, 1.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get news sentiment: {e}")
            return self._get_default_source_data()
    
    def _combine_sentiment_scores(self, twitter_data: Dict, reddit_data: Dict, news_data: Dict) -> float:
        """Combine sentiment scores from multiple sources"""
        # Weighted average based on source reliability
        weights = {
            "twitter": 0.3,
            "reddit": 0.2,
            "news": 0.5
        }
        
        combined_sentiment = (
            twitter_data["sentiment"] * weights["twitter"] +
            reddit_data["sentiment"] * weights["reddit"] +
            news_data["sentiment"] * weights["news"]
        )
        
        return combined_sentiment
    
    def _calculate_confidence(self, twitter_data: Dict, reddit_data: Dict, news_data: Dict) -> float:
        """Calculate confidence in sentiment analysis"""
        # Confidence based on volume and agreement between sources
        total_volume = twitter_data["volume"] + reddit_data["volume"] + news_data["volume"]
        
        # Volume confidence (0 to 0.5)
        volume_confidence = min(total_volume / 100, 0.5)
        
        # Agreement confidence (0 to 0.5)
        sentiments = [twitter_data["sentiment"], reddit_data["sentiment"], news_data["sentiment"]]
        sentiment_std = np.std(sentiments)
        agreement_confidence = max(0, 0.5 - sentiment_std)
        
        return volume_confidence + agreement_confidence
    
    def _detect_sentiment_trend(self, symbol: str, current_sentiment: float) -> str:
        """Detect sentiment trend based on historical data"""
        # In production, this would analyze historical sentiment
        # For now, use simple thresholds
        
        if current_sentiment > self.sentiment_thresholds["BULLISH"]:
            return "BULLISH"
        elif current_sentiment < self.sentiment_thresholds["BEARISH"]:
            return "BEARISH"
        elif abs(current_sentiment) < 0.1:
            return "NEUTRAL"
        else:
            return "VOLATILE"
    
    def _calculate_momentum(self, symbol: str, current_sentiment: float) -> float:
        """Calculate sentiment momentum"""
        # In production, this would compare with previous sentiment
        # For now, simulate momentum
        return np.random.uniform(-0.5, 0.5)
    
    def _detect_catalysts(self, symbol: str, twitter_data: Dict, reddit_data: Dict, news_data: Dict) -> Dict:
        """Detect catalysts from sentiment data"""
        # Combine all text from sources
        all_text = " ".join([
            f"Twitter: {twitter_data.get('sample_text', '')}",
            f"Reddit: {reddit_data.get('sample_text', '')}",
            f"News: {news_data.get('sample_text', '')}"
        ]).lower()
        
        catalyst_detected = False
        catalyst_type = "NONE"
        catalyst_strength = 0.0
        
        # Check for catalyst keywords
        for catalyst_type_name, keywords in self.catalyst_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in all_text)
            if keyword_count > 0:
                catalyst_detected = True
                catalyst_type = catalyst_type_name
                catalyst_strength = min(keyword_count / len(keywords), 1.0)
                break
        
        return {
            "detected": catalyst_detected,
            "type": catalyst_type,
            "strength": catalyst_strength
        }
    
    def _calculate_engagement_score(self, twitter_data: Dict, reddit_data: Dict, news_data: Dict) -> float:
        """Calculate overall engagement score"""
        # Weighted average of engagement scores
        weights = [0.3, 0.2, 0.5]
        engagements = [
            twitter_data["engagement"],
            reddit_data["engagement"],
            news_data["engagement"]
        ]
        
        return sum(w * e for w, e in zip(weights, engagements))
    
    def _get_default_source_data(self) -> Dict:
        """Get default source data when API fails"""
        return {
            "sentiment": 0.0,
            "positive": 0,
            "negative": 0,
            "neutral": 1,
            "volume": 1,
            "engagement": 0.5
        }
    
    def _get_default_sentiment(self, symbol: str) -> SentimentData:
        """Get default sentiment data when analysis fails"""
        return SentimentData(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_sentiment=0.0,
            confidence=0.5,
            twitter_sentiment=0.0,
            reddit_sentiment=0.0,
            news_sentiment=0.0,
            positive_count=0,
            negative_count=0,
            neutral_count=1,
            mention_volume=1,
            engagement_score=0.5,
            sentiment_trend="NEUTRAL",
            momentum_score=0.0,
            catalyst_detected=False,
            catalyst_type="NONE",
            catalyst_strength=0.0
        )
    
    def _clean_cache(self):
        """Clean old cache entries"""
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, (data, timestamp) in self.sentiment_cache.items():
            if current_time - timestamp > self.cache_duration:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.sentiment_cache[key]
    
    def update_catalyst_score(self, pick: Dict) -> Dict:
        """Update catalyst score based on sentiment analysis"""
        try:
            symbol = pick["symbol"]
            sentiment_data = self.sentiment_cache.get(f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}")
            
            if sentiment_data:
                sentiment_data, _ = sentiment_data
                
                # Boost catalyst score based on sentiment
                sentiment_boost = sentiment_data.overall_sentiment * 0.3
                catalyst_boost = sentiment_data.catalyst_strength * 0.2
                
                # Update catalyst score
                current_catalyst = pick["features"].get("catalyst_score", 0.5)
                new_catalyst = current_catalyst + sentiment_boost + catalyst_boost
                
                # Clamp to [0, 1]
                pick["features"]["catalyst_score"] = min(max(new_catalyst, 0.0), 1.0)
                
                # Add sentiment context
                pick["sentiment_context"] = {
                    "overall_sentiment": sentiment_data.overall_sentiment,
                    "confidence": sentiment_data.confidence,
                    "trend": sentiment_data.sentiment_trend,
                    "catalyst_detected": sentiment_data.catalyst_detected,
                    "catalyst_type": sentiment_data.catalyst_type
                }
            
            return pick
            
        except Exception as e:
            self.logger.error(f"Failed to update catalyst score: {e}")
            return pick


# Integration with trading engine
class SentimentEnhancedTradingEngine:
    """Trading engine enhanced with sentiment analysis"""
    
    def __init__(self, sentiment_engine: SentimentEngine):
        self.sentiment_engine = sentiment_engine
        self.logger = logging.getLogger(__name__)
    
    async def generate_sentiment_enhanced_picks(self, symbols: List[str]) -> List[Dict]:
        """Generate picks enhanced with sentiment analysis"""
        try:
            picks = []
            
            for symbol in symbols:
                # Get sentiment data
                sentiment_data = await self.sentiment_engine.analyze_sentiment(symbol)
                
                # Generate base pick
                pick = await self._generate_base_pick(symbol)
                
                # Enhance with sentiment
                pick = self._enhance_pick_with_sentiment(pick, sentiment_data)
                
                picks.append(pick)
            
            return picks
            
        except Exception as e:
            self.logger.error(f"Failed to generate sentiment-enhanced picks: {e}")
            return []
    
    async def _generate_base_pick(self, symbol: str) -> Dict:
        """Generate base pick without sentiment"""
        return {
            "symbol": symbol,
            "side": "LONG",
            "score": np.random.uniform(0.6, 0.9),
            "features": {
                "momentum_15m": np.random.uniform(-0.05, 0.05),
                "rvol_10m": np.random.uniform(0.5, 2.0),
                "vwap_dist": np.random.uniform(-0.01, 0.01),
                "breakout_pct": np.random.uniform(0, 0.02),
                "spread_bps": np.random.uniform(1, 10),
                "catalyst_score": np.random.uniform(0, 1)
            },
            "risk": {
                "atr_5m": np.random.uniform(0.5, 2.0),
                "size_shares": 100,
                "stop": np.random.uniform(0.95, 0.98),
                "targets": [1.02, 1.05],
                "time_stop_min": 120
            },
            "notes": f"Base pick for {symbol}"
        }
    
    def _enhance_pick_with_sentiment(self, pick: Dict, sentiment_data: SentimentData) -> Dict:
        """Enhance pick with sentiment analysis"""
        # Boost score based on sentiment
        sentiment_boost = sentiment_data.overall_sentiment * 0.1
        confidence_boost = sentiment_data.confidence * 0.05
        
        # Update score
        pick["score"] = min(max(pick["score"] + sentiment_boost + confidence_boost, 0.0), 1.0)
        
        # Update catalyst score
        pick["features"]["catalyst_score"] = min(max(
            pick["features"]["catalyst_score"] + sentiment_data.catalyst_strength * 0.3, 0.0
        ), 1.0)
        
        # Add sentiment context
        pick["sentiment_context"] = {
            "overall_sentiment": sentiment_data.overall_sentiment,
            "confidence": sentiment_data.confidence,
            "trend": sentiment_data.sentiment_trend,
            "momentum": sentiment_data.momentum_score,
            "catalyst_detected": sentiment_data.catalyst_detected,
            "catalyst_type": sentiment_data.catalyst_type,
            "mention_volume": sentiment_data.mention_volume,
            "engagement_score": sentiment_data.engagement_score
        }
        
        # Update notes with sentiment insight
        if sentiment_data.catalyst_detected:
            pick["notes"] += f" | Sentiment: {sentiment_data.sentiment_trend} | Catalyst: {sentiment_data.catalyst_type}"
        else:
            pick["notes"] += f" | Sentiment: {sentiment_data.sentiment_trend}"
        
        return pick
