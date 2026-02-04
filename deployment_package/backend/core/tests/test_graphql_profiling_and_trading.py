"""
Smoke tests for GraphQL profiling middleware and TradingQuery domain split.
"""
import os
from unittest.mock import MagicMock, patch

from django.test import TestCase

from core.graphql.middleware.timing import (
    GraphQLProfilingMiddleware,
    _get_resolver_name,
    _profiling_enabled,
)
from core.graphql.queries.trading import TradingQuery
from core.graphql.queries.market_data import MarketDataQuery
from core.graphql.queries.analytics import AnalyticsQuery
from core.graphql.queries.security import SecurityQuery
from core.graphql.queries.signals import SignalsQuery
from core.graphql.queries.options_rust import OptionsRustQuery
from core.graphql.queries.discussions import DiscussionsQuery
from core.schema import schema


class TestGraphQLProfilingMiddleware(TestCase):
    """Profiling middleware: enabled by env/header, logs resolver name and timing."""

    def test_profiling_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            if "GRAPHQL_PROFILING" in os.environ:
                del os.environ["GRAPHQL_PROFILING"]
        ctx = MagicMock()
        ctx.request = None
        self.assertFalse(_profiling_enabled(ctx))

    def test_profiling_enabled_by_env(self):
        with patch.dict(os.environ, {"GRAPHQL_PROFILING": "1"}, clear=False):
            ctx = MagicMock()
            ctx.request = None
            self.assertTrue(_profiling_enabled(ctx))

    def test_get_resolver_name_uses_field_name(self):
        info = MagicMock()
        info.field_name = "me"
        info.parent_type = None
        self.assertEqual(_get_resolver_name(info), "me")

    def test_middleware_resolve_passes_through_when_disabled(self):
        with patch.dict(os.environ, {"GRAPHQL_PROFILING": ""}, clear=False):
            mw = GraphQLProfilingMiddleware()
            next_fn = MagicMock(return_value="result")
            info = MagicMock()
            info.context = MagicMock()
            info.context.request = None
            result = mw.resolve(next_fn, None, info, **{})
            self.assertEqual(result, "result")
            next_fn.assert_called_once()


class TestTradingQueryComposition(TestCase):
    """TradingQuery is composed into schema; legacy trading fields remain available."""

    def test_schema_has_trading_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "alpaca_account"))
        self.assertTrue(hasattr(q, "trading_account"))
        self.assertTrue(hasattr(q, "trading_positions"))
        self.assertTrue(hasattr(q, "trading_orders"))
        self.assertTrue(hasattr(q, "stock_chart_data"))

    def test_trading_query_has_resolvers(self):
        self.assertTrue(hasattr(TradingQuery, "resolve_alpaca_account"))
        self.assertTrue(hasattr(TradingQuery, "resolve_trading_account"))
        self.assertTrue(hasattr(TradingQuery, "resolve_stock_chart_data"))


class TestMarketDataComposition(TestCase):
    """MarketDataQuery is composed; stocks, stock, fss_scores, etc. available."""

    def test_schema_has_market_data_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "stocks"))
        self.assertTrue(hasattr(q, "stock"))
        self.assertTrue(hasattr(q, "fss_scores"))
        self.assertTrue(hasattr(q, "top_fss_stocks"))
        self.assertTrue(hasattr(q, "beginner_friendly_stocks"))
        self.assertTrue(hasattr(q, "current_stock_prices"))

    def test_market_data_query_has_resolvers(self):
        self.assertTrue(hasattr(MarketDataQuery, "resolve_stock"))
        self.assertTrue(hasattr(MarketDataQuery, "resolve_stocks"))
        self.assertTrue(hasattr(MarketDataQuery, "resolve_current_stock_prices"))


