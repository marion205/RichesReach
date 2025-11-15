"""
Unified Data Service
Aggregates data from all sources (news, sentiment, options, economic indicators)
and provides a unified interface for stock moment generation.
"""

import os
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .social_sentiment_service import SocialSentimentService, SentimentData
from .options_flow_service import OptionsFlowService, OptionsFlowData
from .economic_indicators_service import EconomicIndicatorsService, EconomicIndicator

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Unified event structure for moment generation"""
    type: str  # "EARNINGS", "NEWS", "INSIDER", "MACRO", "SENTIMENT", "OPTIONS"
    time: datetime
    headline: str
    summary: str
    url: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedDataService:
    """
    Unified service that aggregates data from all sources.
    This is the main interface for the stock_moment_worker.
    """

    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        self.polygon_api_key = os.getenv("POLYGON_API_KEY", "")
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
        
        self.sentiment_service = SocialSentimentService()
        self.options_service = OptionsFlowService()
        self.economic_service = EconomicIndicatorsService()

    async def get_all_events_for_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """
        Get all events for a symbol from all data sources.
        Deduplicates and prioritizes events.
        """
        events = []

        # 1. Get news events (NewsAPI)
        try:
            news_events = await self._get_news_events(symbol, start_date, end_date)
            events.extend(news_events)
        except Exception as e:
            logger.error(f"Error fetching news events: {e}")

        # 2. Get earnings events (Polygon/Finnhub)
        try:
            earnings_events = await self._get_earnings_events(symbol, start_date, end_date)
            events.extend(earnings_events)
        except Exception as e:
            logger.error(f"Error fetching earnings events: {e}")

        # 3. Get social sentiment events
        try:
            sentiment_events = await self._get_sentiment_events(symbol, start_date, end_date)
            events.extend(sentiment_events)
        except Exception as e:
            logger.error(f"Error fetching sentiment events: {e}")

        # 4. Get options flow events
        try:
            options_events = await self._get_options_events(symbol, start_date, end_date)
            events.extend(options_events)
        except Exception as e:
            logger.error(f"Error fetching options events: {e}")

        # 5. Get economic indicator events
        try:
            macro_events = await self._get_macro_events(start_date, end_date)
            events.extend(macro_events)
        except Exception as e:
            logger.error(f"Error fetching macro events: {e}")

        # Deduplicate events (same headline + time)
        deduplicated = self._deduplicate_events(events)

        # Sort by timestamp
        return sorted(deduplicated, key=lambda x: x.time)

    async def _get_news_events(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Get news events from NewsAPI"""
        if not self.news_api_key:
            return []

        url = "https://newsapi.org/v2/everything"
        
        params = {
            "q": symbol,
            "apiKey": self.news_api_key,
            "sortBy": "publishedAt",
            "pageSize": 50,
            "language": "en",
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"NewsAPI returned {response.status}")
                        return []

                    data = await response.json()
                    articles = data.get("articles", [])

                    events = []
                    for article in articles:
                        published_at = datetime.fromisoformat(
                            article.get("publishedAt", "").replace("Z", "+00:00")
                        )
                        
                        if start_date <= published_at <= end_date:
                            events.append(
                                Event(
                                    type="NEWS",
                                    time=published_at,
                                    headline=article.get("title", "No title"),
                                    summary=article.get("description", "")[:500],
                                    url=article.get("url"),
                                    source="newsapi",
                                    metadata={
                                        "source_name": article.get("source", {}).get("name"),
                                        "author": article.get("author"),
                                    },
                                )
                            )

                    return events
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

    async def _get_earnings_events(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Get earnings events from Polygon/Finnhub"""
        events = []

        # Try Polygon first
        if self.polygon_api_key:
            try:
                polygon_events = await self._get_polygon_earnings(symbol, start_date, end_date)
                events.extend(polygon_events)
            except Exception as e:
                logger.error(f"Polygon earnings error: {e}")

        # Try Finnhub
        if self.finnhub_api_key:
            try:
                finnhub_events = await self._get_finnhub_earnings(symbol, start_date, end_date)
                events.extend(finnhub_events)
            except Exception as e:
                logger.error(f"Finnhub earnings error: {e}")

        return events

    async def _get_polygon_earnings(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Get earnings from Polygon.io"""
        url = f"https://api.polygon.io/v2/reference/financials"
        
        params = {
            "ticker": symbol,
            "apiKey": self.polygon_api_key,
            "timeframe": "quarterly",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = data.get("results", [])

                    events = []
                    for result in results:
                        report_date_str = result.get("start_date", "")
                        if not report_date_str:
                            continue

                        report_date = datetime.fromisoformat(report_date_str)
                        if start_date <= report_date <= end_date:
                            events.append(
                                Event(
                                    type="EARNINGS",
                                    time=report_date,
                                    headline=f"{symbol} Earnings Report",
                                    summary=f"Quarterly earnings released. Revenue: ${result.get('revenue', 0):,.0f}",
                                    source="polygon",
                                    metadata=result,
                                )
                            )

                    return events
        except Exception as e:
            logger.error(f"Polygon earnings API error: {e}")
            return []

    async def _get_finnhub_earnings(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Get earnings from Finnhub"""
        url = "https://finnhub.io/api/v1/calendar/earnings"
        
        params = {
            "symbol": symbol,
            "token": self.finnhub_api_key,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    earnings = data.get("earningsCalendar", [])

                    events = []
                    for earning in earnings:
                        date_str = earning.get("date", "")
                        if not date_str:
                            continue

                        earning_date = datetime.fromisoformat(date_str)
                        if start_date <= earning_date <= end_date:
                            events.append(
                                Event(
                                    type="EARNINGS",
                                    time=earning_date,
                                    headline=f"{symbol} Earnings Expected",
                                    summary=f"Earnings expected. EPS estimate: ${earning.get('epsEstimate', 0):.2f}",
                                    source="finnhub",
                                    metadata=earning,
                                )
                            )

                    return events
        except Exception as e:
            logger.error(f"Finnhub earnings API error: {e}")
            return []

    async def _get_sentiment_events(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Convert sentiment data to events"""
        sentiment_data = await self.sentiment_service.get_sentiment_for_symbol(
            symbol, start_date, end_date
        )

        events = []
        for sentiment in sentiment_data:
            if abs(sentiment.sentiment_score) > 0.3:  # Only significant sentiment
                sentiment_label = "positive" if sentiment.sentiment_score > 0 else "negative"
                events.append(
                    Event(
                        type="SENTIMENT",
                        time=sentiment.timestamp,
                        headline=f"{symbol} Social Sentiment: {sentiment_label.title()}",
                        summary=f"Social sentiment: {sentiment.sentiment_score:.2f} on {sentiment.platform}",
                        url=sentiment.url,
                        source=sentiment.platform,
                        metadata={
                            "sentiment_score": sentiment.sentiment_score,
                            "volume": sentiment.volume,
                            "trending": sentiment.trending,
                        },
                    )
                )

        return events

    async def _get_options_events(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Convert options flow data to events"""
        options_data = await self.options_service.get_unusual_options_activity(
            symbol, start_date, end_date
        )

        events = []
        for option in options_data:
            if option.unusual:
                events.append(
                    Event(
                        type="OPTIONS",
                        time=option.timestamp,
                        headline=f"Unusual {option.type.upper()} Activity: {symbol}",
                        summary=f"Unusual {option.type} volume: {option.volume} contracts at ${option.strike} strike",
                        source="polygon",
                        metadata={
                            "strike": option.strike,
                            "expiry": option.expiry.isoformat(),
                            "premium": option.premium,
                        },
                    )
                )

        return events

    async def _get_macro_events(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Event]:
        """Convert economic indicators to events"""
        indicators = await self.economic_service.get_relevant_indicators(
            start_date, end_date
        )

        events = []
        for indicator in indicators:
            # Only include significant changes
            if abs(indicator.change) > 0.1:
                events.append(
                    Event(
                        type="MACRO",
                        time=indicator.timestamp,
                        headline=f"{indicator.name}: {indicator.change:+.2f}%",
                        summary=indicator.description,
                        source=indicator.source,
                        metadata={
                            "value": indicator.value,
                            "change": indicator.change,
                            "impact": indicator.impact,
                        },
                    )
                )

        return events

    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        """Remove duplicate events (same headline + similar time)"""
        seen = set()
        deduplicated = []

        for event in events:
            # Create a key from headline and rounded time (to nearest hour)
            time_key = event.time.replace(minute=0, second=0, microsecond=0)
            key = (event.headline.lower(), time_key.isoformat())

            if key not in seen:
                seen.add(key)
                deduplicated.append(event)

        return deduplicated

