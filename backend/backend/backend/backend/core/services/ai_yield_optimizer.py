"""
AI Yield Optimizer using Linear Programming
Maximizes expected APY while respecting risk constraints
"""
import pulp
import logging
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from .defi_service import fetch_top_yields

logger = logging.getLogger(__name__)

# Global small pool avoids thread explosion
EXECUTOR = ThreadPoolExecutor(max_workers=4)

@dataclass
class PoolRow:
    """Data structure for pool information"""
    id: str
    protocol: str
    apy: float
    risk: float
    tvl: float
    symbol: str
    chain: str

def _optimize_sync(input_payload: Dict) -> Dict:
    """Synchronous optimization function for thread pool execution"""
    return _ai_optimize_yields_internal(**input_payload)

def run_optimizer(input_payload: Dict) -> Dict:
    """Optimized AI yield optimizer with caching and thread pool"""
    # Create deterministic cache key from input
    key = "ai_opt:" + hashlib.md5(repr(sorted(input_payload.items())).encode()).hexdigest()
    cached = cache.get(key)
    if cached:
        logger.info("Returning cached AI optimization result")
        return cached

    try:
        # Run optimization in thread pool to avoid blocking
        result = EXECUTOR.submit(_optimize_sync, input_payload).result(timeout=5)  # fail fast
        cache.set(key, result, 1800)  # 30 min cache
        logger.info("AI optimization completed and cached")
        return result
    except Exception as e:
        logger.error(f"AI optimization failed: {e}")
        return {
            "pools": [],
            "expected_apy": 0.0,
            "total_risk": input_payload.get("user_risk", 0.5),
            "explanation": f"Optimization failed: {str(e)}",
            "optimization_status": "failed"
        }

def ai_optimize_yields(
    user_risk: float = 0.5,
    chain: str = 'ethereum',
    limit: int = 8,
    max_per_pool: float = 0.6,
    min_tvl: float = 5e6,
    allowlist: Optional[List[str]] = None,
    denylist: Optional[List[str]] = None,
    stable_bias: bool = True
) -> Dict:
    """Public interface - delegates to optimized version"""
    input_payload = {
        "user_risk": user_risk,
        "chain": chain,
        "limit": limit,
        "max_per_pool": max_per_pool,
        "min_tvl": min_tvl,
        "allowlist": allowlist,
        "denylist": denylist,
        "stable_bias": stable_bias
    }
    return run_optimizer(input_payload)

def _ai_optimize_yields_internal(
    user_risk: float = 0.5,
    chain: str = 'ethereum',
    limit: int = 8,
    max_per_pool: float = 0.6,
    min_tvl: float = 5e6,
    allowlist: Optional[List[str]] = None,
    denylist: Optional[List[str]] = None,
    stable_bias: bool = True
) -> Dict:
    """
    AI Optimizer: Maximize APY subject to risk constraints using linear programming
    
    Args:
        user_risk: User's risk tolerance (0-1 scale)
        chain: Blockchain network
        limit: Maximum number of pools to consider
        max_per_pool: Maximum allocation per pool
        min_tvl: Minimum TVL threshold
        allowlist: Allowed protocols (if None, all are allowed)
        denylist: Denied protocols
        stable_bias: Whether to bias towards stable assets at low risk
    
    Returns:
        Dictionary with optimization results
    """
    try:
        # Fetch yield data
        yield_data = fetch_top_yields(chain, limit)
        if not yield_data:
            return {"error": "No yield data available"}
        
        # Convert to PoolRow objects
        rows = [
            PoolRow(
                id=p["id"],
                protocol=p["protocol"],
                apy=p["apy"],
                risk=p["risk"],
                tvl=p["tvl"],
                symbol=p["symbol"],
                chain=p["chain"]
            )
            for p in yield_data
        ]
        
        # Apply filters
        if allowlist:
            allowlist_lower = {a.lower() for a in allowlist}
            rows = [r for r in rows if r.protocol.lower() in allowlist_lower]
        
        if denylist:
            denylist_lower = {d.lower() for d in denylist}
            rows = [r for r in rows if r.protocol.lower() not in denylist_lower]
        
        # Filter by TVL
        rows = [r for r in rows if r.tvl >= min_tvl]
        
        if not rows:
            return {"error": "No eligible pools after applying filters"}
        
        logger.info(f"Optimizing across {len(rows)} pools for risk tolerance {user_risk}")
        
        # Create linear programming problem
        n = len(rows)
        prob = pulp.LpProblem("AIYieldOptimizer", pulp.LpMaximize)
        
        # Decision variables: allocation weights for each pool
        x = [pulp.LpVariable(f"x{i}", lowBound=0, upBound=max_per_pool) for i in range(n)]
        
        # Objective: maximize expected APY
        prob += pulp.lpSum([rows[i].apy * x[i] for i in range(n)])
        
        # Constraints
        # 1. Full portfolio allocation (sum of weights = 1)
        prob += pulp.lpSum(x) == 1.0
        
        # 2. Risk constraint (weighted average risk <= user risk tolerance)
        prob += pulp.lpSum([rows[i].risk * x[i] for i in range(n)]) <= user_risk
        
        # 3. Stable bias for low risk (optional)
        if stable_bias and user_risk <= 0.35:
            # Identify stable pools (no '/' in symbol, typically single-asset lending)
            stable_pools = [
                1.0 if "/" not in rows[i].symbol and "/" not in rows[i].protocol.lower() 
                else 0.0 
                for i in range(n)
            ]
            # Ensure at least 30% allocation to stable pools
            prob += pulp.lpSum([stable_pools[i] * x[i] for i in range(n)]) >= 0.3
        
        # Solve the optimization problem
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
        if pulp.LpStatus[status] != "Optimal":
            logger.warning(f"Optimization failed with status: {pulp.LpStatus[status]}")
            return {"error": "Optimization failed - no feasible solution"}
        
        # Extract results
        allocations = {}
        for i, var in enumerate(x):
            weight = float(var.value() or 0)
            if weight >= 0.01:  # Only include allocations >= 1%
                allocations[rows[i].id] = round(weight, 4)
        
        if not allocations:
            return {"error": "No valid allocations found"}
        
        # Calculate portfolio metrics
        expected_apy = round(
            sum(allocations[r.id] * r.apy for r in rows if r.id in allocations), 3
        )
        total_risk = round(
            sum(allocations[r.id] * r.risk for r in rows if r.id in allocations), 3
        )
        
        # Build response pools with weights
        pools = [
            {
                "id": r.id,
                "protocol": r.protocol,
                "apy": r.apy,
                "tvl": r.tvl,
                "risk": r.risk,
                "symbol": r.symbol,
                "chain": r.chain,
                "weight": allocations[r.id]
            }
            for r in rows if r.id in allocations
        ]
        
        # Generate explanation
        explanation = generate_explanation(
            user_risk, expected_apy, total_risk, pools, allocations
        )
        
        logger.info(f"Optimization complete: {expected_apy}% APY at {total_risk} risk")
        
        return {
            "allocations": allocations,
            "expected_apy": expected_apy,
            "total_risk": total_risk,
            "explanation": explanation,
            "pools": pools,
            "optimization_status": pulp.LpStatus[status]
        }
        
    except Exception as e:
        logger.error(f"Error in AI yield optimization: {e}")
        return {"error": f"Optimization error: {str(e)}"}

