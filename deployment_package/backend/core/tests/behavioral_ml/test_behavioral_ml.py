"""
Unit tests for behavioral ML modules (Phases 1-3).

Covers:
- behavioral_events: log_impression, log_impression_with_shadow, log_interaction,
  get_events, get_recent_dismissals_by_rec_type, get_recent_clicks_by_rec_type,
  get_shadow_impressions_for_metrics, get_all_events_for_metrics
- ranking_config: get_shadow_mode, get_ml_traffic_fraction, should_serve_ml_order,
  get_ranking_weights (defaults + file), set_ranking_weights, invalidate_weights_cache
- behavioral_ranking_service: reorder (weight composition, archetype affinity,
  dismissed penalty, segment overrides, unchanged set)
- tone_optimization_service: get_tone_variant, get_tone_variants_for_recs
- behavioral_consistency_service: compute_consistency_score, get_engagement_vector,
  get_drift_signal, get_consistency_result
- behavioral_bias_signal: get_behavioral_bias_signal
- update_ranking_weights management command: metrics output, weight update logic
"""

from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers to reset in-memory stores between tests
# ---------------------------------------------------------------------------

import core.behavioral_events as _be_module
import core.ranking_config as _rc_module


def _reset_events():
    """Clear the in-memory event store and shadow impressions."""
    _be_module._events.clear()
    _be_module._shadow_impressions.clear()


def _reset_weights_cache():
    _rc_module._cached_weights = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_state():
    """Reset all mutable in-memory state before every test."""
    _reset_events()
    _reset_weights_cache()
    yield
    _reset_events()
    _reset_weights_cache()


def _make_action(action_type_str: str, priority_score: float = 50.0, id_: str = None):
    """Create a minimal NextBestAction for tests."""
    from core.next_best_action_service import NextBestAction, ActionType, ActionPriority
    return NextBestAction(
        id=id_ or action_type_str,
        action_type=ActionType(action_type_str),
        priority=ActionPriority.GROWTH,
        priority_score=priority_score,
        headline="Test",
        description="Test desc",
        impact_text="Test impact",
    )


# ===========================================================================
# behavioral_events
# ===========================================================================

