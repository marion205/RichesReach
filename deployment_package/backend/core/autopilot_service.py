"""Autopilot service for policy storage, repairs, and execution stubs."""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.utils import timezone

from .risk_scoring_service import audit_vault, build_nav_from_apy_series
from .policy_engine import get_policy, policy_gate

logger = logging.getLogger(__name__)


DEFAULT_POLICY = {
    'target_apy': 0.08,
    'max_drawdown': 0.05,
    'risk_level': 'FORTRESS',
    'level': 'NOTIFY_ONLY',
    'spend_limit_24h': 500.0,
    'spend_permission_enabled': False,
    'spend_permission_expires_at': None,
    'orchestration_mode': 'MULTI_AGENT',
}


def _policy_key(user_id: int) -> str:
    return f"autopilot:policy:{user_id}"


def _enabled_key(user_id: int) -> str:
    return f"autopilot:enabled:{user_id}"


def _demo_key(user_id: int) -> str:
    return f"autopilot:demo_repair:{user_id}"


def _last_move_key(user_id: int) -> str:
    return f"autopilot:last_move:{user_id}"


def _parse_iso_datetime(value: Optional[str]) -> Optional[timezone.datetime]:
    if not value:
        return None
    try:
        return timezone.datetime.fromisoformat(value)
    except Exception:
        return None


def get_autopilot_policy(user) -> Dict[str, Any]:
    if not user:
        return DEFAULT_POLICY
    policy = cache.get(_policy_key(user.id), DEFAULT_POLICY)
    expires_at = _parse_iso_datetime(policy.get('spend_permission_expires_at'))
    if expires_at and timezone.now() > expires_at:
        policy = {
            **policy,
            'spend_permission_enabled': False,
            'spend_permission_expires_at': None,
        }
        cache.set(_policy_key(user.id), policy, timeout=None)
    return policy


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


def _spend_permission_active(policy: Dict[str, Any]) -> bool:
    if not policy.get('spend_permission_enabled'):
        return False
    expires_at = _parse_iso_datetime(policy.get('spend_permission_expires_at'))
    if expires_at and timezone.now() > expires_at:
        return False
    return True


