"""
DeFi Analytics Service
Impermanent loss calculations and historical performance tracking
"""
import math
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

def il_pct(price_ratio: float) -> float:
    """Constant-product IL: (2*sqrt(r)/(1+r) - 1) * 100"""
    r = max(1e-9, float(price_ratio))
    return (2*math.sqrt(r)/(1+r) - 1.0) * 100.0

def il_between(p0_a: float, p0_b: float, p1_a: float, p1_b: float) -> float:
    """Calculate IL between two price points"""
    r0 = p1_a/p0_a
    r1 = p1_b/p0_b
    return il_pct(r0/r1)

def historical_il(symbol_a: str, symbol_b: str, days=30):
    """Calculate historical IL for a token pair"""
    try:
        from core.crypto_models import CryptoPrice
        
        end = timezone.now()
        start = end - timedelta(days=days)
        
        # Get price data for both tokens
        A = list(CryptoPrice.objects.filter(
            cryptocurrency__symbol=symbol_a, 
            timestamp__range=(start, end)
        ).order_by("timestamp").values_list("price_usd", flat=True))
        
        B = list(CryptoPrice.objects.filter(
            cryptocurrency__symbol=symbol_b, 
            timestamp__range=(start, end)
        ).order_by("timestamp").values_list("price_usd", flat=True))
        
        if len(A) < 2 or len(B) < 2: 
            return []
        
        out = []
        for i in range(1, min(len(A), len(B))):
            out.append(il_between(A[i-1], B[i-1], A[i], B[i]))
        
        return out  # list of daily IL%
        
    except Exception as e:
        logger.error(f"Historical IL calculation failed for {symbol_a}/{symbol_b}: {e}")
        return []

def estimate_fee_apy(volume24h_usd: float, tvl_usd: float, fee_tier: float = 0.003) -> float:
    """Estimate fee APR for Uniswap-style pools"""
    if not tvl_usd: 
        return 0.0
    
    # Very rough annualized fee APR ignoring compounding
    daily = (volume24h_usd * fee_tier) / tvl_usd
    return min(200.0, daily * 365 * 100)

def compute_pool_analytics(pool) -> dict:
    """Compute comprehensive analytics for a pool"""
    try:
        analytics = {
            "fee_apy": 0.0,
            "il_estimate": 0.0,
            "net_apy": pool.total_apy,
            "risk_score": pool.risk_score,
        }
        
        # Calculate fee APY for Uniswap-style pools
        if pool.protocol.slug.lower() in ['uniswap', 'sushiswap']:
            # This would need volume data from subgraph or events
            analytics["fee_apy"] = estimate_fee_apy(
                volume24h_usd=pool.tvl_usd * 0.1,  # Assume 10% daily volume
                tvl_usd=float(pool.tvl_usd),
                fee_tier=0.003
            )
        
        # Calculate IL estimate for LP pools
        if '/' in pool.symbol:
            tokens = pool.symbol.split('/')
            if len(tokens) == 2:
                il_history = historical_il(tokens[0], tokens[1], days=30)
                if il_history:
                    analytics["il_estimate"] = sum(il_history) / len(il_history)
        
        # Calculate net APY (rewards - IL)
        analytics["net_apy"] = pool.total_apy - abs(analytics["il_estimate"])
        
        return analytics
        
    except Exception as e:
        logger.error(f"Pool analytics computation failed for {pool.id}: {e}")
        return None

def get_pool_performance_metrics(pool, days=30):
    """Get comprehensive performance metrics for a pool"""
    try:
        end = timezone.now()
        start = end - timedelta(days=days)
        
        # This would typically come from a time-series database
        # For now, return mock data structure
        return {
            "total_return": pool.total_apy * (days / 365),
            "volatility": pool.risk_score * 50,  # Convert to percentage
            "max_drawdown": pool.risk_score * 20,
            "sharpe_ratio": (pool.total_apy - 5) / (pool.risk_score * 50),  # Assuming 5% risk-free rate
            "il_impact": abs(historical_il(pool.token0, pool.token1, days)[-1]) if '/' in pool.symbol else 0,
        }
        
    except Exception as e:
        logger.error(f"Performance metrics calculation failed for {pool.id}: {e}")
        return None

def calculate_portfolio_metrics(positions):
    """Calculate portfolio-level metrics from individual positions"""
    try:
        if not positions:
            return None
        
        total_value = sum(float(pos.total_value_usd) for pos in positions)
        if total_value == 0:
            return None
        
        # Weighted average APY
        weighted_apy = sum(
            float(pos.realized_apy) * float(pos.total_value_usd) / total_value 
            for pos in positions
        )
        
        # Portfolio risk (simplified)
        portfolio_risk = sum(
            pos.pool.risk_score * float(pos.total_value_usd) / total_value 
            for pos in positions
        )
        
        # Diversification score (based on number of protocols)
        protocols = set(pos.pool.protocol.slug for pos in positions)
        diversification = min(1.0, len(protocols) / 5.0)  # Max score at 5 protocols
        
        return {
            "total_value_usd": total_value,
            "weighted_apy": weighted_apy,
            "portfolio_risk": portfolio_risk,
            "diversification_score": diversification,
            "active_positions": len(positions),
            "protocols_count": len(protocols),
        }
        
    except Exception as e:
        logger.error(f"Portfolio metrics calculation failed: {e}")
        return None
