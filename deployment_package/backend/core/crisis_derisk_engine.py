"""
Crisis De-Risk Engine

Active position reduction during emergencies.
When the circuit breaker trips or portfolio drawdown is breached,
this engine evaluates which positions to reduce and takes action
based on the user's autonomy level.

Crisis sequence: Stabilize -> Explain -> Repair
This module handles "Stabilize" (reduce risk) and triggers "Explain" (alerts).

Part of Trust-First Framework: Gap 4 — Active De-Risking
"""
import logging
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cooldown: don't re-evaluate same user within this window
DERISK_COOLDOWN_KEY = 'defi:derisk_cooldown:{user_id}'
DERISK_COOLDOWN_SECONDS = 1800  # 30 minutes

# Maximum percentage of a position to de-risk in a single action
DEFAULT_MAX_DERISK_PCT = 0.50  # 50%


class CrisisDeriskEngine:
    """
    Evaluates and executes defensive de-risk actions during crises.
    Respects user autonomy levels and policy guardrails.
    """

    def __init__(self):
        self._load_config()

    def _load_config(self):
        """Load crisis response config from policy."""
        try:
            from .policy_engine import get_policy
            policy = get_policy()
            crisis = policy.get('crisis_response', {})
            self.auto_derisk_on_drawdown = crisis.get('auto_derisk_on_drawdown', True)
            self.auto_derisk_on_incident = crisis.get('auto_derisk_on_protocol_incident', True)
            self.max_derisk_pct = float(crisis.get('max_derisk_pct_per_action', DEFAULT_MAX_DERISK_PCT))
            self.cooldown_seconds = int(crisis.get('derisk_cooldown_minutes', 30)) * 60
        except Exception:
            self.auto_derisk_on_drawdown = True
            self.auto_derisk_on_incident = True
            self.max_derisk_pct = DEFAULT_MAX_DERISK_PCT
            self.cooldown_seconds = DERISK_COOLDOWN_SECONDS

    def evaluate_crisis_response(
        self,
        trigger_type: str,
        chain_id: int = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Evaluate and execute crisis de-risk for affected users.

        Args:
            trigger_type: 'gas_spike', 'protocol_incident', 'portfolio_drawdown',
                         'oracle_stale', 'stablecoin_depeg'
            chain_id: Optional chain filter (only de-risk positions on this chain)
            user: Optional specific user (if None, checks all users with positions)

        Returns:
            dict with: users_evaluated, actions_taken, actions_suggested
        """
        stats = {
            'trigger_type': trigger_type,
            'users_evaluated': 0,
            'actions_taken': 0,
            'actions_suggested': 0,
        }

        # Determine if this trigger type should auto-de-risk
        if trigger_type == 'portfolio_drawdown' and not self.auto_derisk_on_drawdown:
            logger.info("Auto de-risk on drawdown is disabled by policy")
            return stats
        if trigger_type == 'protocol_incident' and not self.auto_derisk_on_incident:
            logger.info("Auto de-risk on protocol incident is disabled by policy")
            return stats

        # Gas spikes don't require de-risking (positions are safe, only new txs blocked)
        if trigger_type == 'gas_spike':
            logger.info("Gas spike: no de-risking needed (positions are safe)")
            return stats

        try:
            if user:
                users = [user]
            else:
                users = self._get_affected_users(chain_id)

            for u in users:
                try:
                    result = self.evaluate_user_derisk(u, trigger_type, chain_id)
                    stats['users_evaluated'] += 1
                    stats['actions_taken'] += result.get('actions_taken', 0)
                    stats['actions_suggested'] += result.get('actions_suggested', 0)
                except Exception as e:
                    logger.warning(
                        f"Error evaluating de-risk for user {u.id}: {e}"
                    )

            logger.info(f"Crisis de-risk evaluation complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in crisis de-risk evaluation: {e}", exc_info=True)
            return stats

    def evaluate_user_derisk(
        self,
        user,
        trigger_type: str,
        chain_id: int = None,
    ) -> Dict[str, Any]:
        """
        Evaluate de-risk actions for a single user.

        Based on autonomy level:
        - NOTIFY_ONLY: Create urgent alert only
        - APPROVE_REPAIRS: Create alert with 1-tap de-risk option
        - AUTO_BOUNDED: Auto-prepare de-risk repairs (within spend limit)
        - AUTO_SPEND: Auto-execute de-risk

        Returns:
            dict with: actions_taken, actions_suggested, actions (list)
        """
        result = {
            'actions_taken': 0,
            'actions_suggested': 0,
            'actions': [],
        }

        # Check cooldown
        cooldown_key = DERISK_COOLDOWN_KEY.format(user_id=user.id)
        if cache.get(cooldown_key):
            logger.debug(f"De-risk cooldown active for user {user.id}")
            return result

        from .autopilot_service import (
            get_autopilot_policy,
            is_autopilot_enabled,
        )

        if not is_autopilot_enabled(user):
            return result

        policy = get_autopilot_policy(user)
        autonomy_level = policy.get('level', 'NOTIFY_ONLY')

        # Get positions to de-risk
        positions = self._get_positions_to_derisk(user, chain_id, trigger_type)
        if not positions:
            return result

        # Prioritize by exposure
        positions = self._prioritize_positions(positions)

        # Generate crisis explanation
        from .proof_narrator import get_proof_narrator
        narrator = get_proof_narrator()

        # Build de-risk actions
        for position in positions:
            action = self._build_derisk_action(position, trigger_type)
            if not action:
                continue

            if autonomy_level in ('AUTO_BOUNDED', 'AUTO_SPEND'):
                # Auto-prepare the de-risk repair
                prepared = self._auto_prepare_derisk(user, action, policy)
                if prepared:
                    result['actions_taken'] += 1
                    action['status'] = 'prepared'
                else:
                    result['actions_suggested'] += 1
                    action['status'] = 'suggested'
            else:
                # Just notify
                result['actions_suggested'] += 1
                action['status'] = 'suggested'

            result['actions'].append(action)

        # Create alert with actions summary
        if result['actions']:
            self._create_crisis_alert(user, trigger_type, result, chain_id)

        # Set cooldown
        cache.set(cooldown_key, True, timeout=self.cooldown_seconds)

        return result

    def _get_affected_users(self, chain_id: int = None) -> list:
        """Get users with active positions, optionally filtered by chain."""
        try:
            from .defi_models import UserDeFiPosition
            from django.contrib.auth import get_user_model
            User = get_user_model()

            filters = {'is_active': True}
            if chain_id:
                filters['pool__chain_id'] = chain_id

            user_ids = UserDeFiPosition.objects.filter(
                **filters
            ).values_list('user_id', flat=True).distinct()

            return list(User.objects.filter(id__in=user_ids))
        except Exception as e:
            logger.warning(f"Error getting affected users: {e}")
            return []

    def _get_positions_to_derisk(
        self, user, chain_id: int = None, trigger_type: str = '',
    ) -> list:
        """Get positions that should be considered for de-risking."""
        try:
            from .defi_models import UserDeFiPosition

            filters = {
                'user': user,
                'is_active': True,
            }
            if chain_id:
                filters['pool__chain_id'] = chain_id

            positions = UserDeFiPosition.objects.filter(
                **filters
            ).select_related('pool', 'pool__protocol')

            return list(positions)
        except Exception as e:
            logger.warning(f"Error getting positions for de-risk: {e}")
            return []

    def _prioritize_positions(self, positions: list) -> list:
        """
        Sort positions by de-risk priority.
        Highest exposure first, most volatile chains first.
        """
        CHAIN_VOLATILITY = {
            1: 1.0,       # Ethereum: baseline
            137: 1.2,     # Polygon: slightly more volatile
            42161: 1.1,   # Arbitrum: similar to Ethereum
            8453: 1.1,    # Base: similar to Ethereum
        }

        def priority_score(position):
            exposure = float(position.staked_value_usd)
            chain_id = position.pool.chain_id if position.pool else 1
            chain_mult = CHAIN_VOLATILITY.get(chain_id, 1.0)
            return exposure * chain_mult

        return sorted(positions, key=priority_score, reverse=True)

    def _build_derisk_action(
        self, position, trigger_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Build a de-risk action for a position."""
        try:
            pool = position.pool
            if not pool:
                return None

            exposure_usd = float(position.staked_value_usd)
            derisk_amount_usd = exposure_usd * self.max_derisk_pct

            protocol_name = ''
            if pool.protocol:
                protocol_name = pool.protocol.name or pool.protocol.slug or ''

            return {
                'type': 'emergency_withdraw',
                'position_id': str(position.id),
                'pool_id': str(pool.id),
                'pool_symbol': pool.symbol,
                'protocol': protocol_name,
                'chain_id': pool.chain_id,
                'wallet_address': position.wallet_address,
                'exposure_usd': round(exposure_usd, 2),
                'derisk_amount_usd': round(derisk_amount_usd, 2),
                'derisk_pct': self.max_derisk_pct,
                'trigger': trigger_type,
                'reason': self._derisk_reason(trigger_type, protocol_name, pool.symbol),
            }
        except Exception as e:
            logger.warning(f"Error building de-risk action: {e}")
            return None

    def _derisk_reason(
        self, trigger_type: str, protocol: str, symbol: str,
    ) -> str:
        """Generate human-readable reason for de-risk action."""
        reasons = {
            'portfolio_drawdown': (
                f"Portfolio drawdown exceeded safety limit. "
                f"Reducing exposure in {protocol} {symbol} to protect capital."
            ),
            'protocol_incident': (
                f"Protocol incident detected. "
                f"Withdrawing from {protocol} {symbol} as a precaution."
            ),
            'oracle_stale': (
                f"Oracle data is stale on this chain. "
                f"Reducing exposure in {protocol} {symbol} until data refreshes."
            ),
            'stablecoin_depeg': (
                f"Stablecoin depeg detected for {symbol}. "
                f"Reducing exposure to limit potential losses."
            ),
        }
        return reasons.get(trigger_type, f"Emergency de-risk for {protocol} {symbol}")

    def _auto_prepare_derisk(
        self, user, action: Dict, policy: Dict,
    ) -> bool:
        """
        Auto-prepare a de-risk action for AUTO_BOUNDED/AUTO_SPEND users.
        Creates a DeFiTransaction record and DeFiAlert.
        Returns True if successfully prepared.
        """
        try:
            from .autopilot_service import _daily_spend_check
            from .defi_models import DeFiTransaction, DeFiPool
            from decimal import Decimal

            # Check daily spend limit
            if not _daily_spend_check(user, action['derisk_amount_usd']):
                logger.info(
                    f"De-risk for user {user.id} exceeds daily spend limit"
                )
                return False

            pool = DeFiPool.objects.filter(id=action['pool_id']).first()
            if not pool:
                return False

            # Create pending withdrawal transaction
            DeFiTransaction.objects.create(
                user=user,
                pool=pool,
                action='withdraw',
                tx_hash=f"crisis_derisk_{timezone.now().timestamp():.0f}",
                chain_id=action['chain_id'],
                amount=Decimal(str(action['derisk_amount_usd'])),
                amount_usd=Decimal(str(action['derisk_amount_usd'])),
                status='pending',
            )

            # Log to repair decision ledger
            try:
                from .defi_models import DeFiRepairDecision, UserDeFiPosition
                position = UserDeFiPosition.objects.filter(
                    id=action['position_id']
                ).first()

                DeFiRepairDecision.objects.create(
                    user=user,
                    position=position,
                    from_pool=pool,
                    to_pool=None,  # Withdraw to wallet
                    repair_id=f"crisis:{action['position_id']}:{action['trigger']}",
                    decision_type='executed',
                    inputs={'trigger': action['trigger'], 'derisk_pct': action['derisk_pct']},
                    explanation=action['reason'],
                    expected_apy_delta=0.0,  # Defensive move, not yield-seeking
                    policy_version=policy.get('version', ''),
                    executed_at=timezone.now(),
                )
            except Exception as e:
                logger.warning(f"Failed to log crisis de-risk decision: {e}")

            return True

        except Exception as e:
            logger.warning(f"Error auto-preparing de-risk action: {e}")
            return False

    def _create_crisis_alert(
        self, user, trigger_type: str, result: Dict, chain_id: int = None,
    ):
        """Create a DeFi alert summarizing crisis de-risk actions."""
        try:
            from .defi_models import DeFiAlert
            from .proof_narrator import get_proof_narrator

            narrator = get_proof_narrator()
            actions = result.get('actions', [])

            # Build crisis explanation
            from .defi_circuit_breaker import get_circuit_state
            cb_state = get_circuit_state()
            crisis_explanation = narrator.narrate_crisis(cb_state)

            total_derisk = sum(a.get('derisk_amount_usd', 0) for a in actions)
            actions_taken = result.get('actions_taken', 0)
            actions_suggested = result.get('actions_suggested', 0)

            if actions_taken > 0:
                title = f"Emergency De-Risk: {actions_taken} Position(s) Protected"
                message = (
                    f"{crisis_explanation} "
                    f"Auto-Pilot has prepared ${total_derisk:,.0f} in "
                    f"protective withdrawals. Approve in your wallet."
                )
            else:
                title = f"Action Needed: {actions_suggested} Position(s) at Risk"
                message = (
                    f"{crisis_explanation} "
                    f"We recommend reducing ${total_derisk:,.0f} in exposure. "
                    f"Review the suggested actions in your Auto-Pilot dashboard."
                )

            DeFiAlert.objects.create(
                user=user,
                alert_type='policy_breach',
                severity='urgent',
                title=title,
                message=message,
                data={
                    'trigger_type': trigger_type,
                    'chain_id': chain_id,
                    'actions': actions,
                    'crisis_explanation': crisis_explanation,
                },
            )

            # Send push notification
            try:
                from .autopilot_notification_service import get_autopilot_notification_service
                service = get_autopilot_notification_service()
                service.notify_policy_breach(user, {
                    'title': title,
                    'message': message,
                    'trigger_type': trigger_type,
                })
            except Exception as e:
                logger.warning(f"Crisis push notification failed: {e}")

        except Exception as e:
            logger.error(f"Failed to create crisis alert for user {user.id}: {e}")