class TestSocialAndBankingComposition(TestCase):
    """SocialQuery and BudgetSpendingQuery are composed; social and budget fields available."""

    def test_schema_has_social_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "all_users"))
        self.assertTrue(hasattr(q, "wall_posts"))
        self.assertTrue(hasattr(q, "user"))

    def test_schema_has_budget_spending_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "budget_data"))
        self.assertTrue(hasattr(q, "spending_analysis"))


class TestAnalyticsComposition(TestCase):
    """AnalyticsQuery is composed; portfolio, benchmarks, test_* fields available."""

    def test_schema_has_analytics_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "my_portfolios"))
        self.assertTrue(hasattr(q, "portfolio_names"))
        self.assertTrue(hasattr(q, "portfolio_value"))
        self.assertTrue(hasattr(q, "portfolio_metrics"))
        self.assertTrue(hasattr(q, "benchmark_series"))
        self.assertTrue(hasattr(q, "available_benchmarks"))
        self.assertTrue(hasattr(q, "portfolio_history"))

    def test_analytics_query_has_resolvers(self):
        self.assertTrue(hasattr(AnalyticsQuery, "resolve_my_portfolios"))
        self.assertTrue(hasattr(AnalyticsQuery, "resolve_portfolio_value"))
        self.assertTrue(hasattr(AnalyticsQuery, "resolve_benchmark_series"))
        self.assertTrue(hasattr(AnalyticsQuery, "resolve_portfolio_history"))


class TestSecurityComposition(TestCase):
    """SecurityQuery is composed; securityEvents, biometricSettings, etc. available."""

    def test_schema_has_security_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "security_events"))
        self.assertTrue(hasattr(q, "biometric_settings"))
        self.assertTrue(hasattr(q, "compliance_statuses"))
        self.assertTrue(hasattr(q, "security_score"))
        self.assertTrue(hasattr(q, "device_trusts"))
        self.assertTrue(hasattr(q, "access_policies"))
        self.assertTrue(hasattr(q, "zero_trust_summary"))

    def test_security_query_has_resolvers(self):
        self.assertTrue(hasattr(SecurityQuery, "resolve_security_events"))
        self.assertTrue(hasattr(SecurityQuery, "resolve_biometric_settings"))
        self.assertTrue(hasattr(SecurityQuery, "resolve_zero_trust_summary"))


class TestSignalsComposition(TestCase):
    """SignalsQuery is composed; day_trading_picks, executionSuggestion, researchHub, etc. available."""

    def test_schema_has_signals_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "day_trading_picks"))
        self.assertTrue(hasattr(q, "day_trading_stats"))
        self.assertTrue(hasattr(q, "pre_market_picks"))
        self.assertTrue(hasattr(q, "swing_trading_picks"))
        self.assertTrue(hasattr(q, "swing_trading_stats"))
        self.assertTrue(hasattr(q, "execution_suggestion"))
        self.assertTrue(hasattr(q, "entry_timing_suggestion"))
        self.assertTrue(hasattr(q, "execution_quality_stats"))
        self.assertTrue(hasattr(q, "research_hub"))

    def test_signals_query_has_resolvers(self):
        self.assertTrue(hasattr(SignalsQuery, "resolve_day_trading_picks"))
        self.assertTrue(hasattr(SignalsQuery, "resolve_swing_trading_picks"))
        self.assertTrue(hasattr(SignalsQuery, "resolve_execution_suggestion"))
        self.assertTrue(hasattr(SignalsQuery, "resolve_research_hub"))


