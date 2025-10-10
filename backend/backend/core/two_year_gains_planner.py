#!/usr/bin/env python3
"""
Two-Year Gains Planner - Best-in-Market Tax Optimization
Schedules gains/harvests across current + next year to keep you inside optimal brackets
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
class GainCandidate:
    id: str
    symbol: str
    gain: float            # if sold
    days_to_lt: int        # 0 if already LT
    current_price: float
    cost_basis: float
    shares: float
    acquire_date: date
    priority: str = "medium"  # high, medium, low

@dataclass
class PlanRequest:
    candidates: List[GainCandidate]
    year1_cap_room: float  # how much gains fit in desired bracket this year
    year2_cap_room: float
    prefer_lt: bool = True
    current_income: float = 0.0
    filing_status: str = "single"  # single, married_filing_jointly, etc.
    state_tax_rate: float = 0.0
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive

@dataclass
class PlanResponse:
    sell_now: List[Dict[str, Any]]
    defer_to_next_year: List[Dict[str, Any]]
    rationale: Dict[str, Any]
    tax_impact: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

# Tax bracket thresholds for 2024
TAX_BRACKETS = {
    "single": [
        {"min": 0, "max": 11000, "rate": 0.10},
        {"min": 11000, "max": 44725, "rate": 0.12},
        {"min": 44725, "max": 95375, "rate": 0.22},
        {"min": 95375, "max": 182050, "rate": 0.24},
        {"min": 182050, "max": 231250, "rate": 0.32},
        {"min": 231250, "max": 578125, "rate": 0.35},
        {"min": 578125, "max": float('inf'), "rate": 0.37}
    ],
    "married_filing_jointly": [
        {"min": 0, "max": 22000, "rate": 0.10},
        {"min": 22000, "max": 89450, "rate": 0.12},
        {"min": 89450, "max": 190750, "rate": 0.22},
        {"min": 190750, "max": 364200, "rate": 0.24},
        {"min": 364200, "max": 462500, "rate": 0.32},
        {"min": 462500, "max": 693750, "rate": 0.35},
        {"min": 693750, "max": float('inf'), "rate": 0.37}
    ]
}

# Long-term capital gains rates
LT_CG_RATES = {
    "single": [
        {"min": 0, "max": 44725, "rate": 0.0},
        {"min": 44725, "max": 492300, "rate": 0.15},
        {"min": 492300, "max": float('inf'), "rate": 0.20}
    ],
    "married_filing_jointly": [
        {"min": 0, "max": 89450, "rate": 0.0},
        {"min": 89450, "max": 553850, "rate": 0.15},
        {"min": 553850, "max": float('inf'), "rate": 0.20}
    ]
}

@require_premium_feature('two_year_gains_planner')
@login_required
@require_http_methods(["POST"])
def two_year_gains_planner(request):
    """
    Two-Year Gains Planner
    Schedules gains/harvests across current + next year for optimal tax brackets
    """
    try:
        data = json.loads(request.body)
        
        # Parse candidates
        candidates_data = data.get('candidates', [])
        candidates = []
        for cand_data in candidates_data:
            candidate = GainCandidate(
                id=cand_data['id'],
                symbol=cand_data['symbol'],
                gain=float(cand_data['gain']),
                days_to_lt=int(cand_data['days_to_lt']),
                current_price=float(cand_data['current_price']),
                cost_basis=float(cand_data['cost_basis']),
                shares=float(cand_data['shares']),
                acquire_date=date.fromisoformat(cand_data['acquire_date']),
                priority=cand_data.get('priority', 'medium')
            )
            candidates.append(candidate)
        
        # Create plan request
        plan_req = PlanRequest(
            candidates=candidates,
            year1_cap_room=float(data.get('year1_cap_room', 0)),
            year2_cap_room=float(data.get('year2_cap_room', 0)),
            prefer_lt=data.get('prefer_lt', True),
            current_income=float(data.get('current_income', 0)),
            filing_status=data.get('filing_status', 'single'),
            state_tax_rate=float(data.get('state_tax_rate', 0.0)),
            risk_tolerance=data.get('risk_tolerance', 'moderate')
        )
        
        # Run planning
        result = plan_two_year_gains(plan_req)
        
        return JsonResponse({
            'status': 'success',
            'result': result.__dict__
        })
        
    except Exception as e:
        logger.error(f"Two-year gains planner error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def plan_two_year_gains(req: PlanRequest) -> PlanResponse:
    """
    Core two-year gains planning logic
    """
    # Calculate current tax situation
    current_tax_situation = calculate_tax_situation(req.current_income, req.filing_status)
    
    # Sort candidates by priority and tax efficiency
    sorted_candidates = sort_candidates_by_priority(req.candidates, req)
    
    # Plan for current year
    sell_now = []
    defer_to_next_year = []
    year1_room_remaining = req.year1_cap_room
    year2_room_remaining = req.year2_cap_room
    
    for candidate in sorted_candidates:
        # Calculate tax impact
        tax_impact = calculate_candidate_tax_impact(candidate, req, current_tax_situation)
        
        # Decision logic
        should_sell_now = should_sell_candidate_now(candidate, tax_impact, year1_room_remaining, req)
        
        if should_sell_now and year1_room_remaining >= candidate.gain:
            sell_now.append({
                "candidate_id": candidate.id,
                "symbol": candidate.symbol,
                "gain": candidate.gain,
                "tax_impact": tax_impact,
                "reason": get_sell_reason(candidate, tax_impact, req),
                "days_to_lt": candidate.days_to_lt,
                "priority": candidate.priority
            })
            year1_room_remaining -= candidate.gain
        else:
            defer_to_next_year.append({
                "candidate_id": candidate.id,
                "symbol": candidate.symbol,
                "gain": candidate.gain,
                "tax_impact": tax_impact,
                "reason": get_defer_reason(candidate, tax_impact, req),
                "days_to_lt": candidate.days_to_lt,
                "priority": candidate.priority
            })
    
    # Calculate tax impact
    tax_impact = calculate_total_tax_impact(sell_now, defer_to_next_year, req)
    
    # Generate rationale
    rationale = generate_planning_rationale(sell_now, defer_to_next_year, req, year1_room_remaining)
    
    # Generate recommendations
    recommendations = generate_recommendations(sell_now, defer_to_next_year, req, tax_impact)
    
    return PlanResponse(
        sell_now=sell_now,
        defer_to_next_year=defer_to_next_year,
        rationale=rationale,
        tax_impact=tax_impact,
        recommendations=recommendations
    )

def calculate_tax_situation(income: float, filing_status: str) -> Dict[str, Any]:
    """
    Calculate current tax situation
    """
    brackets = TAX_BRACKETS.get(filing_status, TAX_BRACKETS["single"])
    lt_brackets = LT_CG_RATES.get(filing_status, LT_CG_RATES["single"])
    
    # Find current bracket
    current_bracket = None
    for bracket in brackets:
        if bracket["min"] <= income < bracket["max"]:
            current_bracket = bracket
            break
    
    # Find LT capital gains bracket
    lt_bracket = None
    for bracket in lt_brackets:
        if bracket["min"] <= income < bracket["max"]:
            lt_bracket = bracket
            break
    
    return {
        "current_bracket": current_bracket,
        "lt_bracket": lt_bracket,
        "income": income,
        "filing_status": filing_status
    }

def sort_candidates_by_priority(candidates: List[GainCandidate], req: PlanRequest) -> List[GainCandidate]:
    """
    Sort candidates by priority and tax efficiency
    """
    def priority_score(candidate):
        score = 0
        
        # Priority weight
        priority_weights = {"high": 3, "medium": 2, "low": 1}
        score += priority_weights.get(candidate.priority, 2)
        
        # Long-term preference
        if candidate.days_to_lt == 0:  # Already long-term
            score += 2
        elif candidate.days_to_lt <= 30:  # Close to long-term
            score += 1
        
        # Gain size (larger gains get higher priority for planning)
        if candidate.gain > 10000:
            score += 1
        elif candidate.gain > 5000:
            score += 0.5
        
        return score
    
    return sorted(candidates, key=priority_score, reverse=True)

def calculate_candidate_tax_impact(candidate: GainCandidate, req: PlanRequest, tax_situation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate tax impact for a candidate
    """
    # Determine if long-term or short-term
    is_long_term = candidate.days_to_lt == 0
    
    if is_long_term:
        # Long-term capital gains rate
        lt_bracket = tax_situation["lt_bracket"]
        lt_rate = lt_bracket["rate"] if lt_bracket else 0.15
        tax_rate = lt_rate + req.state_tax_rate
    else:
        # Short-term (ordinary income rate)
        current_bracket = tax_situation["current_bracket"]
        st_rate = current_bracket["rate"] if current_bracket else 0.22
        tax_rate = st_rate + req.state_tax_rate
    
    tax_amount = candidate.gain * tax_rate
    
    # Calculate potential savings if we wait for long-term
    if not is_long_term and candidate.days_to_lt <= 365:
        potential_lt_rate = 0.15 + req.state_tax_rate  # Assume 15% LT rate
        potential_lt_tax = candidate.gain * potential_lt_rate
        potential_savings = tax_amount - potential_lt_tax
    else:
        potential_savings = 0
    
    return {
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "is_long_term": is_long_term,
        "potential_savings": potential_savings,
        "days_to_lt": candidate.days_to_lt
    }

