"""
Net Worth Service
=================
Two responsibilities:

1. CAPTURE  — compute today's net worth from live ORM data and upsert a
              NetWorthSnapshot row (idempotent: safe to call multiple times
              per day; only the first write lands, subsequent calls are no-ops).

2. QUERY    — return a user's snapshot history (last N days / months) for
              charting, plus key derived metrics:
                • change_7d / change_30d / change_90d / change_1yr
                • change_pct_30d
                • all-time high and the date it was reached
                • streak: consecutive days net worth increased

Design notes
------------
- Reuses FinancialGraphService.build_graph_safe() for the live snapshot so
  all data-loading logic stays in one place.
- DB writes use update_or_create with defaults so the task is idempotent.
- All history queries are read-only.
- Returns plain dataclasses (no Django model instances exposed to callers).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data containers ───────────────────────────────────────────────────────────

@dataclass
class NetWorthPoint:
    """A single snapshot in the history timeline."""
    captured_at: date
    net_worth: float
    portfolio_value: float
    savings_balance: float
    debt: float


@dataclass
class NetWorthHistory:
    """Full history + derived metrics for a user."""
    user_id: int

    # Timeline (oldest → newest)
    history: list = field(default_factory=list)   # list[NetWorthPoint]

    # Current (latest snapshot)
    current_net_worth: float = 0.0
    current_portfolio_value: float = 0.0
    current_savings_balance: float = 0.0
    current_debt: float = 0.0

    # Change metrics (dollar)
    change_7d:   Optional[float] = None
    change_30d:  Optional[float] = None
    change_90d:  Optional[float] = None
    change_1yr:  Optional[float] = None

    # Change metrics (percent, 30-day)
    change_pct_30d: Optional[float] = None

    # Records
    all_time_high:      float = 0.0
    all_time_high_date: Optional[date] = None
    all_time_low:       float = 0.0
    all_time_low_date:  Optional[date] = None

    # Streak: consecutive days net worth increased (ending today)
    increase_streak_days: int = 0

    # Today's capture status
    snapshot_captured_today: bool = False
    data_quality: str = "estimated"   # "actual" | "estimated" | "insufficient"
    headline_sentence: str = ""


# ── Service ───────────────────────────────────────────────────────────────────

class NetWorthService:
    """
    Captures and queries net worth snapshots.

    Typical call pattern
    --------------------
    On Wealth screen load:
        service = NetWorthService()
        service.capture_today(user, source='on_demand')   # upsert — safe to repeat
        history = service.get_history(user, days=90)
    """

    # ── Capture ───────────────────────────────────────────────────────────────

    def capture_today(self, user, source: str = 'on_demand') -> Optional[NetWorthPoint]:
        """
        Compute today's net worth from live data and upsert a snapshot.
        Returns the NetWorthPoint that was written (or already existed).
        Returns None if financial data is unavailable.
        """
        try:
            from .financial_graph_service import FinancialGraphService
            ctx = FinancialGraphService().build_graph_safe(user)
            if ctx is None:
                logger.debug("capture_today: no financial context for user %s", user.pk)
                return None

            net_worth = (
                ctx.portfolio_total_value
                + ctx.total_savings_balance
                - ctx.total_cc_balance
            )

            today = date.today()
            self._upsert(
                user=user,
                captured_at=today,
                net_worth=net_worth,
                portfolio_value=ctx.portfolio_total_value,
                savings_balance=ctx.total_savings_balance,
                debt=ctx.total_cc_balance,
                source=source,
            )
            return NetWorthPoint(
                captured_at=today,
                net_worth=net_worth,
                portfolio_value=ctx.portfolio_total_value,
                savings_balance=ctx.total_savings_balance,
                debt=ctx.total_cc_balance,
            )
        except Exception as exc:
            logger.warning("NetWorthService.capture_today error for user %s: %s", user.pk, exc)
            return None

    def capture_today_safe(self, user, source: str = 'on_demand') -> Optional[NetWorthPoint]:
        try:
            return self.capture_today(user, source=source)
        except Exception as exc:
            logger.warning("NetWorthService.capture_today_safe: %s", exc)
            return None

    def _upsert(
        self,
        user,
        captured_at: date,
        net_worth: float,
        portfolio_value: float,
        savings_balance: float,
        debt: float,
        source: str,
    ) -> None:
        """
        Insert snapshot for (user, captured_at) or do nothing if one already
        exists for today.  We never overwrite an existing snapshot — the first
        write of the day wins (preserves the opening-of-day reading).
        """
        from .net_worth_models import NetWorthSnapshot
        NetWorthSnapshot.objects.get_or_create(
            user=user,
            captured_at=captured_at,
            defaults=dict(
                net_worth=Decimal(str(round(net_worth, 2))),
                portfolio_value=Decimal(str(round(portfolio_value, 2))),
                savings_balance=Decimal(str(round(savings_balance, 2))),
                debt=Decimal(str(round(debt, 2))),
                source=source,
            ),
        )

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_history(self, user, days: int = 365) -> NetWorthHistory:
        """
        Return the last `days` days of net worth snapshots plus derived metrics.
        """
        result = NetWorthHistory(user_id=user.pk)
        try:
            since = date.today() - timedelta(days=days)
            snapshots = self._load_snapshots(user, since)

            if not snapshots:
                result.data_quality = "insufficient"
                result.headline_sentence = (
                    "No net worth history yet. Your first snapshot will be captured today."
                )
                return result

            # Build history list (oldest → newest)
            points = [
                NetWorthPoint(
                    captured_at=s.captured_at,
                    net_worth=float(s.net_worth),
                    portfolio_value=float(s.portfolio_value),
                    savings_balance=float(s.savings_balance),
                    debt=float(s.debt),
                )
                for s in reversed(snapshots)  # DB orders by -captured_at
            ]
            result.history = points

            # Current = latest
            latest = points[-1]
            result.current_net_worth      = latest.net_worth
            result.current_portfolio_value = latest.portfolio_value
            result.current_savings_balance = latest.savings_balance
            result.current_debt           = latest.debt

            today = date.today()
            result.snapshot_captured_today = (latest.captured_at == today)
            result.data_quality = "actual"

            # Change metrics
            by_date = {p.captured_at: p for p in points}
            result.change_7d  = _change(latest, by_date, 7)
            result.change_30d = _change(latest, by_date, 30)
            result.change_90d = _change(latest, by_date, 90)
            result.change_1yr = _change(latest, by_date, 365)

            if result.change_30d is not None and result.current_net_worth != 0:
                base_30d = result.current_net_worth - result.change_30d
                if base_30d != 0:
                    result.change_pct_30d = (result.change_30d / abs(base_30d)) * 100

            # All-time high / low within query window
            ath_point = max(points, key=lambda p: p.net_worth)
            atl_point = min(points, key=lambda p: p.net_worth)
            result.all_time_high      = ath_point.net_worth
            result.all_time_high_date = ath_point.captured_at
            result.all_time_low       = atl_point.net_worth
            result.all_time_low_date  = atl_point.captured_at

            # Increase streak (from end of list going backwards)
            result.increase_streak_days = _compute_streak(points)

            self._build_headline(result)

        except Exception as exc:
            logger.warning("NetWorthService.get_history error for user %s: %s", user.pk, exc)
            result.data_quality = "insufficient"
            result.headline_sentence = (
                "Net worth history temporarily unavailable."
            )

        return result

    def get_history_safe(self, user, days: int = 365) -> NetWorthHistory:
        try:
            return self.get_history(user, days=days)
        except Exception as exc:
            logger.warning("NetWorthService.get_history_safe: %s", exc)
            r = NetWorthHistory(user_id=getattr(user, 'pk', 0))
            r.data_quality = "insufficient"
            return r

    def _load_snapshots(self, user, since: date):
        from .net_worth_models import NetWorthSnapshot
        return list(
            NetWorthSnapshot.objects.filter(
                user=user,
                captured_at__gte=since,
            ).order_by('-captured_at')
        )

    # ── Headline ──────────────────────────────────────────────────────────────

    def _build_headline(self, result: NetWorthHistory) -> None:
        nw = result.current_net_worth
        ch30 = result.change_30d
        pct30 = result.change_pct_30d

        if nw == 0:
            result.headline_sentence = "Your net worth is being calculated."
            return

        nw_str = _fmt(nw)

        if ch30 is not None and pct30 is not None:
            direction = "up" if ch30 >= 0 else "down"
            result.headline_sentence = (
                f"Your net worth is {nw_str}, "
                f"{direction} ${abs(ch30):,.0f} ({abs(pct30):.1f}%) in the last 30 days."
            )
        else:
            result.headline_sentence = f"Your net worth is {nw_str}."

        if result.increase_streak_days >= 7:
            result.headline_sentence += (
                f" You're on a {result.increase_streak_days}-day growth streak."
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _change(latest: NetWorthPoint, by_date: dict, days: int) -> Optional[float]:
    """Dollar change vs N days ago. Returns None if that snapshot doesn't exist."""
    target = latest.captured_at - timedelta(days=days)
    # Find closest available snapshot within ±3 days
    for delta in range(0, 4):
        for d in [target - timedelta(days=delta), target + timedelta(days=delta)]:
            if d in by_date:
                return latest.net_worth - by_date[d].net_worth
    return None


def _compute_streak(points: list) -> int:
    """Count consecutive days (from end) where net_worth increased."""
    if len(points) < 2:
        return 0
    streak = 0
    for i in range(len(points) - 1, 0, -1):
        if points[i].net_worth > points[i - 1].net_worth:
            streak += 1
        else:
            break
    return streak


def _fmt(amount: float) -> str:
    """Human-readable dollar amount."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:,.2f}M"
    if amount >= 1_000:
        return f"${amount:,.0f}"
    return f"${amount:.2f}"
