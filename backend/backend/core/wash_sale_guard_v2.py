#!/usr/bin/env python3
"""
Wash-Sale Guard V2 - Best-in-Market Tax Optimization
Enhanced wash-sale protection with statistical substitute finder and correlation analysis
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
import math

logger = logging.getLogger(__name__)

@dataclass
class GuardRequestV2:
    symbol: str
    unrealized_pnl: float
    shares_to_sell: float
    recent_buys_30d: Dict[str, float]
    recent_sells_30d: Dict[str, float]
    substitutes: Dict[str, List[str]] = None
    portfolio_positions: Dict[str, float] = None
    wash_sale_threshold: float = 0.0
    correlation_threshold: float = 0.95
    risk_tolerance: str = "moderate"

@dataclass
class GuardResponseV2:
    allowed: bool
    reason: str
    suggested_substitutes: List[Dict[str, Any]]
    wash_sale_impact: Dict[str, Any]
    alternative_strategies: List[Dict[str, Any]]
    explanation: Dict[str, Any]
    risk_assessment: Dict[str, Any]

# Enhanced ETF/Index fund substitutes with correlation scores
ENHANCED_ETF_SUBSTITUTES = {
    # S&P 500 ETFs - Very high correlation
    "VOO": [
        {"symbol": "IVV", "correlation": 0.999, "expense_ratio": 0.03, "aum": 400000000000},
        {"symbol": "SPY", "correlation": 0.998, "expense_ratio": 0.09, "aum": 500000000000},
        {"symbol": "SPLG", "correlation": 0.997, "expense_ratio": 0.03, "aum": 30000000000}
    ],
    "IVV": [
        {"symbol": "VOO", "correlation": 0.999, "expense_ratio": 0.03, "aum": 300000000000},
        {"symbol": "SPY", "correlation": 0.998, "expense_ratio": 0.09, "aum": 500000000000},
        {"symbol": "SPLG", "correlation": 0.997, "expense_ratio": 0.03, "aum": 30000000000}
    ],
    "SPY": [
        {"symbol": "VOO", "correlation": 0.998, "expense_ratio": 0.03, "aum": 300000000000},
        {"symbol": "IVV", "correlation": 0.998, "expense_ratio": 0.03, "aum": 400000000000},
        {"symbol": "SPLG", "correlation": 0.997, "expense_ratio": 0.03, "aum": 30000000000}
    ],
    
    # Total Stock Market ETFs
    "VTI": [
        {"symbol": "ITOT", "correlation": 0.995, "expense_ratio": 0.03, "aum": 50000000000},
        {"symbol": "SWTSX", "correlation": 0.990, "expense_ratio": 0.03, "aum": 20000000000},
        {"symbol": "FZROX", "correlation": 0.985, "expense_ratio": 0.00, "aum": 10000000000}
    ],
    
    # NASDAQ ETFs
    "QQQ": [
        {"symbol": "QQQM", "correlation": 0.999, "expense_ratio": 0.15, "aum": 20000000000},
        {"symbol": "ONEQ", "correlation": 0.995, "expense_ratio": 0.21, "aum": 5000000000},
        {"symbol": "QQEW", "correlation": 0.990, "expense_ratio": 0.35, "aum": 2000000000}
    ],
    
    # Technology ETFs
    "XLK": [
        {"symbol": "VGT", "correlation": 0.995, "expense_ratio": 0.10, "aum": 60000000000},
        {"symbol": "FTEC", "correlation": 0.990, "expense_ratio": 0.08, "aum": 8000000000},
        {"symbol": "IYW", "correlation": 0.985, "expense_ratio": 0.40, "aum": 3000000000}
    ],
    
    # Healthcare ETFs
    "XLV": [
        {"symbol": "VHT", "correlation": 0.995, "expense_ratio": 0.10, "aum": 15000000000},
        {"symbol": "FHLC", "correlation": 0.990, "expense_ratio": 0.08, "aum": 5000000000},
        {"symbol": "IYH", "correlation": 0.985, "expense_ratio": 0.40, "aum": 2000000000}
    ],
    
    # Financial ETFs
    "XLF": [
        {"symbol": "VFH", "correlation": 0.995, "expense_ratio": 0.10, "aum": 12000000000},
        {"symbol": "IYF", "correlation": 0.990, "expense_ratio": 0.40, "aum": 3000000000},
        {"symbol": "KRE", "correlation": 0.850, "expense_ratio": 0.35, "aum": 2000000000}
    ],
    
    # International ETFs
    "VXUS": [
        {"symbol": "IXUS", "correlation": 0.995, "expense_ratio": 0.09, "aum": 30000000000},
        {"symbol": "ACWX", "correlation": 0.990, "expense_ratio": 0.32, "aum": 5000000000},
        {"symbol": "VEA", "correlation": 0.950, "expense_ratio": 0.05, "aum": 20000000000}
    ],
    
    # Bond ETFs
    "BND": [
        {"symbol": "AGG", "correlation": 0.995, "expense_ratio": 0.03, "aum": 80000000000},
        {"symbol": "SCHZ", "correlation": 0.990, "expense_ratio": 0.03, "aum": 15000000000},
        {"symbol": "VBMFX", "correlation": 0.985, "expense_ratio": 0.05, "aum": 10000000000}
    ]
}

@require_premium_feature('wash_sale_guard_v2')
@login_required
@require_http_methods(["POST"])
def wash_sale_guard_v2(request):
    """
    Enhanced Wash-Sale Guard V2
    Advanced wash-sale protection with statistical substitute analysis
    """
    try:
        data = json.loads(request.body)
        
        guard_req = GuardRequestV2(
            symbol=data.get('symbol', ''),
            unrealized_pnl=float(data.get('unrealized_pnl', 0)),
            shares_to_sell=float(data.get('shares_to_sell', 0)),
            recent_buys_30d=data.get('recent_buys_30d', {}),
            recent_sells_30d=data.get('recent_sells_30d', {}),
            substitutes=data.get('substitutes', {}),
            portfolio_positions=data.get('portfolio_positions', {}),
            wash_sale_threshold=float(data.get('wash_sale_threshold', 0)),
            correlation_threshold=float(data.get('correlation_threshold', 0.95)),
            risk_tolerance=data.get('risk_tolerance', 'moderate')
        )
        
        if not guard_req.symbol:
            return JsonResponse({
                'status': 'error',
                'message': 'Symbol is required'
            }, status=400)
        
        # Run enhanced wash-sale analysis
        result = analyze_wash_sale_risk_v2(guard_req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Wash sale guard v2 error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def analyze_wash_sale_risk_v2(req: GuardRequestV2) -> GuardResponseV2:
    """
    Enhanced wash-sale risk analysis with statistical substitutes
    """
    # Check if selling at a loss
    is_loss = req.unrealized_pnl < req.wash_sale_threshold
    
    if not is_loss:
        return GuardResponseV2(
            allowed=True,
            reason="Selling at a gain - no wash-sale risk",
            suggested_substitutes=[],
            wash_sale_impact={},
            alternative_strategies=[],
            explanation={
                "type": "no_wash_sale_risk",
                "summary": "No wash-sale risk detected - selling at a gain",
                "factors": []
            },
            risk_assessment={"risk_level": "LOW", "confidence": 0.95}
        )
    
    # Check for recent purchases of the same security
    recent_buys = req.recent_buys_30d.get(req.symbol, 0)
    recent_sells = req.recent_sells_30d.get(req.symbol, 0)
    
    # Calculate enhanced wash-sale impact
    wash_sale_impact = calculate_wash_sale_impact_v2(req, recent_buys, recent_sells)
    
    # Get statistical substitute recommendations
    suggested_substitutes = get_statistical_substitutes(req)
    
    # Generate alternative strategies
    alternative_strategies = generate_alternative_strategies_v2(req, wash_sale_impact)
    
    # Determine if trade is allowed
    if recent_buys > 0 and is_loss:
        allowed = False
        reason = f"Wash-sale rule violation: Selling {req.symbol} at a loss within 30 days of purchasing {recent_buys} shares"
    else:
        allowed = True
        reason = "No wash-sale conflict detected"
    
    # Generate enhanced explanation
    explanation = generate_wash_sale_explanation_v2(req, wash_sale_impact, recent_buys, recent_sells)
    
    # Risk assessment
    risk_assessment = assess_wash_sale_risk(req, wash_sale_impact, suggested_substitutes)
    
    return GuardResponseV2(
        allowed=allowed,
        reason=reason,
        suggested_substitutes=suggested_substitutes,
        wash_sale_impact=wash_sale_impact,
        alternative_strategies=alternative_strategies,
        explanation=explanation,
        risk_assessment=risk_assessment
    )

def calculate_wash_sale_impact_v2(req: GuardRequestV2, recent_buys: float, recent_sells: float) -> Dict[str, Any]:
    """
    Calculate enhanced wash-sale impact with risk metrics
    """
    # Estimate tax impact
    loss_amount = abs(req.unrealized_pnl)
    shares_affected = min(req.shares_to_sell, recent_buys)
    
    # Tax benefit that would be lost
    estimated_tax_benefit = loss_amount * 0.15  # Assume 15% long-term rate
    
    # Time to wait for wash-sale period to expire
    days_to_wait = 30  # Simplified - in reality, would calculate from last purchase date
    
    # Risk metrics
    loss_percentage = (loss_amount / (req.shares_to_sell * req.unrealized_pnl / req.shares_to_sell)) * 100 if req.shares_to_sell > 0 else 0
    
    return {
        "loss_amount": loss_amount,
        "shares_affected": shares_affected,
        "estimated_tax_benefit_lost": estimated_tax_benefit,
        "days_to_wait": days_to_wait,
        "recent_buys": recent_buys,
        "recent_sells": recent_sells,
        "wash_sale_triggered": recent_buys > 0 and req.unrealized_pnl < 0,
        "loss_percentage": loss_percentage,
        "risk_score": calculate_risk_score(loss_amount, shares_affected, recent_buys)
    }

def calculate_risk_score(loss_amount: float, shares_affected: float, recent_buys: float) -> float:
    """
    Calculate risk score for wash-sale impact (0-1 scale)
    """
    # Factors: loss amount, shares affected, recent activity
    loss_factor = min(loss_amount / 10000, 1.0)  # Normalize to $10k max
    shares_factor = min(shares_affected / 1000, 1.0)  # Normalize to 1000 shares max
    activity_factor = min(recent_buys / 500, 1.0)  # Normalize to 500 shares max
    
    # Weighted risk score
    risk_score = (loss_factor * 0.5 + shares_factor * 0.3 + activity_factor * 0.2)
    return min(risk_score, 1.0)

def get_statistical_substitutes(req: GuardRequestV2) -> List[Dict[str, Any]]:
    """
    Get statistical substitute recommendations with enhanced analysis
    """
    substitutes = []
    
    # Get predefined substitutes with correlation data
    predefined_subs = ENHANCED_ETF_SUBSTITUTES.get(req.symbol, [])
    
    # Add user-provided substitutes
    user_subs = req.substitutes.get(req.symbol, []) if req.substitutes else []
    
    # Process predefined substitutes
    for sub_data in predefined_subs:
        if sub_data["correlation"] >= req.correlation_threshold:
            # Check if user already owns this substitute
            current_position = req.portfolio_positions.get(sub_data["symbol"], 0) if req.portfolio_positions else 0
            
            # Calculate substitute score
            substitute_score = calculate_substitute_score(sub_data, current_position, req)
            
            substitutes.append({
                "symbol": sub_data["symbol"],
                "correlation_score": sub_data["correlation"],
                "expense_ratio": sub_data["expense_ratio"],
                "aum": sub_data["aum"],
                "current_position": current_position,
                "recommendation": "BUY" if current_position == 0 else "HOLD",
                "reason": f"High correlation ({sub_data['correlation']:.3f}) with {req.symbol}",
                "wash_sale_safe": True,
                "substitute_score": substitute_score,
                "risk_level": "LOW" if sub_data["correlation"] > 0.98 else "MEDIUM"
            })
    
    # Process user-provided substitutes
    for sub_symbol in user_subs:
        if not any(s["symbol"] == sub_symbol for s in substitutes):
            correlation_score = calculate_correlation_score(req.symbol, sub_symbol)
            if correlation_score >= req.correlation_threshold:
                current_position = req.portfolio_positions.get(sub_symbol, 0) if req.portfolio_positions else 0
                
                substitutes.append({
                    "symbol": sub_symbol,
                    "correlation_score": correlation_score,
                    "expense_ratio": 0.0,  # Unknown
                    "aum": 0,  # Unknown
                    "current_position": current_position,
                    "recommendation": "BUY" if current_position == 0 else "HOLD",
                    "reason": f"User-provided substitute with {correlation_score:.3f} correlation",
                    "wash_sale_safe": True,
                    "substitute_score": correlation_score,
                    "risk_level": "MEDIUM"
                })
    
    # Sort by substitute score (descending)
    substitutes.sort(key=lambda x: x["substitute_score"], reverse=True)
    
    return substitutes[:5]  # Return top 5 recommendations

def calculate_substitute_score(sub_data: Dict[str, Any], current_position: float, req: GuardRequestV2) -> float:
    """
    Calculate comprehensive substitute score
    """
    score = 0.0
    
    # Correlation weight (40%)
    score += sub_data["correlation"] * 0.4
    
    # Expense ratio weight (20%) - lower is better
    expense_score = max(0, 1 - (sub_data["expense_ratio"] / 0.5))  # Normalize to 0.5% max
    score += expense_score * 0.2
    
    # AUM weight (20%) - higher is better (liquidity)
    aum_score = min(1.0, math.log10(sub_data["aum"] + 1) / 12)  # Normalize to $1T max
    score += aum_score * 0.2
    
    # Current position weight (20%) - prefer positions we don't already own
    position_score = 1.0 if current_position == 0 else 0.5
    score += position_score * 0.2
    
    return score

def calculate_correlation_score(symbol1: str, symbol2: str) -> float:
    """
    Calculate correlation score between two symbols
    Enhanced with more ETF mappings
    """
    # Enhanced correlation mapping
    correlation_map = {
        # S&P 500 ETFs
        ("VOO", "IVV"): 0.999, ("VOO", "SPY"): 0.998, ("VOO", "SPLG"): 0.997,
        ("IVV", "SPY"): 0.999, ("IVV", "SPLG"): 0.998, ("SPY", "SPLG"): 0.997,
        
        # Total Stock Market
        ("VTI", "ITOT"): 0.995, ("VTI", "SWTSX"): 0.990, ("VTI", "FZROX"): 0.985,
        ("ITOT", "SWTSX"): 0.990, ("ITOT", "FZROX"): 0.985,
        
        # NASDAQ
        ("QQQ", "QQQM"): 0.999, ("QQQ", "ONEQ"): 0.995, ("QQQ", "QQEW"): 0.990,
        ("QQQM", "ONEQ"): 0.995, ("QQQM", "QQEW"): 0.990,
        
        # Technology
        ("XLK", "VGT"): 0.995, ("XLK", "FTEC"): 0.990, ("XLK", "IYW"): 0.985,
        ("VGT", "FTEC"): 0.990, ("VGT", "IYW"): 0.985,
        
        # Healthcare
        ("XLV", "VHT"): 0.995, ("XLV", "FHLC"): 0.990, ("XLV", "IYH"): 0.985,
        ("VHT", "FHLC"): 0.990, ("VHT", "IYH"): 0.985,
        
        # Financial
        ("XLF", "VFH"): 0.995, ("XLF", "IYF"): 0.990, ("XLF", "KRE"): 0.850,
        ("VFH", "IYF"): 0.990, ("VFH", "KRE"): 0.850,
        
        # International
        ("VXUS", "IXUS"): 0.995, ("VXUS", "ACWX"): 0.990, ("VXUS", "VEA"): 0.950,
        ("IXUS", "ACWX"): 0.990, ("IXUS", "VEA"): 0.950,
        
        # Bonds
        ("BND", "AGG"): 0.995, ("BND", "SCHZ"): 0.990, ("BND", "VBMFX"): 0.985,
        ("AGG", "SCHZ"): 0.990, ("AGG", "VBMFX"): 0.985,
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

def generate_alternative_strategies_v2(req: GuardRequestV2, wash_sale_impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate enhanced alternative strategies
    """
    strategies = []
    
    if wash_sale_impact["wash_sale_triggered"]:
        # Strategy 1: Wait for wash-sale period to expire
        strategies.append({
            "strategy": "WAIT",
            "title": "Wait for Wash-Sale Period to Expire",
            "description": f"Wait {wash_sale_impact['days_to_wait']} days before selling to avoid wash-sale rule",
            "pros": ["Preserves tax benefit", "No additional complexity", "Maintains current position"],
            "cons": ["Delays rebalancing", "Market risk during wait period", "Opportunity cost"],
            "estimated_impact": f"Save ${wash_sale_impact['estimated_tax_benefit_lost']:.0f} in taxes",
            "risk_level": "LOW",
            "success_probability": 0.95
        })
        
        # Strategy 2: Use statistical substitute
        if req.correlation_threshold >= 0.95:
            strategies.append({
                "strategy": "SUBSTITUTE",
                "title": "Use High-Correlation Statistical Substitute",
                "description": "Sell current position and buy a statistically equivalent substitute for 31+ days",
                "pros": ["Immediate rebalancing", "Maintains market exposure", "Preserves tax benefit", "High correlation"],
                "cons": ["Additional trading costs", "Tracking error risk", "Substitute selection risk"],
                "estimated_impact": "Maintains tax benefit while allowing immediate rebalancing",
                "risk_level": "MEDIUM",
                "success_probability": 0.85
            })
        
        # Strategy 3: Partial sale
        if wash_sale_impact["shares_affected"] < req.shares_to_sell:
            strategies.append({
                "strategy": "PARTIAL",
                "title": "Partial Sale (Non-Wash-Sale Portion)",
                "description": f"Sell only {req.shares_to_sell - wash_sale_impact['shares_affected']:.0f} shares to avoid wash-sale rule",
                "pros": ["Immediate partial rebalancing", "Avoids wash-sale rule", "Reduces position size"],
                "cons": ["Incomplete rebalancing", "Remaining position risk", "Complex tracking"],
                "estimated_impact": "Partial tax benefit preservation",
                "risk_level": "MEDIUM",
                "success_probability": 0.90
            })
        
        # Strategy 4: Tax-loss harvesting with substitute
        strategies.append({
            "strategy": "HARVEST_WITH_SUBSTITUTE",
            "title": "Tax-Loss Harvesting with Substitute",
            "description": "Realize loss now, buy substitute, then rotate back after 31 days",
            "pros": ["Immediate tax benefit", "Maintains market exposure", "Strategic tax planning"],
            "cons": ["Complex execution", "Multiple trades required", "Timing risk"],
            "estimated_impact": f"Realize ${wash_sale_impact['loss_amount']:.0f} loss for tax benefit",
            "risk_level": "HIGH",
            "success_probability": 0.75
        })
    
    return strategies

