"""
Market Data Facade (Phase 3).
Single entry point for market data: quotes, historical bars, overview.
Delegates to MarketDataAPIService; callers can use this instead of
instantiating or importing from multiple services (Alpaca, Alpha Vantage,
Finnhub, etc.) directly.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Lazy singleton
_market_data_service: Optional[Any] = None


def get_market_data_service():
    """Return the shared MarketDataAPIService instance (lazy-created)."""
    global _market_data_service
    if _market_data_service is None:
        from core.market_data_api_service import MarketDataAPIService
        _market_data_service = MarketDataAPIService()
    return _market_data_service


class MarketDataManager:
    """
    Facade for market data access. Use get_market_data_manager() to obtain
    the shared instance, then call async methods (get_stock_quote,
    get_historical_data, etc.) from async code. For sync callers use
    run_async() or asyncio.run().
    """

    def __init__(self):
        self._service = get_market_data_service()

    async def get_stock_quote(
        self,
        symbol: str,
        provider: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """Real-time quote for a symbol. Uses cached/rate-limited API."""
        return await self._service.get_stock_quote(symbol, provider=provider)

    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        provider: Optional[Any] = None,
    ) -> Optional[Any]:
        """Historical OHLCV (DataFrame or None)."""
        return await self._service.get_historical_data(
            symbol, period=period, provider=provider
        )

    async def get_market_overview(self) -> Optional[Dict[str, Any]]:
        """Market-wide overview if available from configured providers."""
        return await self._service.get_market_overview()

    async def get_economic_indicators(self) -> Optional[Dict[str, Any]]:
        """Economic indicators / calendar if available."""
        return await self._service.get_economic_indicators()

    def get_available_providers(self) -> List[str]:
        """Names of configured providers (no async)."""
        return [p.value for p in self._service.get_available_providers()]

    def clear_cache(self) -> None:
        """Clear in-memory cache (no async)."""
        self._service.clear_cache()


_manager_instance: Optional[MarketDataManager] = None


def get_market_data_manager() -> MarketDataManager:
    """Return the shared MarketDataManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MarketDataManager()
    return _manager_instance


def run_async(coro):
    """
    Run an async coroutine from sync code (e.g. Django view or GraphQL resolver).
    Prefer using async views/resolvers where possible to avoid blocking.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context; create task or use nest_asyncio
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