def should_sell_candidate_now(candidate: GainCandidate, tax_impact: Dict[str, Any], 
                            year1_room: float, req: PlanRequest) -> bool:
    """
    Determine if a candidate should be sold now
    """
    # If no room in year 1, defer
    if year1_room < candidate.gain:
        return False
    
    # If already long-term and we prefer LT, sell now
    if candidate.days_to_lt == 0 and req.prefer_lt:
        return True
    
    # If close to long-term (within 30 days), defer
    if candidate.days_to_lt <= 30 and req.prefer_lt:
        return False
    
    # If high priority and significant gain, consider selling now
    if candidate.priority == "high" and candidate.gain > 5000:
        return True
    
    # Risk tolerance considerations
    if req.risk_tolerance == "conservative":
        # Conservative: prefer long-term, defer short-term
        return candidate.days_to_lt == 0
    elif req.risk_tolerance == "aggressive":
        # Aggressive: sell now if it fits in bracket
        return True
    else:  # moderate
        # Moderate: balance between tax efficiency and timing
        return candidate.days_to_lt == 0 or (candidate.days_to_lt > 90 and candidate.gain > 2000)

def get_sell_reason(candidate: GainCandidate, tax_impact: Dict[str, Any], req: PlanRequest) -> str:
    """
    Get reason for selling now
    """
    if candidate.days_to_lt == 0:
        return f"Long-term position - optimal tax rate ({tax_impact['tax_rate']*100:.1f}%)"
    elif candidate.priority == "high":
        return f"High priority position - fits in current year bracket"
    elif candidate.gain > 5000:
        return f"Significant gain - take advantage of current bracket room"
    else:
        return f"Fits in current year tax bracket"

