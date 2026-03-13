"""
Unit tests for SubscriptionDetector
=====================================
All tests exercise pure-logic paths.  No database required — transaction
data is passed as plain dicts, and DB-loading is monkey-patched in
integration tests.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch


# ── Helper factories ──────────────────────────────────────────────────────────

def _make_txns(merchant, amount, dates):
    """Build a list of fake transaction dicts."""
    return [
        {"merchant": merchant, "description": merchant, "amount": amount, "date": d}
        for d in dates
    ]


def _monthly_dates(n, start=date(2025, 1, 1)):
    """Generate n monthly dates starting from start."""
    return [start + timedelta(days=30 * i) for i in range(n)]


def _weekly_dates(n, start=date(2025, 1, 1)):
    return [start + timedelta(days=7 * i) for i in range(n)]


# ── _normalise_merchant ───────────────────────────────────────────────────────

class TestNormaliseMerchant:
    def test_strips_card_noise(self):
        from core.subscription_detector import _normalise_merchant
        assert _normalise_merchant("NETFLIX.COM*ABCD1234") == "netflix"

    def test_lowercases(self):
        from core.subscription_detector import _normalise_merchant
        assert "spotify" in _normalise_merchant("SPOTIFY USA")

    def test_strips_inc_llc(self):
        from core.subscription_detector import _normalise_merchant
        result = _normalise_merchant("Adobe Inc")
        assert "inc" not in result
        assert "adobe" in result

    def test_empty_string(self):
        from core.subscription_detector import _normalise_merchant
        assert _normalise_merchant("") == ""


# ── _match_cadence ────────────────────────────────────────────────────────────

class TestMatchCadence:
    def test_monthly_detected(self):
        from core.subscription_detector import _match_cadence
        intervals = [30, 31, 29, 30]
        label, days, conf = _match_cadence(30, intervals)
        assert label == "monthly"
        assert conf > 0.5

    def test_annual_detected(self):
        from core.subscription_detector import _match_cadence
        intervals = [365, 364]
        label, days, conf = _match_cadence(365, intervals)
        assert label == "annual"

    def test_weekly_detected(self):
        from core.subscription_detector import _match_cadence
        intervals = [7, 7, 7]
        label, days, conf = _match_cadence(7, intervals)
        assert label == "weekly"

    def test_irregular_returns_none(self):
        from core.subscription_detector import _match_cadence
        intervals = [15, 45, 10, 60]
        label, days, conf = _match_cadence(32, intervals)
        # Either None or low confidence
        assert label is None or conf < 0.40

    def test_confidence_between_0_and_1(self):
        from core.subscription_detector import _match_cadence
        intervals = [30, 30, 31]
        _, _, conf = _match_cadence(30, intervals)
        assert 0.0 <= conf <= 1.0


# ── _to_monthly ───────────────────────────────────────────────────────────────

class TestToMonthly:
    def test_monthly_passthrough(self):
        from core.subscription_detector import _to_monthly
        assert abs(_to_monthly(15.99, 30) - 15.99) < 0.01

    def test_annual_divided(self):
        from core.subscription_detector import _to_monthly
        # $120/year → $10/month
        result = _to_monthly(120.0, 365)
        assert abs(result - 9.86) < 0.10  # 120 × (30/365) ≈ 9.86

    def test_weekly_multiplied(self):
        from core.subscription_detector import _to_monthly
        # $5/week → ~$21.43/month
        result = _to_monthly(5.0, 7)
        assert abs(result - 21.43) < 0.10

    def test_zero_cadence_returns_amount(self):
        from core.subscription_detector import _to_monthly
        assert _to_monthly(10.0, 0) == 10.0


# ── _classify_merchant ────────────────────────────────────────────────────────

class TestClassifyMerchant:
    def test_netflix_is_streaming(self):
        from core.subscription_detector import _classify_merchant
        assert _classify_merchant("netflix") == "Streaming"

    def test_spotify_is_music(self):
        from core.subscription_detector import _classify_merchant
        assert _classify_merchant("spotify") == "Music"

    def test_unknown_is_subscriptions(self):
        from core.subscription_detector import _classify_merchant
        assert _classify_merchant("randommerchant xyz") == "Subscriptions"

    def test_adobe_is_software(self):
        from core.subscription_detector import _classify_merchant
        assert _classify_merchant("adobe") == "Software/Tools"


# ── _is_likely_unused ─────────────────────────────────────────────────────────

class TestIsLikelyUnused:
    def test_netflix_is_flagged(self):
        from core.subscription_detector import _is_likely_unused
        assert _is_likely_unused("netflix", 15.99, 30) is True

    def test_micro_amount_is_flagged(self):
        from core.subscription_detector import _is_likely_unused
        assert _is_likely_unused("unknownapp", 1.99, 30) is True

    def test_large_amount_not_flagged(self):
        from core.subscription_detector import _is_likely_unused
        assert _is_likely_unused("electric utility", 120.0, 30) is False


# ── _future_value ─────────────────────────────────────────────────────────────

class TestFutureValue:
    def test_zero_rate(self):
        from core.subscription_detector import _future_value
        assert _future_value(1000, 0, 5) == 5000.0

    def test_7_percent_5_years(self):
        from core.subscription_detector import _future_value
        # $1000/year at 7% for 5 years ≈ $5750
        result = _future_value(1000, 0.07, 5)
        assert 5700 < result < 5800

    def test_grows_with_more_years(self):
        from core.subscription_detector import _future_value
        assert _future_value(1000, 0.07, 10) > _future_value(1000, 0.07, 5)


# ── _analyse_merchant (core recurrence engine) ────────────────────────────────

class TestAnalyseMerchant:
    def _svc(self):
        from core.subscription_detector import SubscriptionDetector
        return SubscriptionDetector()

    def test_monthly_subscription_detected(self):
        svc = self._svc()
        txns = _make_txns("netflix", 15.99, _monthly_dates(5))
        sub = svc._analyse_merchant("netflix", txns)
        assert sub is not None
        assert sub.cadence == "monthly"
        assert abs(sub.typical_amount - 15.99) < 0.01
        assert abs(sub.monthly_cost - 15.99) < 0.10

    def test_annual_subscription_detected(self):
        svc = self._svc()
        dates = [date(2024, 1, 15), date(2025, 1, 14)]
        txns = _make_txns("amazon prime", 139.0, dates)
        sub = svc._analyse_merchant("amazon prime", txns)
        assert sub is not None
        assert sub.cadence == "annual"
        # Monthly cost ≈ 139/12 ≈ $11.58
        assert sub.monthly_cost < 15.0

    def test_too_few_occurrences_returns_none(self):
        svc = self._svc()
        txns = _make_txns("netflix", 15.99, [date(2025, 1, 1)])
        sub = svc._analyse_merchant("netflix", txns)
        assert sub is None

    def test_irregular_charges_returns_none(self):
        svc = self._svc()
        # Random amounts — no consistent amount pattern
        txns = [
            {"merchant": "random", "description": "random", "amount": a, "date": d}
            for a, d in [
                (15.99, date(2025, 1, 1)),
                (87.50, date(2025, 2, 5)),
                (3.00,  date(2025, 2, 20)),
                (55.00, date(2025, 3, 15)),
            ]
        ]
        sub = self._svc()._analyse_merchant("random", txns)
        assert sub is None

    def test_amount_tolerance_respected(self):
        """Charges within 10% of median are grouped together."""
        svc = self._svc()
        # $10, $10.50, $9.80 — all within 10% of $10
        txns = [
            {"merchant": "spotify", "description": "spotify", "amount": a, "date": d}
            for a, d in [
                (10.00, date(2025, 1, 1)),
                (10.50, date(2025, 2, 1)),
                (9.80,  date(2025, 3, 3)),
                (10.20, date(2025, 4, 1)),
            ]
        ]
        sub = svc._analyse_merchant("spotify", txns)
        assert sub is not None

    def test_confidence_is_valid_range(self):
        svc = self._svc()
        txns = _make_txns("spotify", 9.99, _monthly_dates(4))
        sub = svc._analyse_merchant("spotify", txns)
        if sub:
            assert 0.0 <= sub.confidence <= 1.0

    def test_last_and_first_charged(self):
        svc = self._svc()
        dates = _monthly_dates(4)
        txns = _make_txns("hulu", 17.99, dates)
        sub = svc._analyse_merchant("hulu", txns)
        assert sub is not None
        assert sub.first_charged == min(dates)
        assert sub.last_charged == max(dates)

    def test_is_likely_unused_flagged(self):
        svc = self._svc()
        txns = _make_txns("netflix", 15.99, _monthly_dates(3))
        sub = svc._analyse_merchant("netflix", txns)
        assert sub is not None
        assert sub.is_likely_unused is True


# ── _group_by_merchant ────────────────────────────────────────────────────────

class TestGroupByMerchant:
    def test_same_merchant_grouped(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()
        txns = [
            {"merchant": "Netflix", "description": "", "amount": 15.99, "date": date(2025, 1, 1)},
            {"merchant": "NETFLIX", "description": "", "amount": 15.99, "date": date(2025, 2, 1)},
        ]
        groups = svc._group_by_merchant(txns)
        assert len(groups) == 1  # both should normalise to same key

    def test_different_merchants_separated(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()
        txns = [
            {"merchant": "Netflix", "description": "", "amount": 15.99, "date": date(2025, 1, 1)},
            {"merchant": "Spotify", "description": "", "amount": 9.99, "date": date(2025, 1, 5)},
        ]
        groups = svc._group_by_merchant(txns)
        assert len(groups) == 2


# ── detect() aggregation ─────────────────────────────────────────────────────

class TestDetectAggregation:
    """Integration tests with mocked DB loading."""

    def _fake_transactions(self):
        """Simulate two clean monthly subscriptions + one irregular charge."""
        txns = []
        # Netflix monthly
        for d in _monthly_dates(5):
            txns.append({"merchant": "netflix", "description": "netflix", "amount": 15.99, "date": d})
        # Spotify monthly
        for d in _monthly_dates(4, start=date(2025, 1, 3)):
            txns.append({"merchant": "spotify", "description": "spotify", "amount": 9.99, "date": d})
        # One-off charge — should not appear as subscription
        txns.append({"merchant": "dentist office", "description": "dental", "amount": 250.0, "date": date(2025, 2, 10)})
        return txns

    def test_two_subscriptions_found(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=self._fake_transactions()):
            user = MagicMock()
            user.pk = 1
            result = svc.detect(user)

        # Should find Netflix and Spotify; dentist is a one-off
        names = {s.merchant_key for s in result.subscriptions}
        assert "netflix" in names
        assert "spotify" in names
        assert "dentist office" not in names

    def test_totals_computed_correctly(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=self._fake_transactions()):
            user = MagicMock()
            user.pk = 1
            result = svc.detect(user)

        expected_monthly = sum(s.monthly_cost for s in result.subscriptions)
        assert abs(result.total_monthly_leak - expected_monthly) < 0.01
        assert abs(result.total_annual_leak - expected_monthly * 12) < 0.01

    def test_top_leak_is_most_expensive(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=self._fake_transactions()):
            user = MagicMock()
            user.pk = 1
            result = svc.detect(user)

        if result.top_leak and len(result.subscriptions) > 1:
            assert result.top_leak.monthly_cost == max(
                s.monthly_cost for s in result.subscriptions
            )

    def test_savings_impact_positive(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=self._fake_transactions()):
            user = MagicMock()
            user.pk = 1
            result = svc.detect(user)

        if result.total_annual_leak > 0:
            assert result.savings_impact_1yr > result.total_annual_leak
            assert result.savings_impact_5yr > result.savings_impact_1yr

    def test_headline_not_empty(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=self._fake_transactions()):
            user = MagicMock()
            user.pk = 1
            result = svc.detect(user)

        assert result.headline_sentence
        assert len(result.headline_sentence) > 20

    def test_empty_transactions_gives_insufficient(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', return_value=[]):
            user = MagicMock()
            user.pk = 2
            result = svc.detect(user)

        assert result.data_quality == "insufficient"
        assert result.subscription_count == 0

    def test_detect_safe_never_raises(self):
        from core.subscription_detector import SubscriptionDetector
        svc = SubscriptionDetector()

        with patch.object(svc, '_load_transactions', side_effect=RuntimeError("db down")):
            user = MagicMock()
            user.pk = 3
            result = svc.detect_safe(user)

        assert result.data_quality == "insufficient"
