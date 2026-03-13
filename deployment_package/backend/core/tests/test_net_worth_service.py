"""
Unit tests for NetWorthService (pure-logic paths, no live DB)
=============================================================
All ORM calls are mocked.  Tests cover:
- _change() helper
- _compute_streak() helper
- _fmt() helper
- get_history() derived metrics
- _build_headline()
- capture_today() happy path
- get_history_safe() / capture_today_safe() never raise
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_point(d, nw, pv=0, sb=0, debt=0):
    from core.net_worth_service import NetWorthPoint
    return NetWorthPoint(
        captured_at=d,
        net_worth=nw,
        portfolio_value=pv,
        savings_balance=sb,
        debt=debt,
    )


def _make_history(points):
    """Build a NetWorthHistory pre-loaded with points."""
    from core.net_worth_service import NetWorthHistory
    h = NetWorthHistory(user_id=1)
    h.history = points
    return h


def _days_ago(n):
    return date.today() - timedelta(days=n)


# ── _fmt ──────────────────────────────────────────────────────────────────────

class TestFmt:
    def test_millions(self):
        from core.net_worth_service import _fmt
        assert "$1.50M" in _fmt(1_500_000)

    def test_thousands(self):
        from core.net_worth_service import _fmt
        result = _fmt(250_000)
        assert "$250,000" in result

    def test_small(self):
        from core.net_worth_service import _fmt
        result = _fmt(500.50)
        assert "$500.50" in result


# ── _change ───────────────────────────────────────────────────────────────────

class TestChange:
    def _setup(self):
        from core.net_worth_service import _change, NetWorthPoint
        today = date.today()
        points = [
            _make_point(today - timedelta(days=90), 50_000),
            _make_point(today - timedelta(days=30), 55_000),
            _make_point(today - timedelta(days=7),  58_000),
            _make_point(today,                      60_000),
        ]
        latest = points[-1]
        by_date = {p.captured_at: p for p in points}
        return latest, by_date

    def test_change_7d(self):
        from core.net_worth_service import _change
        latest, by_date = self._setup()
        result = _change(latest, by_date, 7)
        assert result == pytest.approx(60_000 - 58_000)

    def test_change_30d(self):
        from core.net_worth_service import _change
        latest, by_date = self._setup()
        result = _change(latest, by_date, 30)
        assert result == pytest.approx(60_000 - 55_000)

    def test_change_returns_none_when_no_data(self):
        from core.net_worth_service import _change
        latest, by_date = self._setup()
        # 1-year change — no snapshot exists
        result = _change(latest, by_date, 365)
        assert result is None

    def test_change_tolerance_fuzzy_match(self):
        """Should find a snapshot within ±3 days."""
        from core.net_worth_service import _change
        today = date.today()
        # Snapshot exists 2 days before the 30-day target (not exactly 30 days ago)
        points = [
            _make_point(today - timedelta(days=32), 45_000),
            _make_point(today, 60_000),
        ]
        latest = points[-1]
        by_date = {p.captured_at: p for p in points}
        result = _change(latest, by_date, 30)
        assert result == pytest.approx(60_000 - 45_000)


# ── _compute_streak ───────────────────────────────────────────────────────────

class TestComputeStreak:
    def test_consistent_growth_streak(self):
        from core.net_worth_service import _compute_streak
        points = [
            _make_point(_days_ago(4), 50_000),
            _make_point(_days_ago(3), 51_000),
            _make_point(_days_ago(2), 52_000),
            _make_point(_days_ago(1), 53_000),
            _make_point(_days_ago(0), 54_000),
        ]
        assert _compute_streak(points) == 4

    def test_streak_broken(self):
        from core.net_worth_service import _compute_streak
        points = [
            _make_point(_days_ago(4), 50_000),
            _make_point(_days_ago(3), 51_000),
            _make_point(_days_ago(2), 49_000),  # drop
            _make_point(_days_ago(1), 50_000),
            _make_point(_days_ago(0), 51_000),
        ]
        assert _compute_streak(points) == 2

    def test_no_growth(self):
        from core.net_worth_service import _compute_streak
        points = [
            _make_point(_days_ago(2), 50_000),
            _make_point(_days_ago(1), 50_000),
            _make_point(_days_ago(0), 49_000),
        ]
        assert _compute_streak(points) == 0

    def test_single_point(self):
        from core.net_worth_service import _compute_streak
        assert _compute_streak([_make_point(_days_ago(0), 50_000)]) == 0

    def test_empty(self):
        from core.net_worth_service import _compute_streak
        assert _compute_streak([]) == 0


# ── get_history() derived metrics ────────────────────────────────────────────

class TestGetHistoryMetrics:
    def _build_service_with_snapshots(self, snapshots):
        from core.net_worth_service import NetWorthService
        svc = NetWorthService()
        svc._load_snapshots = MagicMock(return_value=snapshots)
        return svc

    def _make_db_snapshot(self, d, nw, pv=0, sb=0, debt=0):
        snap = MagicMock()
        snap.captured_at = d
        snap.net_worth = Decimal(str(nw))
        snap.portfolio_value = Decimal(str(pv))
        snap.savings_balance = Decimal(str(sb))
        snap.debt = Decimal(str(debt))
        return snap

    def test_current_net_worth_from_latest(self):
        today = date.today()
        # DB returns newest first
        snaps = [
            self._make_db_snapshot(today, 60_000),
            self._make_db_snapshot(today - timedelta(days=30), 50_000),
        ]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user, days=60)
        assert result.current_net_worth == 60_000

    def test_change_30d_computed(self):
        today = date.today()
        # DB returns newest first
        snaps = [
            self._make_db_snapshot(today, 60_000),
            self._make_db_snapshot(today - timedelta(days=30), 50_000),
        ]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user, days=60)
        assert result.change_30d == pytest.approx(10_000)

    def test_change_pct_30d(self):
        today = date.today()
        # DB returns newest first
        snaps = [
            self._make_db_snapshot(today, 60_000),
            self._make_db_snapshot(today - timedelta(days=30), 50_000),
        ]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user, days=60)
        # 10k / 50k = 20%
        assert result.change_pct_30d == pytest.approx(20.0)

    def test_all_time_high_and_low(self):
        today = date.today()
        # DB returns newest first
        snaps = [
            self._make_db_snapshot(today, 60_000),
            self._make_db_snapshot(today - timedelta(days=30), 70_000),
            self._make_db_snapshot(today - timedelta(days=60), 40_000),
        ]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user, days=90)
        assert result.all_time_high == 70_000
        assert result.all_time_low == 40_000

    def test_snapshot_captured_today_true(self):
        today = date.today()
        snaps = [self._make_db_snapshot(today, 60_000)]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user)
        assert result.snapshot_captured_today is True

    def test_snapshot_captured_today_false(self):
        snaps = [self._make_db_snapshot(date.today() - timedelta(days=1), 60_000)]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user)
        assert result.snapshot_captured_today is False

    def test_empty_snapshots_gives_insufficient(self):
        svc = self._build_service_with_snapshots([])
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user)
        assert result.data_quality == "insufficient"

    def test_history_sorted_oldest_first(self):
        today = date.today()
        # DB returns newest first (default ordering)
        snaps = [
            self._make_db_snapshot(today, 60_000),
            self._make_db_snapshot(today - timedelta(days=30), 50_000),
        ]
        svc = self._build_service_with_snapshots(snaps)
        user = MagicMock()
        user.pk = 1
        result = svc.get_history(user)
        # history should be oldest → newest
        assert result.history[0].captured_at < result.history[-1].captured_at

    def test_get_history_safe_never_raises(self):
        from core.net_worth_service import NetWorthService
        svc = NetWorthService()
        svc._load_snapshots = MagicMock(side_effect=RuntimeError("db down"))
        user = MagicMock()
        user.pk = 1
        result = svc.get_history_safe(user)
        assert result.data_quality == "insufficient"


# ── _build_headline ───────────────────────────────────────────────────────────

class TestBuildHeadline:
    def _svc(self):
        from core.net_worth_service import NetWorthService
        return NetWorthService()

    def _make_result(self, nw, change_30d=None, pct=None, streak=0):
        from core.net_worth_service import NetWorthHistory
        r = NetWorthHistory(user_id=1)
        r.current_net_worth = nw
        r.change_30d = change_30d
        r.change_pct_30d = pct
        r.increase_streak_days = streak
        return r

    def test_with_positive_change(self):
        svc = self._svc()
        r = self._make_result(60_000, change_30d=5_000, pct=9.1)
        svc._build_headline(r)
        assert "up" in r.headline_sentence.lower()
        assert "$5,000" in r.headline_sentence

    def test_with_negative_change(self):
        svc = self._svc()
        r = self._make_result(55_000, change_30d=-3_000, pct=-5.2)
        svc._build_headline(r)
        assert "down" in r.headline_sentence.lower()

    def test_streak_appended(self):
        svc = self._svc()
        r = self._make_result(60_000, change_30d=5_000, pct=9.1, streak=10)
        svc._build_headline(r)
        assert "10-day" in r.headline_sentence

    def test_short_streak_not_mentioned(self):
        svc = self._svc()
        r = self._make_result(60_000, change_30d=5_000, pct=9.1, streak=3)
        svc._build_headline(r)
        assert "streak" not in r.headline_sentence

    def test_zero_net_worth(self):
        svc = self._svc()
        r = self._make_result(0)
        svc._build_headline(r)
        assert r.headline_sentence  # just check it doesn't crash


# ── capture_today() happy path ────────────────────────────────────────────────

class TestCaptureToday:
    def _fake_ctx(self, portfolio=50_000, savings=15_000, cc=5_000):
        ctx = MagicMock()
        ctx.portfolio_total_value = portfolio
        ctx.total_savings_balance = savings
        ctx.total_cc_balance = cc
        return ctx

    def test_returns_point_with_correct_net_worth(self):
        from core.net_worth_service import NetWorthService

        ctx = self._fake_ctx()
        with patch("core.financial_graph_service.FinancialGraphService") as MockGFS, \
             patch("core.net_worth_models.NetWorthSnapshot") as MockModel:

            MockGFS.return_value.build_graph_safe.return_value = ctx
            MockModel.objects.get_or_create.return_value = (MagicMock(), True)

            user = MagicMock()
            user.pk = 1
            svc = NetWorthService()
            point = svc.capture_today(user)

        assert point is not None
        # net_worth = 50k + 15k - 5k = 60k
        assert point.net_worth == pytest.approx(60_000)
        assert point.portfolio_value == pytest.approx(50_000)

    def test_returns_none_when_no_context(self):
        from core.net_worth_service import NetWorthService

        with patch("core.financial_graph_service.FinancialGraphService") as MockGFS:
            MockGFS.return_value.build_graph_safe.return_value = None
            user = MagicMock()
            user.pk = 2
            point = NetWorthService().capture_today(user)

        assert point is None

    def test_capture_today_safe_never_raises(self):
        from core.net_worth_service import NetWorthService

        with patch("core.financial_graph_service.FinancialGraphService") as MockGFS:
            MockGFS.return_value.build_graph_safe.side_effect = RuntimeError("crash")
            user = MagicMock()
            user.pk = 3
            point = NetWorthService().capture_today_safe(user)

        assert point is None