def get_defer_reason(candidate: GainCandidate, tax_impact: Dict[str, Any], req: PlanRequest) -> str:
    """
    Get reason for deferring
    """
    if candidate.days_to_lt <= 30:
        return f"Wait {candidate.days_to_lt} days for long-term rate (save ${tax_impact['potential_savings']:.0f})"
    elif candidate.gain > req.year1_cap_room:
        return f"Gain too large for current year bracket room"
    else:
        return f"Defer to next year for better tax planning"

def calculate_total_tax_impact(sell_now: List[Dict], defer_next_year: List[Dict], req: PlanRequest) -> Dict[str, Any]:
    """
    Calculate total tax impact of the plan
    """
    year1_tax = sum(item["tax_impact"]["tax_amount"] for item in sell_now)
    year2_tax = sum(item["tax_impact"]["tax_amount"] for item in defer_next_year)
    
    total_tax = year1_tax + year2_tax
    
    # Calculate potential savings from long-term conversion
    lt_savings = sum(item["tax_impact"]["potential_savings"] for item in defer_next_year)
    
    return {
        "year1_tax": year1_tax,
        "year2_tax": year2_tax,
        "total_tax": total_tax,
        "long_term_savings": lt_savings,
        "effective_rate": (total_tax / (year1_tax + year2_tax) * 100) if (year1_tax + year2_tax) > 0 else 0
    }

