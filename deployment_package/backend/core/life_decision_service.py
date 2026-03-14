"""
Life Decision Simulator
=======================
Answers the question: "What does this financial decision cost my future self?"

Given a proposed purchase or expense, the simulator computes:
  • Immediate cash impact  — how the balance sheet changes on day 1
  • Wealth delta          — difference in net worth N years from now vs not buying
  • Opportunity cost      — what that money would have grown to if invested instead
  • Monthly cash-flow hit — how it affects investable surplus each month
  • Break-even check      — for asset purchases (car, home) that may appreciate

Supported decision types
------------------------
  "purchase"   — one-off buy (car, boat, furniture, gadget)
  "monthly"    — recurring commitment (subscription, gym, lease payment)
  "debt"       — financing a purchase (loan with interest rate + term)
  "investment" — buying an asset expected to appreciate (home, rental)

Design notes
------------
- Reuses FinancialGraphService for baseline financial context.
- Returns plain dataclasses — no ORM writes (read-only simulator).
- All math is deterministic: uses the user's risk_tolerance return rate
  from WealthArrivalService (Conservative 5%, Moderate 7%, Aggressive 9%).
- project_safe() never raises.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

RETURN_RATES = {
    'Conservative': 0.05,
    'Moderate':     0.07,
    'Aggressive':   0.09,
}
DEFAULT_RETURN = 0.07
DEFAULT_HORIZON = 10    # years

# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class DecisionYear:
    """Net-worth snapshot for one year under the 'with decision' scenario."""
    year: int
    net_worth_with: float      # projected net worth if decision is made
    net_worth_without: float   # projected net worth if decision is NOT made
    delta: float               # net_worth_with − net_worth_without


@dataclass
class LifeDecisionResult:
    """Full simulation output for one proposed decision."""
    user_id: int
    decision_type: str              # "purchase" | "monthly" | "debt" | "investment"
    description: str                # echoed back from input
    amount: float                   # total cost (or one-time amount)
    monthly_cost: float = 0.0       # recurring monthly hit to surplus

    # Key metrics
    opportunity_cost_10yr: float = 0.0    # what the money would be worth in 10yr if invested
    net_worth_delta_10yr: float = 0.0     # difference in NW at year 10
    monthly_surplus_impact: float = 0.0  # change in investable_surplus_monthly (negative = reduction)
    break_even_years: Optional[int] = None  # years until asset appreciation offsets cost (investment type)
    total_interest_paid: float = 0.0     # for debt type

    # Year-by-year trajectory
    year_by_year: list = field(default_factory=list)   # list[DecisionYear]

    # Context
    current_net_worth: float = 0.0
    investable_surplus_monthly: float = 0.0
    return_rate: float = DEFAULT_RETURN
    projection_years: int = DEFAULT_HORIZON

    # Output
    headline_sentence: str = ""
    recommendation: str = ""
    data_quality: str = "estimated"


# ── Service ───────────────────────────────────────────────────────────────────

class LifeDecisionService:
    """
    Simulates the long-term financial impact of a proposed life decision.

    Typical call pattern
    --------------------
        result = LifeDecisionService().simulate_safe(
            user,
            decision_type='purchase',
            amount=35_000,
            description='New car',
            monthly_cost=0,
            down_payment=5_000,
            loan_rate=0.065,
            loan_term_months=60,
            appreciation_rate=0.0,
        )
    """

    def simulate(
        self,
        user,
        *,
        decision_type: str = 'purchase',
        amount: float,
        description: str = '',
        monthly_cost: float = 0.0,
        down_payment: float = 0.0,
        loan_rate: float = 0.0,
        loan_term_months: int = 0,
        appreciation_rate: float = 0.0,
        horizon_years: int = DEFAULT_HORIZON,
    ) -> LifeDecisionResult:
        """
        Main entry point. Returns a LifeDecisionResult.

        Parameters
        ----------
        decision_type       : "purchase" | "monthly" | "debt" | "investment"
        amount              : total cost (purchase price or total subscription cost)
        description         : human label, echoed back
        monthly_cost        : additional monthly outgoing (lease, subscription)
        down_payment        : cash paid upfront for debt/investment decisions
        loan_rate           : annual interest rate as decimal (e.g. 0.065 for 6.5%)
        loan_term_months    : loan repayment term
        appreciation_rate   : annual appreciation (e.g. 0.03 for real estate)
        horizon_years       : projection window (default 10)
        """
        from .financial_graph_service import FinancialGraphService
        ctx = FinancialGraphService().build_graph_safe(user)

        result = LifeDecisionResult(
            user_id=user.pk,
            decision_type=decision_type,
            description=description or decision_type,
            amount=amount,
            projection_years=horizon_years,
        )

        # ── Baseline ──────────────────────────────────────────────────────────
        if ctx is not None:
            result.current_net_worth = (
                ctx.portfolio_total_value
                + ctx.total_savings_balance
                - ctx.total_cc_balance
            )
            result.investable_surplus_monthly = ctx.investable_surplus_monthly

            # Determine return rate from IncomeProfile.risk_tolerance
            return_rate = self._get_return_rate(user)
            result.return_rate = return_rate
            result.data_quality = "actual"
        else:
            result.return_rate = DEFAULT_RETURN
            result.data_quality = "estimated"

        # ── Compute decision-specific cash flows ──────────────────────────────
        if decision_type == 'purchase':
            self._simulate_purchase(result, amount, monthly_cost)
        elif decision_type == 'monthly':
            self._simulate_monthly(result, monthly_cost if monthly_cost else amount)
        elif decision_type == 'debt':
            self._simulate_debt(result, amount, down_payment, loan_rate, loan_term_months)
        elif decision_type == 'investment':
            self._simulate_investment(result, amount, down_payment, loan_rate,
                                      loan_term_months, appreciation_rate)
        else:
            # Default: treat as one-off purchase
            self._simulate_purchase(result, amount, monthly_cost)

        # ── Project year-by-year ──────────────────────────────────────────────
        self._build_trajectory(result)
        self._build_headline(result)
        return result

    def simulate_safe(self, user, **kwargs) -> LifeDecisionResult:
        """Wraps simulate() — never raises."""
        try:
            return self.simulate(user, **kwargs)
        except Exception as exc:
            logger.warning("LifeDecisionService.simulate error for user %s: %s",
                           getattr(user, 'pk', '?'), exc)
            amount = kwargs.get('amount', 0)
            r = LifeDecisionResult(
                user_id=getattr(user, 'pk', 0),
                decision_type=kwargs.get('decision_type', 'purchase'),
                description=kwargs.get('description', ''),
                amount=amount,
            )
            r.data_quality = 'insufficient'
            r.headline_sentence = "Decision simulation temporarily unavailable."
            return r

    # ── Decision type simulators ──────────────────────────────────────────────

    def _simulate_purchase(self, result: LifeDecisionResult, amount: float,
                           monthly_cost: float) -> None:
        """One-off cash purchase (e.g. car paid in full, new laptop)."""
        result.monthly_cost = monthly_cost
        # Opportunity cost: invest the lump sum instead
        result.opportunity_cost_10yr = _fv_lump_sum(amount, result.return_rate, result.projection_years)
        # Monthly surplus impact
        result.monthly_surplus_impact = -monthly_cost
        # Net worth delta: lost the asset value (assuming zero resale for simplicity),
        # plus ongoing monthly drag
        result.net_worth_delta_10yr = -(
            result.opportunity_cost_10yr
            + _fv_annuity(monthly_cost, result.return_rate, result.projection_years)
        )

    def _simulate_monthly(self, result: LifeDecisionResult, monthly_cost: float) -> None:
        """Recurring monthly commitment (subscription, gym, etc.)."""
        result.monthly_cost = monthly_cost
        result.monthly_surplus_impact = -monthly_cost
        annual_cost = monthly_cost * 12
        result.opportunity_cost_10yr = _fv_annuity(monthly_cost, result.return_rate,
                                                    result.projection_years)
        result.net_worth_delta_10yr = -result.opportunity_cost_10yr
        result.amount = annual_cost

    def _simulate_debt(self, result: LifeDecisionResult, amount: float, down_payment: float,
                       loan_rate: float, loan_term_months: int) -> None:
        """Financed purchase with a loan (car loan, personal loan)."""
        financed = amount - down_payment
        if loan_rate > 0 and loan_term_months > 0:
            monthly_rate = loan_rate / 12
            n = loan_term_months
            # Monthly payment: PMT formula
            monthly_payment = financed * (monthly_rate * (1 + monthly_rate) ** n) / \
                              ((1 + monthly_rate) ** n - 1)
            total_paid = monthly_payment * n + down_payment
            result.total_interest_paid = total_paid - amount
        else:
            monthly_payment = financed / max(loan_term_months, 1) if loan_term_months else 0
            result.total_interest_paid = 0.0

        result.monthly_cost = monthly_payment
        result.monthly_surplus_impact = -monthly_payment

        # Opportunity cost: invest down payment + monthly payments instead
        opp_down = _fv_lump_sum(down_payment, result.return_rate, result.projection_years)
        opp_monthly = _fv_annuity(monthly_payment, result.return_rate,
                                   result.projection_years)
        result.opportunity_cost_10yr = opp_down + opp_monthly
        result.net_worth_delta_10yr = -(result.opportunity_cost_10yr + result.total_interest_paid)

    def _simulate_investment(self, result: LifeDecisionResult, amount: float,
                             down_payment: float, loan_rate: float,
                             loan_term_months: int, appreciation_rate: float) -> None:
        """Asset purchase expected to appreciate (home, rental property)."""
        # First compute as debt
        self._simulate_debt(result, amount, down_payment, loan_rate, loan_term_months)

        # Then offset with projected asset appreciation
        years = result.projection_years
        appreciated_value = amount * ((1 + appreciation_rate) ** years)
        asset_gain = appreciated_value - amount

        result.net_worth_delta_10yr += asset_gain

        # Break-even: year when cumulative appreciation covers opportunity cost of down payment
        opp_cost_per_year = _fv_lump_sum(down_payment, result.return_rate, 1) - down_payment
        if appreciation_rate > 0 and opp_cost_per_year > 0:
            annual_gain = amount * appreciation_rate
            if annual_gain > opp_cost_per_year:
                result.break_even_years = 1
            else:
                # Solve: amount*((1+r)^n - 1) >= down_payment*((1+ret)^n - 1)
                for yr in range(1, 31):
                    asset_appreciation_yr = amount * ((1 + appreciation_rate) ** yr - 1)
                    opp_cost_yr = _fv_lump_sum(down_payment, result.return_rate, yr) - down_payment
                    if asset_appreciation_yr >= opp_cost_yr:
                        result.break_even_years = yr
                        break

    # ── Year-by-year trajectory ───────────────────────────────────────────────

    def _build_trajectory(self, result: LifeDecisionResult) -> None:
        """
        Build year-by-year (with decision) vs (without decision) net worth.
        Both start from current_net_worth.
        'Without': surplus stays at baseline, grows at return_rate.
        'With': surplus reduced by monthly_cost, lump-sum already removed.
        """
        base_nw = result.current_net_worth
        surplus = result.investable_surplus_monthly
        r = result.return_rate
        years = result.projection_years
        monthly_cost = result.monthly_cost

        # 'Without': invest full surplus each year
        # 'With': invest (surplus - monthly_cost) each year; also subtract lump-sum up-front
        lump_sum = 0.0
        if result.decision_type in ('purchase', 'debt', 'investment'):
            # The one-time cash out (down payment for debt/investment, full amount for purchase)
            if result.decision_type == 'purchase':
                lump_sum = result.amount if result.monthly_cost == 0 else 0
            elif result.decision_type in ('debt', 'investment'):
                # Down payment is already baked into monthly payment via _simulate_debt
                # Approximate: the amount taken from savings is amount - financed portion
                # We'll use total_interest_paid as a proxy for extra cost
                lump_sum = 0  # already captured in net_worth_delta

        points = []
        nw_without = base_nw
        nw_with = base_nw - lump_sum  # cash out on day 1 for purchase
        if result.decision_type == 'purchase' and result.monthly_cost == 0:
            nw_with = base_nw - result.amount

        for yr in range(1, years + 1):
            annual_surplus_without = surplus * 12
            annual_surplus_with = max(surplus - monthly_cost, 0) * 12
            nw_without = (nw_without + annual_surplus_without) * (1 + r)
            nw_with    = (nw_with + annual_surplus_with) * (1 + r)
            delta = nw_with - nw_without
            points.append(DecisionYear(year=yr, net_worth_with=nw_with,
                                       net_worth_without=nw_without, delta=delta))

        result.year_by_year = points
        # Overwrite delta_10yr with actual trajectory result for accuracy
        if points:
            last = points[-1]
            result.net_worth_delta_10yr = last.delta

    # ── Headline ──────────────────────────────────────────────────────────────

    def _build_headline(self, result: LifeDecisionResult) -> None:
        desc = result.description or "this decision"
        horizon = result.projection_years
        delta = result.net_worth_delta_10yr
        opp = result.opportunity_cost_10yr

        if abs(delta) < 1:
            result.headline_sentence = f"'{desc}' has a negligible long-term wealth impact."
            result.recommendation = "Proceed if it adds meaningful value to your life."
            return

        direction = "lower" if delta < 0 else "higher"
        result.headline_sentence = (
            f"'{desc}' will leave your net worth ${abs(delta):,.0f} {direction} "
            f"in {horizon} years compared to not making this decision."
        )

        if result.monthly_cost > 0:
            result.headline_sentence += (
                f" It reduces your monthly investable surplus by ${result.monthly_cost:,.0f}."
            )

        if result.total_interest_paid > 0:
            result.headline_sentence += (
                f" You'll pay ${result.total_interest_paid:,.0f} in interest."
            )

        # Recommendation
        surplus = result.investable_surplus_monthly
        if surplus > 0 and result.monthly_cost > surplus * 0.30:
            result.recommendation = (
                f"Caution: this takes up {result.monthly_cost/surplus*100:.0f}% of your "
                f"investable surplus. Consider waiting until your income grows."
            )
        elif delta < -50_000:
            result.recommendation = (
                f"This is a significant wealth impact. The ${opp:,.0f} opportunity cost "
                f"over {horizon} years is worth considering before committing."
            )
        elif result.break_even_years is not None:
            result.recommendation = (
                f"The asset appreciation breaks even with your investment opportunity "
                f"cost in approximately {result.break_even_years} years."
            )
        elif abs(delta) < 10_000:
            result.recommendation = (
                "The wealth impact is modest. If it improves your quality of life, "
                "it's likely worth it."
            )
        else:
            result.recommendation = (
                "Review your budget to ensure this fits within your financial plan."
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_return_rate(user) -> float:
        """Read risk_tolerance from IncomeProfile; fallback to 7%."""
        try:
            from .models import IncomeProfile
            profile = IncomeProfile.objects.filter(user=user).first()
            if profile and profile.risk_tolerance:
                return RETURN_RATES.get(profile.risk_tolerance, DEFAULT_RETURN)
        except Exception:
            pass
        return DEFAULT_RETURN


# ── Math helpers ──────────────────────────────────────────────────────────────

def _fv_lump_sum(pv: float, annual_rate: float, years: int) -> float:
    """Future value of a lump sum: PV × (1 + r)^n"""
    if years <= 0 or pv <= 0:
        return pv
    return pv * ((1 + annual_rate) ** years)


def _fv_annuity(monthly_payment: float, annual_rate: float, years: int) -> float:
    """Future value of a monthly annuity paid at end of period."""
    if years <= 0 or monthly_payment <= 0:
        return 0.0
    r = annual_rate / 12
    n = years * 12
    if r == 0:
        return monthly_payment * n
    return monthly_payment * (((1 + r) ** n - 1) / r)