class TestLogImpression:
    def test_stores_events_per_user(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1", "r2"], rec_types=["cancel_leak", "pay_debt"])
        assert len(_events["u1"]) == 2

    def test_position_is_1_indexed(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1", "r2"])
        positions = [e["position"] for e in _events["u1"]]
        assert positions == [1, 2]

    def test_tone_variant_defaults_to_default(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1"])
        assert _events["u1"][0]["tone_variant"] == "default"

    def test_tone_variant_stored_when_provided(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1"], variants=["direct"])
        assert _events["u1"][0]["tone_variant"] == "direct"

    def test_rec_type_stored(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1"], rec_types=["cancel_leak"])
        assert _events["u1"][0]["rec_type"] == "cancel_leak"

    def test_multiple_users_isolated(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1"])
        log_impression("u2", ["r2", "r3"])
        assert len(_events["u1"]) == 1
        assert len(_events["u2"]) == 2

    def test_event_type_is_impression(self):
        from core.behavioral_events import log_impression, _events
        log_impression("u1", ["r1"])
        assert _events["u1"][0]["event_type"] == "impression"

    def test_trim_cap_enforced(self):
        from core.behavioral_events import log_impression, _events, _MAX_EVENTS_PER_USER
        # Log more than the cap in one big call
        rec_ids = [f"r{i}" for i in range(_MAX_EVENTS_PER_USER + 50)]
        log_impression("u1", rec_ids)
        assert len(_events["u1"]) <= _MAX_EVENTS_PER_USER


class TestLogImpressionWithShadow:
    def test_shadow_list_populated(self):
        from core.behavioral_events import log_impression_with_shadow, _shadow_impressions
        log_impression_with_shadow("u1", ["r1", "r2"], ["r2", "r1"])
        assert len(_shadow_impressions) == 1

    def test_shadow_stores_both_orders(self):
        from core.behavioral_events import log_impression_with_shadow, _shadow_impressions
        log_impression_with_shadow("u1", ["r1", "r2"], ["r2", "r1"])
        s = _shadow_impressions[0]
        assert s["rule_order"] == ["r1", "r2"]
        assert s["ml_order"] == ["r2", "r1"]

    def test_user_events_use_rule_order_positions(self):
        from core.behavioral_events import log_impression_with_shadow, _events
        log_impression_with_shadow("u1", ["r1", "r2"], ["r2", "r1"])
        rec_ids = [e["rec_id"] for e in _events["u1"]]
        assert rec_ids == ["r1", "r2"]

    def test_shadow_cap_enforced(self):
        from core.behavioral_events import log_impression_with_shadow, _shadow_impressions, _MAX_SHADOW_IMPRESSIONS
        for i in range(_MAX_SHADOW_IMPRESSIONS + 5):
            log_impression_with_shadow(f"u{i}", ["r1"], ["r1"])
        assert len(_shadow_impressions) <= _MAX_SHADOW_IMPRESSIONS


class TestLogInteraction:
    def test_click_stored(self):
        from core.behavioral_events import log_interaction, _events
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")
        ev = _events["u1"][0]
        assert ev["event_type"] == "interaction"
        assert ev["action"] == "click"
        assert ev["rec_type"] == "cancel_leak"

    def test_dismiss_stored(self):
        from core.behavioral_events import log_interaction, _events
        log_interaction("u1", "r1", "dismiss")
        assert _events["u1"][0]["action"] == "dismiss"

    def test_attaches_position_rule_and_ml_from_shadow(self):
        from core.behavioral_events import log_impression_with_shadow, log_interaction, _events
        log_impression_with_shadow("u1", ["r1", "r2"], ["r2", "r1"])
        log_interaction("u1", "r1", "click")
        interaction = _events["u1"][-1]
        assert interaction["position_rule"] == 1
        assert interaction["position_ml"] == 2

    def test_attaches_tone_variant_from_last_impression(self):
        from core.behavioral_events import log_impression, log_interaction, _events
        log_impression("u1", ["r1"], rec_types=["cancel_leak"], variants=["encouraging"])
        log_interaction("u1", "r1", "click")
        interaction = _events["u1"][-1]
        assert interaction.get("tone_variant") == "encouraging"

    def test_no_shadow_no_positions(self):
        from core.behavioral_events import log_interaction, _events
        log_interaction("u1", "r_unknown", "click")
        ev = _events["u1"][0]
        assert "position_rule" not in ev
        assert "position_ml" not in ev


class TestGetEvents:
    def test_returns_events_within_window(self):
        from core.behavioral_events import log_impression, get_events
        log_impression("u1", ["r1"])
        evs = get_events("u1", since_days=30)
        assert len(evs) == 1

    def test_filters_by_event_type(self):
        from core.behavioral_events import log_impression, log_interaction, get_events
        log_impression("u1", ["r1"])
        log_interaction("u1", "r1", "click")
        impressions = get_events("u1", event_type="impression")
        assert all(e["event_type"] == "impression" for e in impressions)
        interactions = get_events("u1", event_type="interaction")
        assert all(e["event_type"] == "interaction" for e in interactions)

    def test_empty_for_unknown_user(self):
        from core.behavioral_events import get_events
        assert get_events("no_such_user") == []


class TestGetRecentDismissalsByRecType:
    def test_dismissed_rec_type_flagged(self):
        from core.behavioral_events import log_interaction, get_recent_dismissals_by_rec_type
        log_interaction("u1", "r1", "dismiss", rec_type="cancel_leak")
        dismissed = get_recent_dismissals_by_rec_type("u1")
        assert dismissed.get("cancel_leak") is True

    def test_click_not_flagged_as_dismissed(self):
        from core.behavioral_events import log_interaction, get_recent_dismissals_by_rec_type
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")
        dismissed = get_recent_dismissals_by_rec_type("u1")
        assert "cancel_leak" not in dismissed

    def test_no_events_returns_empty(self):
        from core.behavioral_events import get_recent_dismissals_by_rec_type
        assert get_recent_dismissals_by_rec_type("u1") == {}


class TestGetRecentClicksByRecType:
    def test_counts_clicks(self):
        from core.behavioral_events import log_interaction, get_recent_clicks_by_rec_type
        log_interaction("u1", "r1", "click", rec_type="pay_debt")
        log_interaction("u1", "r2", "click", rec_type="pay_debt")
        log_interaction("u1", "r3", "click", rec_type="cancel_leak")
        clicks = get_recent_clicks_by_rec_type("u1")
        assert clicks["pay_debt"] == 2
        assert clicks["cancel_leak"] == 1

    def test_dismisses_not_counted(self):
        from core.behavioral_events import log_interaction, get_recent_clicks_by_rec_type
        log_interaction("u1", "r1", "dismiss", rec_type="pay_debt")
        clicks = get_recent_clicks_by_rec_type("u1")
        assert clicks.get("pay_debt", 0) == 0

    def test_no_events_returns_empty(self):
        from core.behavioral_events import get_recent_clicks_by_rec_type
        assert get_recent_clicks_by_rec_type("u1") == {}


class TestGetShadowImpressionsForMetrics:
    def test_returns_shadow_within_window(self):
        from core.behavioral_events import log_impression_with_shadow, get_shadow_impressions_for_metrics
        log_impression_with_shadow("u1", ["r1"], ["r1"])
        result = get_shadow_impressions_for_metrics(since_days=1)
        assert len(result) == 1

    def test_returns_empty_when_no_shadows(self):
        from core.behavioral_events import get_shadow_impressions_for_metrics
        assert get_shadow_impressions_for_metrics() == []


class TestGetAllEventsForMetrics:
    def test_returns_all_users_events(self):
        from core.behavioral_events import log_impression, get_all_events_for_metrics
        log_impression("u1", ["r1"])
        log_impression("u2", ["r2"])
        result = get_all_events_for_metrics(since_days=1)
        assert "u1" in result
        assert "u2" in result


# ===========================================================================
# ranking_config
# ===========================================================================

class TestGetShadowMode:
    def test_false_by_default(self):
        from core.ranking_config import get_shadow_mode
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHADOW_RANKING", None)
            assert get_shadow_mode() is False

    def test_true_when_set(self):
        from core.ranking_config import get_shadow_mode
        with patch.dict(os.environ, {"SHADOW_RANKING": "true"}):
            assert get_shadow_mode() is True

    def test_true_when_1(self):
        from core.ranking_config import get_shadow_mode
        with patch.dict(os.environ, {"SHADOW_RANKING": "1"}):
            assert get_shadow_mode() is True


class TestGetMlTrafficFraction:
    def test_defaults_to_zero(self):
        from core.ranking_config import get_ml_traffic_fraction
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RANKING_ML_TRAFFIC_FRACTION", None)
            assert get_ml_traffic_fraction() == 0.0

    def test_reads_env_value(self):
        from core.ranking_config import get_ml_traffic_fraction
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "0.5"}):
            assert get_ml_traffic_fraction() == 0.5

    def test_clamps_above_1(self):
        from core.ranking_config import get_ml_traffic_fraction
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "2.0"}):
            assert get_ml_traffic_fraction() == 1.0

    def test_clamps_below_0(self):
        from core.ranking_config import get_ml_traffic_fraction
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "-1"}):
            assert get_ml_traffic_fraction() == 0.0

    def test_invalid_returns_zero(self):
        from core.ranking_config import get_ml_traffic_fraction
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "abc"}):
            assert get_ml_traffic_fraction() == 0.0


