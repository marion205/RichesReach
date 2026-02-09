"""Autopilot service for policy storage, repairs, and execution stubs."""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.utils import timezone

from .risk_scoring_service import audit_vault, build_nav_from_apy_series


DEFAULT_POLICY = {
    'target_apy': 0.08,
    'max_drawdown': 0.05,
    'risk_level': 'FORTRESS',
    'level': 'NOTIFY_ONLY',
    'spend_limit_24h': 500.0,
}


def _policy_key(user_id: int) -> str:
    return f"autopilot:policy:{user_id}"


def _enabled_key(user_id: int) -> str:
    return f"autopilot:enabled:{user_id}"


def _demo_key(user_id: int) -> str:
    return f"autopilot:demo_repair:{user_id}"


def _last_move_key(user_id: int) -> str:
    return f"autopilot:last_move:{user_id}"


def get_autopilot_policy(user) -> Dict[str, Any]:
    if not user:
        return DEFAULT_POLICY
    return cache.get(_policy_key(user.id), DEFAULT_POLICY)


def set_autopilot_policy(user, policy: Dict[str, Any]) -> Dict[str, Any]:
    if not user:
        return DEFAULT_POLICY
    def _coerce_value(value: Any) -> Any:
        if hasattr(value, 'value'):
            return value.value
        if hasattr(value, 'name') and isinstance(value.name, str):
            return value.name
        return value

    cleaned = {k: _coerce_value(v) for k, v in policy.items() if v is not None}
    merged = {**DEFAULT_POLICY, **cleaned}
    cache.set(_policy_key(user.id), merged, timeout=None)
    return merged


def is_autopilot_enabled(user) -> bool:
    if not user:
        return False
    return bool(cache.get(_enabled_key(user.id), False))


def set_autopilot_enabled(user, enabled: bool) -> bool:
    if not user:
        return False
    cache.set(_enabled_key(user.id), bool(enabled), timeout=None)
    return bool(enabled)


def get_autopilot_status(user) -> Dict[str, Any]:
    return {
        'enabled': is_autopilot_enabled(user),
        'last_evaluated_at': timezone.now().isoformat(),
        'policy': get_autopilot_policy(user),
        'last_move': get_last_move(user),
    }


def _set_last_move(user, move: Dict[str, Any]) -> None:
    if not user:
        return
    cache.set(_last_move_key(user.id), move, timeout=60 * 60 * 24)


def get_last_move(user) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    move = cache.get(_last_move_key(user.id))
    if not move:
        return None
    executed_at = move.get('executed_at')
    try:
        executed_dt = timezone.datetime.fromisoformat(executed_at) if executed_at else None
    except Exception:
        executed_dt = None
    if not executed_dt:
        return None
    deadline = executed_dt + timezone.timedelta(hours=24)
    now = timezone.now()
    can_revert = now <= deadline
    move['can_revert'] = can_revert
    move['revert_deadline'] = deadline.isoformat()
    return move


def _pool_audit(pool) -> Optional[Dict[str, Any]]:
    snapshots = list(pool.yield_snapshots.order_by('-timestamp')[:2000])
    if not snapshots:
        return None

    daily = {}
    for snap in snapshots:
        day = snap.timestamp.date()
        if day not in daily:
            daily[day] = snap

    if len(daily) < 7:
        return None

    ordered_days = sorted(daily.keys())
    apy_series = [float(daily[day].apy_total) for day in ordered_days]
    tvl_series = [float(daily[day].tvl_usd) for day in ordered_days]
    nav_history = build_nav_from_apy_series(apy_series)

    protocol_name = ''
    if pool.protocol:
        protocol_name = pool.protocol.slug or pool.protocol.name

    audit = audit_vault(
        vault_address=pool.pool_address or str(pool.id),
        protocol=protocol_name,
        symbol=pool.symbol,
        apy=apy_series[-1] if apy_series else 0.0,
        nav_history=nav_history,
        tvl_history=tvl_series,
        is_erc4626_compliant=pool.pool_type in ('vault', 'yield'),
    )

    return {
        'audit': audit,
        'apy_series': apy_series,
        'tvl_series': tvl_series,
    }


def _find_repair_target(pool) -> Optional[Dict[str, Any]]:
    from .defi_models import DeFiPool

    candidates = DeFiPool.objects.filter(
        symbol=pool.symbol,
        chain=pool.chain,
        is_active=True,
    ).exclude(id=pool.id)

    best = None
    for candidate in candidates:
        audit_data = _pool_audit(candidate)
        if not audit_data:
            continue
        audit = audit_data['audit']
        if audit.recommendation.value == 'EXIT':
            continue
        if not best or audit.overall_score > best['audit'].overall_score:
            best = {'pool': candidate, **audit_data}

    return best


