"""
Opportunity Discovery Service
==============================
Returns a curated catalog of investment opportunities across:
  - Real Estate (REITs, direct deals)
  - Alternatives (commodities, hedge funds)
  - Fixed Income (T-Bills, bond ladders, CDs)
  - Private Markets (delegated to existing PrivateMarketsService)

Graph-aware: when a FinancialGraphContext is provided, each opportunity
receives an annotated graph_rationale string explaining why it fits (or
doesn't fit) the user's specific financial situation. High-risk opportunities
are penalized when the user's emergency fund is insufficient.

Design: Demo/static catalog ships first. To replace with a real partner API,
swap out REAL_ESTATE, ALTERNATIVES, FIXED_INCOME class variables or override
get_opportunities().
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── Opportunity dataclass ─────────────────────────────────────────────────────

@dataclass
class Opportunity:
    """A curated investment opportunity across any asset class."""
    id: str
    asset_class: str         # "real_estate" | "alternatives" | "fixed_income" | "private_markets"
    name: str
    tagline: str
    score: int               # 0–100, same scale as Deal.score in Private Markets
    category: str            # e.g. "reit", "hedge_fund", "bond_ladder", "treasury", "commodity"

    # Graph-aware fields (populated by _annotate_opportunity when ctx provided)
    graph_rationale: Optional[str] = None
    graph_edge_ids: List[str] = field(default_factory=list)

    # Display / filter metadata
    minimum_investment: Optional[float] = None
    expected_return_range: Optional[str] = None     # e.g. "4–6%"
    liquidity: Optional[str] = None                 # "daily" | "quarterly" | "illiquid"
    risk_level: Optional[str] = None                # "low" | "moderate" | "high"


# ── Curated catalog ───────────────────────────────────────────────────────────

_REAL_ESTATE: List[Opportunity] = [
    Opportunity(
        id='re_1', asset_class='real_estate',
        name='Vanguard Real Estate ETF (VNQ)',
        tagline='Broad REIT exposure, daily liquidity',
        score=78, category='reit',
        minimum_investment=1.0,
        expected_return_range='5–8%',
        liquidity='daily',
        risk_level='moderate',
    ),
    Opportunity(
        id='re_2', asset_class='real_estate',
        name='Fundrise eREIT',
        tagline='Private real estate, quarterly liquidity',
        score=71, category='reit',
        minimum_investment=10.0,
        expected_return_range='8–12%',
        liquidity='quarterly',
        risk_level='moderate',
    ),
    Opportunity(
        id='re_3', asset_class='real_estate',
        name='Direct Rental Property',
        tagline='Full ownership, maximum control',
        score=65, category='direct',
        minimum_investment=50000.0,
        expected_return_range='6–10%',
        liquidity='illiquid',
        risk_level='high',
    ),
    Opportunity(
        id='re_4', asset_class='real_estate',
        name='Arrived Homes (Fractional Rental)',
        tagline='Single-family rentals from $100',
        score=69, category='reit',
        minimum_investment=100.0,
        expected_return_range='5–7%',
        liquidity='quarterly',
        risk_level='moderate',
    ),
]

_ALTERNATIVES: List[Opportunity] = [
    Opportunity(
        id='alt_1', asset_class='alternatives',
        name='iShares Gold ETF (IAU)',
        tagline='Commodity hedge against inflation',
        score=68, category='commodity',
        minimum_investment=1.0,
        expected_return_range='0–6% (inflation hedge)',
        liquidity='daily',
        risk_level='moderate',
    ),
    Opportunity(
        id='alt_2', asset_class='alternatives',
        name='Man AHL Diversified Futures',
        tagline='Trend-following hedge fund strategy',
        score=62, category='hedge_fund',
        minimum_investment=100000.0,
        expected_return_range='8–15%',
        liquidity='quarterly',
        risk_level='high',
    ),
    Opportunity(
        id='alt_3', asset_class='alternatives',
        name='Bloomberg Commodity ETF (PDBC)',
        tagline='Diversified commodity basket',
        score=65, category='commodity',
        minimum_investment=1.0,
        expected_return_range='2–8%',
        liquidity='daily',
        risk_level='moderate',
    ),
]

_FIXED_INCOME: List[Opportunity] = [
    Opportunity(
        id='fi_1', asset_class='fixed_income',
        name='3-Month Treasury Bills',
        tagline='Risk-free short-term yield',
        score=85, category='treasury',
        minimum_investment=100.0,
        expected_return_range='4.5–5.5%',
        liquidity='daily',
        risk_level='low',
    ),
    Opportunity(
        id='fi_2', asset_class='fixed_income',
        name='5-Year Bond Ladder',
        tagline='Staggered maturities, predictable income',
        score=80, category='bond_ladder',
        minimum_investment=5000.0,
        expected_return_range='4–5%',
        liquidity='quarterly',
        risk_level='low',
    ),
    Opportunity(
        id='fi_3', asset_class='fixed_income',
        name='High-Yield CDs (18-Month)',
        tagline='FDIC-insured, above-market rate',
        score=82, category='cd',
        minimum_investment=1000.0,
        expected_return_range='4.8–5.3%',
        liquidity='illiquid',
        risk_level='low',
    ),
    Opportunity(
        id='fi_4', asset_class='fixed_income',
        name='I-Bonds (Inflation-Linked)',
        tagline='Inflation protection, government-backed',
        score=77, category='treasury',
        minimum_investment=25.0,
        expected_return_range='3.5–6%',
        liquidity='illiquid',
        risk_level='low',
    ),
]


# ── Service ───────────────────────────────────────────────────────────────────

class OpportunityDiscoveryService:
    """
    Returns graph-aware, curated investment opportunities.
    Pass a FinancialGraphContext to activate graph-aware annotation and scoring.
    """

    CATALOG: dict = {
        'real_estate': _REAL_ESTATE,
        'alternatives': _ALTERNATIVES,
        'fixed_income': _FIXED_INCOME,
    }

    def get_opportunities(
        self,
        asset_class: Optional[str] = None,
        graph_context=None,   # FinancialGraphContext | None
        min_score: int = 0,
    ) -> List[Opportunity]:
        """
        Returns sorted, filtered, optionally graph-annotated opportunities.

        Args:
            asset_class: Filter to one class. None = all classes.
            graph_context: FinancialGraphContext from FinancialGraphService.
            min_score: Exclude opportunities below this score (0 = include all).
        """
        # Build the catalog for the requested class(es)
        catalog: List[Opportunity] = []
        if asset_class is None:
            for opps in self.CATALOG.values():
                catalog.extend(opps)
        else:
            catalog.extend(self.CATALOG.get(asset_class, []))

        # Apply min_score filter before graph annotation (annotation may adjust score)
        filtered = [copy.copy(o) for o in catalog if o.score >= min_score]

        # Graph-aware annotation
        if graph_context is not None:
            filtered = self._apply_graph_rationale(filtered, graph_context)
            # Re-filter after score adjustments
            filtered = [o for o in filtered if o.score >= min_score]

        return sorted(filtered, key=lambda o: -o.score)

    # ── Graph annotation ─────────────────────────────────────────────────────

    def _apply_graph_rationale(
        self, opportunities: List[Opportunity], ctx
    ) -> List[Opportunity]:
        edge_map = {e.relationship_id: e for e in ctx.edges}
        return [self._annotate_opportunity(o, edge_map, ctx) for o in opportunities]

    def _annotate_opportunity(
        self, opp: Opportunity, edge_map: dict, ctx
    ) -> Opportunity:
        """
        Injects graph_rationale and adjusts score based on cross-silo edges.
        Mutates the copy (caller already copied).
        """
        rationale_parts: List[str] = []
        triggered_edges: List[str] = []

        # ── Rule 1: Fixed income low-risk + healthy emergency fund ──────────
        if opp.asset_class == 'fixed_income' and opp.risk_level == 'low':
            edge = edge_map.get('emergency_fund_to_risk_capacity')
            if edge and ctx.emergency_fund_months >= 3:
                rationale_parts.append(
                    f"Your {ctx.emergency_fund_months:.1f}-month emergency fund means "
                    f"this low-risk position complements your existing buffer well."
                )
                triggered_edges.append('emergency_fund_to_risk_capacity')

        # ── Rule 2: Liquid REIT + investable surplus freed from debt ─────────
        if opp.asset_class == 'real_estate' and opp.liquidity == 'daily':
            edge = edge_map.get('debt_to_investable_surplus')
            if edge and ctx.investable_surplus_monthly > 100:
                rationale_parts.append(
                    f"With ${ctx.investable_surplus_monthly:,.0f}/month in investable "
                    f"surplus, a liquid REIT lets you build real estate exposure incrementally."
                )
                triggered_edges.append('debt_to_investable_surplus')

        # ── Rule 3: High-risk alternatives penalized if emergency fund low ───
        if opp.risk_level == 'high':
            edge = edge_map.get('emergency_fund_to_risk_capacity')
            if not edge or edge.direction == 'negative' or ctx.emergency_fund_months < 3:
                opp.score = max(opp.score - 15, 0)
                rationale_parts.append(
                    "Building a 3+ month emergency fund before this position is recommended."
                )
            else:
                rationale_parts.append(
                    f"Your {ctx.emergency_fund_months:.1f}-month emergency fund supports "
                    f"taking on this higher-risk position."
                )
                triggered_edges.append('emergency_fund_to_risk_capacity')

        # ── Rule 4: Treasury/bond ladder + low utilization → SBLOC note ─────
        if opp.category in ('treasury', 'bond_ladder', 'cd'):
            edge = edge_map.get('credit_utilization_to_borrowing_power')
            if edge and ctx.avg_credit_utilization < 0.30:
                rationale_parts.append(
                    "Your credit profile qualifies you to use these holdings as "
                    "collateral for a securities-backed line of credit (SBLOC)."
                )
                triggered_edges.append('credit_utilization_to_borrowing_power')

        # ── Rule 5: Wealth velocity context on any opportunity ───────────────
        edge = edge_map.get('income_savings_wealth_velocity')
        if edge and edge.numeric_impact and edge.numeric_impact > 0 and not rationale_parts:
            # Only add as a fallback if no other rationale was generated
            rationale_parts.append(
                f"At your current savings trajectory (${edge.numeric_impact:,.0f}/year "
                f"wealth velocity), adding this position aligns with your growth path."
            )
            triggered_edges.append('income_savings_wealth_velocity')

        opp.graph_rationale = ' '.join(rationale_parts) if rationale_parts else None
        opp.graph_edge_ids = triggered_edges
        return opp