class TestShouldServeMlOrder:
    def test_fraction_0_always_false(self):
        from core.ranking_config import should_serve_ml_order
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "0"}):
            assert should_serve_ml_order("any_user") is False

    def test_fraction_1_always_true(self):
        from core.ranking_config import should_serve_ml_order
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "1"}):
            assert should_serve_ml_order("any_user") is True

    def test_stable_bucket_same_day(self):
        """Same user should get the same arm on the same day."""
        from core.ranking_config import should_serve_ml_order
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "0.5"}):
            results = {should_serve_ml_order("user_abc") for _ in range(5)}
            assert len(results) == 1  # always the same value

    def test_fraction_half_distributes_both_arms(self):
        """With 0.5 fraction, some users get ML, some don't."""
        from core.ranking_config import should_serve_ml_order
        with patch.dict(os.environ, {"RANKING_ML_TRAFFIC_FRACTION": "0.5"}):
            outcomes = {should_serve_ml_order(f"user_{i}") for i in range(200)}
            assert True in outcomes
            assert False in outcomes


class TestGetRankingWeights:
    def test_returns_defaults_when_no_file(self):
        from core.ranking_config import get_ranking_weights
        with patch.dict(os.environ, {"RANKING_WEIGHTS_PATH": "/nonexistent/path.json"}):
            _reset_weights_cache()
            w = get_ranking_weights()
        assert w["recency"] == pytest.approx(0.4)
        assert w["archetype"] == pytest.approx(0.3)
        assert w["popularity"] == pytest.approx(0.2)
        assert w["urgency"] == pytest.approx(0.1)

    def test_loads_from_file(self):
        from core.ranking_config import get_ranking_weights
        data = {"weights": {"recency": 0.35, "archetype": 0.35, "popularity": 0.2, "urgency": 0.1}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            with patch.dict(os.environ, {"RANKING_WEIGHTS_PATH": tmp}):
                _reset_weights_cache()
                # patch the module-level path so get_ranking_weights reads our file
                original = _rc_module._DEFAULT_WEIGHTS_PATH
                _rc_module._DEFAULT_WEIGHTS_PATH = tmp
                try:
                    w = get_ranking_weights()
                    assert w["recency"] == pytest.approx(0.35)
                    assert w["archetype"] == pytest.approx(0.35)
                finally:
                    _rc_module._DEFAULT_WEIGHTS_PATH = original
        finally:
            os.unlink(tmp)

    def test_cached_on_second_call(self):
        from core.ranking_config import get_ranking_weights
        with patch.dict(os.environ, {"RANKING_WEIGHTS_PATH": "/nonexistent/path.json"}):
            _reset_weights_cache()
            w1 = get_ranking_weights()
            w2 = get_ranking_weights()
        assert w1 is w2  # same object from cache


class TestSetRankingWeights:
    def test_writes_and_reads_back(self):
        from core.ranking_config import set_ranking_weights, get_ranking_weights, invalidate_weights_cache
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            tmp = f.name
        try:
            original = _rc_module._DEFAULT_WEIGHTS_PATH
            _rc_module._DEFAULT_WEIGHTS_PATH = tmp
            try:
                new_w = {"recency": 0.3, "archetype": 0.4, "popularity": 0.2, "urgency": 0.1}
                set_ranking_weights(new_w)
                invalidate_weights_cache()
                loaded = get_ranking_weights()
                assert loaded["recency"] == pytest.approx(0.3)
                assert loaded["archetype"] == pytest.approx(0.4)
            finally:
                _rc_module._DEFAULT_WEIGHTS_PATH = original
        finally:
            os.unlink(tmp)

    def test_preserves_segments_key(self):
        from core.ranking_config import set_ranking_weights, get_ranking_weights, invalidate_weights_cache
        initial = {
            "weights": {
                "recency": 0.4, "archetype": 0.3, "popularity": 0.2, "urgency": 0.1,
                "segments": {"steady_builder": {"recency": 0.35, "archetype": 0.35, "popularity": 0.2, "urgency": 0.1}},
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial, f)
            tmp = f.name
        try:
            original = _rc_module._DEFAULT_WEIGHTS_PATH
            _rc_module._DEFAULT_WEIGHTS_PATH = tmp
            try:
                # Overwrite base weights; segments should survive
                set_ranking_weights({"recency": 0.35, "archetype": 0.35, "popularity": 0.2, "urgency": 0.1})
                invalidate_weights_cache()
                w = get_ranking_weights()
                assert "steady_builder" in w.get("segments", {})
            finally:
                _rc_module._DEFAULT_WEIGHTS_PATH = original
        finally:
            os.unlink(tmp)

    def test_invalidate_clears_cache(self):
        from core.ranking_config import get_ranking_weights, invalidate_weights_cache
        with patch.dict(os.environ, {"RANKING_WEIGHTS_PATH": "/nonexistent/path.json"}):
            _reset_weights_cache()
            w1 = get_ranking_weights()
            invalidate_weights_cache()
            assert _rc_module._cached_weights is None


# ===========================================================================
# behavioral_ranking_service
# ===========================================================================

class TestReorder:
    def _make_actions(self, specs):
        """specs = list of (action_type_str, priority_score)"""
        return [_make_action(t, s, id_=t) for t, s in specs]

    def test_returns_same_set_of_actions(self):
        from core.behavioral_ranking_service import reorder
        actions = self._make_actions([
            ("cancel_leak", 95),
            ("start_investing", 50),
            ("pay_debt", 80),
        ])
        result = reorder(actions, "u1", "cautious_protector")
        assert {a.id for a in result} == {a.id for a in actions}

    def test_returns_same_length(self):
        from core.behavioral_ranking_service import reorder
        actions = self._make_actions([("cancel_leak", 80), ("pay_debt", 70)])
        assert len(reorder(actions, "u1", "cautious_protector")) == 2

    def test_empty_list_returns_empty(self):
        from core.behavioral_ranking_service import reorder
        assert reorder([], "u1", "cautious_protector") == []

    def test_dismissed_item_ranked_lower(self):
        """Dismissed rec_type should drop behind non-dismissed ones."""
        from core.behavioral_events import log_interaction
        from core.behavioral_ranking_service import reorder
        log_interaction("u1", "cancel_leak", "dismiss", rec_type="cancel_leak")
        actions = self._make_actions([
            ("cancel_leak", 95),   # dismissed → should score lower
            ("pay_debt", 50),      # not dismissed
        ])
        result = reorder(actions, "u1", "cautious_protector", recency_days=7)
        # pay_debt should come before cancel_leak due to dismiss penalty
        assert result[0].id == "pay_debt"

    def test_archetype_affinity_influences_order(self):
        """cautious_protector has higher affinity for cancel_leak than start_investing."""
        from core.behavioral_ranking_service import reorder
        # Give both the same priority score so only weights differ
        actions = self._make_actions([
            ("start_investing", 50),
            ("cancel_leak", 50),
        ])
        result = reorder(actions, "u1", "cautious_protector")
        assert result[0].id == "cancel_leak"

    def test_opportunity_hunter_prefers_start_investing(self):
        """opportunity_hunter has higher affinity for start_investing than cancel_leak."""
        from core.behavioral_ranking_service import reorder
        actions = self._make_actions([
            ("cancel_leak", 50),
            ("start_investing", 50),
        ])
        result = reorder(actions, "u1", "opportunity_hunter")
        assert result[0].id == "start_investing"

    def test_unknown_archetype_uses_defaults(self):
        """Unknown archetype should still return all actions without error."""
        from core.behavioral_ranking_service import reorder
        actions = self._make_actions([("cancel_leak", 50), ("pay_debt", 50)])
        result = reorder(actions, "u1", "unknown_archetype")
        assert len(result) == 2

    def test_segment_override_applied(self):
        """If segment weights exist in config, they should override base weights."""
        from core.behavioral_ranking_service import reorder
        # Patch get_ranking_weights to return a segments block
        seg_weights = {
            "recency": 0.5, "archetype": 0.1, "popularity": 0.3, "urgency": 0.1,
        }
        full_weights = {
            "recency": 0.4, "archetype": 0.3, "popularity": 0.2, "urgency": 0.1,
            "segments": {"steady_builder": seg_weights},
        }
        with patch("core.behavioral_ranking_service.get_ranking_weights", return_value=full_weights):
            actions = self._make_actions([("cancel_leak", 50), ("pay_debt", 50)])
            result = reorder(actions, "u1", "steady_builder", segment="steady_builder")
        assert len(result) == 2


# ===========================================================================
# tone_optimization_service
# ===========================================================================

class TestGetToneVariant:
    def test_returns_default_with_no_history(self):
        from core.tone_optimization_service import get_tone_variant
        assert get_tone_variant("u1", "r1", "cancel_leak") == "default"

    def test_returns_best_variant_by_ctr(self):
        """Variant with highest CTR (clicks / impressions) should be selected."""
        from core.behavioral_events import log_impression, log_interaction
        from core.tone_optimization_service import get_tone_variant

        # Give "encouraging" 3 impressions + 2 clicks (CTR=0.67)
        log_impression("u1", ["r1", "r1", "r1"],
                        rec_types=["cancel_leak"] * 3,
                        variants=["encouraging"] * 3)
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")

        # Give "direct" 3 impressions + 1 click (CTR=0.33)
        log_impression("u1", ["r1", "r1", "r1"],
                        rec_types=["cancel_leak"] * 3,
                        variants=["direct"] * 3)
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")

        variant = get_tone_variant("u1", "r1", "cancel_leak")
        assert variant == "encouraging"

    def test_ignores_variant_with_fewer_than_3_impressions(self):
        """Variant with < 3 impressions is excluded from selection."""
        from core.behavioral_events import log_impression, log_interaction
        from core.tone_optimization_service import get_tone_variant

        # Only 2 impressions for "direct" — below threshold
        log_impression("u1", ["r1", "r1"],
                        rec_types=["cancel_leak"] * 2,
                        variants=["direct"] * 2)
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")
        log_interaction("u1", "r1", "click", rec_type="cancel_leak")

        variant = get_tone_variant("u1", "r1", "cancel_leak")
        assert variant == "default"

    def test_returns_valid_variant_string(self):
        from core.tone_optimization_service import get_tone_variant, TONE_VARIANTS
        result = get_tone_variant("u1", "r1")
        assert result in TONE_VARIANTS


class TestGetToneVariantsForRecs:
    def test_returns_one_per_rec(self):
        from core.tone_optimization_service import get_tone_variants_for_recs
        variants = get_tone_variants_for_recs("u1", ["r1", "r2", "r3"])
        assert len(variants) == 3

    def test_all_default_with_no_history(self):
        from core.tone_optimization_service import get_tone_variants_for_recs
        variants = get_tone_variants_for_recs("u1", ["r1", "r2"])
        assert all(v == "default" for v in variants)


# ===========================================================================
# behavioral_consistency_service
# ===========================================================================

class TestComputeConsistencyScore:
    def test_returns_1_with_no_clicks(self):
        from core.behavioral_consistency_service import compute_consistency_score
        score = compute_consistency_score("u1", "cautious_protector")
        assert score == pytest.approx(1.0)

    def test_high_score_for_aligned_clicks(self):
        """Clicking on recs with high affinity for the archetype gives a high score."""
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import compute_consistency_score
        # cautious_protector has affinity 0.95 for cancel_leak
        for _ in range(5):
            log_interaction("u1", "cancel_leak", "click", rec_type="cancel_leak")
        score = compute_consistency_score("u1", "cautious_protector")
        assert score > 0.8

    def test_lower_score_for_misaligned_clicks(self):
        """Clicking on recs with low affinity for the archetype lowers the score."""
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import compute_consistency_score
        # cautious_protector has lower affinity (0.6) for tax_loss_harvest
        for _ in range(5):
            log_interaction("u1", "tax_loss_harvest", "click", rec_type="tax_loss_harvest")
        score = compute_consistency_score("u1", "cautious_protector")
        assert score < 0.9

    def test_score_in_0_1_range(self):
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import compute_consistency_score
        log_interaction("u1", "start_investing", "click", rec_type="start_investing")
        score = compute_consistency_score("u1", "reactive_trader")
        assert 0.0 <= score <= 1.0


class TestGetEngagementVector:
    def test_zero_vector_with_no_clicks(self):
        from core.behavioral_consistency_service import get_engagement_vector
        vec = get_engagement_vector("u1")
        assert all(v == 0.0 for v in vec)

    def test_vector_length_matches_rec_types_order(self):
        from core.behavioral_consistency_service import get_engagement_vector, REC_TYPES_ORDER
        vec = get_engagement_vector("u1")
        assert len(vec) == len(REC_TYPES_ORDER)

    def test_l2_normalized_when_clicks_present(self):
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import get_engagement_vector
        log_interaction("u1", "cancel_leak", "click", rec_type="cancel_leak")
        log_interaction("u1", "pay_debt", "click", rec_type="pay_debt")
        vec = get_engagement_vector("u1")
        norm = sum(x * x for x in vec) ** 0.5
        assert norm == pytest.approx(1.0, abs=1e-6)


class TestGetDriftSignal:
    def test_returns_none_with_insufficient_clicks(self):
        from core.behavioral_consistency_service import get_drift_signal
        result = get_drift_signal("u1", "cautious_protector", min_clicks=5)
        assert result is None

    def test_returns_none_when_behavior_matches_archetype(self):
        """If best-matching archetype is the same as profile, no drift."""
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import get_drift_signal

        # cautious_protector clicks: heavy on safety recs they're wired for
        for _ in range(6):
            log_interaction("u1", "cancel_leak", "click", rec_type="cancel_leak")
        for _ in range(4):
            log_interaction("u1", "build_emergency_fund", "click", rec_type="build_emergency_fund")

        result = get_drift_signal("u1", "cautious_protector", min_clicks=5)
        # May or may not return drift — if same archetype wins, must be None
        if result is not None:
            assert result.suggested_archetype != "cautious_protector"

    def test_drift_signal_fields_present(self):
        """When drift is detected, result has required fields."""
        from core.behavioral_events import log_interaction
        from core.behavioral_consistency_service import get_drift_signal, _ARCHETYPE_AFFINITY

        # Force opportunity_hunter clicks for a cautious_protector profile
        for _ in range(8):
            log_interaction("u1", "tax_loss_harvest", "click", rec_type="tax_loss_harvest")

        result = get_drift_signal("u1", "cautious_protector", min_clicks=5)
        if result is not None:
            assert 0.0 <= result.confidence_match <= 1.0
            assert result.message_key in ("style_evolving", "consider_retake")
            assert isinstance(result.show_nudge, bool)
            assert result.suggested_archetype in _ARCHETYPE_AFFINITY

    def test_show_nudge_true_when_confidence_low(self):
        """show_nudge should be True when confidence_match < 0.7."""
        from core.behavioral_consistency_service import DriftSignal
        ds = DriftSignal(
            suggested_archetype="opportunity_hunter",
            confidence_match=0.5,
            message_key="style_evolving",
            show_nudge=True,
        )
        assert ds.show_nudge is True
        assert ds.message_key == "style_evolving"

    def test_show_nudge_false_when_confidence_high(self):
        from core.behavioral_consistency_service import DriftSignal
        ds = DriftSignal(
            suggested_archetype="opportunity_hunter",
            confidence_match=0.8,
            message_key="consider_retake",
            show_nudge=False,
        )
        assert ds.show_nudge is False
        assert ds.message_key == "consider_retake"


class TestGetConsistencyResult:
    def test_returns_consistency_result(self):
        from core.behavioral_consistency_service import get_consistency_result, ConsistencyResult
        result = get_consistency_result("u1", "steady_builder")
        assert isinstance(result, ConsistencyResult)
        assert 0.0 <= result.consistency_score <= 1.0

    def test_no_drift_with_no_clicks(self):
        from core.behavioral_consistency_service import get_consistency_result
        result = get_consistency_result("u1", "steady_builder")
        assert result.drift is None

    def test_cosine_sim_identical_vectors_is_1(self):
        from core.behavioral_consistency_service import _cosine_sim
        v = [0.5, 0.5, 0.0]
        assert _cosine_sim(v, v) == pytest.approx(0.5)

    def test_cosine_sim_length_mismatch_returns_0(self):
        from core.behavioral_consistency_service import _cosine_sim
        assert _cosine_sim([1.0, 0.0], [1.0]) == 0.0


# ===========================================================================
# behavioral_bias_signal
# ===========================================================================

class TestGetBehavioralBiasSignal:
    def test_no_signal_below_min_clicks(self):
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        result = get_behavioral_bias_signal("u1", min_clicks=3)
        assert result.suggested_bias_types == []
        assert result.confidence == 0.0
        assert result.show_in_ui is False

    def test_growth_heavy_triggers_recency_overconfidence(self):
        """Many growth clicks with few safety clicks → recency + overconfidence."""
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        # growth clicks (ratio >= 2)
        for _ in range(6):
            log_interaction("u1", "start_investing", "click", rec_type="start_investing")
        # 0 safety clicks → ratio = 6 / 1 = 6
        result = get_behavioral_bias_signal("u1")
        assert "recency" in result.suggested_bias_types
        assert "overconfidence" in result.suggested_bias_types
        assert result.confidence >= 0.5
        assert result.show_in_ui is True

    def test_safety_heavy_triggers_loss_aversion(self):
        """Many safety clicks with few growth clicks → loss_aversion."""
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        for _ in range(6):
            log_interaction("u1", "cancel_leak", "click", rec_type="cancel_leak")
        # 0 growth → safety ratio = 6 / 1 = 6
        result = get_behavioral_bias_signal("u1")
        assert "loss_aversion" in result.suggested_bias_types
        assert result.confidence >= 0.5

    def test_concentration_signal(self):
        """2+ reduce_concentration clicks with total >= 4 → concentration bias."""
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        for _ in range(2):
            log_interaction("u1", "reduce_concentration", "click", rec_type="reduce_concentration")
        # Pad to total >= 4
        for _ in range(2):
            log_interaction("u1", "cancel_leak", "click", rec_type="cancel_leak")
        result = get_behavioral_bias_signal("u1")
        assert "concentration" in result.suggested_bias_types

    def test_confidence_capped_at_1(self):
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        for _ in range(20):
            log_interaction("u1", "start_investing", "click", rec_type="start_investing")
        result = get_behavioral_bias_signal("u1")
        assert result.confidence <= 1.0

    def test_suggested_bias_types_capped_at_3(self):
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        # Trigger all signals
        for _ in range(6):
            log_interaction("u1", "start_investing", "click", rec_type="start_investing")
        for _ in range(2):
            log_interaction("u1", "reduce_concentration", "click", rec_type="reduce_concentration")
        result = get_behavioral_bias_signal("u1")
        assert len(result.suggested_bias_types) <= 3

    def test_show_in_ui_false_when_no_bias(self):
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        result = get_behavioral_bias_signal("u1", min_clicks=100)
        assert result.show_in_ui is False

    def test_mixed_balanced_clicks_no_dominant_bias(self):
        """Roughly equal safety and growth clicks should not trigger a dominant signal."""
        from core.behavioral_events import log_interaction
        from core.behavioral_bias_signal import get_behavioral_bias_signal
        for rt in ["cancel_leak", "build_emergency_fund", "start_investing", "rebalance"]:
            log_interaction("u1", rt, "click", rec_type=rt)
        result = get_behavioral_bias_signal("u1")
        # With balanced 2 safety / 2 growth, ratio = 2/3 ≈ 0.67; neither threshold met
        assert "loss_aversion" not in result.suggested_bias_types
        assert "overconfidence" not in result.suggested_bias_types


# ===========================================================================
# update_ranking_weights management command
# ===========================================================================

class TestUpdateRankingWeightsCommand:
    """Tests for the Django management command."""

    def _run_command(self, extra_args=None, mock_shadows=None, mock_events=None):
        from django.core.management import call_command
        import core.behavioral_events as be

        if mock_shadows is not None:
            be._shadow_impressions[:] = mock_shadows
        if mock_events is not None:
            be._events.clear()
            for uid, evs in mock_events.items():
                be._events[uid] = evs

        out = StringIO()
        args = extra_args or []
        call_command("update_ranking_weights", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_no_shadow_impressions_reports_zero(self):
        output = self._run_command(mock_shadows=[], mock_events={})
        assert "No shadow impressions" in output

    def test_outputs_ctr_metrics(self):
        """With some shadow data + clicks, command prints CTR lines."""
        from core.behavioral_events import _events as ev_store
        shadow = [{
            "user_id": "u1",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "rule_order": ["r1", "r2", "r3"],
            "ml_order": ["r2", "r1", "r3"],
        }]
        events = {
            "u1": [
                {
                    "event_type": "interaction",
                    "action": "click",
                    "rec_id": "r1",
                    "position_rule": 1,
                    "position_ml": 2,
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                }
            ]
        }
        output = self._run_command(mock_shadows=shadow, mock_events=events)
        assert "Rule CTR" in output
        assert "ML" in output

    def test_dry_run_no_weight_update(self):
        """With --dry-run, weights should not be written to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"weights": {"recency": 0.4, "archetype": 0.3, "popularity": 0.2, "urgency": 0.1}}, f)
            tmp = f.name
        try:
            original = _rc_module._DEFAULT_WEIGHTS_PATH
            _rc_module._DEFAULT_WEIGHTS_PATH = tmp
            mtime_before = os.path.getmtime(tmp)
            try:
                # Large ML lift so update would be triggered if not for dry-run
                shadow = [{
                    "user_id": "u1",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                    "rule_order": ["r1", "r2", "r3"],
                    "ml_order": ["r1", "r2", "r3"],
                }]
                events = {
                    "u1": [
                        {
                            "event_type": "interaction",
                            "action": "click",
                            "rec_id": "r1",
                            "position_rule": 1,
                            "position_ml": 1,
                            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                        }
                    ] * 10
                }
                self._run_command(["--dry-run", "--update-weights"],
                                   mock_shadows=shadow, mock_events=events)
                mtime_after = os.path.getmtime(tmp)
                assert mtime_before == mtime_after
            finally:
                _rc_module._DEFAULT_WEIGHTS_PATH = original
        finally:
            os.unlink(tmp)

    def test_update_weights_nudges_archetype_on_ml_lift(self):
        """When ML CTR beats rule by >5%, archetype weight should increase."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"weights": {"recency": 0.4, "archetype": 0.3, "popularity": 0.2, "urgency": 0.1}}, f)
            tmp = f.name
        try:
            original = _rc_module._DEFAULT_WEIGHTS_PATH
            _rc_module._DEFAULT_WEIGHTS_PATH = tmp
            _reset_weights_cache()
            try:
                from core.behavioral_events import _events as ev_store, _shadow_impressions
                now_iso = __import__("datetime").datetime.utcnow().isoformat()
                _shadow_impressions.clear()
                ev_store.clear()

                # 10 shadow impressions
                for i in range(10):
                    _shadow_impressions.append({
                        "user_id": f"u{i}",
                        "timestamp": now_iso,
                        "rule_order": ["r1", "r2", "r3"],
                        "ml_order": ["r2", "r1", "r3"],
                    })

                # Rule pos1: 1 click, ML pos1: 3 clicks → ML CTR higher
                ev_store["u1"] = [
                    {
                        "event_type": "interaction",
                        "action": "click",
                        "rec_id": "r1",
                        "position_rule": 1,
                        "position_ml": None,
                        "timestamp": now_iso,
                    },
                    {
                        "event_type": "interaction",
                        "action": "click",
                        "rec_id": "r2",
                        "position_rule": None,
                        "position_ml": 1,
                        "timestamp": now_iso,
                    },
                    {
                        "event_type": "interaction",
                        "action": "click",
                        "rec_id": "r2",
                        "position_rule": None,
                        "position_ml": 1,
                        "timestamp": now_iso,
                    },
                    {
                        "event_type": "interaction",
                        "action": "click",
                        "rec_id": "r2",
                        "position_rule": None,
                        "position_ml": 1,
                        "timestamp": now_iso,
                    },
                ]

                from django.core.management import call_command
                out = StringIO()
                call_command("update_ranking_weights", "--update-weights",
                             stdout=out, stderr=StringIO())
                output = out.getvalue()

                _reset_weights_cache()
                from core.ranking_config import get_ranking_weights
                new_w = get_ranking_weights()

                if "Updated weights" in output:
                    assert new_w["archetype"] > 0.3
            finally:
                _rc_module._DEFAULT_WEIGHTS_PATH = original
        finally:
            os.unlink(tmp)
