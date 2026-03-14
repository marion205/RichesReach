"""
Reallocation Strategy Service
==============================
Given freed money (from Leak Detector, spending cuts, etc.) and the user's
Financial Graph context, suggests investment strategy categories with:
  - Projected outcomes at multiple return rates
  - Example assets scored by the Asset Match formula
  - Graph-aware rationale (portfolio overlap warnings, risk alignment)

This powers the "Money Reallocation Engine" — the connector between
finding money leaks and actually investing that money wisely.

Asset Match Score Formula (from Pompian/WealthTech blueprint):
  Asset_Match_Score = (Expense_Ratio_Score × 0.4) + 
                      (Diversification_Delta × 0.4) + 
                      (Liquidity_Score × 0.2)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# ASSET DATABASE — The "Golden List" of pre-approved ETFs
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetData:
    """Complete metadata for a tradeable asset."""
    symbol: str
    name: str
    description: str
    asset_class: str            # "etf", "stock", "bond", "reit"
    
    # Cost efficiency
    expense_ratio: float        # e.g., 0.0003 for 0.03%
    
    # Sector/category exposure (for diversification calc)
    primary_sector: str         # "total_market", "tech", "dividend", "bonds", etc.
    secondary_sectors: List[str] = field(default_factory=list)
    
    # Liquidity (average daily volume in millions USD)
    avg_daily_volume_mm: float = 100.0
    
    # Strategy fit
    strategy_id: str = "growth_etf"
    archetype_fit: List[str] = field(default_factory=list)  # Which archetypes this suits


# The "Simple Path" approved asset list
ASSET_DATABASE: Dict[str, AssetData] = {
    # ── Total Market / Core (The Simple Path defaults) ────────────────────────
    "VTI": AssetData(
        symbol="VTI",
        name="Vanguard Total Stock Market ETF",
        description="Entire U.S. stock market in one ETF. Maximum diversification.",
        asset_class="etf",
        expense_ratio=0.0003,
        primary_sector="total_market",
        secondary_sectors=["large_cap", "mid_cap", "small_cap"],
        avg_daily_volume_mm=450.0,
        strategy_id="growth_etf",
        archetype_fit=["steady_builder", "cautious_protector"],
    ),
    "VOO": AssetData(
        symbol="VOO",
        name="Vanguard S&P 500 ETF",
        description="Tracks the 500 largest U.S. companies. Classic long-term choice.",
        asset_class="etf",
        expense_ratio=0.0003,
        primary_sector="large_cap",
        secondary_sectors=["total_market"],
        avg_daily_volume_mm=380.0,
        strategy_id="growth_etf",
        archetype_fit=["steady_builder"],
    ),
    "VT": AssetData(
        symbol="VT",
        name="Vanguard Total World Stock ETF",
        description="Global diversification — U.S. + International in one ETF.",
        asset_class="etf",
        expense_ratio=0.0007,
        primary_sector="global",
        secondary_sectors=["total_market", "international"],
        avg_daily_volume_mm=120.0,
        strategy_id="growth_etf",
        archetype_fit=["steady_builder"],
    ),
    
    # ── Tech/Growth (Opportunity Hunter) ──────────────────────────────────────
    "QQQ": AssetData(
        symbol="QQQ",
        name="Invesco QQQ Trust",
        description="Tracks the Nasdaq-100. Heavy tech exposure, historically strong growth.",
        asset_class="etf",
        expense_ratio=0.0020,
        primary_sector="tech",
        secondary_sectors=["large_cap", "growth"],
        avg_daily_volume_mm=520.0,
        strategy_id="ai_sector",
        archetype_fit=["opportunity_hunter"],
    ),
    "QQQM": AssetData(
        symbol="QQQM",
        name="Invesco Nasdaq 100 ETF",
        description="Lower-fee version of QQQ. Same exposure, less cost.",
        asset_class="etf",
        expense_ratio=0.0015,
        primary_sector="tech",
        secondary_sectors=["large_cap", "growth"],
        avg_daily_volume_mm=45.0,
        strategy_id="ai_sector",
        archetype_fit=["opportunity_hunter"],
    ),
    "VGT": AssetData(
        symbol="VGT",
        name="Vanguard Information Technology ETF",
        description="Pure tech sector exposure at low cost.",
        asset_class="etf",
        expense_ratio=0.0010,
        primary_sector="tech",
        secondary_sectors=["growth"],
        avg_daily_volume_mm=85.0,
        strategy_id="ai_sector",
        archetype_fit=["opportunity_hunter"],
    ),
    
    # ── Dividend/Income (Cautious Protector) ──────────────────────────────────
    "SCHD": AssetData(
        symbol="SCHD",
        name="Schwab U.S. Dividend Equity ETF",
        description="Quality dividend growers, ~3.5% yield. Strong track record.",
        asset_class="etf",
        expense_ratio=0.0006,
        primary_sector="dividend",
        secondary_sectors=["large_cap", "value"],
        avg_daily_volume_mm=180.0,
        strategy_id="dividend_income",
        archetype_fit=["cautious_protector", "steady_builder"],
    ),
    "VYM": AssetData(
        symbol="VYM",
        name="Vanguard High Dividend Yield ETF",
        description="High-dividend stocks, ~3% yield. Quarterly payouts.",
        asset_class="etf",
        expense_ratio=0.0006,
        primary_sector="dividend",
        secondary_sectors=["large_cap", "value"],
        avg_daily_volume_mm=95.0,
        strategy_id="dividend_income",
        archetype_fit=["cautious_protector"],
    ),
    
    # ── International Diversification ─────────────────────────────────────────
    "VXUS": AssetData(
        symbol="VXUS",
        name="Vanguard Total International Stock ETF",
        description="All non-U.S. stocks. Key for global diversification.",
        asset_class="etf",
        expense_ratio=0.0007,
        primary_sector="international",
        secondary_sectors=["developed", "emerging"],
        avg_daily_volume_mm=110.0,
        strategy_id="growth_etf",
        archetype_fit=["steady_builder"],
    ),
    "VEA": AssetData(
        symbol="VEA",
        name="Vanguard FTSE Developed Markets ETF",
        description="Developed international markets (Europe, Japan, etc.).",
        asset_class="etf",
        expense_ratio=0.0005,
        primary_sector="international",
        secondary_sectors=["developed"],
        avg_daily_volume_mm=85.0,
        strategy_id="growth_etf",
        archetype_fit=["steady_builder"],
    ),
    
    # ── Fixed Income / Bonds ──────────────────────────────────────────────────
    "BND": AssetData(
        symbol="BND",
        name="Vanguard Total Bond Market ETF",
        description="Entire U.S. bond market. Low risk, steady income.",
        asset_class="etf",
        expense_ratio=0.0003,
        primary_sector="bonds",
        secondary_sectors=["fixed_income"],
        avg_daily_volume_mm=220.0,
        strategy_id="fixed_income",
        archetype_fit=["cautious_protector", "reactive_trader"],
    ),
    "SGOV": AssetData(
        symbol="SGOV",
        name="iShares 0-3 Month Treasury Bond ETF",
        description="Ultra-short T-bills. Near risk-free, ~5% yield.",
        asset_class="etf",
        expense_ratio=0.0005,
        primary_sector="treasuries",
        secondary_sectors=["bonds", "fixed_income"],
        avg_daily_volume_mm=65.0,
        strategy_id="fixed_income",
        archetype_fit=["cautious_protector", "reactive_trader"],
    ),
    "TIP": AssetData(
        symbol="TIP",
        name="iShares TIPS Bond ETF",
        description="Inflation-protected bonds. Hedge against rising prices.",
        asset_class="etf",
        expense_ratio=0.0019,
        primary_sector="tips",
        secondary_sectors=["bonds", "fixed_income"],
        avg_daily_volume_mm=45.0,
        strategy_id="fixed_income",
        archetype_fit=["cautious_protector"],
    ),
    
    # ── Real Estate (REITs) ───────────────────────────────────────────────────
    "VNQ": AssetData(
        symbol="VNQ",
        name="Vanguard Real Estate ETF",
        description="Broad REIT exposure, ~4% dividend yield.",
        asset_class="etf",
        expense_ratio=0.0012,
        primary_sector="real_estate",
        secondary_sectors=["reits", "dividend"],
        avg_daily_volume_mm=140.0,
        strategy_id="real_estate",
        archetype_fit=["steady_builder", "cautious_protector"],
    ),
    "O": AssetData(
        symbol="O",
        name="Realty Income Corporation",
        description="Monthly dividend REIT, 'The Monthly Dividend Company'. ~5% yield.",
        asset_class="reit",
        expense_ratio=0.0,  # Stock, no expense ratio
        primary_sector="real_estate",
        secondary_sectors=["reits", "dividend"],
        avg_daily_volume_mm=75.0,
        strategy_id="real_estate",
        archetype_fit=["cautious_protector"],
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# ASSET MATCH SCORE — The three-factor scoring algorithm
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetMatchScore:
    """
    Explicit three-factor asset scoring from the blueprint.
    
    Formula:
      Asset_Match_Score = (Expense_Ratio_Score × 0.4) + 
                          (Diversification_Delta × 0.4) + 
                          (Liquidity_Score × 0.2)
    """
    symbol: str
    
    # Component scores (0-100 each)
    expense_ratio_score: float = 0.0
    diversification_delta: float = 0.0
    liquidity_score: float = 0.0
    
    # Weighted composite
    total_score: float = 0.0
    
    # Explanations for transparency
    expense_rationale: str = ""
    diversification_rationale: str = ""
    liquidity_rationale: str = ""
    
    def calculate_total(self) -> float:
        """Apply the blueprint formula weights."""
        self.total_score = (
            (self.expense_ratio_score * 0.4) +
            (self.diversification_delta * 0.4) +
            (self.liquidity_score * 0.2)
        )
        return self.total_score


class AssetMatchScorer:
    """
    Calculates Asset Match Scores for portfolio reallocation.
    
    The scoring system ensures:
    1. Low-cost funds are prioritized (expense ratio)
    2. Assets that reduce concentration get higher scores (diversification)
    3. Liquid assets preferred for easy exit (liquidity)
    """
    
    # Expense ratio benchmarks
    EXPENSE_EXCELLENT = 0.0003   # 0.03% — Vanguard-tier
    EXPENSE_GOOD = 0.0010       # 0.10%
    EXPENSE_MODERATE = 0.0050  # 0.50%
    EXPENSE_HIGH = 0.0075      # 0.75%
    
    # Liquidity thresholds (avg daily volume in millions USD)
    LIQUIDITY_EXCELLENT = 200.0
    LIQUIDITY_GOOD = 50.0
    LIQUIDITY_MINIMUM = 10.0
    
    def score_asset(
        self,
        asset: AssetData,
        user_sector_exposure: Dict[str, float] = None,
        user_archetype: str = None,
    ) -> AssetMatchScore:
        """
        Calculate the full Asset Match Score for a single asset.
        
        Args:
            asset: The asset to score
            user_sector_exposure: Dict of sector -> percentage (e.g., {"tech": 42.0})
            user_archetype: User's investor archetype for fit bonus
        """
        score = AssetMatchScore(symbol=asset.symbol)
        
        # Factor 1: Expense Ratio Score (inversely proportional)
        score.expense_ratio_score, score.expense_rationale = (
            self._calculate_expense_score(asset.expense_ratio)
        )
        
        # Factor 2: Diversification Delta (how much it helps)
        score.diversification_delta, score.diversification_rationale = (
            self._calculate_diversification_score(asset, user_sector_exposure or {})
        )
        
        # Factor 3: Liquidity Score
        score.liquidity_score, score.liquidity_rationale = (
            self._calculate_liquidity_score(asset.avg_daily_volume_mm)
        )
        
        # Calculate weighted total
        score.calculate_total()
        
        # Archetype fit bonus (up to +10 points)
        if user_archetype and user_archetype in asset.archetype_fit:
            score.total_score = min(100, score.total_score + 10)
        
        return score
    
    def _calculate_expense_score(self, expense_ratio: float) -> tuple[float, str]:
        """
        Score expense ratio inversely: lower fees = higher score.
        
        Scoring:
          0.03% (0.0003) → 100 points
          0.10% → ~85 points
          0.50% → ~40 points
          0.75%+ → 10 points minimum
        """
        if expense_ratio == 0:
            # Individual stocks have no expense ratio
            return 95.0, "Individual stock — no ongoing fees"
        
        if expense_ratio <= self.EXPENSE_EXCELLENT:
            score = 100.0
            rationale = f"Excellent: {expense_ratio*100:.2f}% expense ratio"
        elif expense_ratio <= self.EXPENSE_GOOD:
            # Linear interpolation 85-100
            score = 85 + (15 * (self.EXPENSE_GOOD - expense_ratio) / 
                         (self.EXPENSE_GOOD - self.EXPENSE_EXCELLENT))
            rationale = f"Very good: {expense_ratio*100:.2f}% expense ratio"
        elif expense_ratio <= self.EXPENSE_MODERATE:
            # Linear interpolation 40-85
            score = 40 + (45 * (self.EXPENSE_MODERATE - expense_ratio) / 
                         (self.EXPENSE_MODERATE - self.EXPENSE_GOOD))
            rationale = f"Moderate: {expense_ratio*100:.2f}% expense ratio"
        else:
            # High expense, but not disqualifying
            score = max(10, 40 - (30 * (expense_ratio - self.EXPENSE_MODERATE) / 
                                  (self.EXPENSE_HIGH - self.EXPENSE_MODERATE)))
            rationale = f"Higher cost: {expense_ratio*100:.2f}% expense ratio"
        
        return round(score, 1), rationale
    
    def _calculate_diversification_score(
        self,
        asset: AssetData,
        user_sector_exposure: Dict[str, float],
    ) -> tuple[float, str]:
        """
        Score how much the asset improves diversification.
        
        Logic:
          - If user is 40% tech, a Tech ETF scores LOW
          - If user is 40% tech, an International ETF scores HIGH
          - Total market funds get baseline bonus
        """
        if not user_sector_exposure:
            # No data — give baseline score
            if asset.primary_sector == "total_market":
                return 80.0, "Total market fund — inherently diversified"
            return 60.0, "No portfolio data — baseline score"
        
        primary = asset.primary_sector
        user_in_sector = user_sector_exposure.get(primary, 0.0)
        
        # Calculate how much adding this would help vs hurt
        if primary in ["total_market", "global"]:
            # Always good — inherent diversification
            score = 85.0
            rationale = "Adds broad market diversification"
        elif user_in_sector >= 35:
            # User is already concentrated here — penalize
            penalty = min(50, (user_in_sector - 35) * 2)
            score = max(20, 70 - penalty)
            rationale = f"Portfolio already {user_in_sector:.0f}% in {primary}"
        elif user_in_sector <= 5:
            # User has low exposure — this adds diversification
            bonus = min(30, (35 - user_in_sector) * 0.5)
            score = min(100, 70 + bonus)
            rationale = f"Adds {primary} exposure (currently {user_in_sector:.0f}%)"
        else:
            # Moderate exposure
            score = 70.0
            rationale = f"Balanced {primary} exposure"
        
        # International bonus for U.S.-heavy portfolios
        us_exposure = user_sector_exposure.get("us", 0) + user_sector_exposure.get("total_market", 0)
        if primary == "international" and us_exposure > 70:
            score = min(100, score + 15)
            rationale = f"Adds international diversification (US is {us_exposure:.0f}%)"
        
        return round(score, 1), rationale
    
    def _calculate_liquidity_score(self, avg_daily_volume_mm: float) -> tuple[float, str]:
        """
        Score liquidity based on average daily trading volume.
        
        Higher volume = easier to enter/exit without price impact.
        """
        if avg_daily_volume_mm >= self.LIQUIDITY_EXCELLENT:
            score = 100.0
            rationale = f"Highly liquid: ${avg_daily_volume_mm:.0f}M daily volume"
        elif avg_daily_volume_mm >= self.LIQUIDITY_GOOD:
            score = 70 + (30 * (avg_daily_volume_mm - self.LIQUIDITY_GOOD) / 
                         (self.LIQUIDITY_EXCELLENT - self.LIQUIDITY_GOOD))
            rationale = f"Good liquidity: ${avg_daily_volume_mm:.0f}M daily volume"
        elif avg_daily_volume_mm >= self.LIQUIDITY_MINIMUM:
            score = 40 + (30 * (avg_daily_volume_mm - self.LIQUIDITY_MINIMUM) / 
                         (self.LIQUIDITY_GOOD - self.LIQUIDITY_MINIMUM))
            rationale = f"Adequate liquidity: ${avg_daily_volume_mm:.0f}M daily volume"
        else:
            score = max(20, 40 * avg_daily_volume_mm / self.LIQUIDITY_MINIMUM)
            rationale = f"Lower liquidity: ${avg_daily_volume_mm:.1f}M daily volume"
        
        return round(score, 1), rationale
    
    def rank_assets_for_strategy(
        self,
        strategy_id: str,
        user_sector_exposure: Dict[str, float] = None,
        user_archetype: str = None,
        top_n: int = 3,
    ) -> List[tuple[AssetData, AssetMatchScore]]:
        """
        Rank all assets for a given strategy by Asset Match Score.
        
        Returns top N assets with their scores.
        """
        candidates = [
            asset for asset in ASSET_DATABASE.values()
            if asset.strategy_id == strategy_id
        ]
        
        scored = []
        for asset in candidates:
            score = self.score_asset(asset, user_sector_exposure, user_archetype)
            scored.append((asset, score))
        
        # Sort by total score descending
        scored.sort(key=lambda x: -x[1].total_score)
        
        return scored[:top_n]
    
    def get_best_asset(
        self,
        user_sector_exposure: Dict[str, float] = None,
        user_archetype: str = None,
        exclude_sectors: Set[str] = None,
    ) -> tuple[AssetData, AssetMatchScore]:
        """
        Find the single best asset across all strategies for this user.
        
        Used for "Simple Path" default recommendations.
        """
        exclude = exclude_sectors or set()
        
        candidates = [
            asset for asset in ASSET_DATABASE.values()
            if asset.primary_sector not in exclude
        ]
        
        best_asset = None
        best_score = None
        
        for asset in candidates:
            score = self.score_asset(asset, user_sector_exposure, user_archetype)
            if best_score is None or score.total_score > best_score.total_score:
                best_asset = asset
                best_score = score
        
        return best_asset, best_score


# Create singleton instance
asset_scorer = AssetMatchScorer()


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY DATACLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProjectedOutcome:
    """Projected future value at a given return rate."""
    return_rate: float          # e.g. 0.07 for 7%
    return_label: str           # e.g. "7% (conservative)"
    value_10yr: float           # FV after 10 years
    value_20yr: float           # FV after 20 years
    value_30yr: float           # FV after 30 years


@dataclass
class ScoredAsset:
    """An asset with its match score for UI display."""
    symbol: str
    name: str
    description: str
    asset_class: str
    
    # The three-factor score
    match_score: float
    expense_score: float
    diversification_score: float
    liquidity_score: float
    
    # Rationales for transparency
    expense_rationale: str = ""
    diversification_rationale: str = ""
    liquidity_rationale: str = ""
    
    # Cost info
    expense_ratio_display: str = ""


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
    
    # Legacy example assets (for backward compatibility)
    examples: List[ExampleAsset] = field(default_factory=list)
    
    # NEW: Scored assets with explicit match scores
    scored_assets: List[ScoredAsset] = field(default_factory=list)
    
    projections: List[ProjectedOutcome] = field(default_factory=list)
    
    graph_rationale: Optional[str] = None   # e.g. "Your portfolio is 42% tech. Consider diversifying."
    fit_score: int = 50                     # 0-100, how well this fits user's situation
    warning: Optional[str] = None           # e.g. "High risk, ensure emergency fund first"
    
    # Top recommendation details
    top_asset_symbol: Optional[str] = None
    top_asset_score: Optional[float] = None
    top_asset_rationale: Optional[str] = None


@dataclass
class ReallocationSuggestion:
    """Full suggestion output for a given freed amount."""
    user_id: int
    monthly_amount: float       # The freed amount per month
    annual_amount: float        # monthly × 12
    
    strategies: List[StrategyCategory] = field(default_factory=list)
    
    # NEW: The single best asset recommendation (Simple Path default)
    best_asset: Optional[ScoredAsset] = None
    best_asset_rationale: Optional[str] = None
    
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
    
    Uses the explicit Asset Match Score formula:
      Asset_Match_Score = (Expense_Ratio_Score × 0.4) + 
                          (Diversification_Delta × 0.4) + 
                          (Liquidity_Score × 0.2)
    
    Graph-aware: adjusts fit scores and adds warnings based on user's
    existing portfolio composition and financial health.
    """
    
    def __init__(self):
        self.scorer = asset_scorer
    
    def suggest(
        self,
        user_id: int,
        monthly_amount: float,
        graph_context=None,  # FinancialGraphContext from FinancialGraphService
        user_archetype: str = None,
    ) -> ReallocationSuggestion:
        """
        Generate strategy suggestions for the given monthly amount.
        
        Uses the three-factor Asset Match Score to rank assets within
        each strategy category.
        
        Args:
            user_id: The user ID
            monthly_amount: Amount freed per month (e.g. from cancelling subscriptions)
            graph_context: Optional financial graph for personalized rationale
            user_archetype: User's investor archetype for fit bonus
        """
        annual_amount = monthly_amount * 12
        projections = calculate_projections(monthly_amount)
        
        # Extract sector exposure from graph context
        user_sector_exposure = self._extract_sector_exposure(graph_context)
        
        # Start with all strategies
        strategies: List[StrategyCategory] = []
        
        for base_strategy in STRATEGY_CATALOG:
            # Score assets for this strategy using the explicit formula
            scored_assets = self._score_strategy_assets(
                base_strategy.id,
                user_sector_exposure,
                user_archetype,
            )
            
            strategy = StrategyCategory(
                id=base_strategy.id,
                name=base_strategy.name,
                tagline=base_strategy.tagline,
                icon=base_strategy.icon,
                color=base_strategy.color,
                risk_level=base_strategy.risk_level,
                time_horizon=base_strategy.time_horizon,
                examples=base_strategy.examples[:],
                scored_assets=scored_assets,
                projections=projections,
                fit_score=70,  # Base score
            )
            
            # Set top asset info if we have scored assets
            if scored_assets:
                top = scored_assets[0]
                strategy.top_asset_symbol = top.symbol
                strategy.top_asset_score = top.match_score
                strategy.top_asset_rationale = self._build_asset_rationale(top)
            
            # Apply graph-aware adjustments
            if graph_context:
                strategy = self._apply_graph_rationale(strategy, graph_context)
            
            strategies.append(strategy)
        
        # Sort by fit score
        strategies.sort(key=lambda s: -s.fit_score)
        
        # Find the single best asset (Simple Path default)
        best_asset, best_asset_rationale = self._find_best_overall_asset(
            user_sector_exposure,
            user_archetype,
        )
        
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
            best_asset=best_asset,
            best_asset_rationale=best_asset_rationale,
            headline_sentence=headline,
            current_portfolio_summary=portfolio_summary,
            data_quality=data_quality,
        )
    
    def _extract_sector_exposure(self, graph_context) -> Dict[str, float]:
        """Extract user's current sector allocation from graph context."""
        if not graph_context:
            return {}
        
        exposure = {}
        
        # Map graph context fields to sector exposure
        tech_pct = getattr(graph_context, 'tech_allocation_pct', None)
        if tech_pct:
            exposure['tech'] = tech_pct
        
        bond_pct = getattr(graph_context, 'fixed_income_pct', None)
        if bond_pct:
            exposure['bonds'] = bond_pct
            exposure['fixed_income'] = bond_pct
        
        intl_pct = getattr(graph_context, 'international_pct', None)
        if intl_pct:
            exposure['international'] = intl_pct
        
        us_pct = getattr(graph_context, 'us_equity_pct', None)
        if us_pct:
            exposure['us'] = us_pct
        
        real_estate_pct = getattr(graph_context, 'real_estate_pct', None)
        if real_estate_pct:
            exposure['real_estate'] = real_estate_pct
        
        return exposure
    
    def _score_strategy_assets(
        self,
        strategy_id: str,
        user_sector_exposure: Dict[str, float],
        user_archetype: str,
    ) -> List[ScoredAsset]:
        """
        Score all assets for a strategy using the three-factor formula.
        
        Returns a list of ScoredAsset objects sorted by match score.
        """
        ranked = self.scorer.rank_assets_for_strategy(
            strategy_id=strategy_id,
            user_sector_exposure=user_sector_exposure,
            user_archetype=user_archetype,
            top_n=5,
        )
        
        scored_assets = []
        for asset, score in ranked:
            scored_assets.append(ScoredAsset(
                symbol=asset.symbol,
                name=asset.name,
                description=asset.description,
                asset_class=asset.asset_class,
                match_score=round(score.total_score, 1),
                expense_score=score.expense_ratio_score,
                diversification_score=score.diversification_delta,
                liquidity_score=score.liquidity_score,
                expense_rationale=score.expense_rationale,
                diversification_rationale=score.diversification_rationale,
                liquidity_rationale=score.liquidity_rationale,
                expense_ratio_display=f"{asset.expense_ratio * 100:.2f}%" if asset.expense_ratio > 0 else "N/A",
            ))
        
        return scored_assets
    
    def _find_best_overall_asset(
        self,
        user_sector_exposure: Dict[str, float],
        user_archetype: str,
    ) -> tuple[Optional[ScoredAsset], Optional[str]]:
        """
        Find the single best asset for the user (Simple Path default).
        
        Prioritizes total market funds unless user has specific needs.
        """
        asset, score = self.scorer.get_best_asset(
            user_sector_exposure=user_sector_exposure,
            user_archetype=user_archetype,
        )
        
        if not asset or not score:
            return None, None
        
        scored = ScoredAsset(
            symbol=asset.symbol,
            name=asset.name,
            description=asset.description,
            asset_class=asset.asset_class,
            match_score=round(score.total_score, 1),
            expense_score=score.expense_ratio_score,
            diversification_score=score.diversification_delta,
            liquidity_score=score.liquidity_score,
            expense_rationale=score.expense_rationale,
            diversification_rationale=score.diversification_rationale,
            liquidity_rationale=score.liquidity_rationale,
            expense_ratio_display=f"{asset.expense_ratio * 100:.2f}%",
        )
        
        rationale = self._build_asset_rationale(scored)
        
        return scored, rationale
    
    def _build_asset_rationale(self, asset: ScoredAsset) -> str:
        """
        Build a human-readable rationale for the asset recommendation.
        
        Uses the AI Generation Template from the blueprint:
          - Strategic Fit
          - The 'Anti-Bias' Move
          - Cost Efficiency
        """
        parts = []
        
        # Strategic Fit
        parts.append(f"Score: {asset.match_score}/100")
        
        # Cost Efficiency (from expense ratio)
        if asset.expense_score >= 90:
            parts.append(f"Ultra-low cost ({asset.expense_ratio_display})")
        elif asset.expense_score >= 70:
            parts.append(f"Low cost ({asset.expense_ratio_display})")
        
        # Diversification benefit
        if asset.diversification_score >= 75:
            parts.append("Improves diversification")
        
        return " • ".join(parts)
    
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
