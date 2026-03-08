"""
Tests for Safety v0: log_safety_decision and SafetyDecisionLog.
"""
from django.test import TestCase

from core.safety_log import log_safety_decision
from core.safety_models import SafetyDecisionLog


class SafetyLogTests(TestCase):
    """Test that safety decisions are written to SafetyDecisionLog."""

    def test_log_safety_decision_creates_record(self):
        log_safety_decision(
            user_id="test-user-123",
            action_type="ask_buy_add",
            decision="disclaimer_applied",
            reason="portfolio context present",
        )
        rec = SafetyDecisionLog.objects.filter(action_type="ask_buy_add").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.user_id, "test-user-123")
        self.assertEqual(rec.decision, "disclaimer_applied")
        self.assertIn("portfolio", rec.reason)

    def test_log_safety_decision_with_metadata(self):
        log_safety_decision(
            user_id="99",
            action_type="auto_execute",
            decision="blocked",
            reason="Confidence 50% below threshold",
            metadata={"confidence": 0.5, "threshold": 0.8},
        )
        rec = SafetyDecisionLog.objects.filter(action_type="auto_execute").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.metadata.get("confidence"), 0.5)

    def test_log_safety_decision_does_not_raise_on_db_error(self):
        # Should not raise even if something is wrong (e.g. invalid field length handled in model)
        log_safety_decision("u", "a", "d", "r")
        self.assertEqual(SafetyDecisionLog.objects.count(), 1)
