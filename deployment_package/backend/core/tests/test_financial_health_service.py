"""
Tests for FinancialHealthService

Run with:
  DJANGO_SECRET_KEY=test DJANGO_SETTINGS_MODULE=richesreach.settings \
    PYTHONPATH=. .venv/bin/python -m pytest core/tests/test_financial_health_service.py -v
"""
import pytest
from unittest.mock import MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def fake_ctx(
    portfolio=50_000,
    savings=15_000,
    cc_balance=5_000,
    cc_min=200,
    cc_util=0.20,      # 20%
    monthly_income=8_000,
    emergency_months=0.0,
    credit_score=720,
):
    ctx = MagicMock()
    ctx.portfolio_total_value = portfolio
    ctx.total_savings_balance = savings
    ctx.total_cc_balance = cc_balance
    ctx.total_cc_min_payments = cc_min
    ctx.avg_credit_utilization = cc_util
    ctx.estimated_monthly_income = monthly_income
    ctx.emergency_fund_months = emergency_months
    ctx.best_credit_score = credit_score
    return ctx


def make_service_with_ctx(ctx):
    from core.financial_health_service import FinancialHealthService
    svc = FinancialHealthService()
    with patch("core.financial_graph_service.FinancialGraphService") as MockGFS:
        MockGFS.return_value.build_graph_safe.return_value = ctx
        user = MagicMock(); user.pk = 1
        result = svc.score(user)
    return result


# ── _tier_score ───────────────────────────────────────────────────────────────

class TestTierScore:
    def test_savings_rate_excellent(self):
        from core.financial_health_service import _tier_score, SAVINGS_TIERS
        assert _tier_score(25, SAVINGS_TIERS) == 100

    def test_savings_rate_good(self):
        from core.financial_health_service import _tier_score, SAVINGS_TIERS
        assert _tier_score(17, SAVINGS_TIERS) == 80

    def test_savings_rate_ok(self):
        from core.financial_health_service import _tier_score, SAVINGS_TIERS
        assert _tier_score(12, SAVINGS_TIERS) == 60

    def test_savings_rate_poor(self):
        from core.financial_health_service import _tier_score, SAVINGS_TIERS
        assert _tier_score(7, SAVINGS_TIERS) == 40

    def test_savings_rate_terrible(self):
        from core.financial_health_service import _tier_score, SAVINGS_TIERS
        assert _tier_score(2, SAVINGS_TIERS) == 20

    def test_emergency_6_months(self):
        from core.financial_health_service import _tier_score, EMERGENCY_TIERS
        assert _tier_score(6, EMERGENCY_TIERS) == 100

    def test_emergency_3_months(self):
        from core.financial_health_service import _tier_score, EMERGENCY_TIERS
        # 4.5 months: >= 3 threshold → score 75
        assert _tier_score(4.5, EMERGENCY_TIERS) == 75

    def test_emergency_half_month(self):
        from core.financial_health_service import _tier_score, EMERGENCY_TIERS
        assert _tier_score(0.6, EMERGENCY_TIERS) == 25   # >= 0.5 threshold

    def test_emergency_below_half(self):
        from core.financial_health_service import _tier_score, EMERGENCY_TIERS
        assert _tier_score(0.2, EMERGENCY_TIERS) == 0

    def test_debt_low(self):
        from core.financial_health_service import _tier_score, DEBT_TIERS
        assert _tier_score(5, DEBT_TIERS) == 100

    def test_debt_ok(self):
        from core.financial_health_service import _tier_score, DEBT_TIERS
        assert _tier_score(25, DEBT_TIERS) == 60

    def test_debt_high(self):
        from core.financial_health_service import _tier_score, DEBT_TIERS
        assert _tier_score(50, DEBT_TIERS) == 20

    def test_credit_excellent(self):
        from core.financial_health_service import _tier_score, CREDIT_TIERS
        assert _tier_score(5, CREDIT_TIERS) == 100

    def test_credit_good(self):
        from core.financial_health_service import _tier_score, CREDIT_TIERS
        assert _tier_score(20, CREDIT_TIERS) == 75

    def test_credit_maxed(self):
        from core.financial_health_service import _tier_score, CREDIT_TIERS
        assert _tier_score(90, CREDIT_TIERS) == 0


# ── Pillar scorers ────────────────────────────────────────────────────────────