def generate_planning_rationale(sell_now: List[Dict], defer_next_year: List[Dict], 
                              req: PlanRequest, year1_room_remaining: float) -> Dict[str, Any]:
    """
    Generate rationale for the planning decisions
    """
    total_gains_now = sum(item["gain"] for item in sell_now)
    total_gains_deferred = sum(item["gain"] for item in defer_next_year)
    
    rationale = {
        "policy": "Fill current-year bracket with optimal positions; defer remainder to next year",
        "year1_room_used": req.year1_cap_room - year1_room_remaining,
        "year1_room_remaining": year1_room_remaining,
        "total_gains_now": total_gains_now,
        "total_gains_deferred": total_gains_deferred,
        "long_term_conversions": len([item for item in defer_next_year if item["days_to_lt"] <= 30]),
        "strategy": "Tax-efficient bracket management with long-term preference"
    }
    
    if req.prefer_lt:
        rationale["strategy"] += " - prioritizing long-term positions"
    
    if req.risk_tolerance == "conservative":
        rationale["strategy"] += " - conservative approach with minimal risk"
    elif req.risk_tolerance == "aggressive":
        rationale["strategy"] += " - aggressive approach maximizing current year benefits"
    
    return rationale

def generate_recommendations(sell_now: List[Dict], defer_next_year: List[Dict], 
                           req: PlanRequest, tax_impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate actionable recommendations
    """
    recommendations = []
    
    # Recommendation 1: Execute current year sales
    if sell_now:
        recommendations.append({
            "type": "execute_sales",
            "title": "Execute Current Year Sales",
            "description": f"Execute {len(sell_now)} sales to realize ${sum(item['gain'] for item in sell_now):,.0f} in gains",
            "priority": "HIGH",
            "deadline": "December 31, 2024",
            "tax_impact": f"${tax_impact['year1_tax']:,.0f} in taxes"
        })
    
    # Recommendation 2: Long-term conversions
    lt_conversions = [item for item in defer_next_year if item["days_to_lt"] <= 30]
    if lt_conversions:
        recommendations.append({
            "type": "long_term_conversion",
            "title": "Long-Term Conversion Strategy",
            "description": f"Wait for {len(lt_conversions)} positions to convert to long-term",
            "priority": "HIGH",
            "deadline": "Various dates based on acquisition",
            "tax_impact": f"Save ${sum(item['tax_impact']['potential_savings'] for item in lt_conversions):,.0f} in taxes"
        })
    
    # Recommendation 3: Next year planning
    if defer_next_year:
        recommendations.append({
            "type": "next_year_planning",
            "title": "Next Year Tax Planning",
            "description": f"Plan for {len(defer_next_year)} deferred positions in 2025",
            "priority": "MEDIUM",
            "deadline": "January 1, 2025",
            "tax_impact": f"${tax_impact['year2_tax']:,.0f} in estimated taxes"
        })
    
    # Recommendation 4: Bracket optimization
    if req.year1_cap_room > 0:
        recommendations.append({
            "type": "bracket_optimization",
            "title": "Maximize Current Year Bracket",
            "description": f"Consider additional ${req.year1_cap_room:,.0f} in gains to fill current bracket",
            "priority": "LOW",
            "deadline": "December 31, 2024",
            "tax_impact": "Optimize tax efficiency"
        })
    
    return recommendations
