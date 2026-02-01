"""
Deep Social Sentiment Service
Real-time integration with X/Twitter, Reddit, StockTwits for comprehensive sentiment analysis.
Similar to Trade Ideas' social sentiment features.
"""
import os
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from django.core.cache import cache
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DeepSentimentData:
    """Enhanced sentiment data with time series"""
    platform: str
    symbol: str
    timestamp: datetime
    sentiment_score: float  # -1.0 to 1.0
    volume: int  # Number of mentions
    engagement_score: float  # Likes, retweets, comments weighted
    momentum: float  # Change in sentiment over time
    divergence: float  # Divergence from price action
    
    # Raw data
    mentions: List[Dict[str, Any]] = None
    top_influencers: List[str] = None


class DeepSocialSentimentService:
    """
    Deep integration with social platforms for real-time sentiment.
    Covers top 500 stocks with LSTM-ready time series data.
    """
    
    def __init__(self):
        # API keys
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY', '')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET', '')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
        self.stocktwits_api_key = os.getenv('STOCKTWITS_API_KEY', '')
        
        # Configuration
        self.cache_ttl = 300  # 5 minutes
        self.top_stocks_limit = 500  # Top 500 stocks to monitor
        
        # Sentiment keywords (enhanced)
        self.positive_keywords = [
            'bullish', 'buy', 'moon', 'rocket', 'gains', 'profit', 'strong', 'growth',
            'breakout', 'rally', 'surge', 'soar', 'pump', 'hold', 'long', 'call',
            'beat', 'exceed', 'upgrade', 'target', 'upside'
        ]
        self.negative_keywords = [
            'bearish', 'sell', 'crash', 'dump', 'loss', 'weak', 'decline', 'fall',
            'breakdown', 'drop', 'plunge', 'dip', 'short', 'put', 'downgrade',
            'miss', 'cut', 'reduce', 'crisis', 'warning'
        ]
    
    async def get_comprehensive_sentiment(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> DeepSentimentData:
        """
        Get comprehensive sentiment from all platforms.
        
        Args:
            symbol: Stock symbol
            hours_back: How many hours of history to fetch
        
        Returns:
            Aggregated sentiment data with time series
        """
        start_time = datetime.now() - timedelta(hours=hours_back)
        
        # Fetch from all platforms in parallel
        twitter_data, reddit_data, stocktwits_data = await asyncio.gather(
            self._get_twitter_sentiment(symbol, start_time),
            self._get_reddit_sentiment(symbol, start_time),
            self._get_stocktwits_sentiment(symbol, start_time),
            return_exceptions=True
        )
        
        # Aggregate results
        all_mentions = []
        if isinstance(twitter_data, list):
            all_mentions.extend(twitter_data)
        if isinstance(reddit_data, list):
            all_mentions.extend(reddit_data)
        if isinstance(stocktwits_data, list):
            all_mentions.extend(stocktwits_data)
        
        # Calculate aggregated metrics
        if all_mentions:
            sentiment_scores = [m.get('sentiment', 0.0) for m in all_mentions]
            engagement_scores = [m.get('engagement', 0.0) for m in all_mentions]
            
            # Weighted average sentiment (by engagement)
            total_engagement = sum(engagement_scores)
            if total_engagement > 0:
                weighted_sentiment = sum(
                    s * e for s, e in zip(sentiment_scores, engagement_scores)
                ) / total_engagement
            else:
                weighted_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            # Calculate momentum (change over time)
            if len(all_mentions) > 1:
                # Split into two time periods
                midpoint = len(all_mentions) // 2
                recent_sentiment = np.mean([m.get('sentiment', 0.0) for m in all_mentions[midpoint:]])
                earlier_sentiment = np.mean([m.get('sentiment', 0.0) for m in all_mentions[:midpoint]])
                momentum = recent_sentiment - earlier_sentiment
            else:
                momentum = 0.0
            
            # Top influencers
            top_influencers = self._extract_top_influencers(all_mentions)
            
            return DeepSentimentData(
                platform='aggregated',
                symbol=symbol,
                timestamp=datetime.now(),
                sentiment_score=float(weighted_sentiment),
                volume=len(all_mentions),
                engagement_score=float(np.mean(engagement_scores)),
                momentum=float(momentum),
                divergence=0.0,  # Would need price data to calculate
                mentions=all_mentions,
                top_influencers=top_influencers
            )
        else:
            # Return default if no data
            return DeepSentimentData(
                platform='aggregated',
                symbol=symbol,
                timestamp=datetime.now(),
                sentiment_score=0.0,
                volume=0,
                engagement_score=0.0,
                momentum=0.0,
                divergence=0.0
            )
    
    async def _get_twitter_sentiment(
        self,
        symbol: str,
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get sentiment from X/Twitter API v2"""
        if not self.twitter_bearer_token:
            logger.debug("Twitter bearer token not configured")
            return []
        
        try:
            # Check cache
            cache_key = f"twitter_sentiment:{symbol}:{start_time.date()}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}',
                'Content-Type': 'application/json'
            }
            
            # Build query (exclude retweets, English only)
            query = f"${symbol} OR {symbol} -is:retweet lang:en"
            
            params = {
                'query': query,
                'max_results': 100,
                'tweet.fields': 'created_at,public_metrics,author_id,text',
                'expansions': 'author_id',
                'user.fields': 'username,verified,followers_count'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweets = data.get('data', [])
                        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}
                        
                        mentions = []
                        for tweet in tweets:
                            if datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')) < start_time:
                                continue
                            
                            text = tweet.get('text', '').lower()
                            metrics = tweet.get('public_metrics', {})
                            author = users.get(tweet.get('author_id'))
                            
                            # Calculate sentiment
                            sentiment = self._calculate_sentiment(text)
                            
                            # Calculate engagement (weighted)
                            engagement = (
                                metrics.get('like_count', 0) * 1.0 +
                                metrics.get('retweet_count', 0) * 2.0 +
                                metrics.get('reply_count', 0) * 0.5 +
                                metrics.get('quote_count', 0) * 1.5
                            )
                            
                            # Boost engagement for verified users
                            if author and author.get('verified'):
                                engagement *= 1.5
                            
                            mentions.append({
                                'platform': 'twitter',
                                'text': tweet.get('text', ''),
                                'sentiment': sentiment,
                                'engagement': engagement,
                                'timestamp': datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                                'author': author.get('username') if author else None,
                                'verified': author.get('verified') if author else False,
                                'url': f"https://twitter.com/{author.get('username') if author else 'unknown'}/status/{tweet.get('id')}"
                            })
                        
                        # Cache for 5 minutes
                        cache.set(cache_key, mentions, timeout=self.cache_ttl)
                        return mentions
                    else:
                        logger.warning(f"Twitter API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching Twitter sentiment for {symbol}: {e}")
            return []
    
    async def _get_reddit_sentiment(
        self,
        symbol: str,
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get sentiment from Reddit API"""
        if not self.reddit_client_id:
            logger.debug("Reddit credentials not configured")
            return []
        
        try:
            # Check cache
            cache_key = f"reddit_sentiment:{symbol}:{start_time.date()}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # Reddit API requires OAuth2 - simplified version here
            # In production, use PRAW (Python Reddit API Wrapper)
            url = "https://www.reddit.com/r/wallstreetbets/search.json"
            params = {
                'q': symbol,
                'sort': 'new',
                'limit': 25
            }
            
            headers = {
                'User-Agent': 'RichesReach/1.0'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        mentions = []
                        for post in posts:
                            post_data = post.get('data', {})
                            created_utc = datetime.fromtimestamp(post_data.get('created_utc', 0))
                            
                            if created_utc < start_time:
                                continue
                            
                            title = post_data.get('title', '').lower()
                            selftext = post_data.get('selftext', '').lower()
                            text = f"{title} {selftext}"
                            
                            # Calculate sentiment
                            sentiment = self._calculate_sentiment(text)
                            
                            # Engagement (upvotes, comments)
                            engagement = (
                                post_data.get('ups', 0) * 1.0 +
                                post_data.get('num_comments', 0) * 0.5
                            )
                            
                            mentions.append({
                                'platform': 'reddit',
                                'text': title,
                                'sentiment': sentiment,
                                'engagement': engagement,
                                'timestamp': created_utc,
                                'author': post_data.get('author'),
                                'subreddit': post_data.get('subreddit'),
                                'url': f"https://reddit.com{post_data.get('permalink', '')}"
                            })
                        
                        # Cache for 5 minutes
                        cache.set(cache_key, mentions, timeout=self.cache_ttl)
                        return mentions
                    else:
                        logger.warning(f"Reddit API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching Reddit sentiment for {symbol}: {e}")
            return []
    
    async def _get_stocktwits_sentiment(
        self,
        symbol: str,
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get sentiment from StockTwits API"""
        if not self.stocktwits_api_key:
            logger.debug("StockTwits API key not configured")
            return []
        
        try:
            # Check cache
            cache_key = f"stocktwits_sentiment:{symbol}:{start_time.date()}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            params = {
                'limit': 30
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        messages = data.get('messages', [])
                        
                        mentions = []
                        for msg in messages:
                            created_at = datetime.fromisoformat(
                                msg.get('created_at', '').replace('Z', '+00:00')
                            )
                            
                            if created_at < start_time:
                                continue
                            
                            body = msg.get('body', '').lower()
                            sentiment = self._calculate_sentiment(body)
                            
                            # Engagement (likes, reshares)
                            engagement = (
                                msg.get('likes', {}).get('total', 0) * 1.0 +
                                msg.get('reshares', {}).get('total', 0) * 1.5
                            )
                            
                            mentions.append({
                                'platform': 'stocktwits',
                                'text': msg.get('body', ''),
                                'sentiment': sentiment,
                                'engagement': engagement,
                                'timestamp': created_at,
                                'author': msg.get('user', {}).get('username'),
                                'url': f"https://stocktwits.com/symbol/{symbol}"
                            })
                        
                        # Cache for 5 minutes
                        cache.set(cache_key, mentions, timeout=self.cache_ttl)
                        return mentions
                    else:
                        logger.warning(f"StockTwits API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching StockTwits sentiment: {e}")
            return []
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score from text (-1.0 to 1.0)"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        # Normalize to -1.0 to 1.0
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        
        # Apply intensity (more keywords = stronger sentiment)
        intensity = min((positive_count + negative_count) / 5.0, 1.0)
        
        return sentiment * intensity
    
    def _extract_top_influencers(self, mentions: List[Dict[str, Any]], top_n: int = 5) -> List[str]:
        """Extract top influencers by engagement"""
        influencer_scores = {}
        
        for mention in mentions:
            author = mention.get('author')
            if not author:
                continue
            
            engagement = mention.get('engagement', 0.0)
            verified = mention.get('verified', False)
            
            # Boost score for verified users
            score = engagement * (1.5 if verified else 1.0)
            
            if author in influencer_scores:
                influencer_scores[author] += score
            else:
                influencer_scores[author] = score
        
        # Sort by score and return top N
        sorted_influencers = sorted(
            influencer_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [author for author, score in sorted_influencers[:top_n]]
    
    async def get_sentiment_time_series(
        self,
        symbol: str,
        days: int = 7
    ) -> pd.Series:
        """
        Get sentiment time series (LSTM-ready).
        Returns pandas Series with datetime index.
        """
        try:
            import pandas as pd
            
            # Get data for each day
            sentiment_values = []
            timestamps = []
            
            for day in range(days):
                date = datetime.now() - timedelta(days=day)
                start_time = date.replace(hour=0, minute=0, second=0)
                end_time = date.replace(hour=23, minute=59, second=59)
                
                # Get sentiment for this day
                data = await self.get_comprehensive_sentiment(symbol, hours_back=24)
                sentiment_values.append(data.sentiment_score)
                timestamps.append(date)
            
            # Create time series
            series = pd.Series(sentiment_values, index=pd.to_datetime(timestamps))
            return series.sort_index()
            
        except Exception as e:
            logger.error(f"Error creating sentiment time series: {e}")
            return pd.Series()


# Global instance
_deep_social_sentiment_service = None

def get_deep_social_sentiment_service() -> DeepSocialSentimentService:
    """Get global deep social sentiment service instance"""
    global _deep_social_sentiment_service
    if _deep_social_sentiment_service is None:
        _deep_social_sentiment_service = DeepSocialSentimentService()
    return _deep_social_sentiment_service

