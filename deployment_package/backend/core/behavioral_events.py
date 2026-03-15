"""
Behavioral event store for ML refinement layer.
Logs rec_impression and rec_interaction for ranking and delivery optimization.
In-memory store for MVP; can be replaced with DB/Redis later.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# In-memory store: user_id -> list of events (newest last)
_events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
# Shadow mode: recent impressions with rule_order + ml_order for CTR comparison (newest last)
_shadow_impressions: List[Dict[str, Any]] = []
_MAX_SHADOW_IMPRESSIONS = 10000
# Max events per user to avoid unbounded growth
_MAX_EVENTS_PER_USER = 500


def _parse_ts(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


@dataclass
class BehavioralEvent:
    event_type: str  # "impression" | "interaction"
    rec_id: str
    user_id: str
    action: Optional[str] = None  # "click" | "dismiss" | "save"
    time_to_interact_ms: Optional[int] = None
    position: Optional[int] = None
    rec_type: Optional[str] = None  # cancel_leak, build_emergency_fund, etc.
    timestamp: datetime = field(default_factory=datetime.utcnow)


def log_impression(
    user_id: str,
    rec_ids: List[str],
    rec_types: Optional[List[str]] = None,
    variants: Optional[List[str]] = None,
) -> None:
    """Log that recommendations were shown (e.g. when next-best-actions are returned)."""
    now = datetime.utcnow().isoformat()
    for i, rec_id in enumerate(rec_ids):
        rec_type = rec_types[i] if rec_types and i < len(rec_types) else None
        variant = variants[i] if variants and i < len(variants) else "default"
        ev = {
            "event_type": "impression",
            "rec_id": rec_id,
            "user_id": user_id,
            "position": i + 1,
            "rec_type": rec_type,
            "tone_variant": variant,
            "timestamp": now,
        }
        _events[user_id].append(ev)
    _trim(user_id)
    logger.debug("Logged %d impressions for user %s", len(rec_ids), user_id)


def log_impression_with_shadow(
    user_id: str,
    rule_order: List[str],
    ml_order: List[str],
    rec_types: Optional[List[str]] = None,
    variants: Optional[List[str]] = None,
) -> None:
    """Log impressions with shadow: store both orders for CTR comparison. Uses rule_order for event positions."""
    for i, rec_id in enumerate(rule_order):
        rec_type = rec_types[i] if rec_types and i < len(rec_types) else None
        variant = variants[i] if variants and i < len(variants) else "default"
        ev = {
            "event_type": "impression",
            "rec_id": rec_id,
            "user_id": user_id,
            "position": i + 1,
            "rec_type": rec_type,
            "tone_variant": variant,
            "timestamp": datetime.utcnow().isoformat(),
        }
        _events[user_id].append(ev)
    _trim(user_id)
    _shadow_impressions.append({
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "rule_order": list(rule_order),
        "ml_order": list(ml_order),
    })
    if len(_shadow_impressions) > _MAX_SHADOW_IMPRESSIONS:
        _shadow_impressions[:] = _shadow_impressions[-_MAX_SHADOW_IMPRESSIONS:]
    logger.debug("Logged shadow impression for user %s (rule=%s ml=%s)", user_id, rule_order, ml_order)


def _get_last_shadow_impression_for_rec(user_id: str, rec_id: str) -> Optional[Dict[str, Any]]:
    """Find the most recent shadow impression for this user that contains rec_id (within last 30 min)."""
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    for s in reversed(_shadow_impressions):
        if s["user_id"] != user_id:
            continue
        ts = _parse_ts(s.get("timestamp"))
        if ts and ts < cutoff:
            break
        if rec_id in s.get("rule_order", []) or rec_id in s.get("ml_order", []):
            return s
    return None


def _get_last_impression_tone_for_rec(user_id: str, rec_id: str) -> Optional[str]:
    """Get tone_variant from the most recent impression for this user that contains rec_id (within 30 min)."""
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    for e in reversed(_events.get(user_id, [])):
        if e.get("event_type") != "impression":
            continue
        ts = _parse_ts(e.get("timestamp"))
        if ts and ts < cutoff:
            break
        if e.get("rec_id") == rec_id:
            return e.get("tone_variant") or "default"
    return None


def log_interaction(
    user_id: str,
    rec_id: str,
    action: str,  # "click" | "dismiss" | "save"
    time_to_interact_ms: Optional[int] = None,
    rec_type: Optional[str] = None,
) -> None:
    """Log user interaction with a recommendation (tap, dismiss, save). Attaches position_rule/ml from shadow if available."""
    ev = {
        "event_type": "interaction",
        "rec_id": rec_id,
        "user_id": user_id,
        "action": action,
        "time_to_interact_ms": time_to_interact_ms,
        "rec_type": rec_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    shadow = _get_last_shadow_impression_for_rec(user_id, rec_id)
    if shadow:
        ro = shadow.get("rule_order") or []
        mo = shadow.get("ml_order") or []
        try:
            ev["position_rule"] = ro.index(rec_id) + 1 if rec_id in ro else None
        except ValueError:
            ev["position_rule"] = None
        try:
            ev["position_ml"] = mo.index(rec_id) + 1 if rec_id in mo else None
        except ValueError:
            ev["position_ml"] = None
    tone = _get_last_impression_tone_for_rec(user_id, rec_id)
    if tone:
        ev["tone_variant"] = tone
    _events[user_id].append(ev)
    _trim(user_id)
    logger.debug("Logged interaction %s for user %s rec %s", action, user_id, rec_id)


def get_events(
    user_id: str,
    since_days: int = 30,
    event_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return events for a user, optionally filtered by type and time."""
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    out = []
    for e in _events.get(user_id, []):
        ts = e.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = cutoff
        if ts and ts < cutoff:
            continue
        if event_type and e.get("event_type") != event_type:
            continue
        out.append(e)
    return out