class TestSavingsRatePillar:
    def setup_method(self):
        from core.financial_health_service import FinancialHealthService
        self.svc = FinancialHealthService()

    def test_none_returns_d(self):
        p = self.svc._score_savings_rate(None, 0)
        assert p.grade == 'D'
        assert p.value is None

    def test_20pct_is_a(self):
        p = self.svc._score_savings_rate(20, 8_000)
        assert p.score == 100
        assert p.grade == 'A'

    def test_10pct_is_c(self):
        p = self.svc._score_savings_rate(10, 8_000)
        assert p.grade == 'C'

    def test_3pct_is_f(self):
        p = self.svc._score_savings_rate(3, 8_000)
        assert p.grade == 'F'

    def test_action_pushes_towards_20(self):
        p = self.svc._score_savings_rate(15, 8_000)
        assert "20%" in p.action

    def test_weight_is_30pct(self):
        p = self.svc._score_savings_rate(15, 8_000)
        assert p.weight == pytest.approx(0.30)


class TestEmergencyFundPillar:
    def setup_method(self):
        from core.financial_health_service import FinancialHealthService
        self.svc = FinancialHealthService()

    def test_none_returns_f(self):
        p = self.svc._score_emergency_fund(None)
        assert p.grade == 'F'

    def test_6_months_is_a(self):
        p = self.svc._score_emergency_fund(6.5)
        assert p.score == 100

    def test_4_months_is_b(self):
        p = self.svc._score_emergency_fund(4)
        assert p.score == 75

    def test_0_months_is_f(self):
        p = self.svc._score_emergency_fund(0.1)
        assert p.score == 0

    def test_weight_is_30pct(self):
        p = self.svc._score_emergency_fund(4)
        assert p.weight == pytest.approx(0.30)


class TestDebtRatioPillar:
    def setup_method(self):
        from core.financial_health_service import FinancialHealthService
        self.svc = FinancialHealthService()

    def test_none_returns_assumed_good(self):
        p = self.svc._score_debt_ratio(None)
        assert p.score == 75   # assumed minimal debt

    def test_5pct_is_a(self):
        p = self.svc._score_debt_ratio(5)
        assert p.score == 100

    def test_35pct_is_d(self):
        p = self.svc._score_debt_ratio(35)
        assert p.score == 40

    def test_50pct_is_f(self):
        p = self.svc._score_debt_ratio(50)
        assert p.score == 20

    def test_weight_is_25pct(self):
        p = self.svc._score_debt_ratio(10)
        assert p.weight == pytest.approx(0.25)


class TestCreditUtilizationPillar:
    def setup_method(self):
        from core.financial_health_service import FinancialHealthService
        self.svc = FinancialHealthService()

    def test_none_returns_c(self):
        p = self.svc._score_credit_utilization(None)
        assert p.score == 75

    def test_5pct_is_a(self):
        p = self.svc._score_credit_utilization(5)
        assert p.score == 100

    def test_25pct_is_b(self):
        p = self.svc._score_credit_utilization(25)
        assert p.score == 75

    def test_60pct_is_d(self):
        p = self.svc._score_credit_utilization(60)
        assert p.score == 25

    def test_80pct_is_f(self):
        p = self.svc._score_credit_utilization(80)
        assert p.score == 0

    def test_weight_is_15pct(self):
        p = self.svc._score_credit_utilization(20)
        assert p.weight == pytest.approx(0.15)


# ── Composite score ───────────────────────────────────────────────────────────

