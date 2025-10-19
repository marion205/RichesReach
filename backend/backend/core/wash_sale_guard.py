#!/usr/bin/env python3
"""
Realtime Wash-Sale Guard - Best-in-Market Tax Optimization
Blocks or delays trades that would trigger a wash sale and proposes equivalent substitutes automatically.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .premium_models import require_premium_feature
import json
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GuardRequest:
    symbol: str
    unrealized_pnl: float
    shares_to_sell: float
    recent_buys_30d: Dict[str, float]  # symbol -> shares bought in last 30 days
    recent_sells_30d: Dict[str, float]  # symbol -> shares sold in last 30 days
    substitutes: Dict[str, List[str]] = None  # e.g., {"VOO": ["IVV","SPY"]}
    portfolio_positions: Dict[str, float] = None  # symbol -> current shares
    wash_sale_threshold: float = 0.0  # minimum loss to trigger wash sale check

@dataclass
class GuardResponse:
    allowed: bool
    reason: str
    suggested_substitutes: List[Dict[str, Any]]
    wash_sale_impact: Dict[str, Any]
    alternative_strategies: List[Dict[str, Any]]
    explanation: Dict[str, Any]

# ETF/Index fund substitutes for wash-sale avoidance
ETF_SUBSTITUTES = {
    # S&P 500 ETFs
    "VOO": ["IVV", "SPY", "SPLG"],
    "IVV": ["VOO", "SPY", "SPLG"],
    "SPY": ["VOO", "IVV", "SPLG"],
    "SPLG": ["VOO", "IVV", "SPY"],
    
    # Total Stock Market ETFs
    "VTI": ["ITOT", "SWTSX", "FZROX"],
    "ITOT": ["VTI", "SWTSX", "FZROX"],
    "SWTSX": ["VTI", "ITOT", "FZROX"],
    
    # NASDAQ ETFs
    "QQQ": ["QQQM", "ONEQ", "QQEW"],
    "QQQM": ["QQQ", "ONEQ", "QQEW"],
    "ONEQ": ["QQQ", "QQQM", "QQEW"],
    
    # International ETFs
    "VXUS": ["IXUS", "ACWX", "VEA"],
    "IXUS": ["VXUS", "ACWX", "VEA"],
    "ACWX": ["VXUS", "IXUS", "VEA"],
    
    # Bond ETFs
    "BND": ["AGG", "SCHZ", "VBMFX"],
    "AGG": ["BND", "SCHZ", "VBMFX"],
    "SCHZ": ["BND", "AGG", "VBMFX"],
    
    # REIT ETFs
    "VNQ": ["IYR", "SCHH", "RWO"],
    "IYR": ["VNQ", "SCHH", "RWO"],
    "SCHH": ["VNQ", "IYR", "RWO"],
    
    # Technology ETFs
    "XLK": ["VGT", "FTEC", "IYW"],
    "VGT": ["XLK", "FTEC", "IYW"],
    "FTEC": ["XLK", "VGT", "IYW"],
    
    # Healthcare ETFs
    "XLV": ["VHT", "FHLC", "IYH"],
    "VHT": ["XLV", "FHLC", "IYH"],
    "FHLC": ["XLV", "VHT", "IYH"],
    
    # Financial ETFs
    "XLF": ["VFH", "IYF", "KRE"],
    "VFH": ["XLF", "IYF", "KRE"],
    "IYF": ["XLF", "VFH", "KRE"],
}

@require_premium_feature('wash_sale_guard')
@login_required
@require_http_methods(["POST"])
def wash_sale_guard(request):
    """
    Realtime Wash-Sale Guard
    Checks if a trade would trigger a wash sale and suggests alternatives
    """
    try:
        data = json.loads(request.body)
        
        guard_req = GuardRequest(
            symbol=data.get('symbol', ''),
            unrealized_pnl=float(data.get('unrealized_pnl', 0)),
            shares_to_sell=float(data.get('shares_to_sell', 0)),
            recent_buys_30d=data.get('recent_buys_30d', {}),
            recent_sells_30d=data.get('recent_sells_30d', {}),
            substitutes=data.get('substitutes', {}),
            portfolio_positions=data.get('portfolio_positions', {}),
            wash_sale_threshold=float(data.get('wash_sale_threshold', 0))
        )
        
        if not guard_req.symbol:
            return JsonResponse({
                'status': 'error',
                'message': 'Symbol is required'
            }, status=400)
        
        # Run wash-sale analysis
        result = analyze_wash_sale_risk(guard_req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Wash sale guard error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def analyze_wash_sale_risk(req: GuardRequest) -> GuardResponse:
    """
    Analyze wash-sale risk and provide recommendations
    """
    # Check if selling at a loss
    is_loss = req.unrealized_pnl < req.wash_sale_threshold
    
    if not is_loss:
        return GuardResponse(
            allowed=True,
            reason="Selling at a gain - no wash-sale risk",
            suggested_substitutes=[],
            wash_sale_impact={},
            alternative_strategies=[],
            explanation={
                "type": "no_wash_sale_risk",
                "summary": "No wash-sale risk detected - selling at a gain",
                "factors": []
            }
        )
    
    # Check for recent purchases of the same security
    recent_buys = req.recent_buys_30d.get(req.symbol, 0)
    recent_sells = req.recent_sells_30d.get(req.symbol, 0)
    
    # Calculate wash-sale impact
    wash_sale_impact = calculate_wash_sale_impact(req, recent_buys, recent_sells)
    
    # Get substitute recommendations
    suggested_substitutes = get_substitute_recommendations(req)
    
    # Generate alternative strategies
    alternative_strategies = generate_alternative_strategies(req, wash_sale_impact)
    
    # Determine if trade is allowed
    if recent_buys > 0 and is_loss:
        allowed = False
        reason = f"Wash-sale rule violation: Selling {req.symbol} at a loss within 30 days of purchasing {recent_buys} shares"
    else:
        allowed = True
        reason = "No wash-sale conflict detected"
    
    # Generate explanation
    explanation = generate_wash_sale_explanation(req, wash_sale_impact, recent_buys, recent_sells)
    
    return GuardResponse(
        allowed=allowed,
        reason=reason,
        suggested_substitutes=suggested_substitutes,
        wash_sale_impact=wash_sale_impact,
        alternative_strategies=alternative_strategies,
        explanation=explanation
    )

def calculate_wash_sale_impact(req: GuardRequest, recent_buys: float, recent_sells: float) -> Dict[str, Any]:
    """
    Calculate the financial impact of a potential wash sale
    """
    # Estimate tax impact
    loss_amount = abs(req.unrealized_pnl)
    shares_affected = min(req.shares_to_sell, recent_buys)
    
    # Tax benefit that would be lost
    estimated_tax_benefit = loss_amount * 0.15  # Assume 15% long-term rate
    
    # Time to wait for wash-sale period to expire
    days_to_wait = 30  # Simplified - in reality, would calculate from last purchase date
    
    return {
        "loss_amount": loss_amount,
        "shares_affected": shares_affected,
        "estimated_tax_benefit_lost": estimated_tax_benefit,
        "days_to_wait": days_to_wait,
        "recent_buys": recent_buys,
        "recent_sells": recent_sells,
        "wash_sale_triggered": recent_buys > 0 and req.unrealized_pnl < 0
    }

def get_substitute_recommendations(req: GuardRequest) -> List[Dict[str, Any]]:
    """
    Get substitute recommendations for wash-sale avoidance
    """
    substitutes = []
    
    # Get predefined substitutes
    predefined_subs = ETF_SUBSTITUTES.get(req.symbol, [])
    
    # Add user-provided substitutes
    user_subs = req.substitutes.get(req.symbol, []) if req.substitutes else []
    
    # Combine and deduplicate
    all_subs = list(set(predefined_subs + user_subs))
    
    for sub_symbol in all_subs[:3]:  # Limit to top 3 recommendations
        # Check if user already owns this substitute
        current_position = req.portfolio_positions.get(sub_symbol, 0) if req.portfolio_positions else 0
        
        # Calculate correlation score (simplified)
        correlation_score = calculate_correlation_score(req.symbol, sub_symbol)
        
        substitutes.append({
            "symbol": sub_symbol,
            "correlation_score": correlation_score,
            "current_position": current_position,
            "recommendation": "BUY" if current_position == 0 else "HOLD",
            "reason": f"High correlation ({correlation_score:.2f}) with {req.symbol}",
            "wash_sale_safe": True
        })
    
    # Sort by correlation score (descending)
    substitutes.sort(key=lambda x: x["correlation_score"], reverse=True)
    
    return substitutes

def calculate_correlation_score(symbol1: str, symbol2: str) -> float:
    """
    Calculate correlation score between two symbols
    Simplified implementation - in production, would use real correlation data
    """
    # ETF correlation mapping (simplified)
    correlation_map = {
        # S&P 500 ETFs - very high correlation
        ("VOO", "IVV"): 0.999,
        ("VOO", "SPY"): 0.998,
        ("VOO", "SPLG"): 0.997,
        ("IVV", "SPY"): 0.999,
        ("IVV", "SPLG"): 0.998,
        ("SPY", "SPLG"): 0.997,
        
        # Total Stock Market - high correlation
        ("VTI", "ITOT"): 0.995,
        ("VTI", "SWTSX"): 0.990,
        ("VTI", "FZROX"): 0.985,
        
        # NASDAQ - high correlation
        ("QQQ", "QQQM"): 0.999,
        ("QQQ", "ONEQ"): 0.995,
        ("QQQ", "QQEW"): 0.990,
        
        # International - high correlation
        ("VXUS", "IXUS"): 0.995,
        ("VXUS", "ACWX"): 0.990,
        ("VXUS", "VEA"): 0.985,
        
        # Bond ETFs - high correlation
        ("BND", "AGG"): 0.995,
        ("BND", "SCHZ"): 0.990,
        ("BND", "VBMFX"): 0.985,
    }
    
    # Check both directions
    key1 = (symbol1, symbol2)
    key2 = (symbol2, symbol1)
    
    if key1 in correlation_map:
        return correlation_map[key1]
    elif key2 in correlation_map:
        return correlation_map[key2]
    else:
        # Default correlation for unknown pairs
        return 0.85

def generate_alternative_strategies(req: GuardRequest, wash_sale_impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate alternative strategies to avoid wash-sale issues
    """
    strategies = []
    
    if wash_sale_impact["wash_sale_triggered"]:
        # Strategy 1: Wait for wash-sale period to expire
        strategies.append({
            "strategy": "WAIT",
            "title": "Wait for Wash-Sale Period to Expire",
            "description": f"Wait {wash_sale_impact['days_to_wait']} days before selling to avoid wash-sale rule",
            "pros": ["Preserves tax benefit", "No additional complexity"],
            "cons": ["Delays rebalancing", "Market risk during wait period"],
            "estimated_impact": f"Save ${wash_sale_impact['estimated_tax_benefit_lost']:.0f} in taxes"
        })
        
        # Strategy 2: Use substitute security
        strategies.append({
            "strategy": "SUBSTITUTE",
            "title": "Use High-Correlation Substitute",
            "description": "Sell current position and buy a highly correlated substitute for 31+ days",
            "pros": ["Immediate rebalancing", "Maintains market exposure", "Preserves tax benefit"],
            "cons": ["Additional trading costs", "Tracking error risk"],
            "estimated_impact": "Maintains tax benefit while allowing immediate rebalancing"
        })
        
        # Strategy 3: Partial sale
        if wash_sale_impact["shares_affected"] < req.shares_to_sell:
            strategies.append({
                "strategy": "PARTIAL",
                "title": "Partial Sale (Non-Wash-Sale Portion)",
                "description": f"Sell only {req.shares_to_sell - wash_sale_impact['shares_affected']:.0f} shares to avoid wash-sale rule",
                "pros": ["Immediate partial rebalancing", "Avoids wash-sale rule"],
                "cons": ["Incomplete rebalancing", "Remaining position risk"],
                "estimated_impact": "Partial tax benefit preservation"
            })
    
    return strategies

