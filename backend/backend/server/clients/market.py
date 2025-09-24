# clients/market.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from aiolimiter import AsyncLimiter
from settings import settings
from cache import get_json, set_json, stamp

_finnhub_limiter = AsyncLimiter(settings.FINNHUB_RPS, time_period=1)
_alpha_limiter = AsyncLimiter(settings.ALPHA_RPS, time_period=1)

class MarketClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT_S, follow_redirects=True
        )

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential_jitter(initial=settings.BACKOFF_BASE_S))
    async def _get(self, url: str, params: dict, limiter: AsyncLimiter):
        async with limiter:
            res = await self.client.get(url, params=params)
            res.raise_for_status()
            return res.json()

    async def finnhub_quote(self, symbol: str):
        cache_key = f"quote:{symbol}"
        cached = await get_json(cache_key)
        if cached:
            return cached
        data = await self._get(
            f"{settings.FINNHUB_BASE}/quote",
            {"symbol": symbol, "token": settings.FINNHUB_KEY},
            _finnhub_limiter,
        )
        payload = stamp({"c": data.get("c"), "dp": data.get("dp")}, "finnhub.quote")
        await set_json(cache_key, payload, ttl_s=15)  # 15s freshness
        return await get_json(cache_key)

    async def finnhub_profile2(self, symbol: str):
        cache_key = f"profile:{symbol}"
        cached = await get_json(cache_key)
        if cached: return cached
        data = await self._get(
            f"{settings.FINNHUB_BASE}/stock/profile2",
            {"symbol": symbol, "token": settings.FINNHUB_KEY},
            _finnhub_limiter,
        )
        payload = stamp(data, "finnhub.profile2")
        await set_json(cache_key, payload, ttl_s=3600)
        return await get_json(cache_key)

market = MarketClient()
