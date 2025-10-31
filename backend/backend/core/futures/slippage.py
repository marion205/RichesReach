"""
Slippage Simulation - Realistic Paper Trading
==============================================
Simulates realistic order fills with slippage based on liquidity.
"""

from typing import Dict, Optional
import random


class Quote:
    """Market quote (simplified)"""
    def __init__(self, bid: float, ask: float, volume: int = 1000):
        self.bid = bid
        self.ask = ask
        self.volume = volume
        self.spread = ask - bid


def simulate_fill(
    quote: Quote,
    side: str,
    quantity: int,
    order_type: str = "MARKET",
    limit_price: Optional[float] = None,
) -> float:
    """
    Simulate realistic order fill with slippage.
    
    Args:
        quote: Market quote (bid/ask)
        side: "BUY" or "SELL"
        quantity: Order quantity
        order_type: "MARKET" or "LIMIT"
        limit_price: Limit price if LIMIT order
        
    Returns:
        Fill price
    """
    if order_type == "LIMIT" and limit_price:
        # Limit orders: fill at limit if favorable, otherwise at mid
        if side == "BUY" and limit_price >= quote.ask:
            return limit_price
        elif side == "SELL" and limit_price <= quote.bid:
            return limit_price
        else:
            # Limit not hit, use mid
            mid = (quote.bid + quote.ask) / 2
            return round(mid, 2)
    
    # Market orders: slippage based on spread and liquidity
    spread = quote.spread
    base_slippage = 0.25 * spread  # 25% of spread baseline
    
    # Liquidity adjustment (higher volume = less slippage)
    volume_factor = min(1.0, 1000 / max(quote.volume, 1))
    slippage = base_slippage * (1 + volume_factor)
    
    # Size adjustment (larger orders = more slippage)
    size_factor = min(2.0, 1 + (quantity / 10) * 0.1)
    slippage *= size_factor
    
    # Add randomness
    slippage *= random.uniform(0.8, 1.2)
    
    if side == "BUY":
        fill_price = quote.ask + slippage
    else:  # SELL
        fill_price = quote.bid - slippage
    
    return round(fill_price, 2)


def get_quote_for_symbol(symbol: str) -> Quote:
    """
    Get simulated quote for a futures symbol.
    
    In production, this would fetch real market data.
    """
    # Simplified: base price varies by contract
    base_prices = {
        "MES": 5000.0,
        "MNQ": 18000.0,
        "MYM": 34000.0,
        "M2K": 2000.0,
    }
    
    symbol_base = symbol[:3]
    base_price = base_prices.get(symbol_base, 5000.0)
    
    # Simulate bid/ask spread (typically 1-2 points for micros)
    spread = random.uniform(0.25, 1.0)
    bid = base_price - spread / 2
    ask = base_price + spread / 2
    
    # Simulate volume
    volume = random.randint(500, 2000)
    
    return Quote(bid=bid, ask=ask, volume=volume)

