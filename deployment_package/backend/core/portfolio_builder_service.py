"""
AI Portfolio Builder Service
=============================
Given freed money and user's financial context, automatically constructs
a personalized portfolio allocation with specific percentages and dollar amounts.

This is the "killer feature" — instead of showing strategy categories,
we build an actual investment plan tailored to the user's situation.

Algorithm Overview:
1. Assess risk capacity (emergency fund, debt, income stability)
2. Determine risk tolerance (user preference or inferred from behavior)
3. Apply allocation model based on risk profile + time horizon
4. Adjust for existing portfolio (avoid concentration)
5. Output specific allocations with dollar amounts

Allocation Models:
- Conservative: 60% fixed income, 25% dividend, 15% growth
- Moderate: 40% growth, 30% dividend, 20% fixed income, 10% alternatives
- Aggressive: 50% growth, 25% AI/tech, 15% dividend, 10% real estate
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class AllocationSlice:
    """A single slice of the portfolio allocation."""
    strategy_id: str           # e.g. "growth_etf", "dividend_income"
    strategy_name: str         # e.g. "Growth ETF Investing"
    percentage: float          # 0-100
    monthly_amount: float      # Dollar amount per month
    annual_amount: float       # Dollar amount per year
    color: str                 # For UI visualization
    icon: str                  # Feather icon name
    
    primary_etf: str           # Main recommended ETF symbol
    primary_etf_name: str      # Full name
    rationale: str             # Why this allocation


@dataclass
class ProjectedMilestone:
    """A milestone in the wealth journey."""
    years: int
    value: float
    label: str                 # e.g. "Emergency fund complete"


@dataclass
class PortfolioBuilderResult:
    """Complete portfolio builder output."""
    user_id: int
    monthly_amount: float
    annual_amount: float
    
    risk_profile: str          # "conservative", "moderate", "aggressive"
    risk_rationale: str        # Why this risk level was chosen
    
    allocations: List[AllocationSlice] = field(default_factory=list)
    
    # Combined projections
    projected_10yr: float = 0
    projected_20yr: float = 0
    projected_30yr: float = 0
    expected_return_rate: float = 0.07  # Blended expected return
    
    # Milestones
    milestones: List[ProjectedMilestone] = field(default_factory=list)
    
    # Context
    headline: str = ""
    portfolio_adjustments: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    data_quality: str = "estimated"


# ── Allocation Models ───────────────────────────────────────────────────────────

ALLOCATION_MODELS: Dict[RiskProfile, List[Dict[str, Any]]] = {
    RiskProfile.CONSERVATIVE: [
        {"id": "fixed_income", "name": "Fixed Income & Bonds", "pct": 45, "color": "#6366F1", "icon": "shield",
         "etf": "BND", "etf_name": "Vanguard Total Bond Market",
         "rationale": "Stable foundation with predictable returns"},
        {"id": "dividend_income", "name": "Dividend Income", "pct": 30, "color": "#10B981", "icon": "dollar-sign",
         "etf": "SCHD", "etf_name": "Schwab U.S. Dividend Equity",
         "rationale": "Passive income while preserving capital"},
        {"id": "growth_etf", "name": "Growth ETF", "pct": 20, "color": "#3B82F6", "icon": "trending-up",
         "etf": "VTI", "etf_name": "Vanguard Total Stock Market",
         "rationale": "Modest growth exposure for long-term appreciation"},
        {"id": "real_estate", "name": "Real Estate (REITs)", "pct": 5, "color": "#F59E0B", "icon": "home",
         "etf": "VNQ", "etf_name": "Vanguard Real Estate ETF",
         "rationale": "Inflation hedge and diversification"},
    ],
    RiskProfile.MODERATE: [
        {"id": "growth_etf", "name": "Growth ETF", "pct": 40, "color": "#3B82F6", "icon": "trending-up",
         "etf": "VTI", "etf_name": "Vanguard Total Stock Market",
         "rationale": "Core holding for long-term wealth building"},
        {"id": "dividend_income", "name": "Dividend Income", "pct": 25, "color": "#10B981", "icon": "dollar-sign",
         "etf": "SCHD", "etf_name": "Schwab U.S. Dividend Equity",
         "rationale": "Balance growth with passive income"},
        {"id": "fixed_income", "name": "Fixed Income", "pct": 20, "color": "#6366F1", "icon": "shield",
         "etf": "BND", "etf_name": "Vanguard Total Bond Market",
         "rationale": "Stability during market volatility"},
        {"id": "ai_sector", "name": "AI & Tech Growth", "pct": 10, "color": "#7C3AED", "icon": "cpu",
         "etf": "QQQ", "etf_name": "Invesco QQQ Trust",
         "rationale": "Targeted exposure to technology growth"},
        {"id": "real_estate", "name": "Real Estate", "pct": 5, "color": "#F59E0B", "icon": "home",
         "etf": "VNQ", "etf_name": "Vanguard Real Estate ETF",
         "rationale": "Real asset diversification"},
    ],
    RiskProfile.AGGRESSIVE: [
        {"id": "growth_etf", "name": "Growth ETF", "pct": 35, "color": "#3B82F6", "icon": "trending-up",
         "etf": "VOO", "etf_name": "Vanguard S&P 500",
         "rationale": "Strong foundation in large-cap growth"},
        {"id": "ai_sector", "name": "AI & Tech Growth", "pct": 30, "color": "#7C3AED", "icon": "cpu",
         "etf": "QQQ", "etf_name": "Invesco QQQ Trust",
         "rationale": "High growth potential in technology sector"},
        {"id": "dividend_income", "name": "Dividend Income", "pct": 15, "color": "#10B981", "icon": "dollar-sign",
         "etf": "SCHD", "etf_name": "Schwab U.S. Dividend Equity",
         "rationale": "Income generation for reinvestment"},
        {"id": "real_estate", "name": "Real Estate", "pct": 10, "color": "#F59E0B", "icon": "home",
         "etf": "VNQ", "etf_name": "Vanguard Real Estate ETF",
         "rationale": "Alternative asset class exposure"},
        {"id": "fixed_income", "name": "Fixed Income", "pct": 10, "color": "#6366F1", "icon": "shield",
         "etf": "SGOV", "etf_name": "iShares 0-3 Month Treasury",
         "rationale": "Minimal bond allocation for flexibility"},
    ],
}

# Expected blended returns by risk profile
EXPECTED_RETURNS = {
    RiskProfile.CONSERVATIVE: 0.055,  # 5.5%
    RiskProfile.MODERATE: 0.075,      # 7.5%
    RiskProfile.AGGRESSIVE: 0.095,    # 9.5%
}


# ── Projection Calculator ───────────────────────────────────────────────────────

def calculate_fv(monthly_amount: float, annual_rate: float, years: int) -> float:
    """Calculate future value of monthly investments."""
    monthly_rate = annual_rate / 12
    n = years * 12
    if monthly_rate == 0:
        return monthly_amount * n
    return monthly_amount * (((1 + monthly_rate) ** n - 1) / monthly_rate)


def generate_milestones(monthly_amount: float, annual_rate: float) -> List[ProjectedMilestone]:
    """Generate wealth journey milestones."""
    milestones = []
    
    # First $10K
    years_to_10k = 0
    for y in range(1, 50):
        if calculate_fv(monthly_amount, annual_rate, y) >= 10000:
            years_to_10k = y
            break
    if years_to_10k > 0:
        milestones.append(ProjectedMilestone(
            years=years_to_10k,
            value=10000,
            label="First $10K milestone"
        ))
    
    # First $50K
    for y in range(1, 50):
        if calculate_fv(monthly_amount, annual_rate, y) >= 50000:
            milestones.append(ProjectedMilestone(
                years=y,
                value=50000,
                label="$50K — Serious portfolio"
            ))
            break
    
    # First $100K
    for y in range(1, 50):
        if calculate_fv(monthly_amount, annual_rate, y) >= 100000:
            milestones.append(ProjectedMilestone(
                years=y,
                value=100000,
                label="$100K — The hardest milestone"
            ))
            break
    
    # $500K
    for y in range(1, 50):
        if calculate_fv(monthly_amount, annual_rate, y) >= 500000:
            milestones.append(ProjectedMilestone(
                years=y,
                value=500000,
                label="$500K — Half millionaire"
            ))
            break
    
    return milestones


# ── Risk Assessment ─────────────────────────────────────────────────────────────

def assess_risk_profile(
    user_risk_preference: Optional[str] = None,
    emergency_fund_months: Optional[float] = None,
    debt_to_income: Optional[float] = None,
    age: Optional[int] = None,
    income_stability: Optional[str] = None,  # "stable", "variable", "uncertain"
) -> tuple[RiskProfile, str]:
    """
    Determine appropriate risk profile based on user's financial situation.
    Returns (profile, rationale).
    """
    # Start with user preference if provided
    if user_risk_preference:
        pref_lower = user_risk_preference.lower()
        if pref_lower in ["conservative", "low"]:
            return RiskProfile.CONSERVATIVE, "Based on your preference for lower risk"
        elif pref_lower in ["aggressive", "high"]:
            return RiskProfile.AGGRESSIVE, "Based on your preference for higher growth"
        elif pref_lower in ["moderate", "medium", "balanced"]:
            return RiskProfile.MODERATE, "Based on your preference for balanced growth"
    
    # Risk capacity score (0-100)
    capacity_score = 50  # Start neutral
    rationale_parts = []
    
    # Emergency fund check
    if emergency_fund_months is not None:
        if emergency_fund_months < 3:
            capacity_score -= 20
            rationale_parts.append("building emergency fund")
        elif emergency_fund_months >= 6:
            capacity_score += 10
    
    # Debt check
    if debt_to_income is not None:
        if debt_to_income > 0.4:
            capacity_score -= 15
            rationale_parts.append("managing existing debt")
        elif debt_to_income < 0.2:
            capacity_score += 10
    
    # Age check (younger = more risk capacity)
    if age is not None:
        if age < 30:
            capacity_score += 15
        elif age > 50:
            capacity_score -= 10
            rationale_parts.append("preserving capital closer to retirement")
    
    # Income stability
    if income_stability == "uncertain":
        capacity_score -= 15
        rationale_parts.append("variable income")
    elif income_stability == "stable":
        capacity_score += 5
    
    # Determine profile from score
    if capacity_score >= 65:
        profile = RiskProfile.AGGRESSIVE
        base_rationale = "Your financial foundation supports growth-focused investing"
    elif capacity_score >= 40:
        profile = RiskProfile.MODERATE
        base_rationale = "A balanced approach suits your current situation"
    else:
        profile = RiskProfile.CONSERVATIVE
        base_rationale = "Building a stable foundation first"
    
    # Combine rationale
    if rationale_parts:
        rationale = f"{base_rationale} while {', '.join(rationale_parts)}"
    else:
        rationale = base_rationale
    
    return profile, rationale


# ── Portfolio Adjustments ───────────────────────────────────────────────────────

def adjust_for_existing_portfolio(
    allocations: List[Dict[str, Any]],
    existing_tech_pct: Optional[float] = None,
    existing_bond_pct: Optional[float] = None,
) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Adjust allocations based on existing portfolio to avoid concentration.
    Returns (adjusted_allocations, adjustment_notes).
    """
    adjusted = [dict(a) for a in allocations]  # Deep copy
    notes = []
    
    # If already heavy in tech, reduce AI/tech allocation
    if existing_tech_pct and existing_tech_pct > 35:
        for a in adjusted:
            if a["id"] == "ai_sector":
                original_pct = a["pct"]
                a["pct"] = max(5, a["pct"] - 10)
                diff = original_pct - a["pct"]
                # Redistribute to fixed income
                for b in adjusted:
                    if b["id"] == "fixed_income":
                        b["pct"] += diff
                notes.append(f"Reduced tech allocation (you already have {existing_tech_pct:.0f}% tech)")
                break
    
    # If low on bonds, boost fixed income
    if existing_bond_pct is not None and existing_bond_pct < 10:
        for a in adjusted:
            if a["id"] == "fixed_income":
                a["pct"] += 5
                # Take from largest allocation
                largest = max(adjusted, key=lambda x: x["pct"])
                if largest["id"] != "fixed_income":
                    largest["pct"] -= 5
                notes.append("Added bond allocation for stability")
                break
    
    return adjusted, notes


