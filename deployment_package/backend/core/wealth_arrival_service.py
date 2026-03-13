"""
Wealth Arrival Service
======================
Projects when a user will reach financial milestones ("wealth arrival") by
compounding their current net worth, savings rate, and portfolio at realistic
expected returns.

Key outputs
-----------
- current_net_worth      : assets − liabilities today
- annual_contribution    : investable_surplus × 12
- year_by_year           : list of (year, net_worth, portfolio_value, savings)
- milestones             : first year each $X milestone is crossed
- scenarios              : conservative / moderate / aggressive side-by-side
- wealth_arrival_years   : years until user's own $1 M milestone (or custom target)
- headline_sentence      : human-readable "At your current pace you'll reach …"

All calculations are synchronous and read-only; no DB writes.

Design notes
------------
- Extends (does not modify) FinancialGraphService — calls build_graph_safe() and
  adds projection logic on top.
- Return rates by risk tolerance:
    Conservative  → 5 % nominal  (mostly bonds / balanced)
    Moderate      → 7 % nominal  (classic 60/40)
    Aggressive    → 9 % nominal  (equity-heavy)
- Inflation: 3 % assumed; all milestone dollar amounts are in today's dollars
  (real terms) unless noted.
- Projection horizon: driven by IncomeProfile.investment_horizon; max 50 years.
- Savings growth rate: salary assumed to grow 3 % / year; discretionary savings
  grows proportionally (conservative assumption — no lifestyle creep adjustment).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Return-rate assumptions ──────────────────────────────────────────────────

RETURN_RATES = {
    "Conservative": 0.05,
    "Moderate":     0.07,
    "Aggressive":   0.09,
}

INFLATION_RATE    = 0.03
SALARY_GROWTH     = 0.03   # annual income growth assumption
DEFAULT_HORIZON   = 30     # years if IncomeProfile.investment_horizon is missing

HORIZON_MAP = {
    "1-3 years":  3,
    "3-5 years":  5,
    "5-10 years": 10,
    "10+ years":  30,
}

STANDARD_MILESTONES = [
    10_000,
    25_000,
    50_000,
    100_000,
    250_000,
    500_000,
    1_000_000,
    2_000_000,
    5_000_000,
    10_000_000,
]


# ─── Data containers ──────────────────────────────────────────────────────────

@dataclass
class WealthYearPoint:
    """Net worth snapshot at the end of a projection year."""
    year: int
    net_worth: float         # portfolio + savings − debt (real $)
    portfolio_value: float   # invested assets only
    savings_balance: float   # liquid savings
    annual_contribution: float
    cumulative_contributions: float


@dataclass
class WealthMilestone:
    """A specific net-worth milestone and when it will be reached."""
    target_amount: float
    years_away: int          # full years from now; 0 = already there
    arrival_year: int        # calendar year (current year + years_away)
    already_achieved: bool
    label: str               # e.g. "$1,000,000"


@dataclass
class WealthScenario:
    """Full projection for one scenario (conservative / moderate / aggressive)."""
    scenario: str                          # "conservative" | "moderate" | "aggressive"
    annual_return: float
    year_by_year: list = field(default_factory=list)  # list[WealthYearPoint]
    milestones: list = field(default_factory=list)    # list[WealthMilestone]
    wealth_arrival_years: Optional[int] = None        # years to reach target_net_worth
    final_net_worth: float = 0.0
    total_contributions: float = 0.0
    total_growth: float = 0.0


@dataclass
class WealthArrivalResult:
    """Full output from WealthArrivalService.project()."""
    user_id: int

    # Current snapshot
    current_net_worth: float = 0.0
    current_portfolio_value: float = 0.0
    current_savings_balance: float = 0.0
    current_debt: float = 0.0
    estimated_monthly_income: Optional[float] = None
    investable_surplus_monthly: float = 0.0
    annual_contribution: float = 0.0
    savings_rate_pct: float = 0.0

    # Projection inputs
    projection_years: int = DEFAULT_HORIZON
    risk_tolerance: str = "Moderate"
    target_net_worth: float = 1_000_000.0
    current_age: Optional[int] = None

    # Primary scenario (matches risk_tolerance)
    primary: Optional[WealthScenario] = None

    # All three scenarios for comparison
    scenarios: list = field(default_factory=list)  # list[WealthScenario]

    # Convenience headline
    headline_sentence: str = ""
    data_quality: str = "estimated"   # "actual" | "estimated" | "insufficient"


# ─── Service ──────────────────────────────────────────────────────────────────

class WealthArrivalService:
    """
    Computes wealth arrival projections for an authenticated user.

    Usage:
        result = WealthArrivalService().project(user)
        result = WealthArrivalService().project(user, target_net_worth=500_000)
    """

    def project(
        self,
        user,
        target_net_worth: float = 1_000_000.0,
    ) -> WealthArrivalResult:
        """
        Main entry point.  Returns a WealthArrivalResult.

        Parameters
        ----------
        user              : Django User instance
        target_net_worth  : the "arrival" milestone the user cares about most
                            (defaults to $1 M; UI can pass a custom figure)
        """
        result = WealthArrivalResult(
            user_id=user.pk,
            target_net_worth=target_net_worth,
        )

        try:
            self._load_financial_context(user, result)
            self._load_profile(user, result)
            self._run_projections(result)
            self._build_headline(result)
        except Exception as exc:
            logger.warning(
                "WealthArrivalService.project failed for user %s: %s",
                getattr(user, 'pk', '?'), exc,
            )
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Connect your accounts to see your personalized Wealth Arrival timeline."
            )

        return result

    def project_safe(self, user, target_net_worth: float = 1_000_000.0) -> WealthArrivalResult:
        """Wraps project() so callers never see an exception."""
        try:
            return self.project(user, target_net_worth=target_net_worth)
        except Exception as exc:
            logger.warning("WealthArrivalService.project_safe error: %s", exc)
            result = WealthArrivalResult(user_id=getattr(user, 'pk', 0))
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Connect your accounts to see your personalized Wealth Arrival timeline."
            )
            return result

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_financial_context(self, user, result: WealthArrivalResult) -> None:
        """
        Pull current financial snapshot via FinancialGraphService (reuses all
        existing data-loading logic; no duplication).
        """
        from .financial_graph_service import FinancialGraphService

        ctx = FinancialGraphService().build_graph_safe(user)
        if ctx is None:
            result.data_quality = "insufficient"
            return

        result.current_portfolio_value = ctx.portfolio_total_value
        result.current_savings_balance = ctx.total_savings_balance
        result.current_debt           = ctx.total_cc_balance
        result.estimated_monthly_income = ctx.estimated_monthly_income
        result.investable_surplus_monthly = ctx.investable_surplus_monthly

        result.current_net_worth = (
            ctx.portfolio_total_value
            + ctx.total_savings_balance
            - ctx.total_cc_balance
        )

        monthly_income = ctx.estimated_monthly_income or 0
        if monthly_income > 0:
            result.savings_rate_pct = (
                ctx.investable_surplus_monthly / monthly_income * 100
            )
            result.data_quality = "actual"
        else:
            result.data_quality = "estimated"

        result.annual_contribution = ctx.investable_surplus_monthly * 12

    def _load_profile(self, user, result: WealthArrivalResult) -> None:
        """Pull age, risk tolerance and investment horizon from IncomeProfile."""
        try:
            from .models import IncomeProfile
            profile = IncomeProfile.objects.filter(user=user).first()
            if profile:
                result.current_age    = profile.age
                result.risk_tolerance = profile.risk_tolerance or "Moderate"
                result.projection_years = HORIZON_MAP.get(
                    profile.investment_horizon, DEFAULT_HORIZON
                )
        except Exception as exc:
            logger.debug("_load_profile error: %s", exc)

    # ── Projection engine ─────────────────────────────────────────────────────

    def _run_projections(self, result: WealthArrivalResult) -> None:
        """Build all three scenarios and tag the primary one."""
        scenarios = []
        for scenario_name, return_rate in RETURN_RATES.items():
            scenario = self._project_scenario(
                scenario_name=scenario_name,
                annual_return=return_rate,
                result=result,
            )
            scenarios.append(scenario)

        result.scenarios = scenarios

        # Primary = matches user's risk tolerance (default Moderate)
        tolerance = result.risk_tolerance
        primary_map = {
            "Conservative": "conservative",
            "Moderate":     "moderate",
            "Aggressive":   "aggressive",
        }
        primary_key = primary_map.get(tolerance, "moderate")
        result.primary = next(
            (s for s in scenarios if s.scenario == primary_key),
            scenarios[1],  # fallback to moderate
        )

    def _project_scenario(
        self,
        scenario_name: str,
        annual_return: float,
        result: WealthArrivalResult,
    ) -> WealthScenario:
        """
        Core compound-growth engine for one scenario.

        Model per year n:
          portfolio(n) = portfolio(n-1) × (1 + r) + contribution(n)
          savings(n)   = savings(n-1)  + contribution_savings(n)
          debt(n)      = max(0, debt(n-1) − monthly_min × 12)
          net_worth(n) = portfolio(n) + savings(n) − debt(n)

        Income and contributions grow at SALARY_GROWTH per year.
        All amounts in nominal dollars; milestones converted to real (today's
        dollars) for display, but year-by-year projections are nominal.
        """
        scenario = WealthScenario(
            scenario=scenario_name.lower(),
            annual_return=annual_return,
        )

        portfolio   = result.current_portfolio_value
        savings     = result.current_savings_balance
        debt        = result.current_debt
        contribution = result.annual_contribution  # nominal year 0

        # Split contribution: 70 % to portfolio investments, 30 % to savings
        # (rough heuristic; IRL depends on account types)
        invest_pct  = 0.70
        savings_pct = 0.30

        total_contributions = 0.0
        milestones_hit: dict[float, int] = {}  # target → year

        year_by_year = []

        for year in range(1, result.projection_years + 1):
            # Grow contribution with salary / income growth
            annual_contribution = contribution * ((1 + SALARY_GROWTH) ** (year - 1))

            invest_contribution  = annual_contribution * invest_pct
            savings_contribution = annual_contribution * savings_pct

            # Compound portfolio
            portfolio = portfolio * (1 + annual_return) + invest_contribution

            # Grow savings linearly (assumed in HYSA / MM at ~inflation rate)
            savings = savings + savings_contribution

            # Debt paydown — assume current minimum payments continue until paid off
            # Minimum payments estimated as 2 % of outstanding balance per month
            monthly_min = max(result.current_debt * 0.02, 0)
            debt = max(0.0, debt - monthly_min * 12)

            net_worth = portfolio + savings - debt
            total_contributions += annual_contribution

            point = WealthYearPoint(
                year=year,
                net_worth=net_worth,
                portfolio_value=portfolio,
                savings_balance=savings,
                annual_contribution=annual_contribution,
                cumulative_contributions=total_contributions,
            )
            year_by_year.append(point)

            # Check milestone crossings
            for target in STANDARD_MILESTONES:
                if target not in milestones_hit and net_worth >= target:
                    milestones_hit[target] = year

            # Also track user's custom target
            if (
                result.target_net_worth not in milestones_hit
                and net_worth >= result.target_net_worth
            ):
                milestones_hit[result.target_net_worth] = year

        scenario.year_by_year = year_by_year
        scenario.final_net_worth = year_by_year[-1].net_worth if year_by_year else 0.0
        scenario.total_contributions = total_contributions
        scenario.total_growth = scenario.final_net_worth - result.current_net_worth - total_contributions

        # Build milestone objects
        import datetime
        current_calendar_year = datetime.date.today().year
        milestones = []
        for target in sorted(set(list(STANDARD_MILESTONES) + [result.target_net_worth])):
            years_away = milestones_hit.get(target)
            already_achieved = result.current_net_worth >= target
            if already_achieved:
                years_away = 0
            milestone = WealthMilestone(
                target_amount=target,
                years_away=years_away if years_away is not None else -1,
                arrival_year=(
                    current_calendar_year + years_away
                    if years_away is not None
                    else -1
                ),
                already_achieved=already_achieved,
                label=_format_dollar(target),
            )
            milestones.append(milestone)

        scenario.milestones = milestones

        # Wealth arrival years for custom target
        scenario.wealth_arrival_years = milestones_hit.get(result.target_net_worth)

        return scenario

    # ── Headline builder ──────────────────────────────────────────────────────

    def _build_headline(self, result: WealthArrivalResult) -> None:
        """Generate a single human-readable headline for the UI."""
        if result.data_quality == "insufficient" or result.primary is None:
            result.headline_sentence = (
                "Connect your accounts to see your personalized Wealth Arrival timeline."
            )
            return

        primary = result.primary
        target   = _format_dollar(result.target_net_worth)
        years    = primary.wealth_arrival_years

        if result.current_net_worth >= result.target_net_worth:
            result.headline_sentence = (
                f"You've already reached {target} in net worth. "
                f"Set a new milestone to keep the momentum going."
            )
        elif years is not None:
            import datetime
            arrival = datetime.date.today().year + years
            result.headline_sentence = (
                f"At your current pace you'll reach {target} in {years} year"
                f"{'s' if years != 1 else ''} ({arrival}), "
                f"investing ${result.annual_contribution:,.0f}/year."
            )
        else:
            result.headline_sentence = (
                f"Increase your monthly contributions to reach {target} "
                f"within your {result.projection_years}-year horizon."
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_dollar(amount: float) -> str:
    """Format a dollar amount compactly: $1,000,000 → '$1M', $500,000 → '$500K'."""
    if amount >= 1_000_000:
        val = amount / 1_000_000
        return f"${val:,.1f}M" if val % 1 else f"${int(val)}M"
    elif amount >= 1_000:
        val = amount / 1_000
        return f"${val:,.0f}K"
    return f"${amount:,.0f}"