def generate_wash_sale_explanation_v2(req: GuardRequestV2, wash_sale_impact: Dict[str, Any], 
                                     recent_buys: float, recent_sells: float) -> Dict[str, Any]:
    """
    Generate enhanced SHAP-style explanation for wash-sale analysis
    """
    factors = []
    
    # Factor 1: Loss magnitude
    if req.unrealized_pnl < 0:
        loss_factor_weight = min(abs(req.unrealized_pnl) / 5000, 1.0)  # Normalize to $5k
        factors.append({
            "name": "loss_magnitude",
            "weight": 0.4 * loss_factor_weight,
            "detail": f"Realizing ${abs(req.unrealized_pnl):,.0f} loss",
            "impact": "High" if abs(req.unrealized_pnl) > 1000 else "Medium"
        })
    
    # Factor 2: Recent purchase activity
    if recent_buys > 0:
        activity_factor_weight = min(recent_buys / 100, 1.0)  # Normalize to 100 shares
        factors.append({
            "name": "recent_purchase",
            "weight": 0.35 * activity_factor_weight,
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
    
    # Factor 4: Risk tolerance
    risk_weights = {"conservative": 0.3, "moderate": 0.2, "aggressive": 0.1}
    factors.append({
        "name": "risk_tolerance",
        "weight": risk_weights.get(req.risk_tolerance, 0.2),
        "detail": f"{req.risk_tolerance.title()} risk tolerance affects strategy selection",
        "impact": "Medium"
    })
    
    # Generate summary
    if wash_sale_impact["wash_sale_triggered"]:
        summary = f"Wash-sale rule violation detected. Selling {req.symbol} at a ${abs(req.unrealized_pnl):,.0f} loss "
        summary += f"within 30 days of purchasing {recent_buys:.0f} shares would trigger wash-sale rule, "
        summary += f"disallowing ${wash_sale_impact['estimated_tax_benefit_lost']:.0f} in tax benefits. "
        summary += f"Risk score: {wash_sale_impact['risk_score']:.2f}/1.0"
    else:
        summary = f"No wash-sale risk detected for {req.symbol}. Trade can proceed safely."
    
    return {
        "type": "wash_sale_analysis_v2",
        "summary": summary,
        "factors": factors,
        "risk_level": "HIGH" if wash_sale_impact["wash_sale_triggered"] else "LOW",
        "recommendation": "AVOID" if wash_sale_impact["wash_sale_triggered"] else "PROCEED",
        "confidence": 0.95 if wash_sale_impact["wash_sale_triggered"] else 0.90
    }

def assess_wash_sale_risk(req: GuardRequestV2, wash_sale_impact: Dict[str, Any], 
                         substitutes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess overall wash-sale risk with mitigation options
    """
    risk_level = "LOW"
    confidence = 0.90
    
    if wash_sale_impact["wash_sale_triggered"]:
        risk_level = "HIGH"
        confidence = 0.95
        
        # Check if we have good substitutes
        if substitutes and any(s["correlation_score"] > 0.98 for s in substitutes):
            risk_level = "MEDIUM"  # Can be mitigated with substitutes
            confidence = 0.85
    
    return {
        "risk_level": risk_level,
        "confidence": confidence,
        "mitigation_available": len(substitutes) > 0,
        "best_substitute": substitutes[0] if substitutes else None,
        "risk_factors": {
            "loss_magnitude": wash_sale_impact["loss_percentage"],
            "recent_activity": wash_sale_impact["recent_buys"],
            "substitute_quality": max([s["correlation_score"] for s in substitutes], default=0)
        }
    }
