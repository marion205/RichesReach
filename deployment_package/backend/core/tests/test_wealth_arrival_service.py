"""
Unit tests for WealthArrivalService
=====================================
These tests exercise pure-logic paths of the service and dataclasses
without requiring a live database.  All DB-dependent methods are mocked
via monkeypatching the relevant service calls.
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch


# ── Import the service ────────────────────────────────────────────────────────

# Adjust sys.path so we can import from the backend package without Django setup
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_graph_context(
    portfolio=50_000,
    savings=15_000,
    cc_balance=5_000,
    monthly_income=8_000,
    cc_min_payments=150,
    investable_surplus=1_450,
):
    """Return a fake FinancialGraphContext dataclass-like object."""
    ctx = MagicMock()
    ctx.portfolio_total_value     = portfolio
    ctx.total_savings_balance     = savings
    ctx.total_cc_balance          = cc_balance
    ctx.estimated_monthly_income  = monthly_income
    ctx.total_cc_min_payments     = cc_min_payments
    ctx.investable_surplus_monthly = investable_surplus
    return ctx


def _make_profile(age=35, risk="Moderate", horizon="10+ years"):
    profile = MagicMock()
    profile.age                = age
    profile.risk_tolerance     = risk
    profile.investment_horizon = horizon
    return profile


# ── Dollar formatter ──────────────────────────────────────────────────────────

class TestFormatDollar:
    def test_millions(self):
        from core.wealth_arrival_service import _format_dollar
        assert _format_dollar(1_000_000) == "$1M"
        assert _format_dollar(2_500_000) == "$2.5M"

    def test_thousands(self):
        from core.wealth_arrival_service import _format_dollar
        assert _format_dollar(500_000) == "$500K"
        assert _format_dollar(250_000) == "$250K"
        assert _format_dollar(100_000) == "$100K"

    def test_small(self):
        from core.wealth_arrival_service import _format_dollar
        assert _format_dollar(999) == "$999"
        assert _format_dollar(0) == "$0"


# ── WealthArrivalResult dataclass defaults ────────────────────────────────────

class TestWealthArrivalResultDefaults:
    def test_defaults(self):
        from core.wealth_arrival_service import WealthArrivalResult
        r = WealthArrivalResult(user_id=1)
        assert r.current_net_worth == 0.0
        assert r.risk_tolerance == "Moderate"
        assert r.target_net_worth == 1_000_000.0
        assert r.scenarios == []
        assert r.data_quality == "estimated"


# ── _project_scenario (core math engine) ─────────────────────────────────────

class TestProjectScenario:
    """Tests for the compound-growth engine."""

    def _make_result(self, **kwargs):
        from core.wealth_arrival_service import WealthArrivalResult
        defaults = dict(
            user_id=1,
            current_portfolio_value=50_000,
            current_savings_balance=10_000,
            current_debt=0,
            annual_contribution=12_000,
            investable_surplus_monthly=1_000,
            target_net_worth=1_000_000,
            projection_years=30,
            risk_tolerance="Moderate",
        )
        defaults.update(kwargs)
        r = WealthArrivalResult(**defaults)
        return r

    def test_net_worth_grows_over_time(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        scenario = svc._project_scenario("Moderate", 0.07, result)
        year_1 = scenario.year_by_year[0]
        year_10 = scenario.year_by_year[9]
        year_30 = scenario.year_by_year[29]
        assert year_10.net_worth > year_1.net_worth
        assert year_30.net_worth > year_10.net_worth

    def test_zero_contribution_still_grows(self):
        """Portfolio should still grow at the return rate even with no contributions."""
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result(annual_contribution=0)
        scenario = svc._project_scenario("Moderate", 0.07, result)
        # Portfolio starts at 50k; after 1 year at 7% = 53,500
        year_1 = scenario.year_by_year[0]
        assert year_1.portfolio_value > 50_000

    def test_higher_return_produces_higher_net_worth(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        conservative = svc._project_scenario("Conservative", 0.05, result)
        aggressive   = svc._project_scenario("Aggressive", 0.09, result)
        assert aggressive.final_net_worth > conservative.final_net_worth

    def test_milestone_detection(self):
        """$100K milestone should be hit before $1M milestone."""
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        scenario = svc._project_scenario("Moderate", 0.07, result)

        by_target = {m.target_amount: m for m in scenario.milestones}
        m100k = by_target.get(100_000)
        m1m   = by_target.get(1_000_000)

        # Current net worth is 60k; $100K should be hit relatively early
        if m100k and not m100k.already_achieved:
            assert m100k.years_away > 0
        if m1m and m100k and not m1m.already_achieved and not m100k.already_achieved:
            assert m1m.years_away > m100k.years_away

    def test_already_achieved_milestone(self):
        """If current net worth > target, milestone is marked already_achieved."""
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result(
            current_portfolio_value=400_000,
            current_savings_balance=100_000,
            target_net_worth=250_000,
        )
        result.current_net_worth = 500_000  # net worth > target → already_achieved
        scenario = svc._project_scenario("Moderate", 0.07, result)
        by_target = {m.target_amount: m for m in scenario.milestones}
        m250k = by_target.get(250_000)
        assert m250k is not None
        assert m250k.already_achieved is True
        assert m250k.years_away == 0

    def test_cumulative_contributions_increase(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        scenario = svc._project_scenario("Moderate", 0.07, result)
        for i in range(1, len(scenario.year_by_year)):
            assert (
                scenario.year_by_year[i].cumulative_contributions
                > scenario.year_by_year[i - 1].cumulative_contributions
            )

    def test_arrival_year_is_calendar_year(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        scenario = svc._project_scenario("Moderate", 0.07, result)
        current_year = datetime.date.today().year
        for m in scenario.milestones:
            if m.years_away is not None and m.years_away > 0:
                assert m.arrival_year == current_year + m.years_away

    def test_wealth_arrival_years_within_horizon(self):
        """Wealth arrival years should be set for a reachable target."""
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        # High contribution, moderate target — should be reachable in 30 years
        result = self._make_result(
            current_portfolio_value=200_000,
            annual_contribution=24_000,
            target_net_worth=500_000,
            projection_years=30,
        )
        scenario = svc._project_scenario("Moderate", 0.07, result)
        assert scenario.wealth_arrival_years is not None
        assert 0 < scenario.wealth_arrival_years <= 30

    def test_total_contributions_equals_sum(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result(projection_years=10)
        scenario = svc._project_scenario("Moderate", 0.07, result)
        # total_contributions should match last year's cumulative
        assert abs(
            scenario.total_contributions
            - scenario.year_by_year[-1].cumulative_contributions
        ) < 0.01


# ── _run_projections (all three scenarios) ────────────────────────────────────

class TestRunProjections:
    def _make_result(self):
        from core.wealth_arrival_service import WealthArrivalResult
        return WealthArrivalResult(
            user_id=1,
            current_portfolio_value=50_000,
            current_savings_balance=10_000,
            current_debt=0,
            annual_contribution=12_000,
            investable_surplus_monthly=1_000,
            target_net_worth=1_000_000,
            projection_years=30,
            risk_tolerance="Moderate",
        )

    def test_three_scenarios_produced(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        svc._run_projections(result)
        assert len(result.scenarios) == 3
        names = {s.scenario for s in result.scenarios}
        assert names == {"conservative", "moderate", "aggressive"}

    def test_primary_matches_risk_tolerance(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        result.risk_tolerance = "Aggressive"
        svc._run_projections(result)
        assert result.primary.scenario == "aggressive"

    def test_moderate_is_default_primary(self):
        from core.wealth_arrival_service import WealthArrivalService
        svc = WealthArrivalService()
        result = self._make_result()
        svc._run_projections(result)
        assert result.primary.scenario == "moderate"


# ── _build_headline ───────────────────────────────────────────────────────────

class TestBuildHeadline:
    def _run(self, **kwargs):
        from core.wealth_arrival_service import WealthArrivalService, WealthArrivalResult
        svc = WealthArrivalService()
        portfolio = kwargs.get("portfolio", 50_000)
        savings   = kwargs.get("savings", 10_000)
        debt      = kwargs.get("debt", 0)
        result = WealthArrivalResult(
            user_id=1,
            current_portfolio_value=portfolio,
            current_savings_balance=savings,
            current_debt=debt,
            current_net_worth=portfolio + savings - debt,  # compute like service does
            annual_contribution=kwargs.get("contribution", 12_000),
            investable_surplus_monthly=kwargs.get("surplus", 1_000),
            target_net_worth=kwargs.get("target", 1_000_000),
            projection_years=30,
            risk_tolerance="Moderate",
            data_quality="actual",
        )
        svc._run_projections(result)
        svc._build_headline(result)
        return result

    def test_headline_not_empty(self):
        result = self._run()
        assert result.headline_sentence
        assert len(result.headline_sentence) > 10

    def test_already_achieved_headline(self):
        result = self._run(portfolio=900_000, savings=200_000, target=500_000)
        assert "already reached" in result.headline_sentence.lower()

    def test_on_track_headline_contains_year(self):
        result = self._run(portfolio=200_000, savings=50_000, contribution=24_000, target=500_000)
        current_year = datetime.date.today().year
        # Should mention a future year
        headline = result.headline_sentence
        # Check that headline contains pace/year reference
        assert any(str(current_year + i) in headline for i in range(1, 31)) or \
               "Increase" in headline  # fallback if not reachable

    def test_insufficient_data_headline(self):
        from core.wealth_arrival_service import WealthArrivalResult, WealthArrivalService
        svc = WealthArrivalService()
        result = WealthArrivalResult(user_id=1, data_quality="insufficient")
        svc._build_headline(result)
        assert "Connect" in result.headline_sentence


# ── Integration: project_safe with mocked DB ─────────────────────────────────

class TestProjectSafeIntegration:
    """Test project_safe end-to-end with mocked FinancialGraphService and IncomeProfile."""

    def test_returns_result_with_three_scenarios(self):
        from core.wealth_arrival_service import WealthArrivalService

        fake_ctx = _make_graph_context()
        fake_profile = _make_profile()

        with patch(
            "core.wealth_arrival_service.FinancialGraphService"
        ) as MockGFS, patch(
            "core.wealth_arrival_service.IncomeProfile"
        ) as MockIP:
            MockGFS.return_value.build_graph_safe.return_value = fake_ctx
            MockIP.objects.filter.return_value.first.return_value = fake_profile

            svc = WealthArrivalService()
            user = MagicMock()
            user.pk = 42

            result = svc.project_safe(user, target_net_worth=1_000_000)

        assert result.user_id == 42
        assert len(result.scenarios) == 3
        assert result.primary is not None
        assert result.current_net_worth == (50_000 + 15_000 - 5_000)  # 60_000
        assert result.annual_contribution == pytest.approx(1_450 * 12)

    def test_graceful_on_none_context(self):
        """When FinancialGraphService returns None, result is degraded but not an exception."""
        from core.wealth_arrival_service import WealthArrivalService

        with patch(
            "core.wealth_arrival_service.FinancialGraphService"
        ) as MockGFS:
            MockGFS.return_value.build_graph_safe.return_value = None

            svc = WealthArrivalService()
            user = MagicMock()
            user.pk = 99

            result = svc.project_safe(user)

        assert result.data_quality == "insufficient"
        assert "Connect" in result.headline_sentence

    def test_savings_rate_calculated(self):
        from core.wealth_arrival_service import WealthArrivalService

        fake_ctx = _make_graph_context(monthly_income=8_000, investable_surplus=1_600)
        fake_profile = _make_profile()

        with patch(
            "core.wealth_arrival_service.FinancialGraphService"
        ) as MockGFS, patch(
            "core.wealth_arrival_service.IncomeProfile"
        ) as MockIP:
            MockGFS.return_value.build_graph_safe.return_value = fake_ctx
            MockIP.objects.filter.return_value.first.return_value = fake_profile

            result = WealthArrivalService().project_safe(MagicMock())

        # 1600 / 8000 = 20 %
        assert result.savings_rate_pct == pytest.approx(20.0)
