"""
Reallocation Strategy Service
==============================
Given freed money (from Leak Detector, spending cuts, etc.) and the user's
Financial Graph context, suggests investment strategy categories with:
  - Projected outcomes at multiple return rates
  - Example assets
  - Graph-aware rationale (portfolio overlap warnings, risk alignment)

This powers the "Money Reallocation Engine" — the connector between
finding money leaks and actually investing that money wisely.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── Strategy dataclasses ───────────────────────────────────────────────────────

@dataclass
class ProjectedOutcome:
    """Projected future value at a given return rate."""
    return_rate: float          # e.g. 0.07 for 7%
    return_label: str           # e.g. "7% (conservative)"
    value_10yr: float           # FV after 10 years
    value_20yr: float           # FV after 20 years
    value_30yr: float           # FV after 30 years


@dataclass
class ExampleAsset:
    """A representative asset for a strategy category."""
    symbol: str                 # e.g. "QQQ", "VYM", "BND"
    name: str                   # e.g. "Invesco QQQ Trust"
    description: str            # 1-2 sentence explanation
    asset_class: str            # "etf", "stock", "bond", "reit"


@dataclass
class StrategyCategory:
    """An investment strategy category with examples and projections."""
    id: str                     # e.g. "growth_etf", "dividend_income"
    name: str                   # e.g. "Growth ETF Investing"
    tagline: str                # e.g. "Long-term capital appreciation"
    icon: str                   # Feather icon name
    color: str                  # Hex color for UI
    
    risk_level: str             # "low", "moderate", "high"
    time_horizon: str           # "short", "medium", "long"
    
    examples: List[ExampleAsset] = field(default_factory=list)
    projections: List[ProjectedOutcome] = field(default_factory=list)
    
    graph_rationale: Optional[str] = None   # e.g. "Your portfolio is 42% tech. Consider diversifying."
    fit_score: int = 50                     # 0-100, how well this fits user's situation
    warning: Optional[str] = None           # e.g. "High risk, ensure emergency fund first"


@dataclass
class ReallocationSuggestion:
    """Full suggestion output for a given freed amount."""
    user_id: int
    monthly_amount: float       # The freed amount per month
    annual_amount: float        # monthly × 12
    
    strategies: List[StrategyCategory] = field(default_factory=list)
    
    headline_sentence: str = ""
    current_portfolio_summary: Optional[str] = None  # e.g. "42% tech, 30% bonds, 28% cash"
    data_quality: str = "actual"  # "actual" | "estimated" | "insufficient"


# ── Strategy Catalog ───────────────────────────────────────────────────────────

def _growth_etf_strategy() -> StrategyCategory:
    return StrategyCategory(
        id="growth_etf",
        name="Growth ETF Investing",
        tagline="Long-term capital appreciation via broad market exposure",
        icon="trending-up",
        color="#3B82F6",
        risk_level="moderate",
        time_horizon="long",
        examples=[
            ExampleAsset("QQQ", "Invesco QQQ Trust", 
                "Tracks the Nasdaq-100. Heavy tech exposure, historically strong growth.", "etf"),
            ExampleAsset("VTI", "Vanguard Total Stock Market", 
                "Entire U.S. stock market in one ETF. Maximum diversification.", "etf"),
            ExampleAsset("VOO", "Vanguard S&P 500", 
                "Tracks the 500 largest U.S. companies. Classic long-term choice.", "etf"),
        ],
    )


def _dividend_income_strategy() -> StrategyCategory:
    return StrategyCategory(
        id="dividend_income",
        name="Dividend Income",
        tagline="Generate passive income through dividend-paying stocks",
        icon="dollar-sign",
        color="#10B981",
        risk_level="moderate",
        time_horizon="medium",
        examples=[
            ExampleAsset("VYM", "Vanguard High Dividend Yield", 
                "High-dividend stocks, ~3% yield. Quarterly payouts.", "etf"),
            ExampleAsset("SCHD", "Schwab U.S. Dividend Equity", 
                "Quality dividend growers, ~3.5% yield. Strong track record.", "etf"),
            ExampleAsset("O", "Realty Income Corp", 
                "Monthly dividend REIT, 'The Monthly Dividend Company'. ~5% yield.", "reit"),
        ],
    )


def _ai_sector_strategy() -> StrategyCategory:
    return StrategyCategory(
        id="ai_sector",
        name="AI & Tech Growth",
        tagline="Exposure to artificial intelligence and technology leaders",
        icon="cpu",
        color="#7C3AED",
        risk_level="high",
        time_horizon="long",
        examples=[
            ExampleAsset("NVDA", "NVIDIA Corporation", 
                "Leading AI chip maker. High growth, high volatility.", "stock"),
            ExampleAsset("MSFT", "Microsoft Corporation", 
                "Cloud + AI integration (Azure, Copilot). Diversified tech giant.", "stock"),
            ExampleAsset("BOTZ", "Global X Robotics & AI ETF", 
                "Basket of robotics and AI companies. Diversified sector exposure.", "etf"),
        ],
    )


def _fixed_income_strategy() -> StrategyCategory:
    return StrategyCategory(
        id="fixed_income",
        name="Fixed Income & Bonds",
        tagline="Stable, predictable returns with lower volatility",
        icon="shield",
        color="#6366F1",
        risk_level="low",
        time_horizon="short",
        examples=[
            ExampleAsset("BND", "Vanguard Total Bond Market", 
                "Entire U.S. bond market. Low risk, steady income.", "etf"),
            ExampleAsset("SGOV", "iShares 0-3 Month Treasury", 
                "Ultra-short T-bills. Near risk-free, ~5% yield.", "etf"),
            ExampleAsset("TIP", "iShares TIPS Bond ETF", 
                "Inflation-protected bonds. Hedge against rising prices.", "etf"),
        ],
    )


def _real_estate_strategy() -> StrategyCategory:
    return StrategyCategory(
        id="real_estate",
        name="Real Estate (REITs)",
        tagline="Real estate exposure without buying property",
        icon="home",
        color="#F59E0B",
        risk_level="moderate",
        time_horizon="medium",
        examples=[
            ExampleAsset("VNQ", "Vanguard Real Estate ETF", 
                "Broad REIT exposure, ~4% dividend yield.", "etf"),
            ExampleAsset("STAG", "STAG Industrial", 
                "Industrial warehouses. Monthly dividend, ~4% yield.", "reit"),
            ExampleAsset("AMT", "American Tower Corp", 
                "Cell tower infrastructure. Growing 5G demand.", "reit"),
        ],
    )


STRATEGY_CATALOG = [
    _growth_etf_strategy(),
    _dividend_income_strategy(),
    _ai_sector_strategy(),
    _fixed_income_strategy(),
    _real_estate_strategy(),
]


# ── Projection Calculator ──────────────────────────────────────────────────────

def calculate_projections(monthly_amount: float) -> List[ProjectedOutcome]:
    """
    Calculate future value of monthly investments at different return rates.
    Uses compound monthly formula: FV = PMT × (((1 + r)^n - 1) / r)
    """
    outcomes = []
    scenarios = [
        (0.05, "5% (conservative)"),
        (0.07, "7% (moderate)"),
        (0.10, "10% (aggressive)"),
    ]
    
    for annual_rate, label in scenarios:
        monthly_rate = annual_rate / 12
        
        def fv(years: int) -> float:
            n = years * 12
            if monthly_rate == 0:
                return monthly_amount * n
            return monthly_amount * (((1 + monthly_rate) ** n - 1) / monthly_rate)
        
        outcomes.append(ProjectedOutcome(
            return_rate=annual_rate,
            return_label=label,
            value_10yr=round(fv(10), 2),
            value_20yr=round(fv(20), 2),
            value_30yr=round(fv(30), 2),
        ))
    
    return outcomes


# ── Service ────────────────────────────────────────────────────────────────────

class ReallocationStrategyService:
    """
    Suggests investment strategies for freed/reallocated money.
    Graph-aware: adjusts fit scores and adds warnings based on user's
    existing portfolio composition and financial health.
    """
    
    def suggest(
        self,
        user_id: int,
        monthly_amount: float,
        graph_context=None,  # FinancialGraphContext from FinancialGraphService
    ) -> ReallocationSuggestion:
        """
        Generate strategy suggestions for the given monthly amount.
        
        Args:
            user_id: The user ID
            monthly_amount: Amount freed per month (e.g. from cancelling subscriptions)
            graph_context: Optional financial graph for personalized rationale
        """
        annual_amount = monthly_amount * 12
        projections = calculate_projections(monthly_amount)
        
        # Start with all strategies
        strategies: List[StrategyCategory] = []
        
        for base_strategy in STRATEGY_CATALOG:
            strategy = StrategyCategory(
                id=base_strategy.id,
                name=base_strategy.name,
                tagline=base_strategy.tagline,
                icon=base_strategy.icon,
                color=base_strategy.color,
                risk_level=base_strategy.risk_level,
                time_horizon=base_strategy.time_horizon,
                examples=base_strategy.examples[:],
                projections=projections,
                fit_score=70,  # Base score
            )
            
            # Apply graph-aware adjustments
            if graph_context:
                strategy = self._apply_graph_rationale(strategy, graph_context)
            
            strategies.append(strategy)
        
        # Sort by fit score
        strategies.sort(key=lambda s: -s.fit_score)
        
        # Generate headline
        best_30yr = max(p.value_30yr for p in projections) if projections else 0
        headline = (
            f"Investing ${monthly_amount:.0f}/month could grow to "
            f"${best_30yr:,.0f} in 30 years."
        )
        
        portfolio_summary = None
        data_quality = "estimated"
        
        if graph_context:
            portfolio_summary = self._summarize_portfolio(graph_context)
            data_quality = "actual"
        
        return ReallocationSuggestion(
            user_id=user_id,
            monthly_amount=monthly_amount,
            annual_amount=annual_amount,
            strategies=strategies,
            headline_sentence=headline,
            current_portfolio_summary=portfolio_summary,
            data_quality=data_quality,
        )
    
    def suggest_safe(self, user_id: int, monthly_amount: float, graph_context=None) -> ReallocationSuggestion:
        """Safe wrapper that returns empty suggestion on error."""
        try:
            return self.suggest(user_id, monthly_amount, graph_context)
        except Exception as e:
            logger.warning(f"ReallocationStrategyService.suggest error: {e}")
            return ReallocationSuggestion(
                user_id=user_id,
                monthly_amount=monthly_amount,
                annual_amount=monthly_amount * 12,
                headline_sentence="Could not generate suggestions. Please try again.",
                data_quality="insufficient",
            )
    
    def _apply_graph_rationale(
        self,
        strategy: StrategyCategory,
        graph_context,
    ) -> StrategyCategory:
        """
        Adjust strategy fit score and add rationale based on financial graph.
        """
        # Extract portfolio composition from graph if available
        tech_pct = getattr(graph_context, 'tech_allocation_pct', None)
        bond_pct = getattr(graph_context, 'fixed_income_pct', None)
        emergency_fund_months = getattr(graph_context, 'emergency_fund_months', None)
        debt_to_income = getattr(graph_context, 'debt_to_income_ratio', None)
        
        # AI/Tech strategy: warn if already heavy in tech
        if strategy.id == "ai_sector" and tech_pct and tech_pct > 35:
            strategy.fit_score = 40
            strategy.graph_rationale = (
                f"Your portfolio is already {tech_pct:.0f}% in tech. "
                "Consider diversifying into other sectors."
            )
            strategy.warning = "High concentration risk"
        
        # Growth ETF: boost if young investor (long horizon)
        if strategy.id == "growth_etf":
            strategy.fit_score = 75
            strategy.graph_rationale = (
                "Growth ETFs align well with long-term wealth building. "
                "Best for 10+ year horizons."
            )
        
        # Fixed income: boost if emergency fund is low
        if strategy.id == "fixed_income":
            if emergency_fund_months and emergency_fund_months < 3:
                strategy.fit_score = 85
                strategy.graph_rationale = (
                    f"Your emergency fund covers only {emergency_fund_months:.1f} months. "
                    "Consider building a cash buffer before aggressive investing."
                )
                strategy.warning = "Build emergency fund first"
            else:
                strategy.graph_rationale = (
                    "Fixed income provides stability and predictable returns."
                )
        
        # Dividend: good for passive income seekers
        if strategy.id == "dividend_income":
            strategy.fit_score = 72
            strategy.graph_rationale = (
                "Dividend investing generates passive income while you wait for growth."
            )
        
        # Real estate: moderate fit for diversification
        if strategy.id == "real_estate":
            strategy.fit_score = 68
            strategy.graph_rationale = (
                "REITs add real estate exposure without the hassle of property management."
            )
        
        return strategy
    
    def _summarize_portfolio(self, graph_context) -> str:
        """Generate a 1-line portfolio summary from graph context."""
        parts = []
        
        tech_pct = getattr(graph_context, 'tech_allocation_pct', None)
        bond_pct = getattr(graph_context, 'fixed_income_pct', None)
        cash_pct = getattr(graph_context, 'cash_pct', None)
        
        if tech_pct:
            parts.append(f"{tech_pct:.0f}% tech")
        if bond_pct:
            parts.append(f"{bond_pct:.0f}% bonds")
        if cash_pct:
            parts.append(f"{cash_pct:.0f}% cash")
        
        if not parts:
            return "Portfolio data not available"
        
        return ", ".join(parts)