def get_pending_repairs(user) -> List[Dict[str, Any]]:
    if not user or not getattr(user, 'is_authenticated', False):
        return []

    demo = cache.get(_demo_key(user.id))
    if demo:
        return [demo]
    try:
        from .defi_models import UserDeFiPosition

        policy = get_autopilot_policy(user)
        max_drawdown = policy.get('max_drawdown') or DEFAULT_POLICY['max_drawdown']

        positions = UserDeFiPosition.objects.filter(user=user, is_active=True).select_related('pool', 'pool__protocol')
        repairs: List[Dict[str, Any]] = []

        for position in positions:
            pool = position.pool
            if not pool:
                continue

            current = _pool_audit(pool)
            if not current:
                continue

            current_audit = current['audit']
            if current_audit.recommendation.value == 'HOLD':
                continue

            target = _find_repair_target(pool)
            if not target:
                continue

            target_audit = target['audit']
            calmar_improvement = target_audit.risk.calmar_ratio - current_audit.risk.calmar_ratio
            apy_delta = target_audit.apy - current_audit.apy
            policy_alignment = target_audit.risk.max_drawdown <= max_drawdown
            tvl_ok = target_audit.risk.tvl_stability >= 0.7

            repair_id = f"{position.id}:{target['pool'].id}"
            repairs.append({
                'id': repair_id,
                'from_vault': current_audit.vault_address,
                'to_vault': target_audit.vault_address,
                'estimated_apy_delta': apy_delta,
                'gas_estimate': 220000.0,
                'proof': {
                    'calmar_improvement': calmar_improvement,
                    'integrity_check': {
                        'altman_z_score': target_audit.integrity.altman_z_score,
                        'beneish_m_score': target_audit.integrity.beneish_m_score,
                        'is_erc4626_compliant': target_audit.integrity.is_erc4626_compliant,
                    },
                    'tvl_stability_check': tvl_ok,
                    'policy_alignment': policy_alignment,
                    'explanation': target_audit.explanation,
                },
                'from_pool_id': str(pool.id),
                'to_pool_id': str(target['pool'].id),
            })

        return repairs
    except Exception:
        return []


def seed_demo_repair(user) -> Dict[str, Any]:
    if not user or not getattr(user, 'is_authenticated', False):
        return {}

    demo = {
        'id': f"demo:{user.id}",
        'from_vault': 'Aave USDC',
        'to_vault': 'Yearn ERC-4626 USDC',
        'estimated_apy_delta': 0.021,
        'gas_estimate': 190000.0,
        'proof': {
            'calmar_improvement': 0.6,
            'integrity_check': {
                'altman_z_score': 2.4,
                'beneish_m_score': -2.1,
                'is_erc4626_compliant': True,
            },
            'tvl_stability_check': True,
            'policy_alignment': True,
            'explanation': 'Demo repair: higher Calmar ratio with stable TVL.',
        },
    }

    cache.set(_demo_key(user.id), demo, timeout=3600)
    return demo


def execute_repair(user, repair_id: str) -> Dict[str, Any]:
    if not user or not getattr(user, 'is_authenticated', False):
        return {'success': False, 'message': 'Authentication required.'}

    repairs = get_pending_repairs(user)
    repair = next((r for r in repairs if r['id'] == repair_id), None)
    if not repair:
        return {'success': False, 'message': 'Repair not found or no longer valid.'}

    if repair_id.startswith('demo:'):
        _set_last_move(user, {
            'id': repair_id,
            'from_vault': repair.get('from_vault'),
            'to_vault': repair.get('to_vault'),
            'executed_at': timezone.now().isoformat(),
        })
        cache.delete(_demo_key(user.id))
        return {
            'success': True,
            'tx_hash': None,
            'message': 'Demo repair executed. Ready for real positions.',
        }

    try:
        from .defi_models import DeFiTransaction, DeFiPool
        from decimal import Decimal

        pool = DeFiPool.objects.filter(id=repair.get('from_pool_id')).first()
        if pool:
            DeFiTransaction.objects.create(
                user=user,
                pool=pool,
                action='swap',
                tx_hash=f"repair_{timezone.now().timestamp():.0f}",
                chain_id=pool.chain_id,
                amount=Decimal('0'),
                amount_usd=Decimal('0'),
                status='pending',
            )

        _set_last_move(user, {
            'id': repair_id,
            'from_vault': repair.get('from_vault'),
            'to_vault': repair.get('to_vault'),
            'executed_at': timezone.now().isoformat(),
        })

        return {
            'success': True,
            'tx_hash': None,
            'message': 'Repair queued. Approve the on-chain transaction in your wallet.',
        }
    except Exception as e:
        return {'success': False, 'message': f'Failed to queue repair: {e}'}


def revert_last_move(user) -> Dict[str, Any]:
    if not user or not getattr(user, 'is_authenticated', False):
        return {'success': False, 'message': 'Authentication required.'}

    last_move = get_last_move(user)
    if not last_move or not last_move.get('can_revert'):
        return {'success': False, 'message': 'Revert window expired or no move found.'}

    cache.delete(_last_move_key(user.id))
    return {
        'success': True,
        'tx_hash': None,
        'message': 'Revert queued. Approve the on-chain transaction in your wallet.',
    }
