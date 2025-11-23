"""
Futures API - Real market data for futures recommendations
Uses multiple providers (Polygon, Finnhub, Alpaca) with fallback strategy
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
import logging
import os
import requests
import aiohttp
import asyncio
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

# Try to import MarketDataAPIService for provider management
try:
    from .market_data_api_service import MarketDataAPIService, DataProvider
    MARKET_DATA_SERVICE_AVAILABLE = True
except ImportError:
    MARKET_DATA_SERVICE_AVAILABLE = False
    logger.warning("MarketDataAPIService not available, using direct API calls")

router = APIRouter(prefix="/api/futures", tags=["futures"])

# ============================================================================
# Response Models
# ============================================================================

class FuturesRecommendation(BaseModel):
    symbol: str
    name: str
    why_now: str
    max_loss: float
    max_gain: float
    probability: int
    action: str  # 'Buy' or 'Sell'

class FuturesRecommendationsResponse(BaseModel):
    recommendations: List[FuturesRecommendation]

class FuturesOrderRequest(BaseModel):
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    order_type: Optional[str] = 'MARKET'
    limit_price: Optional[float] = None

class FuturesOrderResponse(BaseModel):
    order_id: str
    status: str
    message: Optional[str] = None
    why_not: Optional[Dict[str, Any]] = None
    client_order_id: Optional[str] = None

class FuturesPosition(BaseModel):
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float

class FuturesPositionsResponse(BaseModel):
    positions: List[FuturesPosition]
    account_balance: Optional[float] = None
    total_pnl: Optional[float] = None

# ============================================================================
# Futures Contract Specifications
# ============================================================================

FUTURES_CONTRACTS = {
    'MES': {  # Micro E-mini S&P 500
        'name': 'Micro E-mini S&P 500',
        'tick_size': 0.25,
        'tick_value': 1.25,  # $1.25 per 0.25 point
        'contract_size': 5,  # $5 per point
        'margin_requirement': 1200,  # Approximate
    },
    'MNQ': {  # Micro E-mini NASDAQ-100
        'name': 'Micro E-mini NASDAQ-100',
        'tick_size': 0.25,
        'tick_value': 0.50,  # $0.50 per 0.25 point
        'contract_size': 2,  # $2 per point
        'margin_requirement': 1200,
    },
    'M6E': {  # Micro Euro FX
        'name': 'Micro Euro FX',
        'tick_size': 0.0001,
        'tick_value': 1.25,  # $1.25 per 0.0001
        'contract_size': 12500,  # €12,500
        'margin_requirement': 500,
    },
    'MGC': {  # Micro Gold
        'name': 'Micro Gold',
        'tick_size': 0.10,
        'tick_value': 1.0,  # $1 per 0.10
        'contract_size': 10,  # 10 oz
        'margin_requirement': 1000,
    },
    'MYM': {  # Micro E-mini Dow
        'name': 'Micro E-mini Dow',
        'tick_size': 1.0,
        'tick_value': 0.50,  # $0.50 per point
        'contract_size': 0.50,
        'margin_requirement': 1200,
    },
    'M2K': {  # Micro E-mini Russell 2000
        'name': 'Micro E-mini Russell 2000',
        'tick_size': 0.10,
        'tick_value': 0.50,  # $0.50 per 0.10
        'contract_size': 5,
        'margin_requirement': 1200,
    },
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_contract_spec(symbol: str) -> Optional[Dict[str, Any]]:
    """Extract contract root from symbol (e.g., 'MESZ5' -> 'MES')"""
    # Remove month/year codes (Z5 = December 2025)
    for root in FUTURES_CONTRACTS.keys():
        if symbol.startswith(root):
            return FUTURES_CONTRACTS[root]
    return None

def calculate_risk_reward(
    current_price: float,
    contract_spec: Dict[str, Any],
    volatility: float,
    direction: str  # 'up' or 'down'
) -> Tuple[float, float, int]:
    """
    Calculate max_loss, max_gain, and probability based on market data.
    
    Returns:
        (max_loss, max_gain, probability)
    """
    margin = contract_spec.get('margin_requirement', 1000)
    tick_value = contract_spec.get('tick_value', 1.0)
    contract_size = contract_spec.get('contract_size', 1.0)
    
    # Calculate stop loss and take profit based on volatility
    # Use 2x ATR (Average True Range) equivalent for stop, 3x for target
    stop_distance = volatility * 2.0  # 2 standard deviations
    target_distance = volatility * 3.0  # 3 standard deviations
    
    # Convert price movement to dollar amounts
    if direction == 'up':
        max_loss = abs(stop_distance) * contract_size  # Stop loss below
        max_gain = abs(target_distance) * contract_size  # Target above
    else:
        max_loss = abs(stop_distance) * contract_size  # Stop loss above
        max_gain = abs(target_distance) * contract_size  # Target below
    
    # Cap losses at margin requirement (risk management)
    max_loss = min(max_loss, margin * 0.8)  # Max 80% of margin
    
    # Calculate probability based on volatility and trend strength
    # Lower volatility = higher probability
    # Strong trend = higher probability
    base_probability = 50
    volatility_factor = max(0, 30 - (volatility * 10))  # Lower vol = higher prob
    trend_factor = 20  # Assume moderate trend
    
    probability = int(base_probability + volatility_factor + trend_factor)
    probability = max(60, min(85, probability))  # Clamp between 60-85%
    
    return max_loss, max_gain, probability

def generate_why_now(
    symbol: str,
    contract_name: str,
    current_price: float,
    price_change: float,
    price_change_pct: float,
    volatility: float
) -> str:
    """Generate a 'why_now' explanation based on market conditions"""
    
    # Determine market sentiment
    if price_change_pct > 0.5:
        sentiment = "strong upward momentum"
        trend = "bullish"
    elif price_change_pct > 0:
        sentiment = "positive momentum"
        trend = "bullish"
    elif price_change_pct < -0.5:
        sentiment = "downward pressure"
        trend = "bearish"
    else:
        sentiment = "consolidation"
        trend = "neutral"
    
    # Volatility assessment
    if volatility > 2.0:
        vol_desc = "elevated volatility"
    elif volatility < 0.5:
        vol_desc = "low volatility"
    else:
        vol_desc = "moderate volatility"
    
    # Generate context-specific explanations
    if 'S&P 500' in contract_name or 'SPX' in symbol:
        if trend == "bullish":
            return f"Strong earnings season momentum and positive macro indicators suggest continued upward trend. {vol_desc.capitalize()} provides entry opportunities."
        else:
            return f"Market showing {sentiment}. {vol_desc.capitalize()} may present reversal opportunities for contrarian traders."
    
    elif 'NASDAQ' in contract_name or 'NQ' in symbol:
        if trend == "bullish":
            return f"Tech sector showing resilience with AI-driven growth. Support level holding strong. {vol_desc.capitalize()} creates favorable risk/reward."
        else:
            return f"Tech sector experiencing {sentiment}. {vol_desc.capitalize()} suggests potential for mean reversion."
    
    elif 'Euro' in contract_name or 'EUR' in symbol:
        return f"ECB policy pivot expected. Dollar strength may be reaching peak. {vol_desc.capitalize()} indicates potential for directional moves."
    
    elif 'Gold' in contract_name or 'GC' in symbol:
        return f"Inflation concerns and geopolitical tensions supporting safe-haven demand. {vol_desc.capitalize()} provides trading opportunities."
    
    else:
        # Generic explanation
        return f"Market showing {sentiment} with {vol_desc}. Current price action suggests favorable risk/reward setup."

# ============================================================================
# Multi-Provider API Integration (Polygon -> Finnhub -> Alpaca)
# ============================================================================

async def fetch_futures_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current price and market data for a futures contract.
    Tries multiple providers: Polygon -> Finnhub -> Alpaca
    """
    # Try Polygon first (best for futures)
    price_data = await _fetch_price_from_polygon(symbol)
    if price_data:
        logger.debug(f"Got price for {symbol} from Polygon")
        return price_data
    
    # Try Finnhub as fallback
    price_data = await _fetch_price_from_finnhub(symbol)
    if price_data:
        logger.debug(f"Got price for {symbol} from Finnhub")
        return price_data
    
    # Try Alpaca as last resort (may not have futures)
    price_data = await _fetch_price_from_alpaca(symbol)
    if price_data:
        logger.debug(f"Got price for {symbol} from Alpaca")
        return price_data
    
    logger.warning(f"Could not fetch price for {symbol} from any provider")
    return None