def get_recent_dismissals_by_rec_type(
    user_id: str,
    days: int = 7,
) -> Dict[str, bool]:
    """
    For MVP ranking: which rec_types did this user dismiss (or ignore) recently?
    Used as negative weight: if they dismissed 'cancel_leak' in last 7 days, rank it lower.
    """
    events = get_events(user_id, since_days=days, event_type="interaction")
    dismissed: Dict[str, bool] = {}
    for e in events:
        act = e.get("action")
        rt = e.get("rec_type") or e.get("rec_id")
        if act in ("dismiss", "ignore") and rt:
            dismissed[rt] = True
        # Also treat "no click" as weak signal - we don't have explicit dismiss yet,
        # so we only use explicit dismiss when we add that flow.
    return dismissed


def get_recent_clicks_by_rec_type(
    user_id: str,
    days: int = 30,
) -> Dict[str, int]:
    """Count clicks per rec_type in last N days (positive signal for ranking)."""
    events = get_events(user_id, since_days=days, event_type="interaction")
    clicks: Dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("action") != "click":
            continue
        rt = e.get("rec_type") or e.get("rec_id")
        if rt:
            clicks[rt] += 1
    return dict(clicks)


def _trim(user_id: str) -> None:
    if len(_events[user_id]) > _MAX_EVENTS_PER_USER:
        _events[user_id] = _events[user_id][-_MAX_EVENTS_PER_USER:]


def get_shadow_impressions_for_metrics(since_days: int = 14) -> List[Dict[str, Any]]:
    """Return shadow impressions in the last N days for feedback loop metrics."""
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    out = []
    for s in _shadow_impressions:
        ts = _parse_ts(s.get("timestamp"))
        if ts and ts >= cutoff:
            out.append(s)
    return out


def get_all_events_for_metrics(since_days: int = 14) -> Dict[str, List[Dict[str, Any]]]:
    """Return all users' events in the last N days (for feedback job). In production use DB."""
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for user_id, events in _events.items():
        for e in events:
            ts = _parse_ts(e.get("timestamp"))
            if ts and ts < cutoff:
                continue
            out.setdefault(user_id, []).append(e)
    return out