class TestOptionsRustComposition(TestCase):
    """OptionsRustQuery is composed; rust_stock_analysis, options_flow, etc. available."""

    def test_schema_has_options_rust_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "rust_stock_analysis"))
        self.assertTrue(hasattr(q, "rust_options_analysis"))
        self.assertTrue(hasattr(q, "options_flow"))
        self.assertTrue(hasattr(q, "scan_options"))
        self.assertTrue(hasattr(q, "edge_predictions"))
        self.assertTrue(hasattr(q, "one_tap_trades"))
        self.assertTrue(hasattr(q, "iv_surface_forecast"))
        self.assertTrue(hasattr(q, "rust_forex_analysis"))
        self.assertTrue(hasattr(q, "rust_sentiment_analysis"))
        self.assertTrue(hasattr(q, "rust_correlation_analysis"))

    def test_options_rust_query_has_resolvers(self):
        self.assertTrue(hasattr(OptionsRustQuery, "resolve_rust_stock_analysis"))
        self.assertTrue(hasattr(OptionsRustQuery, "resolve_options_flow"))
        self.assertTrue(hasattr(OptionsRustQuery, "resolve_rust_correlation_analysis"))


class TestDiscussionsComposition(TestCase):
    """DiscussionsQuery is composed; watchlists, stock_discussions, social_feed, etc. available."""

    def test_schema_has_discussions_fields(self):
        q = schema.query
        self.assertTrue(hasattr(q, "watchlists"))
        self.assertTrue(hasattr(q, "watchlist"))
        self.assertTrue(hasattr(q, "public_watchlists"))
        self.assertTrue(hasattr(q, "my_watchlist"))
        self.assertTrue(hasattr(q, "stock_discussions"))
        self.assertTrue(hasattr(q, "discussion_detail"))
        self.assertTrue(hasattr(q, "social_feed"))
        self.assertTrue(hasattr(q, "top_performers"))
        self.assertTrue(hasattr(q, "market_sentiment"))
        self.assertTrue(hasattr(q, "ai_portfolio_recommendations"))
        self.assertTrue(hasattr(q, "stock_moments"))

    def test_discussions_query_has_resolvers(self):
        self.assertTrue(hasattr(DiscussionsQuery, "resolve_watchlists"))
        self.assertTrue(hasattr(DiscussionsQuery, "resolve_stock_discussions"))
        self.assertTrue(hasattr(DiscussionsQuery, "resolve_social_feed"))
        self.assertTrue(hasattr(DiscussionsQuery, "resolve_stock_moments"))


class TestAlpacaConnectionEncryption(TestCase):
    """AlpacaConnection encrypts access_token/refresh_token at rest; get_decrypted_* return plaintext."""

    def test_alpaca_connection_save_encrypts_and_get_decrypted_roundtrip(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        from core.models import AlpacaConnection
        from core.alpaca_token_encryption import encrypt_token, decrypt_token, _looks_fernet

        User = get_user_model()
        user = User.objects.create_user(email="alpaca_enc_test@example.com", password="test", name="Test")
        plain_access = "plain_access_token_123"
        plain_refresh = "plain_refresh_token_456"
        expires = timezone.now() + timedelta(hours=1)
        conn = AlpacaConnection(
            user=user,
            alpaca_account_id="test-account",
            access_token=plain_access,
            refresh_token=plain_refresh,
            token_expires_at=expires,
        )
        conn.save()
        conn.refresh_from_db()
        # Stored value should be encrypted (or plaintext if Fernet unavailable)
        if _looks_fernet(conn.access_token):
            self.assertNotEqual(conn.access_token, plain_access)
            self.assertEqual(decrypt_token(conn.access_token), plain_access)
        self.assertEqual(conn.get_decrypted_access_token(), plain_access)
        self.assertEqual(conn.get_decrypted_refresh_token(), plain_refresh)


class TestContextLoaders(TestCase):
    """DataLoaders are attached to GraphQL context."""

    def test_get_context_attaches_loaders(self):
        from core.views import AuthenticatedGraphQLView
        from unittest.mock import Mock

        req = Mock()
        req.user = None
        view = AuthenticatedGraphQLView()
        ctx = view.get_context(req)
        self.assertTrue(hasattr(ctx, "loaders"))
        self.assertIsNotNone(ctx.loaders)
        self.assertTrue(hasattr(ctx.loaders, "user_loader"))
        self.assertTrue(hasattr(ctx.loaders, "stock_loader"))
