"""
Safety v0 — log safety decisions to SafetyDecisionLog.
Never raises; failures are logged and ignored so the main flow is not broken.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def log_safety_decision(
    user_id: str,
    action_type: str,
    decision: str,
    reason: str = "",
    metadata: Optional[dict] = None,
) -> None:
    """
    Append a record to SafetyDecisionLog. Safe to call from FastAPI or Django.
    user_id can be string ID (e.g. 'demo-user' or '123').
    """
    try:
        from .safety_models import SafetyDecisionLog
        SafetyDecisionLog.objects.create(
            user_id=str(user_id),
            action_type=action_type[:64],
            decision=decision[:32],
            reason=reason or "",
            metadata=dict(metadata or {}),
        )
    except Exception as e:
        logger.warning("SafetyDecisionLog create failed (non-fatal): %s", e)
