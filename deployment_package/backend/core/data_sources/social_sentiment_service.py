"""
Social Sentiment Service
Aggregates sentiment data from StockTwits, Reddit, and other social platforms.
"""

import os
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SentimentData:
    """Social sentiment data point"""
    platform: str
    symbol: str
    timestamp: datetime
    sentiment_score: float  # -1.0 to 1.0
    volume: int  # Number of mentions
    trending: bool
    url: Optional[str] = None
    summary: Optional[str] = None


class SocialSentimentService:
    """Service for aggregating social sentiment data"""

    def __init__(self):
        self.stocktwits_api_key = os.getenv("STOCKTWITS_API_KEY", "")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.enabled = bool(self.stocktwits_api_key or self.reddit_client_id)

    async def get_sentiment_for_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SentimentData]:
        """
        Get aggregated sentiment data for a symbol across all platforms.
        """
        if not self.enabled:
            logger.warning("Social sentiment service not configured")
            return []

        results = []
        
        # Get StockTwits sentiment
        try:
            stocktwits_data = await self._get_stocktwits_sentiment(
                symbol, start_date, end_date
            )
            results.extend(stocktwits_data)
        except Exception as e:
            logger.error(f"Error fetching StockTwits sentiment: {e}")

        # Get Reddit sentiment
        try:
            reddit_data = await self._get_reddit_sentiment(
                symbol, start_date, end_date
            )
            results.extend(reddit_data)
        except Exception as e:
            logger.error(f"Error fetching Reddit sentiment: {e}")

        return sorted(results, key=lambda x: x.timestamp)

    async def _get_stocktwits_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SentimentData]:
        """Get sentiment from StockTwits API"""
        if not self.stocktwits_api_key:
            return []

        # StockTwits API endpoint
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        
        headers = {
            "Authorization": f"Bearer {self.stocktwits_api_key}",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"StockTwits API returned {response.status}")
                        return []

                    data = await response.json()
                    messages = data.get("messages", [])

                    sentiment_data = []
                    for msg in messages:
                        msg_time = datetime.fromisoformat(
                            msg["created_at"].replace("Z", "+00:00")
                        )
                        if start_date <= msg_time <= end_date:
                            # Calculate sentiment from message
                            sentiment_score = self._calculate_sentiment_score(msg)
                            
                            sentiment_data.append(
                                SentimentData(
                                    platform="stocktwits",
                                    symbol=symbol,
                                    timestamp=msg_time,
                                    sentiment_score=sentiment_score,
                                    volume=1,
                                    trending=False,
                                    url=f"https://stocktwits.com/symbol/{symbol}",
                                    summary=msg.get("body", "")[:200],
                                )
                            )

                    return sentiment_data
            except Exception as e:
                logger.error(f"StockTwits API error: {e}")
                return []

    async def _get_reddit_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SentimentData]:
        """Get sentiment from Reddit API (using PRAW or direct API)"""
        if not self.reddit_client_id:
            return []

        # For now, return empty - can be enhanced with PRAW
        # PRAW requires more setup and authentication
        return []

    def _calculate_sentiment_score(self, message: Dict[str, Any]) -> float:
        """
        Simple sentiment analysis from message content.
        Returns score from -1.0 (very negative) to 1.0 (very positive).
        """
        body = message.get("body", "").lower()
        
        # Simple keyword-based sentiment
        positive_words = ["bull", "buy", "moon", "rocket", "gains", "profit", "up", "good", "great"]
        negative_words = ["bear", "sell", "crash", "drop", "loss", "down", "bad", "terrible"]
        
        positive_count = sum(1 for word in positive_words if word in body)
        negative_count = sum(1 for word in negative_words if word in body)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        # Normalize to -1.0 to 1.0
        score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        return max(-1.0, min(1.0, score))

    async def get_aggregated_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Get aggregated sentiment metrics for a time period.
        """
        sentiment_data = await self.get_sentiment_for_symbol(
            symbol, start_date, end_date
        )

        if not sentiment_data:
            return {
                "average_sentiment": 0.0,
                "total_volume": 0,
                "trending": False,
                "sources": [],
            }

        avg_sentiment = sum(s.sentiment_score for s in sentiment_data) / len(sentiment_data)
        total_volume = sum(s.volume for s in sentiment_data)
        trending = any(s.trending for s in sentiment_data)
        sources = list(set(s.platform for s in sentiment_data))

        return {
            "average_sentiment": avg_sentiment,
            "total_volume": total_volume,
            "trending": trending,
            "sources": sources,
            "data_points": len(sentiment_data),
        }