def _symbol_to_decimals(symbol: Optional[str]) -> int:
    """Map common token symbols to ERC-20 decimals. Default 18."""
    if not symbol:
        return 18
    s = (symbol or '').upper()
    if s in ('USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'FRAX', 'GUSD'):
        return 6
    if s in ('WBTC', 'WETH'):
        return 18
    return 18


def _has_valid_eip712_spend_permission(
    user,
    wallet_address: str,
    chain_id: int,
    amount_wei: int,
) -> bool:
    """True if user has a valid DeFiSpendPermission for this wallet/chain and amount <= max."""
    if not user or not wallet_address:
        return False
    try:
        from .defi_models import DeFiSpendPermission
        now = timezone.now()
        perms = DeFiSpendPermission.objects.filter(
            user=user,
            wallet_address__iexact=wallet_address.strip(),
            chain_id=chain_id,
            valid_until__gt=now,
        )
        for p in perms:
            try:
                max_wei = int(p.max_amount_wei)
                if amount_wei <= max_wei:
                    return True
            except (ValueError, TypeError):
                continue
        return False
    except Exception as e:
        logger.warning(f"EIP-712 spend permission check failed: {e}")
        return False


def grant_spend_permission(user, hours: int = 24) -> Dict[str, Any]:
    if not user:
        return DEFAULT_POLICY
    expires_at = timezone.now() + timezone.timedelta(hours=max(1, int(hours or 24)))
    updated = set_autopilot_policy(user, {
        'spend_permission_enabled': True,
        'spend_permission_expires_at': expires_at.isoformat(),
    })
    return updated


def revoke_spend_permission(user) -> Dict[str, Any]:
    if not user:
        return DEFAULT_POLICY
    updated = set_autopilot_policy(user, {
        'spend_permission_enabled': False,
        'spend_permission_expires_at': None,
    })
    return updated


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


def _find_repair_options(
    pool,
    current_audit,
    user,
    max_drawdown: float,
    guardrails: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Return three repair options for this position: FORTRESS (best Calmar),
    BALANCED (best overall score), YIELD_MAX (highest APY within policy).
    """
    from .defi_models import DeFiPool

    candidates = DeFiPool.objects.filter(
        symbol=pool.symbol,
        chain=pool.chain,
        is_active=True,
    ).exclude(id=pool.id)

    valid = []
    for candidate in candidates:
        audit_data = _pool_audit(candidate)
        if not audit_data:
            continue
        audit = audit_data['audit']
        if audit.recommendation.value == 'EXIT':
            continue
        latest = candidate.yield_snapshots.order_by('-timestamp').first()
        gate_ok, gate_meta = policy_gate(candidate, latest, guardrails)
        valid.append({
            'pool': candidate,
            'audit': audit,
            'audit_data': audit_data,
            'gate_ok': gate_ok,
            'gate_meta': gate_meta,
            'policy_alignment': audit.risk.max_drawdown <= max_drawdown and gate_ok,
        })

    if not valid:
        return []

    apy_delta = lambda v: v['audit'].apy - current_audit.apy
    calmar_improvement = lambda v: v['audit'].risk.calmar_ratio - current_audit.risk.calmar_ratio

    fortress = max(valid, key=lambda v: v['audit'].risk.calmar_ratio)
    balanced = max(valid, key=lambda v: v['audit'].overall_score)
    yield_candidates = [v for v in valid if v['policy_alignment']]
    yield_max = max(yield_candidates, key=lambda v: v['audit'].apy) if yield_candidates else balanced

    def option_dict(variant: str, choice: Dict) -> Dict[str, Any]:
        a = choice['audit']
        p = choice['pool']
        delta = apy_delta(choice)
        return {
            'variant': variant,
            'to_vault': a.vault_address,
            'to_pool_id': str(p.id),
            'estimated_apy_delta': delta,
            'proof': {
                'calmar_improvement': calmar_improvement(choice),
                'integrity_check': {
                    'altman_z_score': a.integrity.altman_z_score,
                    'beneish_m_score': a.integrity.beneish_m_score,
                    'is_erc4626_compliant': a.integrity.is_erc4626_compliant,
                },
                'tvl_stability_check': a.risk.tvl_stability >= 0.7,
                'policy_alignment': choice['policy_alignment'],
                'explanation': a.explanation,
                'policy_version': guardrails.get('version', ''),
                'guardrails': choice.get('gate_meta', {}),
            },
        }

    options = []
    seen_ids = set()
    for variant, choice in [('FORTRESS', fortress), ('BALANCED', balanced), ('YIELD_MAX', yield_max)]:
        pid = str(choice['pool'].id)
        if pid not in seen_ids:
            seen_ids.add(pid)
            options.append(option_dict(variant, choice))
    return options[:3]


def _strategy_suggestions_as_repairs(user) -> List[Dict[str, Any]]:
    """
    Convert StrategyEvaluation rotation suggestions into repair-action format
    so they appear in the unified repair queue alongside risk-triggered repairs.

    Strategy engine suggestions are APY-improvement-driven rotations that also
    pass the policy_gate() guardrails.
    """
    try:
        from .defi_strategy_engine import StrategyEvaluation
        from .defi_models import DeFiPool

        engine = StrategyEvaluation()
        suggestions = engine.evaluate_positions(user)
        guardrails = get_policy()

        repair_format_items: List[Dict[str, Any]] = []

        for suggestion in suggestions:
            # Only convert 'rotate' suggestions, not 'harvest'
            if suggestion.get('suggestion_type') != 'rotate':
                continue

            suggested_pool_id = suggestion.get('suggested_pool_id')
            if not suggested_pool_id:
                continue

            # Validate target pool through policy_gate
            target_pool = DeFiPool.objects.filter(
                id=suggested_pool_id, is_active=True
            ).select_related('protocol').first()
            if not target_pool:
                continue

            latest_snapshot = target_pool.yield_snapshots.order_by('-timestamp').first()
            gate_ok, gate_meta = policy_gate(target_pool, latest_snapshot, guardrails)
            if not gate_ok:
                continue

            position_id = suggestion.get('position_id', '')
            repair_id = f"strategy:{position_id}:{suggested_pool_id}"

            # Normalize APY: strategy engine uses percentage (e.g., 8.5),
            # autopilot repair format uses decimal (e.g., 0.085)
            current_apy = suggestion.get('current_apy', 0)
            suggested_apy = suggestion.get('suggested_apy', 0)
            apy_delta = (suggested_apy - current_apy) / 100.0

            protocol_name = suggestion.get('suggested_pool_protocol', '')
            pool_symbol = suggestion.get('suggested_pool_symbol', '')

            repair_format_items.append({
                'id': repair_id,
                'from_vault': suggestion.get('current_pool_symbol', ''),
                'to_vault': f"{protocol_name} {pool_symbol}".strip(),
                'estimated_apy_delta': apy_delta,
                'gas_estimate': 220000.0,
                'proof': {
                    'calmar_improvement': 0.0,
                    'integrity_check': {
                        'altman_z_score': 0.0,
                        'beneish_m_score': 0.0,
                        'is_erc4626_compliant': target_pool.pool_type in ('vault', 'yield'),
                    },
                    'tvl_stability_check': True,
                    'policy_alignment': gate_ok,
                    'explanation': suggestion.get('reason', ''),
                    'policy_version': guardrails.get('version'),
                    'guardrails': gate_meta,
                },
                'from_pool_id': str(suggestion.get('current_pool_id', '')),
                'to_pool_id': str(suggested_pool_id),
                'source': 'strategy_engine',
                'options': [],
            })

        return repair_format_items

    except Exception as e:
        logger.warning(f"Error converting strategy suggestions to repairs: {e}")
        return []


def _build_execution_plan(from_pool, to_pool, policy: Dict[str, Any]) -> Dict[str, Any]:
    is_erc4626 = False
    if from_pool and to_pool:
        is_erc4626 = (
            from_pool.pool_type in ('vault', 'yield')
            and to_pool.pool_type in ('vault', 'yield')
        )

    plan_type = 'erc4626_one_tx' if is_erc4626 else 'two_tx'
    steps = ['redeem', 'deposit'] if is_erc4626 else ['withdraw', 'deposit']
    return {
        'type': plan_type,
        'one_tx': is_erc4626,
        'steps': steps,
        'requires_wallet_approval': policy.get('level') != 'AUTO_SPEND',
        'spend_permission_active': _spend_permission_active(policy),
    }


def _attach_orchestration_metadata(
    repairs: List[Dict[str, Any]],
    policy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    try:
        from .defi_models import DeFiPool
    except Exception:
        return repairs

    pool_ids = set()
    for repair in repairs:
        if repair.get('from_pool_id'):
            pool_ids.add(repair['from_pool_id'])
        if repair.get('to_pool_id'):
            pool_ids.add(repair['to_pool_id'])

    pools = {
        str(p.id): p
        for p in DeFiPool.objects.filter(id__in=list(pool_ids))
    }

    for repair in repairs:
        from_pool = pools.get(repair.get('from_pool_id'))
        to_pool = pools.get(repair.get('to_pool_id'))

        execution_plan = _build_execution_plan(from_pool, to_pool, policy)
        repair['execution_plan'] = execution_plan

        repair['agent_trace'] = {
            'scout': {
                'from_pool_id': repair.get('from_pool_id'),
                'to_pool_id': repair.get('to_pool_id'),
                'source': repair.get('source', 'unknown'),
            },
            'risk': {
                'policy_alignment': repair.get('proof', {}).get('policy_alignment'),
                'calmar_improvement': repair.get('proof', {}).get('calmar_improvement'),
                'tvl_stability_check': repair.get('proof', {}).get('tvl_stability_check'),
            },
            'executor': execution_plan,
        }

    return repairs


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
        guardrails = get_policy()
        policy_version = guardrails.get('version')

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

            latest_snapshot = target['pool'].yield_snapshots.order_by('-timestamp').first()
            gate_ok, gate_meta = policy_gate(target['pool'], latest_snapshot, guardrails)
            if not gate_ok:
                continue

            repair_id = f"{position.id}:{target['pool'].id}"
            options = _find_repair_options(pool, current_audit, user, max_drawdown, guardrails)
            repair_entry = {
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
                    'policy_alignment': policy_alignment and gate_ok,
                    'explanation': target_audit.explanation,
                    'policy_version': policy_version,
                    'guardrails': gate_meta,
                },
                'from_pool_id': str(pool.id),
                'to_pool_id': str(target['pool'].id),
                'source': 'risk_scoring',
                'options': options,
            }
            repairs.append(repair_entry)
            try:
                from .defi_models import DeFiRepairDecision
                DeFiRepairDecision.objects.create(
                    user=user,
                    position=position,
                    from_pool=pool,
                    to_pool=target['pool'],
                    repair_id=repair_id,
                    decision_type='suggested',
                    inputs={
                        'current_apy': current_audit.apy,
                        'target_apy': target_audit.apy,
                        'max_drawdown': max_drawdown,
                    },
                    explanation=target_audit.explanation or '',
                    expected_apy_delta=apy_delta,
                    policy_version=policy_version or '',
                )
            except Exception as e:
                logger.warning(f"Decision ledger write (suggested) failed: {e}")

        # Merge strategy engine rotation suggestions into the repair queue.
        # Skip strategy suggestions for positions already covered by risk repairs.
        existing_from_pools = {r.get('from_pool_id') for r in repairs}
        strategy_repairs = _strategy_suggestions_as_repairs(user)
        for sr in strategy_repairs:
            if sr.get('from_pool_id') not in existing_from_pools:
                repairs.append(sr)

        if policy.get('orchestration_mode') == 'MULTI_AGENT':
            return _attach_orchestration_metadata(repairs, policy)

        return repairs
    except Exception:
        return []


def seed_demo_repair(user) -> Dict[str, Any]:
    if not user or not getattr(user, 'is_authenticated', False):
        return {}

    guardrails = get_policy()
    policy_version = guardrails.get('version')

    demo = {
        'id': f"demo:{user.id}",
        'from_vault': 'Aave USDC',
        'to_vault': 'Yearn ERC-4626 USDC',
        'estimated_apy_delta': 0.021,
        'gas_estimate': 190000.0,
        'source': 'demo',
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
            'policy_version': policy_version,
            'guardrails': {
                'trust_score': 92.0,
                'tvl': 890000000.0,
                'verified': True,
                'min_trust': 85.0,
                'min_tvl': 100000000.0,
            },
        },
        'execution_plan': {
            'type': 'erc4626_one_tx',
            'one_tx': True,
            'steps': ['redeem', 'deposit'],
            'requires_wallet_approval': True,
            'spend_permission_active': False,
        },
        'agent_trace': {
            'scout': {'source': 'demo'},
            'risk': {'policy_alignment': True, 'calmar_improvement': 0.6},
            'executor': {'type': 'erc4626_one_tx', 'one_tx': True},
        },
        'options': [],
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
        from .defi_models import DeFiTransaction, DeFiPool, UserDeFiPosition
        from decimal import Decimal

        # Resolve position and pool from repair_id (format: "position_id:pool_id"
        # or "strategy:position_id:pool_id")
        parts = repair_id.split(':')
        position = None
        if parts[0] == 'strategy' and len(parts) >= 3:
            position = UserDeFiPosition.objects.filter(id=parts[1]).first()
        elif len(parts) >= 2:
            position = UserDeFiPosition.objects.filter(id=parts[0]).first()

        amount = position.staked_amount if position else Decimal('0')
        amount_usd = position.staked_value_usd if position else Decimal('0')

        from_pool = DeFiPool.objects.filter(id=repair.get('from_pool_id')).first()
        to_pool = DeFiPool.objects.filter(id=repair.get('to_pool_id')).first()
        decimals = _symbol_to_decimals(from_pool.symbol if from_pool else None)
        amount_wei = int(amount * (10 ** decimals)) if amount else 0
        wallet_address = (position.wallet_address or '') if position else ''
        chain_id_for_perm = from_pool.chain_id if from_pool else 0
        eip712_auto_approved = _has_valid_eip712_spend_permission(
            user, wallet_address, chain_id_for_perm, amount_wei
        )

        policy = get_autopilot_policy(user)
        allow_auto_spend = (
            (policy.get('level') == 'AUTO_SPEND' and _spend_permission_active(policy))
            or eip712_auto_approved
        )
        txn_status = 'confirmed' if allow_auto_spend else 'pending'
        confirmed_at = timezone.now() if allow_auto_spend else None

        pool = from_pool
        if pool:
            DeFiTransaction.objects.create(
                user=user,
                pool=pool,
                action='swap',
                tx_hash=f"repair_{timezone.now().timestamp():.0f}",
                chain_id=pool.chain_id,
                amount=amount,
                amount_usd=amount_usd,
                status=txn_status,
                confirmed_at=confirmed_at,
            )

        _set_last_move(user, {
            'id': repair_id,
            'from_vault': repair.get('from_vault'),
            'to_vault': repair.get('to_vault'),
            'executed_at': timezone.now().isoformat(),
        })

        try:
            from .defi_models import DeFiRepairDecision
            DeFiRepairDecision.objects.create(
                user=user,
                position=position,
                from_pool=from_pool,
                to_pool=to_pool,
                repair_id=repair_id,
                decision_type='executed',
                inputs={'repair': repair.get('proof', {})},
                explanation=(repair.get('proof') or {}).get('explanation', ''),
                expected_apy_delta=repair.get('estimated_apy_delta'),
                policy_version=(repair.get('proof') or {}).get('policy_version', ''),
                executed_at=timezone.now(),
                tx_hash=repair.get('tx_hash') or f"repair_{timezone.now().timestamp():.0f}",
            )
        except Exception as e:
            logger.warning(f"Decision ledger write (executed) failed: {e}")

        # Build execution payload for client to submit on-chain (WalletConnect)
        execution_payload = None
        if from_pool and to_pool and position:
            amount_human = str(amount)
            execution_payload = {
                'chainId': from_pool.chain_id,
                'fromPoolId': str(from_pool.id),
                'toPoolId': str(to_pool.id),
                'fromVaultAddress': from_pool.pool_address or '',
                'toVaultAddress': to_pool.pool_address or '',
                'amountHuman': amount_human,
                'decimals': decimals,
                'withinSpendPermission': eip712_auto_approved,
                'steps': [
                    {'type': 'redeem', 'vaultAddress': from_pool.pool_address or '', 'amountHuman': amount_human},
                    {'type': 'deposit', 'vaultAddress': to_pool.pool_address or '', 'amountHuman': amount_human},
                ],
            }

        if allow_auto_spend:
            return {
                'success': True,
                'tx_hash': None,
                'message': 'Repair executed within spend permission. On-chain execution in progress.',
                'execution_payload': execution_payload,
            }

        return {
            'success': True,
            'tx_hash': None,
            'message': 'Repair queued. Approve the on-chain transaction in your wallet.',
            'execution_payload': execution_payload,
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


# ------------------------------------------------------------------
# AUTO_BOUNDED execution helpers
# ------------------------------------------------------------------


def _daily_spend_check(user, amount_usd: float) -> bool:
    """
    Check if a repair amount would exceed the user's 24h spend limit.
    Returns True if the spend is within limits. Fails closed on error.
    """
    policy = get_autopilot_policy(user)
    spend_limit = float(policy.get('spend_limit_24h', DEFAULT_POLICY['spend_limit_24h']))

    try:
        from .defi_models import DeFiTransaction
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        recent_txns = DeFiTransaction.objects.filter(
            user=user,
            created_at__gte=cutoff,
            status__in=('pending', 'confirmed'),
        )
        spent_24h = sum(float(tx.amount_usd) for tx in recent_txns)
        return (spent_24h + amount_usd) <= spend_limit
    except Exception as e:
        logger.warning(f"Error in daily spend check: {e}")
        return False  # Fail closed: if we can't check, don't auto-spend


def auto_evaluate_and_prepare(user) -> Dict[str, Any]:
    """
    AUTO_BOUNDED execution: auto-prepare qualifying repairs.

    1. Verify user's autonomy level is AUTO_BOUNDED or AUTO_SPEND
    2. Get pending repairs (risk + strategy engine unified queue)
    3. Filter repairs within spend_limit_24h
    4. For qualifying repairs: execute_repair() creates DeFiTransaction + stores last_move
    5. Create DeFiAlert record + send push notification
    6. AUTO_SPEND will auto-execute within spend permission window

    Returns dict with 'prepared_count' and 'repairs_prepared' list.
    """
    result: Dict[str, Any] = {'prepared_count': 0, 'repairs_prepared': []}

    if not user or not getattr(user, 'is_authenticated', False):
        return result

    policy = get_autopilot_policy(user)
    if policy.get('level') not in ('AUTO_BOUNDED', 'AUTO_SPEND'):
        return result

    allow_auto_spend = policy.get('level') == 'AUTO_SPEND' and _spend_permission_active(policy)

    repairs = get_pending_repairs(user)
    if not repairs:
        return result

    from .autopilot_notification_service import get_autopilot_notification_service
    notification_service = get_autopilot_notification_service()

    for repair in repairs:
        repair_id = repair.get('id', '')

        # Skip demo repairs
        if repair_id.startswith('demo:'):
            continue

        # Estimate USD value from position for spend limit check.
        # Use from_pool_id to look up position value.
        estimated_usd = 0.0
        try:
            from .defi_models import UserDeFiPosition
            parts = repair_id.split(':')
            pos_id = parts[1] if parts[0] == 'strategy' and len(parts) >= 3 else parts[0]
            position = UserDeFiPosition.objects.filter(id=pos_id).first()
            if position:
                estimated_usd = float(position.staked_value_usd)
        except Exception:
            pass

        if not _daily_spend_check(user, estimated_usd):
            logger.info(f"Skipping auto repair {repair_id}: exceeds daily spend limit")
            continue

        # Execute repair (creates DeFiTransaction + stores last_move)
        exec_result = execute_repair(user, repair_id)
        if exec_result.get('success'):
            result['prepared_count'] += 1
            result['repairs_prepared'].append(repair_id)

            # Create DeFiAlert record
            try:
                from .defi_models import DeFiAlert
                action_phrase = 'Auto-executed' if allow_auto_spend else 'Prepared'
                DeFiAlert.objects.create(
                    user=user,
                    alert_type='repair_executed',
                    severity='medium' if allow_auto_spend else 'low',
                    title=f"Auto-Pilot {action_phrase} a Move",
                    message=(
                        f"{action_phrase} move from {repair.get('from_vault', '?')} to "
                        f"{repair.get('to_vault', '?')}. "
                        f"{'No wallet approval needed.' if allow_auto_spend else 'Approve in your wallet within 24h.'}"
                    ),
                    data=repair,
                    repair_id=repair_id,
                )
            except Exception as e:
                logger.warning(f"Failed to create DeFiAlert for auto repair: {e}")

            # Send push notification
            notification_service.notify_repair_executed(user, repair)

    return result
