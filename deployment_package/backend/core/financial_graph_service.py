"""
Financial Intelligence Graph Service
=====================================
Computes cross-silo financial relationships from existing Django ORM data.
No new DB models — queries BankAccount, CreditCard, CreditScore, Portfolio,
and IncomeProfile, then derives four relationship edges:

1. Debt → Investable Surplus
2. Emergency Fund → Risk Capacity
3. Credit Utilization → Borrowing Power
4. Income → Savings Rate → Wealth Velocity

Returns a FinancialGraphContext dataclass that is:
  - Serialized to GraphQL via financial_graph_types.py
  - Injected into the Oracle prompt in ai_insights_types.py
  - Used by OpportunityDiscoveryService to annotate curated deals
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class GraphEdge:
    """A computed relationship between two financial silos."""
    relationship_id: str        # e.g. "debt_to_investable_surplus"
    source_label: str           # e.g. "Credit Card Debt"
    target_label: str           # e.g. "Monthly Investable Surplus"
    explanation: str            # Human-readable sentence for Oracle + UI
    numeric_impact: Optional[float]
    unit: str                   # "$/month", "months covered", "% utilization", "$/year"
    direction: str              # "positive" | "negative" | "neutral"
    confidence: float           # 0.0–1.0


@dataclass
class FinancialGraphContext:
    """
    Full computed graph for a user. Immutable after build_graph() returns.
    Passed to the Oracle as structured context and to OpportunityDiscoveryService
    for graph-aware deal annotation.
    """
    user_id: int
    edges: list = field(default_factory=list)            # list[GraphEdge]
    summary_sentences: list = field(default_factory=list)  # list[str]

    # Raw silo snapshots (kept for Oracle prompt injection + opportunity matching)
    total_cc_balance: float = 0.0
    total_cc_min_payments: float = 0.0
    total_savings_balance: float = 0.0
    emergency_fund_months: float = 0.0
    avg_credit_utilization: float = 0.0
    best_credit_score: Optional[int] = None
    estimated_monthly_income: Optional[float] = None
    investable_surplus_monthly: float = 0.0
    portfolio_total_value: float = 0.0


# ── Service ───────────────────────────────────────────────────────────────────

class FinancialGraphService:
    """
    Computes cross-silo financial relationships from Django ORM data.
    All methods are synchronous (called inside GraphQL resolver thread).
    No writes — read-only.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def build_graph(self, user) -> FinancialGraphContext:
        """
        Main entry point. Fetches ORM data, computes all four graph edges,
        and returns a fully populated FinancialGraphContext.
        """
        ctx = FinancialGraphContext(user_id=user.pk)
        self._load_banking_data(user, ctx)
        self._load_credit_data(user, ctx)
        self._load_income_data(user, ctx)
        self._load_portfolio_data(user, ctx)

        self._compute_debt_to_investable_surplus(ctx)
        self._compute_emergency_fund_to_risk_capacity(ctx)
        self._compute_credit_utilization_to_borrowing_power(ctx)
        self._compute_income_savings_wealth_velocity(ctx)

        ctx.summary_sentences = [e.explanation for e in ctx.edges]
        return ctx

    def build_graph_safe(self, user) -> Optional[FinancialGraphContext]:
        """
        Wraps build_graph() in a broad exception handler.
        Returns None on any failure so callers can degrade gracefully.
        """
        try:
            return self.build_graph(user)
        except Exception as exc:
            logger.warning(
                "FinancialGraphService.build_graph failed for user %s: %s",
                getattr(user, 'pk', '?'), exc,
            )
            return None

    # ── ORM loaders ──────────────────────────────────────────────────────────

    def _load_banking_data(self, user, ctx: FinancialGraphContext) -> None:
        """
        Loads BankAccount balances and estimates monthly income from
        large CREDIT transactions over the past 90 days.
        """
        try:
            from .banking_models import BankAccount, BankTransaction
            from django.db.models import Sum
            from django.utils import timezone
            from datetime import timedelta

            accounts = BankAccount.objects.filter(user=user)
            savings_agg = accounts.filter(
                account_type__in=['SAVINGS', 'CHECKING']
            ).aggregate(total=Sum('balance_current'))
            ctx.total_savings_balance = float(savings_agg.get('total') or 0)

            # Estimate monthly income from average 90-day CREDIT inflows (payroll scale)
            ninety_days_ago = timezone.now().date() - timedelta(days=90)
            credit_agg = BankTransaction.objects.filter(
                user=user,
                transaction_type='CREDIT',
                posted_date__gte=ninety_days_ago,
                amount__gte=500,  # ignore small credits; focus on payroll-scale deposits
            ).aggregate(total=Sum('amount'))
            total_credits = float(credit_agg.get('total') or 0)
            if total_credits > 0:
                ctx.estimated_monthly_income = total_credits / 3.0
        except Exception as exc:
            logger.debug("_load_banking_data error: %s", exc)

    def _load_credit_data(self, user, ctx: FinancialGraphContext) -> None:
        """
        Loads CreditCard aggregates (total balance, minimum payments, utilization)
        and most-recent CreditScore.
        """
        try:
            from .credit_models import CreditCard, CreditScore
            from django.db.models import Sum

            cards = CreditCard.objects.filter(user=user)
            agg = cards.aggregate(
                total_balance=Sum('balance'),
                total_limit=Sum('limit'),
                total_min=Sum('minimum_payment'),
            )
            ctx.total_cc_balance = float(agg.get('total_balance') or 0)
            ctx.total_cc_min_payments = float(agg.get('total_min') or 0)
            total_limit = float(agg.get('total_limit') or 0)
            if total_limit > 0:
                ctx.avg_credit_utilization = ctx.total_cc_balance / total_limit

            score_record = CreditScore.objects.filter(user=user).order_by('-date').first()
            if score_record:
                ctx.best_credit_score = score_record.score
        except Exception as exc:
            logger.debug("_load_credit_data error: %s", exc)

    def _load_income_data(self, user, ctx: FinancialGraphContext) -> None:
        """
        Uses IncomeProfile.income_bracket to refine the income estimate
        if banking transactions didn't yield one.
        """
        try:
            from .models import IncomeProfile
            profile = IncomeProfile.objects.filter(user=user).first()
            if profile and ctx.estimated_monthly_income is None:
                annual = self._parse_income_bracket(profile.income_bracket)
                if annual:
                    ctx.estimated_monthly_income = annual / 12.0
        except Exception as exc:
            logger.debug("_load_income_data error: %s", exc)

    def _load_portfolio_data(self, user, ctx: FinancialGraphContext) -> None:
        """
        Sums Portfolio.total_value across all holdings.
        """
        try:
            from .models import Portfolio
            from django.db.models import Sum
            agg = Portfolio.objects.filter(user=user).aggregate(total=Sum('total_value'))
            ctx.portfolio_total_value = float(agg.get('total') or 0)
        except Exception as exc:
            logger.debug("_load_portfolio_data error: %s", exc)

    # ── Graph relationship computations ───────────────────────────────────────

    def _compute_debt_to_investable_surplus(self, ctx: FinancialGraphContext) -> None:
        """
        Relationship 1: Paying off card debt frees $X/month to invest.
        Impact = total minimum_payment across all credit cards.
        """
        if ctx.total_cc_min_payments <= 0:
            return

        ctx.edges.append(GraphEdge(
            relationship_id='debt_to_investable_surplus',
            source_label='Credit Card Debt',
            target_label='Monthly Investable Surplus',
            explanation=(
                f"Eliminating your ${ctx.total_cc_min_payments:,.0f}/month in minimum "
                f"payments would free that amount to invest each month."
            ),
            numeric_impact=ctx.total_cc_min_payments,
            unit='$/month',
            direction='positive',
            confidence=0.90,
        ))

        # Update investable surplus estimate
        monthly_income = ctx.estimated_monthly_income or 0
        ctx.investable_surplus_monthly = max(
            monthly_income * 0.20 - ctx.total_cc_min_payments, 0
        )

    def _compute_emergency_fund_to_risk_capacity(self, ctx: FinancialGraphContext) -> None:
        """
        Relationship 2: Savings buffer → investment risk capacity.
        Standard benchmark: 3–6 months of expenses = adequate emergency fund.
        Monthly expenses estimated as 80% of income (20% assumed savings rate).
        """
        monthly_income = ctx.estimated_monthly_income or 0
        monthly_expenses = monthly_income * 0.80
        if monthly_expenses <= 0 or ctx.total_savings_balance <= 0:
            return

        months = ctx.total_savings_balance / monthly_expenses
        ctx.emergency_fund_months = months

        if months >= 3:
            direction = 'positive'
            explanation = (
                f"Your ${ctx.total_savings_balance:,.0f} emergency fund covers "
                f"{months:.1f} months of expenses — enough to support moderate-to-high "
                f"risk investment positions."
            )
        else:
            direction = 'negative'
            explanation = (
                f"Your emergency fund covers only {months:.1f} months of expenses. "
                f"Building it to 3+ months before increasing investment risk is recommended."
            )

        ctx.edges.append(GraphEdge(
            relationship_id='emergency_fund_to_risk_capacity',
            source_label='Emergency Fund',
            target_label='Investment Risk Capacity',
            explanation=explanation,
            numeric_impact=months,
            unit='months covered',
            direction=direction,
            confidence=0.85,
        ))

    def _compute_credit_utilization_to_borrowing_power(self, ctx: FinancialGraphContext) -> None:
        """
        Relationship 3: Credit utilization → borrowing power & SBLOC eligibility.
        <10% = excellent (SBLOC-eligible), <30% = good, ≥30% = limiting.
        """
        if ctx.avg_credit_utilization <= 0:
            return

        pct = ctx.avg_credit_utilization * 100

        if pct < 10:
            direction = 'positive'
            explanation = (
                f"Your {pct:.0f}% credit utilization is excellent — you qualify for "
                f"the best interest rates and are SBLOC-eligible."
            )
        elif pct < 30:
            direction = 'positive'
            explanation = (
                f"Your {pct:.0f}% credit utilization is good. Reducing it below 10% "
                f"would unlock even better borrowing rates and SBLOC access."
            )
        else:
            direction = 'negative'
            explanation = (
                f"Your {pct:.0f}% credit utilization is limiting your borrowing power. "
                f"Reducing it below 30% could meaningfully improve loan rates."
            )

        ctx.edges.append(GraphEdge(
            relationship_id='credit_utilization_to_borrowing_power',
            source_label='Credit Utilization',
            target_label='Borrowing Power',
            explanation=explanation,
            numeric_impact=pct,
            unit='% utilization',
            direction=direction,
            confidence=0.80,
        ))

    def _compute_income_savings_wealth_velocity(self, ctx: FinancialGraphContext) -> None:
        """
        Relationship 4: Income → Savings Rate → Wealth Velocity.
        Wealth velocity = (portfolio_value × 7% expected return) + annual new contributions.
        Savings rate estimated at 20% of income minus debt service.
        """
        monthly_income = ctx.estimated_monthly_income
        if not monthly_income or monthly_income <= 0:
            return

        # Investable after debt service
        investable_monthly = max(monthly_income * 0.20 - ctx.total_cc_min_payments, 0)
        savings_rate_pct = (investable_monthly / monthly_income) * 100
        annual_contributions = investable_monthly * 12

        # Simplified wealth velocity: portfolio growth + new contributions
        portfolio_growth = ctx.portfolio_total_value * 0.07
        wealth_velocity = portfolio_growth + annual_contributions

        if wealth_velocity <= 0:
            return

        ctx.edges.append(GraphEdge(
            relationship_id='income_savings_wealth_velocity',
            source_label='Monthly Income',
            target_label='Annual Wealth Velocity',
            explanation=(
                f"At a {savings_rate_pct:.0f}% savings rate (${investable_monthly:,.0f}/month), "
                f"your estimated annual wealth velocity is ${wealth_velocity:,.0f} "
                f"(portfolio growth + new contributions)."
            ),
            numeric_impact=wealth_velocity,
            unit='$/year',
            direction='positive',
            confidence=0.75,
        ))

        # Keep investable surplus in sync if not already set
        if ctx.investable_surplus_monthly == 0:
            ctx.investable_surplus_monthly = investable_monthly

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_income_bracket(bracket: str) -> Optional[float]:
        """
        Converts an income_bracket string to an annual dollar midpoint.
        Handles formats: "100k-150k", "150k+", "$50,000-$75,000", "100000-150000"
        """
        if not bracket:
            return None
        bracket = bracket.lower().replace(',', '').replace('$', '').strip()
        # Find all numeric chunks (with optional 'k' suffix)
        tokens = re.findall(r'(\d+(?:\.\d+)?)(k?)', bracket)
        values = []
        for num_str, suffix in tokens:
            val = float(num_str)
            if suffix == 'k':
                val *= 1000
            values.append(val)

        if len(values) >= 2:
            return (values[0] + values[1]) / 2.0
        elif len(values) == 1:
            # "150k+" → use 110% of stated value as estimate
            return values[0] * 1.10
        return None