# ── Service ─────────────────────────────────────────────────────────────────────

class PortfolioBuilderService:
    """
    AI Portfolio Builder — constructs personalized investment allocations.
    """
    
    def build(
        self,
        user_id: int,
        monthly_amount: float,
        risk_preference: Optional[str] = None,
        graph_context=None,
    ) -> PortfolioBuilderResult:
        """
        Build a personalized portfolio allocation.
        
        Args:
            user_id: The user ID
            monthly_amount: Amount to invest per month
            risk_preference: Optional user risk preference ("conservative", "moderate", "aggressive")
            graph_context: Optional FinancialGraphContext for personalization
        """
        annual_amount = monthly_amount * 12
        
        # Extract context from financial graph
        emergency_fund_months = None
        debt_to_income = None
        age = None
        income_stability = None
        existing_tech_pct = None
        existing_bond_pct = None
        
        if graph_context:
            emergency_fund_months = getattr(graph_context, 'emergency_fund_months', None)
            debt_to_income = getattr(graph_context, 'debt_to_income_ratio', None)
            existing_tech_pct = getattr(graph_context, 'tech_allocation_pct', None)
            existing_bond_pct = getattr(graph_context, 'fixed_income_pct', None)
            # Age could come from user profile
            age = getattr(graph_context, 'user_age', None)
            income_stability = getattr(graph_context, 'income_stability', None)
        
        # Assess risk profile
        risk_profile, risk_rationale = assess_risk_profile(
            user_risk_preference=risk_preference,
            emergency_fund_months=emergency_fund_months,
            debt_to_income=debt_to_income,
            age=age,
            income_stability=income_stability,
        )
        
        # Get base allocation model
        base_allocations = ALLOCATION_MODELS[risk_profile]
        
        # Adjust for existing portfolio
        adjusted_allocations, adjustment_notes = adjust_for_existing_portfolio(
            base_allocations,
            existing_tech_pct=existing_tech_pct,
            existing_bond_pct=existing_bond_pct,
        )
        
        # Build allocation slices with dollar amounts
        allocation_slices = []
        for alloc in adjusted_allocations:
            pct = alloc["pct"]
            monthly_slice = monthly_amount * (pct / 100)
            annual_slice = annual_amount * (pct / 100)
            
            allocation_slices.append(AllocationSlice(
                strategy_id=alloc["id"],
                strategy_name=alloc["name"],
                percentage=pct,
                monthly_amount=round(monthly_slice, 2),
                annual_amount=round(annual_slice, 2),
                color=alloc["color"],
                icon=alloc["icon"],
                primary_etf=alloc["etf"],
                primary_etf_name=alloc["etf_name"],
                rationale=alloc["rationale"],
            ))
        
        # Calculate projections
        expected_return = EXPECTED_RETURNS[risk_profile]
        projected_10yr = calculate_fv(monthly_amount, expected_return, 10)
        projected_20yr = calculate_fv(monthly_amount, expected_return, 20)
        projected_30yr = calculate_fv(monthly_amount, expected_return, 30)
        
        # Generate milestones
        milestones = generate_milestones(monthly_amount, expected_return)
        
        # Generate headline
        headline = (
            f"Investing ${monthly_amount:.0f}/month with a {risk_profile.value} approach "
            f"could grow to ${projected_30yr:,.0f} in 30 years."
        )
        
        # Warnings
        warnings = []
        if monthly_amount < 50:
            warnings.append("Consider increasing your investment amount for meaningful growth")
        if emergency_fund_months and emergency_fund_months < 3:
            warnings.append("Prioritize building 3-6 months emergency fund alongside investing")
        
        return PortfolioBuilderResult(
            user_id=user_id,
            monthly_amount=monthly_amount,
            annual_amount=annual_amount,
            risk_profile=risk_profile.value,
            risk_rationale=risk_rationale,
            allocations=allocation_slices,
            projected_10yr=round(projected_10yr, 2),
            projected_20yr=round(projected_20yr, 2),
            projected_30yr=round(projected_30yr, 2),
            expected_return_rate=expected_return,
            milestones=milestones,
            headline=headline,
            portfolio_adjustments=adjustment_notes,
            warnings=warnings,
            data_quality="actual" if graph_context else "estimated",
        )
    
    def build_safe(
        self,
        user_id: int,
        monthly_amount: float,
        risk_preference: Optional[str] = None,
        graph_context=None,
    ) -> PortfolioBuilderResult:
        """Safe wrapper that returns empty result on error."""
        try:
            return self.build(user_id, monthly_amount, risk_preference, graph_context)
        except Exception as e:
            logger.warning(f"PortfolioBuilderService.build error: {e}")
            return PortfolioBuilderResult(
                user_id=user_id,
                monthly_amount=monthly_amount,
                annual_amount=monthly_amount * 12,
                risk_profile="moderate",
                risk_rationale="Could not assess risk profile",
                headline="Could not build portfolio. Please try again.",
                data_quality="insufficient",
            )
