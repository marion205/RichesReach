"""
Financial Health Score Service
================================
Computes a composite 0–100 financial health score from four pillars:

  1. Savings Rate      — how much of income is being saved / invested
  2. Debt Ratio        — monthly debt service as % of income (lower = better)
  3. Emergency Fund    — months of expenses covered by liquid savings
  4. Credit Utilization— average utilization across credit cards (lower = better)

Each pillar produces:
  • a raw score  0–100
  • a letter grade  A / B / C / D / F
  • a one-sentence insight
  • a concrete next action

The composite score is a weighted average:
  Savings Rate       30 %
  Emergency Fund     30 %
  Debt Ratio         25 %
  Credit Utilization 15 %

Design notes
------------
- Delegates all data loading to FinancialGraphService.build_graph_safe().
  No duplicate ORM queries.
- Returns plain dataclasses — no Django model instances exposed.
- All methods are synchronous (called inside GraphQL resolver thread).
- project_safe() wraps project() in a broad exception handler.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Weights ───────────────────────────────────────────────────────────────────

WEIGHT_SAVINGS    = 0.30
WEIGHT_EMERGENCY  = 0.30
WEIGHT_DEBT       = 0.25
WEIGHT_CREDIT     = 0.15

# ── Pillar thresholds ────────────────────────────────────────────────────────
#   These align with widely-cited personal finance benchmarks.

# Savings rate %  →  pillar score
# ≥20 % = 100, ≥15 % = 80, ≥10 % = 60, ≥5 % = 40, <5 % = 20
SAVINGS_TIERS = [(20, 100), (15, 80), (10, 60), (5, 40), (0, 20)]

# Emergency fund months  →  pillar score
# ≥6 = 100, ≥3 = 75, ≥1 = 50, ≥0.5 = 25, <0.5 = 0
EMERGENCY_TIERS = [(6, 100), (3, 75), (1, 50), (0.5, 25), (0, 0)]

# Debt-to-income ratio %  →  pillar score (inverted: lower DTI = higher score)
# ≤10 % = 100, ≤20 % = 80, ≤30 % = 60, ≤40 % = 40, >40 % = 20
DEBT_TIERS = [(10, 100), (20, 80), (30, 60), (40, 40), (float('inf'), 20)]

# Credit utilization %  →  pillar score (inverted: lower = higher score)
# ≤10 % = 100, ≤30 % = 75, ≤50 % = 50, ≤75 % = 25, >75 % = 0
CREDIT_TIERS = [(10, 100), (30, 75), (50, 50), (75, 25), (float('inf'), 0)]


def _letter(score: float) -> str:
    if score >= 90: return 'A'
    if score >= 80: return 'B'
    if score >= 70: return 'C'
    if score >= 55: return 'D'
    return 'F'


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class HealthPillar:
    """Result for a single scoring pillar."""
    name: str                      # "savings_rate" | "emergency_fund" | "debt_ratio" | "credit_utilization"
    label: str                     # Human-readable name
    score: float                   # 0–100
    grade: str                     # A / B / C / D / F
    value: Optional[float]         # The raw metric (savings_rate_pct, months, dti_pct, util_pct)
    unit: str                      # "%", "months", etc.
    insight: str                   # 1-sentence explanation of the score
    action: str                    # 1-sentence concrete next step
    weight: float                  # contribution weight in composite (0.0–1.0)


@dataclass
class FinancialHealthResult:
    """Composite financial health score for a user."""
    user_id: int

    # Composite
    score: float = 0.0             # 0–100 weighted average
    grade: str = 'F'
    headline_sentence: str = ""
    data_quality: str = "estimated"   # "actual" | "estimated" | "insufficient"

    # Pillars (populated even if data is partial)
    pillars: list = field(default_factory=list)   # list[HealthPillar]

    # Raw inputs (for UI display)
    savings_rate_pct: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_debt_service: float = 0.0
    debt_to_income_pct: Optional[float] = None
    emergency_fund_months: Optional[float] = None
    credit_utilization_pct: Optional[float] = None


# ── Service ───────────────────────────────────────────────────────────────────

class FinancialHealthService:
    """
    Computes a composite financial health score from FinancialGraphContext data.

    Typical call pattern
    --------------------
    On Health screen load:
        result = FinancialHealthService().score_safe(user)
    """

    def score(self, user) -> FinancialHealthResult:
        """
        Main entry point. Returns a FinancialHealthResult with composite score
        and four scored pillars.
        """
        from .financial_graph_service import FinancialGraphService
        ctx = FinancialGraphService().build_graph_safe(user)

        result = FinancialHealthResult(user_id=user.pk)

        if ctx is None:
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Connect your accounts to get your Financial Health Score."
            )
            return result

        # ── Derive inputs from graph context ──────────────────────────────────
        monthly_income = ctx.estimated_monthly_income or 0.0
        monthly_expenses = monthly_income * 0.80 if monthly_income > 0 else 0.0
        monthly_debt_service = ctx.total_cc_min_payments   # minimum payments proxy

        savings_rate_pct: Optional[float] = None
        if monthly_income > 0:
            investable = max(monthly_income * 0.20 - monthly_debt_service, 0)
            savings_rate_pct = (investable / monthly_income) * 100

        debt_to_income_pct: Optional[float] = None
        if monthly_income > 0:
            debt_to_income_pct = (monthly_debt_service / monthly_income) * 100

        emergency_months: Optional[float] = None
        if monthly_expenses > 0 and ctx.total_savings_balance > 0:
            emergency_months = ctx.total_savings_balance / monthly_expenses
        elif ctx.emergency_fund_months > 0:
            emergency_months = ctx.emergency_fund_months

        credit_util_pct: Optional[float] = None
        if ctx.avg_credit_utilization > 0:
            credit_util_pct = ctx.avg_credit_utilization * 100

        # Store raw inputs
        result.monthly_income = monthly_income if monthly_income > 0 else None
        result.monthly_debt_service = monthly_debt_service
        result.savings_rate_pct = savings_rate_pct
        result.debt_to_income_pct = debt_to_income_pct
        result.emergency_fund_months = emergency_months
        result.credit_utilization_pct = credit_util_pct

        # ── Score each pillar ─────────────────────────────────────────────────
        pillars = []

        pillars.append(self._score_savings_rate(savings_rate_pct, monthly_income))
        pillars.append(self._score_emergency_fund(emergency_months))
        pillars.append(self._score_debt_ratio(debt_to_income_pct))
        pillars.append(self._score_credit_utilization(credit_util_pct))

        result.pillars = pillars

        # ── Composite ─────────────────────────────────────────────────────────
        total_weight = sum(p.weight for p in pillars)
        if total_weight > 0:
            result.score = sum(p.score * p.weight for p in pillars) / total_weight
        result.grade = _letter(result.score)

        result.data_quality = (
            "actual" if (
                savings_rate_pct is not None
                and emergency_months is not None
                and debt_to_income_pct is not None
                and credit_util_pct is not None
            ) else "estimated"
        )

        self._build_headline(result)
        return result

    def score_safe(self, user) -> FinancialHealthResult:
        """Wraps score() — never raises, returns insufficient result on error."""
        try:
            return self.score(user)
        except Exception as exc:
            logger.warning("FinancialHealthService.score error for user %s: %s",
                           getattr(user, 'pk', '?'), exc)
            r = FinancialHealthResult(user_id=getattr(user, 'pk', 0))
            r.data_quality = "insufficient"
            r.headline_sentence = "Financial health score temporarily unavailable."
            return r

    # ── Pillar scorers ────────────────────────────────────────────────────────

    def _score_savings_rate(
        self, savings_rate_pct: Optional[float], monthly_income: float
    ) -> HealthPillar:
        if savings_rate_pct is None:
            return HealthPillar(
                name='savings_rate', label='Savings Rate',
                score=50, grade='D', value=None, unit='%',
                insight="We couldn't determine your savings rate yet.",
                action="Link your bank accounts for a personalised savings rate.",
                weight=WEIGHT_SAVINGS,
            )

        score = _tier_score(savings_rate_pct, SAVINGS_TIERS)
        grade = _letter(score)
        sr = savings_rate_pct

        if sr >= 20:
            insight = f"You're saving {sr:.0f}% of income — excellent discipline."
            action = "Consider maxing out tax-advantaged accounts (IRA, 401k)."
        elif sr >= 15:
            insight = f"A {sr:.0f}% savings rate is solid. You're ahead of most people."
            action = f"Push to 20% by trimming ${monthly_income * 0.05:,.0f}/month in discretionary spending."
        elif sr >= 10:
            insight = f"Saving {sr:.0f}% is a good start but leaves room to grow."
            action = "Set up an automatic transfer of an extra 2–3% on payday."
        elif sr >= 5:
            insight = f"A {sr:.0f}% savings rate puts you at risk of falling behind inflation."
            action = "Identify one recurring expense to cut and redirect that amount to savings."
        else:
            insight = f"Saving only {sr:.0f}% makes it very hard to build lasting wealth."
            action = "Start with $50/week automated savings — even small amounts compound."

        return HealthPillar(
            name='savings_rate', label='Savings Rate',
            score=score, grade=grade, value=sr, unit='%',
            insight=insight, action=action, weight=WEIGHT_SAVINGS,
        )

    def _score_emergency_fund(self, months: Optional[float]) -> HealthPillar:
        if months is None:
            return HealthPillar(
                name='emergency_fund', label='Emergency Fund',
                score=25, grade='F', value=None, unit='months',
                insight="No emergency fund data found.",
                action="Open a high-yield savings account and target 1 month of expenses first.",
                weight=WEIGHT_EMERGENCY,
            )

        score = _tier_score(months, EMERGENCY_TIERS)
        grade = _letter(score)

        if months >= 6:
            insight = f"Your {months:.1f}-month emergency fund is excellent."
            action = "Put any excess beyond 6 months into investments for higher returns."
        elif months >= 3:
            insight = f"{months:.1f} months of expenses covered — you're on solid ground."
            action = "Keep building towards 6 months for full security."
        elif months >= 1:
            insight = f"Only {months:.1f} months covered — you're vulnerable to unexpected costs."
            action = "Aim to add 1 month of expenses to your savings in the next 90 days."
        else:
            insight = f"Less than 1 month of expenses saved — high financial fragility."
            action = "Pause extra debt payments and build a $1,000 starter emergency fund first."

        return HealthPillar(
            name='emergency_fund', label='Emergency Fund',
            score=score, grade=grade, value=months, unit='months',
            insight=insight, action=action, weight=WEIGHT_EMERGENCY,
        )

    def _score_debt_ratio(self, dti_pct: Optional[float]) -> HealthPillar:
        if dti_pct is None:
            return HealthPillar(
                name='debt_ratio', label='Debt-to-Income',
                score=75, grade='C', value=None, unit='%',
                insight="No debt data found — assuming minimal debt.",
                action="Connect credit card accounts to get an accurate debt ratio.",
                weight=WEIGHT_DEBT,
            )

        score = _tier_score(dti_pct, DEBT_TIERS)
        grade = _letter(score)

        if dti_pct <= 10:
            insight = f"Debt payments at {dti_pct:.0f}% of income — exceptional."
            action = "Maintain current habits. You have maximum flexibility to invest."
        elif dti_pct <= 20:
            insight = f"A {dti_pct:.0f}% debt-to-income ratio is manageable."
            action = "Tackle the highest-rate balance first to accelerate payoff."
        elif dti_pct <= 30:
            insight = f"At {dti_pct:.0f}% DTI, debt is squeezing your investable surplus."
            action = "Make one extra payment per month on your highest-rate card."
        elif dti_pct <= 40:
            insight = f"A {dti_pct:.0f}% DTI is straining your finances."
            action = "Explore a balance transfer or debt consolidation to lower your rate."
        else:
            insight = f"Debt payments at {dti_pct:.0f}% of income — critical level."
            action = "Contact a non-profit credit counsellor about a debt management plan."

        return HealthPillar(
            name='debt_ratio', label='Debt-to-Income',
            score=score, grade=grade, value=dti_pct, unit='%',
            insight=insight, action=action, weight=WEIGHT_DEBT,
        )

    def _score_credit_utilization(self, util_pct: Optional[float]) -> HealthPillar:
        if util_pct is None:
            return HealthPillar(
                name='credit_utilization', label='Credit Utilization',
                score=75, grade='C', value=None, unit='%',
                insight="No credit card data found.",
                action="Connect your credit cards to track utilization.",
                weight=WEIGHT_CREDIT,
            )

        score = _tier_score(util_pct, CREDIT_TIERS)
        grade = _letter(score)

        if util_pct <= 10:
            insight = f"{util_pct:.0f}% utilization — excellent for your credit score."
            action = "Keep utilization below 10% to maintain top-tier borrowing rates."
        elif util_pct <= 30:
            insight = f"{util_pct:.0f}% utilization is good; under 10% is ideal."
            action = "Pay down the card closest to its limit to drop your overall utilization."
        elif util_pct <= 50:
            insight = f"{util_pct:.0f}% utilization is hurting your credit score."
            action = "Pay down balances before the monthly statement closing date."
        elif util_pct <= 75:
            insight = f"{util_pct:.0f}% utilization signals financial stress to lenders."
            action = "Request a credit limit increase while paying down balances."
        else:
            insight = f"At {util_pct:.0f}% utilization, your borrowing power is severely limited."
            action = "Stop new charges on maxed cards and make more than the minimum payment."

        return HealthPillar(
            name='credit_utilization', label='Credit Utilization',
            score=score, grade=grade, value=util_pct, unit='%',
            insight=insight, action=action, weight=WEIGHT_CREDIT,
        )

    # ── Headline ──────────────────────────────────────────────────────────────

    def _build_headline(self, result: FinancialHealthResult) -> None:
        score = result.score
        grade = result.grade

        if score >= 90:
            quality = "excellent"
        elif score >= 80:
            quality = "strong"
        elif score >= 70:
            quality = "good"
        elif score >= 55:
            quality = "fair"
        else:
            quality = "needs attention"

        result.headline_sentence = (
            f"Your financial health is {quality} — {score:.0f}/100 (Grade {grade})."
        )

        # Append the weakest pillar's action as a nudge
        if result.pillars:
            worst = min(result.pillars, key=lambda p: p.score)
            if worst.score < 75:
                result.headline_sentence += f" Priority: {worst.action}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tier_score(value: float, tiers: list) -> float:
    """
    Walk through (threshold, score) pairs and return the matching score.

    Two tier conventions are supported:

    "Higher is better" (savings rate, emergency fund):
        Tiers are listed highest-threshold-first.  Each entry means
        "if value >= threshold, return this score."
        Example: SAVINGS_TIERS = [(20, 100), (15, 80), (10, 60), (5, 40), (0, 20)]
        → value=17 matches the (15, 80) tier → returns 80.

    "Lower is better" (debt ratio, credit utilization):
        Tiers are listed lowest-threshold-first with float('inf') as the final
        catch-all.  Each entry means "if value <= threshold, return this score."
        Example: DEBT_TIERS = [(10, 100), (20, 80), (30, 60), (40, 40), (inf, 20)]
        → value=25 is not <= 10, not <= 20, is <= 30 → returns 60.

    Detection: if the first threshold is larger than the last (ignoring inf),
    we are in "higher is better" mode.
    """
    # Filter out inf to detect direction
    finite = [t for t in tiers if t[0] != float('inf')]
    higher_is_better = len(finite) > 1 and finite[0][0] > finite[-1][0]

    if higher_is_better:
        # Walk descending list; return score of first threshold the value meets
        for minimum, s in tiers:
            if value >= minimum:
                return float(s)
        return float(tiers[-1][1])
    else:
        # Lower is better; return score of first threshold the value is at or under
        for maximum, s in tiers:
            if value <= maximum:
                return float(s)
        return float(tiers[-1][1])
