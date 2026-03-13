"""
Subscription / Financial Leak Detector
=======================================
Scans a user's BankTransaction history to identify recurring charges —
subscriptions, memberships, and auto-renewals — that represent "leaks"
draining money that could otherwise be invested.

Algorithm overview
------------------
1. Pull all DEBIT transactions for the past LOOKBACK_DAYS (default 180 days).
2. Group by normalised merchant key (merchant_name → normalised, falling back
   to description prefix).
3. For each merchant group, look for a recurring-amount signature:
   - At least MIN_OCCURRENCES hits where the amount is within AMOUNT_TOLERANCE
     of the group median.
   - Interval between consecutive charges fits a known cadence bucket:
     weekly (~7 d), biweekly (~14 d), monthly (~30 d), quarterly (~90 d),
     semi-annual (~180 d), or annual (~365 d).
4. Compute per-subscription:
   - monthly_cost     : normalised to $/month regardless of cadence
   - confidence       : 0.0–1.0 (based on regularity and occurrence count)
   - category         : maps merchant → spending category (reuses CATEGORY_KEYWORDS)
   - is_likely_unused : flag if amount is small (≤$15) and cadence is monthly+
     AND the merchant is on the "easy-to-forget" list
5. Aggregate totals and produce a headline.

No DB writes.  Synchronous and read-only.

Key outputs (LeakDetectorResult)
---------------------------------
- subscriptions        : list[DetectedSubscription]
- total_monthly_leak   : sum of monthly_cost across all subscriptions
- total_annual_leak    : total_monthly_leak × 12
- likely_unused_monthly: sub-total for is_likely_unused subscriptions
- savings_impact_1yr   : if redirected to 7% portfolio: total_annual_leak × 1.07
- savings_impact_5yr   : compound value of that annual amount over 5 years
- top_leak             : the single most expensive subscription
- headline_sentence    : human-readable summary
- data_quality         : "actual" | "insufficient"
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median, stdev
from typing import Optional

logger = logging.getLogger(__name__)

# ── Tuning knobs ──────────────────────────────────────────────────────────────

LOOKBACK_DAYS      = 180   # ~6 months of history
MIN_OCCURRENCES    = 2     # need at least 2 hits to call it recurring
AMOUNT_TOLERANCE   = 0.10  # ±10% of median amount counts as "same charge"
MIN_AMOUNT         = 1.00  # ignore micro-transactions under $1

# Cadence buckets: (label, centre_days, tolerance_days)
CADENCES = [
    ("weekly",      7,   3),
    ("biweekly",   14,   4),
    ("monthly",    30,   8),
    ("quarterly",  91,  15),
    ("semi-annual",182,  20),
    ("annual",     365,  30),
]

# Merchants that are commonly forgotten / passive
EASILY_FORGOTTEN = {
    "audible", "amazon prime", "apple", "apple.com/bill", "icloud",
    "google", "google one", "google storage", "microsoft",
    "spotify", "netflix", "hulu", "disney", "disney+", "hbo",
    "paramount", "peacock", "sling", "fubo", "youtube premium",
    "dropbox", "box", "adobe", "canva", "grammarly", "notion",
    "duolingo", "headspace", "calm", "noom", "weight watchers",
    "linkedin", "indeed", "match", "tinder", "bumble",
    "new york times", "wsj", "washington post", "the atlantic",
    "gym", "planet fitness", "anytime fitness", "equinox",
    "amazon", "amazon.com",
}

# Category keywords (mirrors SpendingHabitsService for consistency)
CATEGORY_KEYWORDS = {
    "Streaming":      ["netflix", "hulu", "disney", "hbo", "paramount", "peacock",
                       "sling", "fubo", "youtube premium", "apple tv", "amazon prime video"],
    "Music":          ["spotify", "apple music", "tidal", "pandora", "amazon music"],
    "Cloud Storage":  ["icloud", "google one", "dropbox", "box", "onedrive"],
    "Software/Tools": ["adobe", "microsoft", "canva", "grammarly", "notion",
                       "1password", "lastpass", "zoom", "slack"],
    "News/Media":     ["new york times", "wsj", "washington post", "the atlantic",
                       "bloomberg", "economist", "medium"],
    "Health/Fitness": ["gym", "planet fitness", "anytime fitness", "equinox",
                       "peloton", "noom", "weight watchers", "headspace", "calm"],
    "Dating":         ["tinder", "bumble", "match", "hinge", "eharmony"],
    "Shopping/Prime": ["amazon prime", "amazon", "costco", "walmart+", "instacart"],
    "Gaming":         ["xbox", "playstation", "nintendo", "steam", "twitch"],
    "Productivity":   ["linkedin premium", "duolingo", "masterclass", "skillshare",
                       "coursera", "udemy"],
    "Tech/Apple":     ["apple", "apple.com/bill", "icloud", "apple music", "apple tv"],
    "Subscriptions":  ["subscription", "monthly", "annual", "membership"],
}


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class DetectedSubscription:
    """A single recurring charge pattern detected in transaction history."""
    merchant_key: str           # normalised merchant name
    display_name: str           # prettified for UI
    category: str               # e.g. "Streaming", "Cloud Storage"
    cadence: str                # "monthly", "annual", etc.
    cadence_days: int           # approximate interval in days
    typical_amount: float       # median charge amount
    monthly_cost: float         # normalised to $/month
    annual_cost: float          # monthly_cost × 12
    occurrences: int            # how many times seen in lookback window
    last_charged: date          # most recent transaction date
    first_charged: date         # oldest transaction date in window
    confidence: float           # 0.0–1.0
    is_likely_unused: bool      # small, passive, easy-to-forget
    transaction_dates: list = field(default_factory=list)  # list[date]


@dataclass
class LeakDetectorResult:
    """Full output from SubscriptionDetector.detect()."""
    user_id: int

    subscriptions: list = field(default_factory=list)  # list[DetectedSubscription]

    total_monthly_leak: float = 0.0
    total_annual_leak: float = 0.0
    likely_unused_monthly: float = 0.0
    likely_unused_annual: float = 0.0

    # Opportunity cost: what these dollars would be worth invested
    savings_impact_1yr: float = 0.0    # total_annual_leak × 1.07
    savings_impact_5yr: float = 0.0    # FV of annual_leak over 5 years at 7%

    top_leak: Optional[DetectedSubscription] = None
    subscription_count: int = 0
    likely_unused_count: int = 0

    headline_sentence: str = ""
    data_quality: str = "estimated"  # "actual" | "insufficient"


# ── Service ───────────────────────────────────────────────────────────────────

class SubscriptionDetector:
    """
    Detects recurring subscription charges in a user's transaction history.

    Usage:
        result = SubscriptionDetector().detect(user)
        result = SubscriptionDetector().detect_safe(user)
    """

    def detect(self, user) -> LeakDetectorResult:
        result = LeakDetectorResult(user_id=user.pk)
        try:
            transactions = self._load_transactions(user)
            if not transactions:
                result.data_quality = "insufficient"
                result.headline_sentence = (
                    "Connect a bank account to see your subscription leaks."
                )
                return result

            groups = self._group_by_merchant(transactions)
            subscriptions = []
            for merchant_key, txns in groups.items():
                sub = self._analyse_merchant(merchant_key, txns)
                if sub is not None:
                    subscriptions.append(sub)

            # Sort by monthly cost descending
            subscriptions.sort(key=lambda s: s.monthly_cost, reverse=True)
            result.subscriptions = subscriptions
            result.subscription_count = len(subscriptions)

            result.total_monthly_leak = sum(s.monthly_cost for s in subscriptions)
            result.total_annual_leak  = result.total_monthly_leak * 12

            unused = [s for s in subscriptions if s.is_likely_unused]
            result.likely_unused_count   = len(unused)
            result.likely_unused_monthly = sum(s.monthly_cost for s in unused)
            result.likely_unused_annual  = result.likely_unused_monthly * 12

            result.top_leak = subscriptions[0] if subscriptions else None

            # Opportunity cost at 7% annual return
            annual = result.total_annual_leak
            result.savings_impact_1yr = annual * 1.07
            result.savings_impact_5yr = _future_value(annual, 0.07, 5)

            result.data_quality = "actual"
            self._build_headline(result)
        except Exception as exc:
            logger.warning(
                "SubscriptionDetector.detect failed for user %s: %s",
                getattr(user, 'pk', '?'), exc,
            )
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Connect a bank account to see your subscription leaks."
            )
        return result

    def detect_safe(self, user) -> LeakDetectorResult:
        try:
            return self.detect(user)
        except Exception as exc:
            logger.warning("SubscriptionDetector.detect_safe error: %s", exc)
            r = LeakDetectorResult(user_id=getattr(user, 'pk', 0))
            r.data_quality = "insufficient"
            r.headline_sentence = "Connect a bank account to see your subscription leaks."
            return r

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_transactions(self, user) -> list:
        """Return list of (merchant_name, description, amount_float, posted_date)."""
        from .banking_models import BankTransaction
        from django.utils import timezone

        since = timezone.now().date() - timedelta(days=LOOKBACK_DAYS)
        qs = BankTransaction.objects.filter(
            user=user,
            transaction_type='DEBIT',
            status='POSTED',
            posted_date__gte=since,
            amount__gte=MIN_AMOUNT,
        ).values('merchant_name', 'description', 'amount', 'posted_date').order_by('posted_date')

        return [
            {
                'merchant': (row['merchant_name'] or '').strip(),
                'description': (row['description'] or '').strip(),
                'amount': float(row['amount']),
                'date': row['posted_date'],
            }
            for row in qs
        ]

    # ── Grouping ──────────────────────────────────────────────────────────────

    def _group_by_merchant(self, transactions: list) -> dict:
        """
        Group transactions by normalised merchant key.
        Returns dict[str → list[dict]].
        """
        groups: dict = {}
        for txn in transactions:
            key = _normalise_merchant(txn['merchant'] or txn['description'])
            if not key:
                continue
            groups.setdefault(key, []).append(txn)
        return groups

    # ── Recurrence analysis ───────────────────────────────────────────────────

    def _analyse_merchant(self, merchant_key: str, txns: list) -> Optional[DetectedSubscription]:
        """
        Examine one merchant's transaction list for recurring patterns.
        Returns a DetectedSubscription or None if no pattern found.
        """
        if len(txns) < MIN_OCCURRENCES:
            return None

        amounts = [t['amount'] for t in txns]
        med_amount = median(amounts)

        # Filter to transactions within AMOUNT_TOLERANCE of median
        consistent = [
            t for t in txns
            if abs(t['amount'] - med_amount) / max(med_amount, 0.01) <= AMOUNT_TOLERANCE
        ]
        if len(consistent) < MIN_OCCURRENCES:
            return None

        dates = sorted(t['date'] for t in consistent)

        # Compute intervals between consecutive charges
        intervals = [
            (dates[i + 1] - dates[i]).days
            for i in range(len(dates) - 1)
        ]
        if not intervals:
            return None

        med_interval = median(intervals)
        cadence_label, cadence_days, confidence = _match_cadence(med_interval, intervals)
        if cadence_label is None:
            return None

        if confidence < 0.40:
            return None

        typical_amount = median([t['amount'] for t in consistent])
        monthly_cost   = _to_monthly(typical_amount, cadence_days)
        annual_cost    = monthly_cost * 12

        category       = _classify_merchant(merchant_key)
        is_unused      = _is_likely_unused(merchant_key, typical_amount, cadence_days)
        display_name   = _prettify(merchant_key)

        return DetectedSubscription(
            merchant_key=merchant_key,
            display_name=display_name,
            category=category,
            cadence=cadence_label,
            cadence_days=cadence_days,
            typical_amount=round(typical_amount, 2),
            monthly_cost=round(monthly_cost, 2),
            annual_cost=round(annual_cost, 2),
            occurrences=len(consistent),
            last_charged=max(dates),
            first_charged=min(dates),
            confidence=round(confidence, 2),
            is_likely_unused=is_unused,
            transaction_dates=dates,
        )

    # ── Headline ──────────────────────────────────────────────────────────────

    def _build_headline(self, result: LeakDetectorResult) -> None:
        if result.total_monthly_leak <= 0:
            result.headline_sentence = (
                "No recurring subscription charges detected in the last 6 months."
            )
            return

        monthly  = result.total_monthly_leak
        annual   = result.total_annual_leak
        count    = result.subscription_count
        unused_c = result.likely_unused_count

        parts = [
            f"You have {count} recurring subscription{'s' if count != 1 else ''} "
            f"costing ${monthly:,.0f}/month (${annual:,.0f}/year)."
        ]
        if unused_c > 0:
            parts.append(
                f" {unused_c} of them look{'s' if unused_c == 1 else ''} forgotten or unused."
            )
        if result.top_leak:
            parts.append(
                f" Your biggest leak: {result.top_leak.display_name} "
                f"at ${result.top_leak.monthly_cost:,.2f}/month."
            )
        result.headline_sentence = "".join(parts)


# ── Pure helper functions ─────────────────────────────────────────────────────

def _normalise_merchant(raw: str) -> str:
    """
    Lowercase, strip card/transaction noise, collapse whitespace.
    e.g. "NETFLIX.COM*XXXXX" → "netflix"
    """
    s = raw.lower()
    # Strip trailing noise: *xxxxx, #12345, trailing digits after space
    s = re.sub(r'[*#]\S*', '', s)
    s = re.sub(r'\s+\d{4,}$', '', s)
    # Remove common prefixes/suffixes that add no info
    s = re.sub(r'\b(inc|llc|ltd|corp|co|the|www|com|net|org)\b', '', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _match_cadence(
    med_interval: float,
    intervals: list,
) -> tuple:
    """
    Find the best-fitting cadence for a given median interval.
    Returns (label, centre_days, confidence) or (None, None, 0).

    Confidence is computed from:
      - How close med_interval is to the cadence centre (±tolerance)
      - How consistent the intervals are (low stdev = high confidence)
    """
    best_label, best_days, best_conf = None, None, 0.0

    for label, centre, tolerance in CADENCES:
        if abs(med_interval - centre) <= tolerance:
            # Regularity: use coefficient of variation (stdev / mean) so the
            # penalty is proportional to the cadence itself.
            # CV = 0   → perfect regularity (conf contribution = 1.0)
            # CV = 0.5 → moderately irregular (conf contribution = 0.0)
            # CV > 0.5 → clamped to 0
            if len(intervals) >= 2:
                try:
                    mean_interval = sum(intervals) / len(intervals)
                    sd = stdev(intervals)
                    cv = sd / max(mean_interval, 1)
                    regularity = max(0.0, 1.0 - cv * 2.0)
                except Exception:
                    regularity = 0.5
            else:
                regularity = 0.5

            # Proximity bonus: how close to centre
            proximity = 1.0 - abs(med_interval - centre) / max(tolerance, 1)
            # Weight regularity heavily — irregular intervals must score low
            conf = 0.75 * regularity + 0.25 * proximity

            if conf > best_conf:
                best_label, best_days, best_conf = label, centre, conf

    return best_label, best_days, best_conf


def _to_monthly(amount: float, cadence_days: int) -> float:
    """Convert a per-occurrence amount to $/month."""
    if cadence_days <= 0:
        return amount
    return amount * (30.0 / cadence_days)


def _classify_merchant(merchant_key: str) -> str:
    """Map normalised merchant key to a category string."""
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in merchant_key:
                return category
    return "Subscriptions"


def _is_likely_unused(merchant_key: str, amount: float, cadence_days: int) -> bool:
    """
    Heuristic: flag as 'likely unused' if:
    - Merchant is in the EASILY_FORGOTTEN set, AND
    - Amount is ≤ $15, OR cadence is monthly/annual (not weekly utility bill)
    """
    for forgotten in EASILY_FORGOTTEN:
        if forgotten in merchant_key:
            return True
    # Also flag any subscription ≤ $5 regardless of merchant (trial / forgotten)
    if amount <= 5.0 and cadence_days >= 28:
        return True
    return False


def _prettify(merchant_key: str) -> str:
    """Title-case a normalised merchant key for display."""
    return merchant_key.replace('_', ' ').title()


def _future_value(annual_contribution: float, rate: float, years: int) -> float:
    """FV of end-of-year annuity: PMT × [((1+r)^n − 1) / r]."""
    if rate == 0:
        return annual_contribution * years
    return annual_contribution * (((1 + rate) ** years - 1) / rate)
