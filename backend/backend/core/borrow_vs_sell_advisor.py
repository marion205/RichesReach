#!/usr/bin/env python3
"""
Borrow-vs-Sell Advisor - Best-in-Market Tax Optimization
Compares selling with capital gains vs. SBLOC/Aave borrow (interest, LTV, tax carryforwards).
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .premium_models import require_premium_feature
import json
import logging
from datetime import date, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

@dataclass
class BorrowVsSellRequest:
    needed_cash: float
    est_cap_gain: float
    cap_gain_rate: float
    borrow_rate: float      # SBLOC or DeFi APR (decimal)
    horizon_years: float
    ltv: float = 0.5
    fees_rate: float = 0.0
    portfolio_value: float = 0.0
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    tax_bracket: float = 0.22
    state_tax_rate: float = 0.0
    inflation_rate: float = 0.03
    opportunity_cost_rate: float = 0.07  # Expected portfolio return

@dataclass
class BorrowVsSellResponse:
    sell_net_cash: float
    borrow_cost_total: float
    recommendation: str
    detailed_analysis: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    explanation: Dict[str, Any]

@require_premium_feature('borrow_vs_sell_advisor')
@login_required
@require_http_methods(["POST"])
def borrow_vs_sell_advisor(request):
    """
    Borrow-vs-Sell Advisor
    Compares selling with capital gains vs. borrowing to raise cash
    """
    try:
        data = json.loads(request.body)
        
        req = BorrowVsSellRequest(
            needed_cash=float(data.get('needed_cash', 0)),
            est_cap_gain=float(data.get('est_cap_gain', 0)),
            cap_gain_rate=float(data.get('cap_gain_rate', 0.15)),
            borrow_rate=float(data.get('borrow_rate', 0.06)),
            horizon_years=float(data.get('horizon_years', 1.0)),
            ltv=float(data.get('ltv', 0.5)),
            fees_rate=float(data.get('fees_rate', 0.0)),
            portfolio_value=float(data.get('portfolio_value', 0)),
            risk_tolerance=data.get('risk_tolerance', 'moderate'),
            tax_bracket=float(data.get('tax_bracket', 0.22)),
            state_tax_rate=float(data.get('state_tax_rate', 0.0)),
            inflation_rate=float(data.get('inflation_rate', 0.03)),
            opportunity_cost_rate=float(data.get('opportunity_cost_rate', 0.07))
        )
        
        if req.needed_cash <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'needed_cash must be greater than 0'
            }, status=400)
        
        # Run analysis
        result = analyze_borrow_vs_sell(req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Borrow vs sell advisor error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def analyze_borrow_vs_sell(req: BorrowVsSellRequest) -> BorrowVsSellResponse:
    """
    Analyze borrow vs sell scenarios
    """
    # Calculate sell scenario
    sell_analysis = calculate_sell_scenario(req)
    
    # Calculate borrow scenario
    borrow_analysis = calculate_borrow_scenario(req)
    
    # Generate scenarios for different time horizons
    scenarios = generate_scenarios(req)
    
    # Determine recommendation
    recommendation = determine_recommendation(sell_analysis, borrow_analysis, req)
    
    # Generate detailed analysis
    detailed_analysis = {
        "sell_scenario": sell_analysis,
        "borrow_scenario": borrow_analysis,
        "net_advantage": borrow_analysis["total_cost"] - sell_analysis["total_cost"],
        "break_even_horizon": calculate_break_even_horizon(req),
        "risk_analysis": analyze_risk_factors(req, sell_analysis, borrow_analysis)
    }
    
    # Generate explanation
    explanation = generate_borrow_vs_sell_explanation(req, sell_analysis, borrow_analysis, recommendation)
    
    return BorrowVsSellResponse(
        sell_net_cash=sell_analysis["net_cash"],
        borrow_cost_total=borrow_analysis["total_cost"],
        recommendation=recommendation,
        detailed_analysis=detailed_analysis,
        scenarios=scenarios,
        explanation=explanation
    )

def calculate_sell_scenario(req: BorrowVsSellRequest) -> Dict[str, Any]:
    """
    Calculate the cost of selling to raise cash
    """
    # Tax on capital gains
    tax_on_gains = req.est_cap_gain * (req.cap_gain_rate + req.state_tax_rate)
    
    # Net cash after taxes
    net_cash = req.needed_cash - tax_on_gains
    
    # Opportunity cost (lost portfolio growth)
    opportunity_cost = req.needed_cash * req.opportunity_cost_rate * req.horizon_years
    
    # Total cost
    total_cost = tax_on_gains + opportunity_cost
    
    return {
        "gross_cash": req.needed_cash,
        "tax_on_gains": tax_on_gains,
        "net_cash": net_cash,
        "opportunity_cost": opportunity_cost,
        "total_cost": total_cost,
        "effective_rate": total_cost / req.needed_cash if req.needed_cash > 0 else 0
    }

def calculate_borrow_scenario(req: BorrowVsSellRequest) -> Dict[str, Any]:
    """
    Calculate the cost of borrowing to raise cash
    """
    # Interest cost
    interest_cost = req.needed_cash * req.borrow_rate * req.horizon_years
    
    # Fees
    fees = req.needed_cash * req.fees_rate
    
    # Tax deduction on interest (if applicable)
    interest_deduction = interest_cost * req.tax_bracket
    
    # Net interest cost after tax deduction
    net_interest_cost = interest_cost - interest_deduction
    
    # Total cost
    total_cost = net_interest_cost + fees
    
    # LTV risk assessment
    ltv_risk = assess_ltv_risk(req)
    
    return {
        "gross_cash": req.needed_cash,
        "interest_cost": interest_cost,
        "fees": fees,
        "interest_deduction": interest_deduction,
        "net_interest_cost": net_interest_cost,
        "total_cost": total_cost,
        "effective_rate": total_cost / req.needed_cash if req.needed_cash > 0 else 0,
        "ltv_risk": ltv_risk
    }

def assess_ltv_risk(req: BorrowVsSellRequest) -> Dict[str, Any]:
    """
    Assess loan-to-value risk
    """
    if req.portfolio_value == 0:
        return {"risk_level": "UNKNOWN", "margin_call_risk": 0}
    
    current_ltv = req.needed_cash / req.portfolio_value
    
    # Risk levels based on LTV
    if current_ltv <= 0.3:
        risk_level = "LOW"
        margin_call_risk = 0.05
    elif current_ltv <= 0.5:
        risk_level = "MODERATE"
        margin_call_risk = 0.15
    elif current_ltv <= 0.7:
        risk_level = "HIGH"
        margin_call_risk = 0.30
    else:
        risk_level = "VERY_HIGH"
        margin_call_risk = 0.50
    
    return {
        "risk_level": risk_level,
        "current_ltv": current_ltv,
        "margin_call_risk": margin_call_risk,
        "recommended_max_ltv": 0.5 if req.risk_tolerance == "conservative" else 0.7
    }

def generate_scenarios(req: BorrowVsSellRequest) -> List[Dict[str, Any]]:
    """
    Generate scenarios for different time horizons and market conditions
    """
    scenarios = []
    
    # Different time horizons
    horizons = [0.25, 0.5, 1.0, 2.0, 3.0]  # 3 months to 3 years
    
    for horizon in horizons:
        # Create modified request for this horizon
        horizon_req = BorrowVsSellRequest(
            needed_cash=req.needed_cash,
            est_cap_gain=req.est_cap_gain,
            cap_gain_rate=req.cap_gain_rate,
            borrow_rate=req.borrow_rate,
            horizon_years=horizon,
            ltv=req.ltv,
            fees_rate=req.fees_rate,
            portfolio_value=req.portfolio_value,
            risk_tolerance=req.risk_tolerance,
            tax_bracket=req.tax_bracket,
            state_tax_rate=req.state_tax_rate,
            inflation_rate=req.inflation_rate,
            opportunity_cost_rate=req.opportunity_cost_rate
        )
        
        sell_cost = calculate_sell_scenario(horizon_req)["total_cost"]
        borrow_cost = calculate_borrow_scenario(horizon_req)["total_cost"]
        
        scenarios.append({
            "horizon_years": horizon,
            "sell_cost": sell_cost,
            "borrow_cost": borrow_cost,
            "advantage": borrow_cost - sell_cost,
            "recommendation": "BORROW" if borrow_cost < sell_cost else "SELL"
        })
    
    return scenarios

def calculate_break_even_horizon(req: BorrowVsSellRequest) -> float:
    """
    Calculate the break-even time horizon where borrow and sell costs are equal
    """
    # Tax cost (one-time)
    tax_cost = req.est_cap_gain * (req.cap_gain_rate + req.state_tax_rate)
    
    # Annual borrow cost
    annual_borrow_cost = req.needed_cash * req.borrow_rate * (1 - req.tax_bracket)
    
    # Annual opportunity cost of selling
    annual_opportunity_cost = req.needed_cash * req.opportunity_cost_rate
    
    # Break-even when: tax_cost = (annual_borrow_cost - annual_opportunity_cost) * years
    net_annual_borrow_cost = annual_borrow_cost - annual_opportunity_cost
    
    if net_annual_borrow_cost <= 0:
        return float('inf')  # Borrow is always better
    
    break_even_years = tax_cost / net_annual_borrow_cost
    return max(0, break_even_years)

def analyze_risk_factors(req: BorrowVsSellRequest, sell_analysis: Dict, borrow_analysis: Dict) -> Dict[str, Any]:
    """
    Analyze risk factors for both scenarios
    """
    return {
        "sell_risks": {
            "market_timing": "Risk of selling at market low",
            "tax_irreversibility": "Cannot undo tax payment",
            "opportunity_cost": "Lost portfolio growth potential"
        },
        "borrow_risks": {
            "interest_rate_risk": "Rates may increase",
            "margin_call_risk": borrow_analysis["ltv_risk"]["margin_call_risk"],
            "portfolio_volatility": "Asset values may decline",
            "liquidity_risk": "May need to sell at unfavorable time"
        },
        "risk_tolerance_impact": {
            "conservative": "Favor selling to avoid leverage risk",
            "moderate": "Consider both options based on cost",
            "aggressive": "Favor borrowing to maintain portfolio exposure"
        }
    }

def determine_recommendation(sell_analysis: Dict, borrow_analysis: Dict, req: BorrowVsSellRequest) -> str:
    """
    Determine the recommendation based on analysis
    """
    cost_difference = borrow_analysis["total_cost"] - sell_analysis["total_cost"]
    
    # Risk-adjusted recommendation
    if req.risk_tolerance == "conservative":
        # Conservative investors prefer selling unless borrowing is significantly cheaper
        if cost_difference < -0.02 * req.needed_cash:  # 2% threshold
            return "BORROW"
        else:
            return "SELL"
    elif req.risk_tolerance == "aggressive":
        # Aggressive investors prefer borrowing unless selling is significantly cheaper
        if cost_difference > 0.02 * req.needed_cash:  # 2% threshold
            return "SELL"
        else:
            return "BORROW"
    else:  # moderate
        # Moderate investors choose based on cost
        if cost_difference < 0:
            return "BORROW"
        else:
            return "SELL"

def generate_borrow_vs_sell_explanation(req: BorrowVsSellRequest, sell_analysis: Dict, 
                                       borrow_analysis: Dict, recommendation: str) -> Dict[str, Any]:
    """
    Generate SHAP-style explanation for borrow vs sell analysis
    """
    factors = []
    
    # Factor 1: Tax impact
    tax_impact = sell_analysis["tax_on_gains"]
    factors.append({
        "name": "tax_impact",
        "weight": 0.3,
        "detail": f"${tax_impact:,.0f} in capital gains tax if selling",
        "impact": "High" if tax_impact > req.needed_cash * 0.1 else "Medium"
    })
    
    # Factor 2: Interest cost
    interest_cost = borrow_analysis["net_interest_cost"]
    factors.append({
        "name": "interest_cost",
        "weight": 0.25,
        "detail": f"${interest_cost:,.0f} in net interest cost over {req.horizon_years:.1f} years",
        "impact": "High" if interest_cost > req.needed_cash * 0.05 else "Medium"
    })
    
    # Factor 3: Opportunity cost
    opportunity_cost = sell_analysis["opportunity_cost"]
    factors.append({
        "name": "opportunity_cost",
        "weight": 0.2,
        "detail": f"${opportunity_cost:,.0f} in lost portfolio growth if selling",
        "impact": "High" if opportunity_cost > req.needed_cash * 0.1 else "Medium"
    })
    
    # Factor 4: Risk tolerance
    factors.append({
        "name": "risk_tolerance",
        "weight": 0.15,
        "detail": f"{req.risk_tolerance.title()} risk tolerance",
        "impact": "High" if req.risk_tolerance == "conservative" else "Medium"
    })
    
    # Factor 5: LTV risk
    ltv_risk = borrow_analysis["ltv_risk"]["risk_level"]
    factors.append({
        "name": "leverage_risk",
        "weight": 0.1,
        "detail": f"{ltv_risk} leverage risk at current LTV",
        "impact": "High" if ltv_risk in ["HIGH", "VERY_HIGH"] else "Low"
    })
    
    # Generate summary
    cost_difference = borrow_analysis["total_cost"] - sell_analysis["total_cost"]
    
    if recommendation == "BORROW":
        summary = f"Borrowing is recommended. Save ${abs(cost_difference):,.0f} compared to selling "
        summary += f"(${borrow_analysis['total_cost']:,.0f} vs ${sell_analysis['total_cost']:,.0f}). "
        summary += f"Maintains portfolio exposure while avoiding ${sell_analysis['tax_on_gains']:,.0f} in taxes."
    else:
        summary = f"Selling is recommended. Save ${abs(cost_difference):,.0f} compared to borrowing "
        summary += f"(${sell_analysis['total_cost']:,.0f} vs ${borrow_analysis['total_cost']:,.0f}). "
        summary += f"Avoids leverage risk and interest costs."
    
    return {
        "type": "borrow_vs_sell_analysis",
        "summary": summary,
        "factors": factors,
        "cost_difference": cost_difference,
        "break_even_horizon": calculate_break_even_horizon(req),
        "confidence": "HIGH" if abs(cost_difference) > req.needed_cash * 0.05 else "MEDIUM"
    }
