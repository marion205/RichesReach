"""Policy engine for Auto-Pilot decisioning."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

DEFAULT_POLICY: Dict[str, Any] = {
    'version': '2.1.4',
    'governance': {
        'emergency_stop_enabled': True,
        'human_in_the_loop_required': True,
        'audit_level': 'VERBOSE',
    },
    'risk_thresholds': {
        'max_drawdown_limit': 0.08,
        'min_protocol_trust_score': 85,
        'min_tvl_depth': 100_000_000,
        'max_slippage_tolerance': 0.005,
    },
    'autonomy_levels': {},
    'rollback_logic': {
        'window_duration': '24h',
        'automatic_position_tracking': True,
        'path_reversal_buffer': 0.02,
        'reserve_gas_for_revert': True,
    },
    'verified_protocols': [
        {'id': 'aave_v3'},
        {'id': 'compound_v3'},
        {'id': 'morpho_blue'},
    ],
    'verified_assets': ['USDC', 'USDT', 'DAI', 'ETH', 'WBTC'],
}


def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception:
        return None

    try:
        with path.open('r', encoding='utf-8') as handle:
            return yaml.safe_load(handle)
    except Exception as exc:
        logger.warning(f"Failed to load policy YAML: {exc}")
        return None


def get_policy(policy_path: Optional[Path] = None) -> Dict[str, Any]:
    path = policy_path or Path(__file__).with_name('autopilot_policy.yaml')
    if path.exists():
        loaded = _load_yaml(path)
        if isinstance(loaded, dict):
            merged = {**DEFAULT_POLICY, **loaded}
            merged['version'] = loaded.get('version', DEFAULT_POLICY['version'])
            return merged
    return DEFAULT_POLICY


def protocol_trust_score(pool) -> float:
    try:
        risk_score = float(getattr(pool.protocol, 'risk_score', 0.5)) if pool and pool.protocol else 0.5
        return max(0.0, min(100.0, (1.0 - risk_score) * 100.0))
    except Exception:
        return 50.0


def is_protocol_verified(pool, policy: Dict[str, Any]) -> bool:
    verified = policy.get('verified_protocols', [])
    if not verified:
        return True
    if not pool or not pool.protocol:
        return False
    slug = (pool.protocol.slug or pool.protocol.name or '').lower()
    for item in verified:
        if item.get('id', '').lower() == slug.replace('-', '_'):
            return True
    return False


def policy_gate(pool, latest_snapshot, policy: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    thresholds = policy.get('risk_thresholds', {})
    min_trust = float(thresholds.get('min_protocol_trust_score', 0))
    min_tvl = float(thresholds.get('min_tvl_depth', 0))

    trust_score = protocol_trust_score(pool)
    tvl = float(getattr(latest_snapshot, 'tvl_usd', 0) or 0)

    verified = is_protocol_verified(pool, policy)
    ok = verified and trust_score >= min_trust and tvl >= min_tvl

    return ok, {
        'trust_score': trust_score,
        'tvl': tvl,
        'verified': verified,
        'min_trust': min_trust,
        'min_tvl': min_tvl,
    }


def build_audit_trail_id(prefix: str, pool_id: str) -> str:
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{pool_id}_{ts}"