class TestCompositeScore:
    def test_four_pillars_present(self):
        ctx = fake_ctx(monthly_income=8_000, cc_min=200, cc_util=0.20, savings=15_000)
        result = make_service_with_ctx(ctx)
        assert len(result.pillars) == 4
        names = {p.name for p in result.pillars}
        assert names == {'savings_rate', 'emergency_fund', 'debt_ratio', 'credit_utilization'}

    def test_composite_is_weighted_average(self):
        ctx = fake_ctx(monthly_income=8_000, cc_min=200, cc_util=0.20, savings=15_000)
        result = make_service_with_ctx(ctx)
        expected = sum(p.score * p.weight for p in result.pillars) / sum(p.weight for p in result.pillars)
        assert result.score == pytest.approx(expected, rel=1e-4)

    def test_perfect_finances_score_high(self):
        # 20%+ savings, 6+ months emergency, <10% DTI, <10% utilization
        ctx = fake_ctx(
            monthly_income=10_000,
            savings=60_000,   # 7.5 months of expenses (60k / 8k*0.8)
            cc_balance=500,
            cc_min=25,
            cc_util=0.05,     # 5%
        )
        result = make_service_with_ctx(ctx)
        assert result.score >= 80
        assert result.grade in ('A', 'B')

    def test_no_context_returns_insufficient(self):
        from core.financial_health_service import FinancialHealthService
        svc = FinancialHealthService()
        with patch("core.financial_graph_service.FinancialGraphService") as MockGFS:
            MockGFS.return_value.build_graph_safe.return_value = None
            user = MagicMock(); user.pk = 1
            result = svc.score(user)
        assert result.data_quality == "insufficient"
        assert result.score == 0.0

    def test_score_safe_never_raises(self):
        from core.financial_health_service import FinancialHealthService
        svc = FinancialHealthService()
        with patch("core.financial_graph_service.FinancialGraphService") as MockGFS:
            MockGFS.return_value.build_graph_safe.side_effect = RuntimeError("boom")
            user = MagicMock(); user.pk = 2
            result = svc.score_safe(user)
        assert result.data_quality == "insufficient"
        assert result.headline_sentence  # not empty

    def test_grade_a_when_score_above_90(self):
        from core.financial_health_service import _letter
        assert _letter(92) == 'A'

    def test_grade_b(self):
        from core.financial_health_service import _letter
        assert _letter(85) == 'B'

    def test_grade_c(self):
        from core.financial_health_service import _letter
        assert _letter(72) == 'C'

    def test_grade_d(self):
        from core.financial_health_service import _letter
        assert _letter(60) == 'D'

    def test_grade_f(self):
        from core.financial_health_service import _letter
        assert _letter(40) == 'F'


# ── Headline ──────────────────────────────────────────────────────────────────

class TestHeadline:
    def test_headline_contains_score(self):
        ctx = fake_ctx(monthly_income=8_000, cc_min=200, cc_util=0.20, savings=15_000)
        result = make_service_with_ctx(ctx)
        assert "/100" in result.headline_sentence

    def test_headline_contains_grade(self):
        ctx = fake_ctx(monthly_income=8_000, cc_min=200, cc_util=0.20, savings=15_000)
        result = make_service_with_ctx(ctx)
        assert "Grade" in result.headline_sentence

    def test_weak_pillar_action_appended(self):
        # Zero emergency fund → should append action
        ctx = fake_ctx(monthly_income=8_000, savings=0, cc_min=0, cc_util=0.05)
        result = make_service_with_ctx(ctx)
        # emergency fund pillar will be weak; headline should contain action nudge
        assert len(result.headline_sentence) > 50  # has appended text

    def test_high_score_says_excellent(self):
        ctx = fake_ctx(
            monthly_income=10_000, savings=70_000,
            cc_balance=200, cc_min=10, cc_util=0.02,
        )
        result = make_service_with_ctx(ctx)
        if result.score >= 90:
            assert "excellent" in result.headline_sentence


# ── Raw inputs stored ─────────────────────────────────────────────────────────

class TestRawInputs:
    def test_monthly_income_stored(self):
        ctx = fake_ctx(monthly_income=8_000)
        result = make_service_with_ctx(ctx)
        assert result.monthly_income == pytest.approx(8_000)

    def test_savings_rate_computed(self):
        # income=8000, cc_min=200
        # investable = max(8000*0.20 - 200, 0) = max(1600-200,0) = 1400
        # savings_rate = 1400/8000 = 17.5%
        ctx = fake_ctx(monthly_income=8_000, cc_min=200)
        result = make_service_with_ctx(ctx)
        assert result.savings_rate_pct == pytest.approx(17.5)

    def test_dti_computed(self):
        # dti = 200 / 8000 = 2.5%
        ctx = fake_ctx(monthly_income=8_000, cc_min=200)
        result = make_service_with_ctx(ctx)
        assert result.debt_to_income_pct == pytest.approx(2.5)

    def test_emergency_months_computed(self):
        # savings=15000, monthly_expenses = 8000*0.80 = 6400, months = 15000/6400 ≈ 2.34
        ctx = fake_ctx(monthly_income=8_000, savings=15_000)
        result = make_service_with_ctx(ctx)
        assert result.emergency_fund_months == pytest.approx(15_000 / (8_000 * 0.80), rel=0.01)

    def test_credit_utilization_stored(self):
        ctx = fake_ctx(cc_util=0.22)
        result = make_service_with_ctx(ctx)
        assert result.credit_utilization_pct == pytest.approx(22.0)
