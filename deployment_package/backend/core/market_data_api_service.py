"""
Market Data API Service for Real Financial Data
Integrates with Alpha Vantage, Finnhub, Yahoo Finance, and other providers
"""
try:
    import yfinance as yf
except ImportError:
    yf = None
import ssl
import os
import logging
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataProvider(Enum):
    """Supported data providers"""
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    YAHOO_FINANCE = "yahoo_finance"
    QUANDL = "quandl"
    POLYGON = "polygon"
    IEX_CLOUD = "iex_cloud"


@dataclass
class APIKey:
    """API key configuration"""
    provider: DataProvider
    key: str
    rate_limit: int  # requests per minute
    last_request: float = 0.0
    request_count: int = 0


class MarketDataAPIService:
    """
    Service for fetching real market data from various providers.
    Handles basic rate limiting and light in-memory caching.
    """

    def __init__(self) -> None:
        # Rate limiting per provider (free-tier friendly defaults)
        self.rate_limits: Dict[DataProvider, int] = {
            DataProvider.ALPHA_VANTAGE: 5,    # 5 requests per minute (free tier)
            DataProvider.FINNHUB: 60,         # 60 requests per minute (free tier)
            DataProvider.YAHOO_FINANCE: 100,  # estimated
            DataProvider.QUANDL: 50,          # 50 requests per day (free tier)
            DataProvider.POLYGON: 5,          # example low limit
            DataProvider.IEX_CLOUD: 100,       # typical higher limit,
        }

        # Loaded API keys mapped by provider
        self.api_keys: Dict[DataProvider, APIKey] = self._load_api_keys()

        # Shared aiohttp session (lazy-created)
        self.session: Optional[aiohttp.ClientSession] = None

        # Very simple in-memory cache
        # cache_key -> (timestamp, payload)
        self.cache: Dict[str, Any] = {}
        self.cache_duration: int = 300  # seconds (5 minutes)

    # -------------------------------------------------------------------------
    # Lifecycle / context manager
    # -------------------------------------------------------------------------
    async def __aenter__(self) -> "MarketDataAPIService":
        if self.session is None:
            # For dev: allow unverified SSL; adjust for prod if needed
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _load_api_keys(self) -> Dict[DataProvider, APIKey]:
        """Load API keys from environment variables."""
        api_keys: Dict[DataProvider, APIKey] = {}

        # Alpha Vantage
        alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if alpha_key:
            api_keys[DataProvider.ALPHA_VANTAGE] = APIKey(
                provider=DataProvider.ALPHA_VANTAGE,
                key=alpha_key,
                rate_limit=self.rate_limits[DataProvider.ALPHA_VANTAGE],
            )

        # Finnhub
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            api_keys[DataProvider.FINNHUB] = APIKey(
                provider=DataProvider.FINNHUB,
                key=finnhub_key,
                rate_limit=self.rate_limits[DataProvider.FINNHUB],
            )

        # Quandl
        quandl_key = os.getenv("QUANDL_API_KEY")
        if quandl_key:
            api_keys[DataProvider.QUANDL] = APIKey(
                provider=DataProvider.QUANDL,
                key=quandl_key,
                rate_limit=self.rate_limits[DataProvider.QUANDL],
            )

        # Polygon
        polygon_key = os.getenv("POLYGON_API_KEY")
        if polygon_key:
            api_keys[DataProvider.POLYGON] = APIKey(
                provider=DataProvider.POLYGON,
                key=polygon_key,
                rate_limit=self.rate_limits[DataProvider.POLYGON],
            )

        # IEX Cloud
        iex_key = os.getenv("IEX_CLOUD_API_KEY")
        if iex_key:
            api_keys[DataProvider.IEX_CLOUD] = APIKey(
                provider=DataProvider.IEX_CLOUD,
                key=iex_key,
                rate_limit=self.rate_limits[DataProvider.IEX_CLOUD],
            )

        logger.info("Loaded %d API keys", len(api_keys))
        return api_keys

    def _check_rate_limit(self, provider: DataProvider) -> bool:
        """
        Basic in-memory rate limit check.
        Returns True if a request is allowed, False if we should back off.
        """
        api_key = self.api_keys.get(provider)
        if not api_key:
            return False

        current_time = time.time()

        # Reset counter if more than 60s passed
        if current_time - api_key.last_request >= 60:
            api_key.request_count = 0
            api_key.last_request = current_time

        if api_key.request_count >= api_key.rate_limit:
            logger.warning(
                "Rate limit reached for provider %s (limit=%s)",
                provider.value,
                api_key.rate_limit,
            )
            return False

        api_key.request_count += 1
        return True

    def _get_cache_key(self, provider: str, symbol: str, data_type: str) -> str:
        """
        Generate a cache key. Currently uses provider/symbol/data_type + hour,
        so data is refreshed at least hourly even if cache_duration is longer.
        """
        return f"{provider}_{symbol}_{data_type}_{datetime.utcnow().strftime('%Y%m%d_%H')}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still within cache_duration."""
        if cache_key not in self.cache:
            return False
        cache_time, _ = self.cache[cache_key]
        return (time.time() - cache_time) < self.cache_duration

    # -------------------------------------------------------------------------
    # Public API: Quotes
    # -------------------------------------------------------------------------
    async def get_stock_quote(
        self,
        symbol: str,
        provider: Optional[DataProvider] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock quote.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            provider: Preferred data provider (optional)

        Returns:
            Stock quote data or None if error.
        """
        try:
            # Ensure we have an aiohttp session
            if self.session is None:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                self.session = aiohttp.ClientSession(connector=connector)

            # Cache check
            cache_key = self._get_cache_key(
                provider.value if provider else "auto",
                symbol,
                "quote",
            )
            if self._is_cache_valid(cache_key):
                _, cached = self.cache[cache_key]
                return cached

            # Try preferred provider first
            if provider and self._check_rate_limit(provider):
                quote = await self._fetch_quote_from_provider(symbol, provider)
                if quote:
                    self.cache[cache_key] = (time.time(), quote)
                    return quote

            # Try other available providers (only implemented ones)
            implemented_providers = {
                DataProvider.ALPHA_VANTAGE,
                DataProvider.FINNHUB,
                DataProvider.YAHOO_FINANCE,
                DataProvider.IEX_CLOUD,
            }

            for available_provider in self.api_keys.keys():
                if (
                    available_provider != provider
                    and available_provider in implemented_providers
                    and self._check_rate_limit(available_provider)
                ):
                    quote = await self._fetch_quote_from_provider(symbol, available_provider)
                    if quote:
                        self.cache[cache_key] = (time.time(), quote)
                        return quote

            logger.warning("No available providers for stock quote: %s", symbol)
            return None
        except Exception as e:
            logger.error("Error fetching stock quote for %s: %s", symbol, e)
            return None

    async def _fetch_quote_from_provider(
        self,
        symbol: str,
        provider: DataProvider,
    ) -> Optional[Dict[str, Any]]:
        """Fetch quote from a specific provider."""
        try:
            if provider == DataProvider.ALPHA_VANTAGE:
                return await self._fetch_alpha_vantage_quote(symbol)
            if provider == DataProvider.FINNHUB:
                return await self._fetch_finnhub_quote(symbol)
            if provider == DataProvider.YAHOO_FINANCE:
                return await self._fetch_yahoo_quote(symbol)
            if provider == DataProvider.IEX_CLOUD:
                return await self._fetch_iex_quote(symbol)

            logger.warning("Provider %s not implemented for quotes", provider.value)
            return None
        except Exception as e:
            logger.error(
                "Error fetching quote from %s for %s: %s",
                provider.value,
                symbol,
                e,
            )
            return None

    async def _fetch_alpha_vantage_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Alpha Vantage."""
        api_key = self.api_keys.get(DataProvider.ALPHA_VANTAGE)
        if not api_key or self.session is None:
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key.key,
        }

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            if "Global Quote" not in data:
                return None
            quote = data["Global Quote"]
            try:
                return {
                    "symbol": symbol,
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": float(
                        quote.get("10. change percent", "0%").rstrip("%")
                    ),
                    "volume": int(quote.get("06. volume", 0)),
                    # Alpha Vantage free tier does not directly return market cap
                    "market_cap": float(quote.get("07. market cap", 0) or 0),
                    "provider": "alpha_vantage",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error("Error parsing Alpha Vantage quote for %s: %s", symbol, e)
                return None

    async def _fetch_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Finnhub."""
        api_key = self.api_keys.get(DataProvider.FINNHUB)
        if not api_key or self.session is None:
            return None

        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": api_key.key,
        }

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            try:
                return {
                    "symbol": symbol,
                    "price": data.get("c", 0),
                    "change": data.get("d", 0),
                    "change_percent": data.get("dp", 0),
                    "high": data.get("h", 0),
                    "low": data.get("l", 0),
                    "open": data.get("o", 0),
                    "previous_close": data.get("pc", 0),
                    "provider": "finnhub",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error("Error parsing Finnhub quote for %s: %s", symbol, e)
                return None

    async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Yahoo Finance (via yfinance)."""
        try:
            if yf is None:
                logger.warning("yfinance not available for Yahoo Finance quotes")
                return None
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "price": info.get("regularMarketPrice", 0),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "provider": "yahoo_finance",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except ImportError:
            logger.warning("yfinance not available for Yahoo Finance quotes")
            return None
        except Exception as e:
            logger.error("Error fetching Yahoo Finance quote for %s: %s", symbol, e)
            return None

    async def _fetch_iex_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from IEX Cloud."""
        api_key = self.api_keys.get(DataProvider.IEX_CLOUD)
        if not api_key or self.session is None:
            return None

        url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
        params = {"token": api_key.key}

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            try:
                return {
                    "symbol": data.get("symbol", symbol),
                    "price": data.get("latestPrice", 0),
                    "change": data.get("change", 0),
                    "change_percent": data.get("changePercent", 0),
                    "volume": data.get("volume", 0),
                    "market_cap": data.get("marketCap", 0),
                    "pe_ratio": data.get("peRatio", 0),
                    "dividend_yield": data.get("ytdChange", 0),
                    "provider": "iex_cloud",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error("Error parsing IEX quote for %s: %s", symbol, e)
                return None

    # -------------------------------------------------------------------------
    # Public API: Historical data
    # -------------------------------------------------------------------------
    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        provider: Optional[DataProvider] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y',
                   '2y', '5y', '10y', 'ytd', 'max')
            provider: Preferred data provider

        Returns:
            Historical data DataFrame or None if error.
        """
        try:
            # Prefer Yahoo Finance for historical data if not explicitly overridden
            if provider is None or provider == DataProvider.YAHOO_FINANCE:
                try:
                    if yf is None:
                        logger.warning("yfinance not available for historical data")
                    else:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period=period)
                        if not hist.empty:
                            return hist
                except ImportError:
                    logger.warning("yfinance not available for historical data")
                except Exception as e:
                    logger.warning("Yahoo Finance historical failed for %s: %s", symbol, e)

            # Try other providers
            for available_provider in self.api_keys.keys():
                if available_provider == provider:
                    continue
                if not self._check_rate_limit(available_provider):
                    continue
                df = await self._fetch_historical_from_provider(
                    symbol, period, available_provider
                )
                if df is not None and not df.empty:
                    return df

            logger.warning("No available providers for historical data: %s", symbol)
            return None
        except Exception as e:
            logger.error("Error fetching historical data for %s: %s", symbol, e)
            return None

    async def _fetch_historical_from_provider(
        self,
        symbol: str,
        period: str,
        provider: DataProvider,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data from a specific provider."""
        try:
            if provider == DataProvider.ALPHA_VANTAGE:
                return await self._fetch_alpha_vantage_historical(symbol, period)
            if provider == DataProvider.FINNHUB:
                return await self._fetch_finnhub_historical(symbol, period)

            logger.warning(
                "Provider %s not implemented for historical data", provider.value
            )
            return None
        except Exception as e:
            logger.error(
                "Error fetching historical data from %s for %s: %s",
                provider.value,
                symbol,
                e,
            )
            return None

    async def _fetch_alpha_vantage_historical(
        self,
        symbol: str,
        period: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical daily data from Alpha Vantage."""
        api_key = self.api_keys.get(DataProvider.ALPHA_VANTAGE)
        if not api_key or self.session is None:
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key.key,
            "outputsize": "full",
        }

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            if "Time Series (Daily)" not in data:
                return None

            time_series = data["Time Series (Daily)"]
            df = pd.DataFrame.from_dict(time_series, orient="index")
            df.index = pd.to_datetime(df.index)
            df.columns = ["open", "high", "low", "close", "volume"]

            for col in df.columns:
                df[col] = pd.to_numeric(df[col])

            df = df.sort_index()
            return df

    async def _fetch_finnhub_historical(
        self,
        symbol: str,
        period: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical daily data from Finnhub."""
        api_key = self.api_keys.get(DataProvider.FINNHUB)
        if not api_key or self.session is None:
            return None

        end_date = datetime.utcnow()

        if period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "1mo":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=365)

        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp()),
            "token": api_key.key,
        }

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            if data.get("s") != "ok":
                return None

            df = pd.DataFrame(
                {
                    "open": data["o"],
                    "high": data["h"],
                    "low": data["l"],
                    "close": data["c"],
                    "volume": data["v"],
                },
                index=pd.to_datetime(data["t"], unit="s"),
            )
            return df

    # -------------------------------------------------------------------------
    # Public API: Market overview & economic indicators
    # -------------------------------------------------------------------------
    async def get_market_overview(self) -> Optional[Dict[str, Any]]:
        """Get an overview of major indices + simple sentiment."""
        try:
            indices = ["^GSPC", "^DJI", "^IXIC", "^VIX"]  # S&P 500, Dow, NASDAQ, VIX
            market_data: Dict[str, Any] = {}

            for index in indices:
                quote = await self.get_stock_quote(index)
                if quote:
                    market_data[index] = quote

            if not market_data:
                return None

            # Simple sentiment: average % change of tracked indices
            changes = [
                q.get("change_percent", 0)
                for q in market_data.values()
                if isinstance(q.get("change_percent", 0), (int, float))
            ]
            avg_change = sum(changes) / len(changes) if changes else 0

            if avg_change > 1:
                sentiment = "bullish"
            elif avg_change < -1:
                sentiment = "bearish"
            else:
                sentiment = "neutral"

            return {
                "indices": market_data,
                "sentiment": sentiment,
                "average_change": avg_change,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Error fetching market overview: %s", e)
            return None

    async def get_economic_indicators(self) -> Optional[Dict[str, Any]]:
        """Get key economic indicators from available providers."""
        try:
            indicators: Dict[str, Any] = {}

            for provider in self.api_keys.keys():
                if provider == DataProvider.ALPHA_VANTAGE and self._check_rate_limit(
                    provider
                ):
                    gdp_data = await self._fetch_alpha_vantage_economic(
                        "REAL_GDP", provider
                    )
                    if gdp_data:
                        indicators["gdp"] = gdp_data

                elif provider == DataProvider.FINNHUB and self._check_rate_limit(
                    provider
                ):
                    calendar = await self._fetch_finnhub_economic_calendar(provider)
                    if calendar:
                        indicators["economic_calendar"] = calendar

            return indicators or None
        except Exception as e:
            logger.error("Error fetching economic indicators: %s", e)
            return None

    async def _fetch_alpha_vantage_economic(
        self,
        indicator: str,
        provider: DataProvider,
    ) -> Optional[Dict[str, Any]]:
        """Fetch economic data from Alpha Vantage."""
        api_key = self.api_keys.get(provider)
        if not api_key or self.session is None:
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            "function": indicator,
            "apikey": api_key.key,
        }

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            return data

    async def _fetch_finnhub_economic_calendar(
        self,
        provider: DataProvider,
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch economic calendar from Finnhub."""
        api_key = self.api_keys.get(provider)
        if not api_key or self.session is None:
            return None

        url = "https://finnhub.io/api/v1/calendar/economic"
        params = {"token": api_key.key}

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            return data.get("economicCalendar", [])

    # -------------------------------------------------------------------------
    # Cache & provider status utilities
    # -------------------------------------------------------------------------
    def get_available_providers(self) -> List[DataProvider]:
        """Get list of available data providers (with API keys configured)."""
        return list(self.api_keys.keys())

    def get_provider_status(self) -> Dict[str, Any]:
        """Get simple status view of all data providers."""
        status: Dict[str, Any] = {}
        for provider, api_key in self.api_keys.items():
            status[provider.value] = {
                "available": True,
                "rate_limit": api_key.rate_limit,
                "requests_this_minute": api_key.request_count,
                "last_request": api_key.last_request,
            }
        return status

    def set_cache_duration(self, seconds: int) -> None:
        """Set cache duration in seconds."""
        self.cache_duration = max(0, int(seconds))

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_duration": self.cache_duration,
            "cache_keys": list(self.cache.keys()),
        }