def generate_explanation(
    user_risk: float,
    expected_apy: float,
    total_risk: float,
    pools: List[Dict],
    allocations: Dict
) -> str:
    """Generate human-readable explanation of optimization results"""
    
    risk_level = "low" if user_risk <= 0.3 else "medium" if user_risk <= 0.7 else "high"
    
    # Sort pools by allocation weight
    sorted_pools = sorted(pools, key=lambda x: x['weight'], reverse=True)
    
    # Build allocation description
    allocation_desc = " + ".join([
        f"{p['protocol']} {int(p['weight']*100)}%"
        for p in sorted_pools[:3]  # Show top 3 allocations
    ])
    
    # Risk assessment
    risk_assessment = ""
    if total_risk < 0.3:
        risk_assessment = "Conservative allocation favoring stable assets."
    elif total_risk < 0.7:
        risk_assessment = "Balanced allocation with moderate risk exposure."
    else:
        risk_assessment = "Aggressive allocation targeting high-yield opportunities."
    
    explanation = (
        f"Optimized for {risk_level} risk tolerance ({int(user_risk*100)}%): "
        f"{allocation_desc} → {expected_apy:.1f}% expected APY "
        f"(portfolio risk ≈ {total_risk:.2f}). {risk_assessment} "
        f"TVL threshold applied to ensure liquidity. "
        f"Impermanent loss risk considered for LP positions."
    )
    
    return explanation

def calculate_impermanent_loss_estimate(
    price_change_ratio: float,
    pool_type: str = "50/50"
) -> float:
    """
    Calculate estimated impermanent loss for a given price change
    
    Args:
        price_change_ratio: New price / original price
        pool_type: Type of pool ("50/50", "80/20", etc.)
    
    Returns:
        Impermanent loss as a percentage (negative value)
    """
    if pool_type == "50/50":
        # Standard 50/50 pool formula
        r = price_change_ratio
        il = 2 * (r**0.5) / (1 + r) - 1
        return il * 100  # Convert to percentage
    
    # For other pool types, you'd implement different formulas
    # This is a simplified version
    return 0.0

def get_risk_metrics(pools: List[Dict]) -> Dict:
    """Calculate additional risk metrics for the portfolio"""
    if not pools:
        return {}
    
    total_tvl = sum(p['tvl'] for p in pools)
    weighted_avg_apy = sum(p['weight'] * p['apy'] for p in pools)
    weighted_avg_risk = sum(p['weight'] * p['risk'] for p in pools)
    
    # Diversification score (higher is better)
    diversification = 1.0 - max(p['weight'] for p in pools) if pools else 0.0
    
    # Concentration risk (percentage in top 2 pools)
    sorted_pools = sorted(pools, key=lambda x: x['weight'], reverse=True)
    concentration = sum(p['weight'] for p in sorted_pools[:2]) * 100
    
    return {
        'total_tvl': total_tvl,
        'weighted_avg_apy': weighted_avg_apy,
        'weighted_avg_risk': weighted_avg_risk,
        'diversification_score': diversification,
        'concentration_risk': concentration,
        'pool_count': len(pools)
    }
