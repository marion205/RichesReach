from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class Quote:
    price: Decimal
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    ts: datetime
    source: str

MAX_AGE = timedelta(seconds=3)

def _is_fresh(ts: datetime) -> bool:
    """Check if timestamp is within MAX_AGE"""
    if not ts: 
        return False
    now = datetime.now(timezone.utc)
    if not ts.tzinfo:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now - ts) <= MAX_AGE

def _norm(d: dict, source: str) -> Optional[Quote]:
    """Normalize provider response to Quote object"""
    if not d: 
        return None
    
    # Handle timestamp
    ts = d.get("ts") or d.get("timestamp") or d.get("created_at")
    if isinstance(ts, (int, float)):  # epoch seconds
        ts = datetime.fromtimestamp(ts, tz=timezone.utc)
    elif isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)
    
    # Handle price
    price = d.get("price") or d.get("last") or d.get("mid") or d.get("price_usd")
    if price is None: 
        return None
    
    try:
        q = Quote(
            price=Decimal(str(price)),
            bid=Decimal(str(d["bid"])) if d.get("bid") is not None else None,
            ask=Decimal(str(d["ask"])) if d.get("ask") is not None else None,
            ts=ts,
            source=source,
        )
        return q if _is_fresh(q.ts) else None
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to normalize quote from {source}: {e}")
        return None

def get_fresh_crypto_quote(symbol: str) -> Quote:
    """
    Get fresh crypto quote with fallback chain:
    Broker -> Finnhub -> Polygon -> Alpha Vantage -> Database
    """
    sym = symbol.upper().strip()
    
    # 1) Try Finnhub first (most reliable for crypto)
    try:
        from .market_data_service import MarketDataService
        service = MarketDataService()
        fh_data = service.get_crypto_price(sym)
        if fh_data:
            quote = _norm(fh_data, "finnhub")
            if quote:
                logger.info(f"Got fresh quote from Finnhub: {sym} = ${quote.price}")
                return quote
    except Exception as e:
        logger.warning(f"Finnhub quote failed for {sym}: {e}")
    
    # 2) Try Polygon
    try:
        from .market_data_service import MarketDataService
        service = MarketDataService()
        pg_data = service.get_crypto_price(sym, provider="polygon")
        if pg_data:
            quote = _norm(pg_data, "polygon")
            if quote:
                logger.info(f"Got fresh quote from Polygon: {sym} = ${quote.price}")
                return quote
    except Exception as e:
        logger.warning(f"Polygon quote failed for {sym}: {e}")
    
    # 3) Try Alpha Vantage
    try:
        from .market_data_service import MarketDataService
        service = MarketDataService()
        av_data = service.get_crypto_price(sym, provider="alpha_vantage")
        if av_data:
            quote = _norm(av_data, "alpha_vantage")
            if quote:
                logger.info(f"Got fresh quote from Alpha Vantage: {sym} = ${quote.price}")
                return quote
    except Exception as e:
        logger.warning(f"Alpha Vantage quote failed for {sym}: {e}")
    
    # 4) Fallback to database (last resort)
    try:
        from .models import CryptoPrice, Cryptocurrency
        crypto = Cryptocurrency.objects.filter(symbol=sym, is_active=True).first()
        if crypto:
            price_obj = CryptoPrice.objects.filter(cryptocurrency=crypto).order_by('-created_at').first()
            if price_obj:
                quote = Quote(
                    price=price_obj.price_usd,
                    bid=None,
                    ask=None,
                    ts=price_obj.created_at,
                    source="database"
                )
                if _is_fresh(quote.ts):
                    logger.info(f"Got fresh quote from database: {sym} = ${quote.price}")
                    return quote
                else:
                    logger.warning(f"Database quote for {sym} is stale: {quote.ts}")
    except Exception as e:
        logger.warning(f"Database quote failed for {sym}: {e}")
    
    raise RuntimeError(f"No fresh crypto quote available for {sym}")

def get_quote_with_fallback(symbol: str, max_age_seconds: int = 30) -> Quote:
    """
    Get quote with relaxed freshness requirements for display purposes
    """
    global MAX_AGE
    original_max_age = MAX_AGE
    MAX_AGE = timedelta(seconds=max_age_seconds)
    
    try:
        return get_fresh_crypto_quote(symbol)
    finally:
        MAX_AGE = original_max_age