def generate_wash_sale_explanation(req: GuardRequest, wash_sale_impact: Dict[str, Any], 
                                 recent_buys: float, recent_sells: float) -> Dict[str, Any]:
    """
    Generate SHAP-style explanation for wash-sale analysis
    """
    factors = []
    
    # Factor 1: Loss magnitude
    if req.unrealized_pnl < 0:
        factors.append({
            "name": "loss_magnitude",
            "weight": 0.4,
            "detail": f"Realizing ${abs(req.unrealized_pnl):,.0f} loss",
            "impact": "High" if abs(req.unrealized_pnl) > 1000 else "Medium"
        })
    
    # Factor 2: Recent purchase activity
    if recent_buys > 0:
        factors.append({
            "name": "recent_purchase",
            "weight": 0.35,
            "detail": f"Purchased {recent_buys:.0f} shares in last 30 days",
            "impact": "High"
        })
    
    # Factor 3: Wash-sale rule compliance
    factors.append({
        "name": "wash_sale_compliance",
        "weight": 0.25,
        "detail": "IRS wash-sale rule prevents claiming losses on repurchased securities",
        "impact": "High" if wash_sale_impact["wash_sale_triggered"] else "Low"
    })
    
    # Generate summary
    if wash_sale_impact["wash_sale_triggered"]:
        summary = f"Wash-sale rule violation detected. Selling {req.symbol} at a ${abs(req.unrealized_pnl):,.0f} loss "
        summary += f"within 30 days of purchasing {recent_buys:.0f} shares would trigger wash-sale rule, "
        summary += f"disallowing ${wash_sale_impact['estimated_tax_benefit_lost']:.0f} in tax benefits."
    else:
        summary = f"No wash-sale risk detected for {req.symbol}. Trade can proceed safely."
    
    return {
        "type": "wash_sale_analysis",
        "summary": summary,
        "factors": factors,
        "risk_level": "HIGH" if wash_sale_impact["wash_sale_triggered"] else "LOW",
        "recommendation": "AVOID" if wash_sale_impact["wash_sale_triggered"] else "PROCEED"
    }