async def _fetch_price_from_polygon(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch futures price from Polygon API"""
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        return None
    
    try:
        # Try aggregates endpoint first (most reliable)
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {'adjusted': 'true', 'apiKey': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if results and len(results) > 0:
                        result = results[0]
                        price = float(result.get('c', 0))  # Close price
                        if price > 0:
                            return {
                                'price': price,
                                'timestamp': result.get('t', 0),
                                'volume': result.get('v', 0),
                                'high': float(result.get('h', price)),
                                'low': float(result.get('l', price)),
                                'provider': 'polygon'
                            }
        
        # Fallback: try last trade endpoint
        url = f"https://api.polygon.io/v2/last/trade/{symbol}"
        params = {'apiKey': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('results', {})
                    if result:
                        price = float(result.get('p', 0))
                        if price > 0:
                            return {
                                'price': price,
                                'timestamp': result.get('t', 0),
                                'provider': 'polygon'
                            }
        
        return None
    
    except asyncio.TimeoutError:
        logger.debug(f"Polygon timeout for {symbol}")
        return None
    except Exception as e:
        logger.debug(f"Polygon error for {symbol}: {e}")
        return None

async def _fetch_price_from_finnhub(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch futures price from Finnhub API"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        return None
    
    try:
        # Finnhub quote endpoint
        url = "https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data.get('c', 0)  # Current price
                    if price and price > 0:
                        return {
                            'price': float(price),
                            'timestamp': int(datetime.now().timestamp() * 1000),
                            'high': float(data.get('h', price)),
                            'low': float(data.get('l', price)),
                            'open': float(data.get('o', price)),
                            'provider': 'finnhub'
                        }
        
        return None
    
    except asyncio.TimeoutError:
        logger.debug(f"Finnhub timeout for {symbol}")
        return None
    except Exception as e:
        logger.debug(f"Finnhub error for {symbol}: {e}")
        return None

async def _fetch_price_from_alpaca(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch price from Alpaca API (may not support all futures)"""
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    if not api_key or not api_secret:
        return None
    
    try:
        # Alpaca latest bar endpoint
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars/latest"
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    bar = data.get('bar', {})
                    if bar:
                        price = float(bar.get('c', 0))  # Close price
                        if price > 0:
                            return {
                                'price': price,
                                'timestamp': bar.get('t', 0),
                                'volume': bar.get('v', 0),
                                'high': float(bar.get('h', price)),
                                'low': float(bar.get('l', price)),
                                'open': float(bar.get('o', price)),
                                'provider': 'alpaca'
                            }
        
        return None
    
    except asyncio.TimeoutError:
        logger.debug(f"Alpaca timeout for {symbol}")
        return None
    except Exception as e:
        logger.debug(f"Alpaca error for {symbol}: {e}")
        return None

async def fetch_futures_historical(symbol: str, days: int = 20) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch historical data to calculate volatility.
    Tries multiple providers: Polygon -> Finnhub -> Alpaca
    """
    # Try Polygon first
    historical = await _fetch_historical_from_polygon(symbol, days)
    if historical:
        return historical
    
    # Try Finnhub
    historical = await _fetch_historical_from_finnhub(symbol, days)
    if historical:
        return historical
    
    # Try Alpaca
    historical = await _fetch_historical_from_alpaca(symbol, days)
    if historical:
        return historical
    
    return None

async def _fetch_historical_from_polygon(symbol: str, days: int) -> Optional[List[Dict[str, Any]]]:
    """Fetch historical data from Polygon"""
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        return None
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': days,
            'apiKey': api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    return results
        
        return None
    
    except Exception as e:
        logger.debug(f"Polygon historical error for {symbol}: {e}")
        return None

async def _fetch_historical_from_finnhub(symbol: str, days: int) -> Optional[List[Dict[str, Any]]]:
    """Fetch historical data from Finnhub"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        return None
    
    try:
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            'symbol': symbol,
            'resolution': 'D',
            'from': start_timestamp,
            'to': end_timestamp,
            'token': api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('s') == 'ok':
                        # Convert Finnhub format to Polygon-like format
                        results = []
                        for i in range(len(data.get('c', []))):
                            results.append({
                                'c': data['c'][i],  # close
                                'h': data['h'][i],  # high
                                'l': data['l'][i],  # low
                                'o': data['o'][i],  # open
                                'v': data['v'][i],  # volume
                                't': data['t'][i] * 1000,  # timestamp (convert to ms)
                            })
                        return results
        
        return None
    
    except Exception as e:
        logger.debug(f"Finnhub historical error for {symbol}: {e}")
        return None

async def _fetch_historical_from_alpaca(symbol: str, days: int) -> Optional[List[Dict[str, Any]]]:
    """Fetch historical data from Alpaca"""
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    if not api_key or not api_secret:
        return None
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
        params = {
            'timeframe': '1Day',
            'start': start_time.strftime('%Y-%m-%dT%H:%M:%S-05:00'),
            'end': end_time.strftime('%Y-%m-%dT%H:%M:%S-05:00'),
            'limit': days
        }
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    bars = data.get('bars', [])
                    if bars:
                        # Convert Alpaca format to Polygon-like format
                        results = []
                        for bar in bars:
                            results.append({
                                'c': bar.get('c', 0),  # close
                                'h': bar.get('h', 0),  # high
                                'l': bar.get('l', 0),  # low
                                'o': bar.get('o', 0),  # open
                                'v': bar.get('v', 0),  # volume
                                't': int(bar.get('t', 0) / 1000000) if bar.get('t') else 0,  # timestamp
                            })
                        return results
        
        return None
    
    except Exception as e:
        logger.debug(f"Alpaca historical error for {symbol}: {e}")
        return None

def calculate_volatility(historical_data: List[Dict[str, Any]]) -> float:
    """Calculate volatility from historical price data"""
    if not historical_data or len(historical_data) < 2:
        return 1.0  # Default volatility
    
    try:
        prices = [float(bar.get('c', 0)) for bar in historical_data if bar.get('c')]
        if len(prices) < 2:
            return 1.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if not returns:
            return 1.0
        
        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        # Annualize (assuming 252 trading days)
        annualized_vol = std_dev * math.sqrt(252)
        
        # Return as percentage
        return annualized_vol * 100
    
    except Exception as e:
        logger.error(f"Error calculating volatility: {e}")
        return 1.0

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/recommendations", response_model=FuturesRecommendationsResponse)
async def get_futures_recommendations():
    """
    Get futures trading recommendations using real market data from Polygon.
    """
    logger.info("Fetching futures recommendations with real market data")
    
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        logger.warning("POLYGON_API_KEY not set, returning empty recommendations")
        return FuturesRecommendationsResponse(recommendations=[])
    
    recommendations = []
    
    # Focus on micro contracts (lower risk, beginner-friendly)
    priority_contracts = ['MES', 'MNQ', 'M6E', 'MGC', 'MYM', 'M2K']
    
    # Generate month codes (current and next month)
    now = datetime.now()
    month_codes = ['H', 'M', 'U', 'Z']  # March, June, September, December
    current_month_idx = (now.month - 1) // 3
    year_code = str(now.year % 10)  # Last digit of year
    
    for contract_root in priority_contracts:
        contract_spec = FUTURES_CONTRACTS.get(contract_root)
        if not contract_spec:
            continue
        
        # Try current and next quarterly contract
        for month_idx in [current_month_idx, (current_month_idx + 1) % 4]:
            month_code = month_codes[month_idx]
            symbol = f"{contract_root}{month_code}{year_code}"
            
            # Fetch current price (tries Polygon -> Finnhub -> Alpaca)
            price_data = await fetch_futures_price(symbol)
            if not price_data or price_data.get('price', 0) == 0:
                # Try alternative symbol format
                symbol_alt = f"{contract_root}{month_code}{year_code}"
                price_data = await fetch_futures_price(symbol_alt)
                if not price_data or price_data.get('price', 0) == 0:
                    continue
            
            current_price = price_data['price']
            provider_used = price_data.get('provider', 'unknown')
            logger.debug(f"Using {provider_used} for {symbol} price: ${current_price}")
            
            # Fetch historical data for volatility (tries multiple providers)
            historical = await fetch_futures_historical(symbol, days=20)
            volatility = calculate_volatility(historical) if historical else 1.5
            
            # Calculate price change
            price_change = 0.0
            price_change_pct = 0.0
            if historical and len(historical) >= 2:
                prev_price = float(historical[-2].get('c', current_price))
                price_change = current_price - prev_price
                if prev_price > 0:
                    price_change_pct = (price_change / prev_price) * 100
            
            # Determine direction (simple trend following)
            if price_change_pct > 0.1:
                direction = 'up'
                action = 'Buy'
            elif price_change_pct < -0.1:
                direction = 'down'
                action = 'Sell'
            else:
                # Neutral/consolidation - default to buy with lower probability
                direction = 'up'
                action = 'Buy'
            
            # Calculate risk/reward
            max_loss, max_gain, probability = calculate_risk_reward(
                current_price, contract_spec, volatility, direction
            )
            
            # Generate explanation
            why_now = generate_why_now(
                symbol, contract_spec['name'], current_price,
                price_change, price_change_pct, volatility
            )
            
            recommendations.append(FuturesRecommendation(
                symbol=symbol,
                name=contract_spec['name'],
                why_now=why_now,
                max_loss=round(max_loss, 2),
                max_gain=round(max_gain, 2),
                probability=probability,
                action=action
            ))
            
            # Limit to 4-6 recommendations
            if len(recommendations) >= 6:
                break
        
        if len(recommendations) >= 6:
            break
    
    # If no real data, return empty (frontend will use mock data)
    if not recommendations:
        logger.warning("No futures recommendations generated, frontend will use mock data")
        return FuturesRecommendationsResponse(recommendations=[])
    
    logger.info(f"Generated {len(recommendations)} futures recommendations with real market data")
    return FuturesRecommendationsResponse(recommendations=recommendations)

@router.post("/order", response_model=FuturesOrderResponse)
async def place_futures_order(order: FuturesOrderRequest):
    """
    Place a futures order (simulated - returns success but doesn't execute real trades).
    In production, this would integrate with a broker API (Interactive Brokers, Alpaca, etc.)
    """
    logger.info(f"Futures order request: {order.symbol} {order.side} {order.quantity}")
    
    # Validate order
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    if order.side not in ['BUY', 'SELL']:
        raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
    
    contract_spec = get_contract_spec(order.symbol)
    if not contract_spec:
        raise HTTPException(status_code=400, detail=f"Unknown futures contract: {order.symbol}")
    
    # Simulate order placement
    # In production, this would call a broker API
    order_id = f"FUT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order.symbol}"
    
    return FuturesOrderResponse(
        order_id=order_id,
        status="submitted",
        message=f"Order submitted for {order.quantity} {order.symbol} {order.side}",
        client_order_id=order_id
    )

@router.get("/positions", response_model=FuturesPositionsResponse)
async def get_futures_positions():
    """
    Get current futures positions (simulated - returns empty in demo).
    In production, this would fetch from a broker API.
    """
    logger.info("Fetching futures positions")
    
    # In production, fetch from broker API
    return FuturesPositionsResponse(
        positions=[],
        account_balance=None,
        total_pnl=None
    )

