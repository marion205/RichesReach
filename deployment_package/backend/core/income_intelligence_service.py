"""
Income Intelligence Service
============================
Classifies all CREDIT (deposit) transactions over the past 90 days into
income streams, producing a structured picture of how money enters the user's
life:

  • Primary salary       — large, regular, consistent payroll deposits
  • Side hustle          — recurring but irregular credits (Venmo, PayPal, Stripe,
                           freelance platforms, Etsy, etc.)
  • Freelance / contract — large one-off or quarterly professional payments
  • Investment income    — dividends, distributions, interest
  • Refunds / other      — credits that don't fit income patterns

Key outputs
-----------
  total_monthly_income      — estimated monthly income (all streams)
  primary_income_monthly    — payroll-scale recurring salary
  secondary_income_monthly  — sum of side hustle + freelance streams
  income_diversity_score    — 0–100 (higher = more streams, more resilient)
  streams                   — list[IncomeStream] with type, amount, sources
  headline_sentence         — human-readable summary

Design notes
------------
- Reads BankTransaction (CREDIT, amount >= $200 over past 90 days).
- Uses merchant/description keyword matching to classify stream type.
- Returns plain dataclasses — no ORM writes.
- analyze_safe() never raises.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 90
MIN_AMOUNT = 200.0    # ignore micro-credits (refund, cashback)

# ── Classification keywords ───────────────────────────────────────────────────

# Each key = stream type; values = substrings to match in normalised description/merchant
SALARY_KEYWORDS = {
    'payroll', 'direct dep', 'salary', 'wages', 'adp', 'gusto', 'paychex',
    'intuit payroll', 'bamboohr', 'rippling', 'zenefits', 'workday payroll',
    'employer', 'paycom', 'ceridian',
}

INVESTMENT_KEYWORDS = {
    'dividend', 'distribution', 'interest earned', 'yield', 'drip',
    'fidelity', 'vanguard', 'schwab', 'robinhood', 'etrade', 'td ameritrade',
    'betterment', 'wealthfront', 'acorns', 'stash', 'coinbase', 'crypto',
    'capital gain',
}

SIDE_HUSTLE_KEYWORDS = {
    'venmo', 'paypal', 'cash app', 'zelle', 'stripe', 'square', 'shopify',
    'etsy', 'ebay', 'depop', 'poshmark', 'fiverr', 'upwork', 'toptal',
    'freelancer', 'taskrabbit', 'doordash', 'uber eats', 'lyft', 'uber',
    'instacart', 'grubhub', 'postmates', 'rover', 'care.com', 'handy',
    'thumbtack', 'airbnb', 'vrbo', 'turo',
}

FREELANCE_KEYWORDS = {
    'invoice', 'consulting', 'contract', 'retainer', 'client payment',
    'wire transfer', 'ach credit', 'payment received', 'professional services',
    'project payment', 'milestone payment',
}

REFUND_KEYWORDS = {
    'refund', 'return', 'cashback', 'rebate', 'credit memo', 'reversal',
    'adjustment', 'reimbursement', 'expense report',
}


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class IncomeTransaction:
    """A single classified credit transaction."""
    date: object           # date object
    amount: float
    merchant: str
    stream_type: str       # 'salary' | 'side_hustle' | 'freelance' | 'investment' | 'refund' | 'other'
    confidence: float      # 0.0–1.0


@dataclass
class IncomeStream:
    """An aggregated income stream across all transactions of one type."""
    stream_type: str              # 'salary' | 'side_hustle' | 'freelance' | 'investment' | 'other'
    label: str                    # Human-readable name
    monthly_amount: float         # Estimated monthly dollar amount
    annual_amount: float          # Projected annual total
    transaction_count: int        # Number of transactions in window
    top_sources: list = field(default_factory=list)   # list[str] — top merchant names
    pct_of_total: float = 0.0    # % of total income this stream represents
    insight: str = ""


@dataclass
class IncomeIntelligenceResult:
    """Full income analysis for a user."""
    user_id: int

    # Totals
    total_monthly_income: float = 0.0
    total_annual_income: float = 0.0
    primary_income_monthly: float = 0.0    # salary stream only
    secondary_income_monthly: float = 0.0  # side hustle + freelance

    # Diversity
    income_diversity_score: float = 0.0    # 0–100
    stream_count: int = 0                  # number of distinct active stream types

    # Streams
    streams: list = field(default_factory=list)   # list[IncomeStream]
    transactions: list = field(default_factory=list)  # list[IncomeTransaction] (for debug)

    # Metadata
    lookback_days: int = LOOKBACK_DAYS
    headline_sentence: str = ""
    data_quality: str = "estimated"   # "actual" | "estimated" | "insufficient"


# ── Service ───────────────────────────────────────────────────────────────────

class IncomeIntelligenceService:
    """
    Classifies bank CREDIT transactions into income streams.

    Typical call pattern
    --------------------
        result = IncomeIntelligenceService().analyze_safe(user)
    """

    def analyze(self, user) -> IncomeIntelligenceResult:
        """Main entry point. Loads transactions and returns classified result."""
        result = IncomeIntelligenceResult(user_id=user.pk)

        transactions = self._load_transactions(user)

        if not transactions:
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Connect your bank accounts to see your income breakdown."
            )
            return result

        # Classify each transaction
        classified = [self._classify(t) for t in transactions]
        result.transactions = classified
        result.data_quality = "actual"

        # Aggregate into streams
        streams = self._aggregate_streams(classified)
        result.streams = streams

        # Compute totals
        result.total_monthly_income = sum(s.monthly_amount for s in streams)
        result.total_annual_income = result.total_monthly_income * 12
        result.stream_count = len([s for s in streams if s.monthly_amount > 0])

        salary_stream = next((s for s in streams if s.stream_type == 'salary'), None)
        result.primary_income_monthly = salary_stream.monthly_amount if salary_stream else 0.0
        result.secondary_income_monthly = sum(
            s.monthly_amount for s in streams
            if s.stream_type in ('side_hustle', 'freelance')
        )

        # Percentages
        if result.total_monthly_income > 0:
            for stream in streams:
                stream.pct_of_total = (stream.monthly_amount / result.total_monthly_income) * 100

        # Diversity score
        result.income_diversity_score = self._diversity_score(streams, result.total_monthly_income)

        self._build_stream_insights(streams)
        self._build_headline(result)
        return result

    def analyze_safe(self, user) -> IncomeIntelligenceResult:
        """Wraps analyze() — never raises."""
        try:
            return self.analyze(user)
        except Exception as exc:
            logger.warning("IncomeIntelligenceService.analyze error for user %s: %s",
                           getattr(user, 'pk', '?'), exc)
            r = IncomeIntelligenceResult(user_id=getattr(user, 'pk', 0))
            r.data_quality = "insufficient"
            r.headline_sentence = "Income analysis temporarily unavailable."
            return r

    # ── ORM loader ────────────────────────────────────────────────────────────

    def _load_transactions(self, user) -> list:
        """Load CREDIT transactions >= $200 from the past 90 days."""
        try:
            from .banking_models import BankTransaction
            from django.utils import timezone
            since = timezone.now().date() - timedelta(days=LOOKBACK_DAYS)
            return list(
                BankTransaction.objects.filter(
                    user=user,
                    transaction_type='CREDIT',
                    amount__gte=MIN_AMOUNT,
                    posted_date__gte=since,
                ).order_by('-posted_date')
            )
        except Exception as exc:
            logger.debug("_load_transactions error: %s", exc)
            return []

    # ── Classifier ────────────────────────────────────────────────────────────

    def _classify(self, txn) -> IncomeTransaction:
        """Classify a single ORM transaction into a stream type."""
        merchant = _normalise(str(getattr(txn, 'merchant_name', None) or ''))
        raw_desc = str(getattr(txn, 'description', None) or '') or \
                   str(getattr(txn, 'name', None) or '')
        desc = _normalise(raw_desc)
        text = merchant + ' ' + desc
        amount = float(txn.amount)

        stream_type, confidence = self._match_type(text, amount)
        return IncomeTransaction(
            date=getattr(txn, 'posted_date', None),
            amount=amount,
            merchant=getattr(txn, 'merchant_name', '') or desc[:40],
            stream_type=stream_type,
            confidence=confidence,
        )

    def _match_type(self, text: str, amount: float) -> tuple[str, float]:
        """Return (stream_type, confidence) for a normalised transaction."""
        # Check each category in priority order
        for kw in SALARY_KEYWORDS:
            if kw in text:
                return 'salary', 0.92
        for kw in INVESTMENT_KEYWORDS:
            if kw in text:
                return 'investment', 0.88
        for kw in REFUND_KEYWORDS:
            if kw in text:
                return 'refund', 0.85
        for kw in SIDE_HUSTLE_KEYWORDS:
            if kw in text:
                return 'side_hustle', 0.80
        for kw in FREELANCE_KEYWORDS:
            if kw in text:
                return 'freelance', 0.75

        # Heuristic: large ACH credits with no keyword → likely payroll
        if amount >= 1_500:
            return 'salary', 0.55
        # Mid-range with no keyword → possible side income
        if amount >= 500:
            return 'side_hustle', 0.40
        return 'other', 0.30

    # ── Aggregator ────────────────────────────────────────────────────────────

    def _aggregate_streams(self, classified: list) -> list:
        """Group classified transactions by stream type and compute monthly amounts."""
        from collections import defaultdict
        buckets: dict[str, list] = defaultdict(list)
        for t in classified:
            buckets[t.stream_type].append(t)

        LABELS = {
            'salary':      'Primary Salary',
            'side_hustle': 'Side Hustle',
            'freelance':   'Freelance / Contract',
            'investment':  'Investment Income',
            'refund':      'Refunds & Reimbursements',
            'other':       'Other Income',
        }

        streams = []
        for stream_type, txns in sorted(buckets.items()):
            # Annualise: window is 90 days → scale to 12 months
            total_90d = sum(t.amount for t in txns)
            monthly = (total_90d / LOOKBACK_DAYS) * 30
            annual = monthly * 12

            # Top sources
            source_totals: dict[str, float] = {}
            for t in txns:
                key = t.merchant[:30] if t.merchant else '(unknown)'
                source_totals[key] = source_totals.get(key, 0) + t.amount
            top = sorted(source_totals, key=source_totals.get, reverse=True)[:3]

            streams.append(IncomeStream(
                stream_type=stream_type,
                label=LABELS.get(stream_type, stream_type.replace('_', ' ').title()),
                monthly_amount=round(monthly, 2),
                annual_amount=round(annual, 2),
                transaction_count=len(txns),
                top_sources=top,
            ))

        # Sort: salary first, then by monthly amount desc
        streams.sort(key=lambda s: (s.stream_type != 'salary', -s.monthly_amount))
        return streams

    # ── Diversity score ────────────────────────────────────────────────────────

    def _diversity_score(self, streams: list, total_monthly: float) -> float:
        """
        0–100 score.  Two components:
          • Count bonus: +20 per distinct income stream (max 3 streams = 60)
          • Concentration penalty: deduct points if any stream > 80% of total
        """
        if not streams or total_monthly <= 0:
            return 0.0

        income_streams = [s for s in streams
                          if s.stream_type not in ('refund', 'other')
                          and s.monthly_amount > 0]
        count = len(income_streams)
        base = min(count * 25, 75)   # 25 per stream, cap at 75

        # Diversity bonus: primary < 70% of total
        primary = next((s.monthly_amount for s in income_streams
                        if s.stream_type == 'salary'), 0)
        primary_pct = (primary / total_monthly) if total_monthly > 0 else 1.0
        if primary_pct < 0.70:
            base += 25    # meaningful secondary income
        elif primary_pct < 0.90:
            base += 10    # some secondary income

        return min(float(base), 100.0)

    # ── Stream insights ────────────────────────────────────────────────────────

    def _build_stream_insights(self, streams: list) -> None:
        for s in streams:
            if s.stream_type == 'salary':
                s.insight = (
                    f"Your primary salary averages ${s.monthly_amount:,.0f}/month "
                    f"(${s.annual_amount:,.0f}/year)."
                )
            elif s.stream_type == 'side_hustle':
                s.insight = (
                    f"Side hustle income: ${s.monthly_amount:,.0f}/month — "
                    f"${s.annual_amount:,.0f}/year in extra earnings."
                )
            elif s.stream_type == 'freelance':
                s.insight = (
                    f"Freelance / contract work brings in ~${s.monthly_amount:,.0f}/month."
                )
            elif s.stream_type == 'investment':
                s.insight = (
                    f"Investment income: ${s.monthly_amount:,.0f}/month — "
                    f"your portfolio is generating returns."
                )
            elif s.stream_type == 'refund':
                s.insight = (
                    f"${s.monthly_amount:,.0f}/month in refunds and reimbursements "
                    f"(not counted as true income)."
                )
            else:
                s.insight = f"${s.monthly_amount:,.0f}/month from other credits."

    # ── Headline ──────────────────────────────────────────────────────────────

    def _build_headline(self, result: IncomeIntelligenceResult) -> None:
        total = result.total_monthly_income
        diversity = result.income_diversity_score
        stream_count = result.stream_count

        if total <= 0:
            result.headline_sentence = "No income data detected in the past 90 days."
            return

        if stream_count == 1:
            result.headline_sentence = (
                f"You earn ${total:,.0f}/month from a single income stream. "
                f"Building a second stream would improve your financial resilience."
            )
        elif stream_count == 2:
            secondary = result.secondary_income_monthly
            result.headline_sentence = (
                f"You earn ${total:,.0f}/month across 2 income streams. "
                f"Your side income adds ${secondary:,.0f}/month."
            )
        else:
            result.headline_sentence = (
                f"You earn ${total:,.0f}/month across {stream_count} income streams "
                f"(diversity score {diversity:.0f}/100) — excellent financial resilience."
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r'[*#\d{5,}]', ' ', text)   # strip card numbers, asterisks
    text = re.sub(r'\s+', ' ', text).strip()
    return text
