"""
DeFi Strategy Rotation Engine

Auto-compounding and yield optimization engine that:
- Evaluates user positions against current pool APYs
- Suggests strategy rotations when a materially better opportunity exists
- Identifies harvestable rewards above a minimum threshold
- Records rotation intents as DeFiTransactions for audit trail

Runs as a Celery periodic task every 30 minutes.

Part of Phase 5: Yield Forge
"""
import logging
from decimal import Decimal
from datetime import timedelta
from typing import List, Dict, Optional

from django.utils import timezone
from django.db.models import Avg, Max, Q, Subquery, OuterRef

logger = logging.getLogger(__name__)


# ---- Strategy Constants ----

ROTATION_THRESHOLD = 0.20       # 20% APY improvement required to suggest rotation
MIN_HARVEST_USD = 10            # Minimum $10 in rewards before suggesting harvest
EVALUATION_LOOKBACK_DAYS = 7    # Use 7-day average APY for stability
MIN_TVL_USD = 100_000           # Minimum TVL for a target pool to be considered
MAX_RISK_SCORE_DELTA = 0.20     # Don't suggest pools with >0.20 higher risk score
MIN_POSITION_AGE_HOURS = 24     # Don't rotate positions less than 24 hours old
MAX_SUGGESTIONS_PER_USER = 5    # Cap rotation suggestions per evaluation run


# ---- Lazy Model Imports ----

def _get_models():
    """Lazy import DeFi models to avoid circular imports."""
    try:
        from .defi_models import (
            DeFiPool,
            DeFiTransaction,
            UserDeFiPosition,
            YieldSnapshot,
            DeFiProtocol,
        )
        return {
            'DeFiPool': DeFiPool,
            'DeFiTransaction': DeFiTransaction,
            'UserDeFiPosition': UserDeFiPosition,
            'YieldSnapshot': YieldSnapshot,
            'DeFiProtocol': DeFiProtocol,
        }
    except ImportError as e:
        logger.error(f"Failed to import DeFi models: {e}")
        return None


def _get_validation_service():
    """Lazy import validation service."""
    try:
        from .defi_validation_service import validate_transaction, ValidationResult
        return {
            'validate_transaction': validate_transaction,
            'ValidationResult': ValidationResult,
        }
    except ImportError as e:
        logger.warning(f"Validation service not available: {e}")
        return None


# ---- Strategy Evaluation ----

class StrategyEvaluation:
    """
    Evaluates a user's active DeFi positions against current market yields
    and produces actionable rotation suggestions.

    Each evaluation:
    1. Loads the user's active positions
    2. Retrieves the rolling average APY for each position's pool
    3. Compares against the best available pools (same chain, same type, similar risk)
    4. Suggests rotation when APY improvement exceeds ROTATION_THRESHOLD
    """

    def __init__(
        self,
        rotation_threshold: float = ROTATION_THRESHOLD,
        min_harvest_usd: float = MIN_HARVEST_USD,
        lookback_days: int = EVALUATION_LOOKBACK_DAYS,
    ):
        self.rotation_threshold = rotation_threshold
        self.min_harvest_usd = min_harvest_usd
        self.lookback_days = lookback_days
        self.models = _get_models()

    def evaluate_positions(self, user) -> List[Dict]:
        """
        Main evaluation entry point. Scans all active positions for a user
        and returns a list of StrategyRotationSuggestion dicts.

        Each suggestion dict contains:
            - position_id: ID of the current position
            - current_pool_id: current pool ID
            - current_pool_symbol: current pool symbol
            - current_apy: rolling average APY of current pool
            - suggested_pool_id: target pool ID
            - suggested_pool_symbol: target pool symbol
            - suggested_apy: rolling average APY of target pool
            - apy_improvement_pct: relative improvement as a decimal (e.g. 0.35 = 35%)
            - risk_delta: difference in risk score (positive = riskier)
            - suggestion_type: 'rotate' or 'harvest'
            - reason: human-readable explanation

        Returns:
            List of suggestion dicts, capped at MAX_SUGGESTIONS_PER_USER.
        """
        if not self.models:
            logger.error("DeFi models not available, cannot evaluate positions")
            return []

        UserDeFiPosition = self.models['UserDeFiPosition']

        try:
            active_positions = UserDeFiPosition.objects.filter(
                user=user,
                is_active=True,
            ).select_related('pool', 'pool__protocol')

            if not active_positions.exists():
                logger.debug(f"No active positions for user {user.id}")
                return []

            suggestions = []

            for position in active_positions:
                try:
                    rotation = self.evaluate_single_position(position)
                    if rotation:
                        suggestions.append(rotation)

                    harvest = self._check_harvest_opportunity(position)
                    if harvest:
                        suggestions.append(harvest)

                except Exception as e:
                    logger.warning(
                        f"Error evaluating position {position.id} "
                        f"for user {user.id}: {e}"
                    )

            # Sort by APY improvement descending, cap results
            suggestions.sort(
                key=lambda s: s.get('apy_improvement_pct', 0),
                reverse=True,
            )

            logger.info(
                f"Strategy evaluation for user {user.id}: "
                f"{active_positions.count()} positions checked, "
                f"{len(suggestions)} suggestions generated"
            )

            return suggestions[:MAX_SUGGESTIONS_PER_USER]

        except Exception as e:
            logger.error(
                f"Error evaluating positions for user {user.id}: {e}",
                exc_info=True,
            )
            return []

    def evaluate_single_position(self, position) -> Optional[Dict]:
        """
        Evaluate a single position for rotation opportunity.

        Compares the position's current pool APY (rolling average over
        lookback_days) against the best available pool on the same chain
        with a compatible type and risk profile.

        Args:
            position: UserDeFiPosition instance

        Returns:
            StrategyRotationSuggestion dict if a worthwhile rotation exists,
            None otherwise.
        """
        if not self.models:
            return None

        YieldSnapshot = self.models['YieldSnapshot']
        DeFiPool = self.models['DeFiPool']

        try:
            # Skip positions that are too new to evaluate
            min_age = timezone.now() - timedelta(hours=MIN_POSITION_AGE_HOURS)
            if position.created_at > min_age:
                logger.debug(
                    f"Position {position.id} is too new to evaluate "
                    f"(created {position.created_at})"
                )
                return None

            current_pool = position.pool
            if not current_pool or not current_pool.is_active:
                return None

            # Calculate rolling average APY for current pool
            current_avg_apy = self._get_rolling_avg_apy(current_pool.id)
            if current_avg_apy is None:
                logger.debug(
                    f"No yield data for pool {current_pool.id}, skipping"
                )
                return None

            # Get current risk score for the position's pool
            current_risk = self._get_latest_risk_score(current_pool.id)

            # Find candidate pools: same chain, same type, active, sufficient TVL
            candidate_pools = DeFiPool.objects.filter(
                chain=current_pool.chain,
                pool_type=current_pool.pool_type,
                is_active=True,
            ).exclude(
                id=current_pool.id,
            ).select_related('protocol')

            best_candidate = None
            best_apy = current_avg_apy
            best_risk = current_risk

            for candidate in candidate_pools:
                candidate_apy = self._get_rolling_avg_apy(candidate.id)
                if candidate_apy is None:
                    continue

                candidate_risk = self._get_latest_risk_score(candidate.id)
                candidate_tvl = self._get_latest_tvl(candidate.id)

                # Filter: minimum TVL
                if candidate_tvl is not None and candidate_tvl < MIN_TVL_USD:
                    continue

                # Filter: don't suggest significantly riskier pools
                risk_delta = candidate_risk - current_risk
                if risk_delta > MAX_RISK_SCORE_DELTA:
                    continue

                # Check if this candidate beats the current best
                if candidate_apy > best_apy:
                    best_candidate = candidate
                    best_apy = candidate_apy
                    best_risk = candidate_risk

            # Determine if the improvement is worth suggesting
            if best_candidate is None:
                return None

            if current_avg_apy <= 0:
                # Avoid division by zero; any positive APY is an improvement
                improvement_pct = 1.0 if best_apy > 0 else 0
            else:
                improvement_pct = (best_apy - current_avg_apy) / current_avg_apy

            if improvement_pct < self.rotation_threshold:
                return None

            risk_delta = best_risk - current_risk

            suggestion = {
                'position_id': position.id,
                'current_pool_id': current_pool.id,
                'current_pool_symbol': current_pool.symbol,
                'current_apy': round(current_avg_apy, 2),
                'suggested_pool_id': best_candidate.id,
                'suggested_pool_symbol': best_candidate.symbol,
                'suggested_pool_protocol': best_candidate.protocol.name,
                'suggested_apy': round(best_apy, 2),
                'apy_improvement_pct': round(improvement_pct, 4),
                'risk_delta': round(risk_delta, 3),
                'suggestion_type': 'rotate',
                'reason': (
                    f"{best_candidate.protocol.name} {best_candidate.symbol} offers "
                    f"{best_apy:.1f}% APY vs your current {current_avg_apy:.1f}% "
                    f"({improvement_pct:.0%} improvement) on {current_pool.chain}."
                ),
            }

            logger.info(
                f"Rotation suggestion for position {position.id}: "
                f"pool {current_pool.id} -> {best_candidate.id} "
                f"(APY {current_avg_apy:.1f}% -> {best_apy:.1f}%)"
            )

            return suggestion

        except Exception as e:
            logger.warning(
                f"Error evaluating single position {position.id}: {e}"
            )
            return None

    def _check_harvest_opportunity(self, position) -> Optional[Dict]:
        """
        Check if a position has harvestable rewards above the minimum threshold.

        Args:
            position: UserDeFiPosition instance

        Returns:
            Harvest suggestion dict if rewards exceed MIN_HARVEST_USD,
            None otherwise.
        """
        try:
            rewards_value = float(position.rewards_earned)

            if rewards_value < self.min_harvest_usd:
                return None

            current_apy = self._get_rolling_avg_apy(position.pool_id)

            return {
                'position_id': position.id,
                'current_pool_id': position.pool_id,
                'current_pool_symbol': position.pool.symbol,
                'current_apy': round(current_apy, 2) if current_apy else 0,
                'suggested_pool_id': None,
                'suggested_pool_symbol': None,
                'suggested_pool_protocol': None,
                'suggested_apy': None,
                'apy_improvement_pct': 0,
                'risk_delta': 0,
                'suggestion_type': 'harvest',
                'rewards_usd': round(rewards_value, 2),
                'reason': (
                    f"${rewards_value:.2f} in rewards ready to harvest on your "
                    f"{position.pool.symbol} position. Consider compounding or withdrawing."
                ),
            }

        except Exception as e:
            logger.warning(
                f"Error checking harvest opportunity for position {position.id}: {e}"
            )
            return None

    def _get_rolling_avg_apy(self, pool_id: int) -> Optional[float]:
        """
        Calculate the rolling average APY for a pool over the lookback window.

        Uses YieldSnapshot records from the last EVALUATION_LOOKBACK_DAYS to
        smooth out short-term APY fluctuations and provide a stable comparison.

        Args:
            pool_id: DeFiPool ID

        Returns:
            Average APY as a float, or None if no data is available.
        """
        YieldSnapshot = self.models['YieldSnapshot']

        cutoff = timezone.now() - timedelta(days=self.lookback_days)

        result = YieldSnapshot.objects.filter(
            pool_id=pool_id,
            timestamp__gte=cutoff,
        ).aggregate(avg_apy=Avg('apy_total'))

        avg_apy = result.get('avg_apy')
        return float(avg_apy) if avg_apy is not None else None

    def _get_latest_risk_score(self, pool_id: int) -> float:
        """
        Get the most recent risk score for a pool.

        Args:
            pool_id: DeFiPool ID

        Returns:
            Risk score as float, defaults to 0.5 if unavailable.
        """
        YieldSnapshot = self.models['YieldSnapshot']

        latest = YieldSnapshot.objects.filter(
            pool_id=pool_id,
        ).order_by('-timestamp').values_list('risk_score', flat=True).first()

        return float(latest) if latest is not None else 0.5

    def _get_latest_tvl(self, pool_id: int) -> Optional[float]:
        """
        Get the most recent TVL for a pool.

        Args:
            pool_id: DeFiPool ID

        Returns:
            TVL in USD as float, or None if unavailable.
        """
        YieldSnapshot = self.models['YieldSnapshot']

        latest = YieldSnapshot.objects.filter(
            pool_id=pool_id,
        ).order_by('-timestamp').values_list('tvl_usd', flat=True).first()

        return float(latest) if latest is not None else None


# ---- Public Functions ----

def evaluate_positions(user) -> List[Dict]:
    """
    Evaluate all active DeFi positions for a user and return rotation
    and harvest suggestions.

    This is the primary entry point for on-demand evaluation (e.g., from
    a GraphQL query or user-initiated refresh).

    Args:
        user: Django User instance

    Returns:
        List of StrategyRotationSuggestion dicts
    """
    engine = StrategyEvaluation()
    return engine.evaluate_positions(user)


def evaluate_single_position(position) -> Optional[Dict]:
    """
    Evaluate a single UserDeFiPosition for rotation opportunity.

    Args:
        position: UserDeFiPosition instance

    Returns:
        StrategyRotationSuggestion dict or None
    """
    engine = StrategyEvaluation()
    return engine.evaluate_single_position(position)


def auto_compound_check() -> Dict:
    """
    Scan all active positions across all users for harvestable rewards
    that exceed MIN_HARVEST_USD.

    Returns a summary dict with harvest opportunities grouped by user.

    Returns:
        dict with:
            - total_positions_checked: int
            - harvest_opportunities: list of dicts with user_id, position_id,
              pool_symbol, rewards_usd
            - total_harvestable_usd: float
    """
    models = _get_models()
    if not models:
        logger.error("DeFi models not available for auto-compound check")
        return {
            'total_positions_checked': 0,
            'harvest_opportunities': [],
            'total_harvestable_usd': 0,
        }

    UserDeFiPosition = models['UserDeFiPosition']

    try:
        active_positions = UserDeFiPosition.objects.filter(
            is_active=True,
        ).select_related('pool', 'pool__protocol', 'user')

        opportunities = []
        total_harvestable = 0.0
        positions_checked = 0

        for position in active_positions:
            positions_checked += 1

            try:
                rewards_value = float(position.rewards_earned)

                if rewards_value >= MIN_HARVEST_USD:
                    opportunities.append({
                        'user_id': position.user_id,
                        'position_id': position.id,
                        'pool_id': position.pool_id,
                        'pool_symbol': position.pool.symbol,
                        'protocol': position.pool.protocol.name,
                        'chain': position.pool.chain,
                        'rewards_usd': round(rewards_value, 2),
                        'staked_value_usd': float(position.staked_value_usd),
                    })
                    total_harvestable += rewards_value

            except Exception as e:
                logger.warning(
                    f"Error checking harvest for position {position.id}: {e}"
                )

        logger.info(
            f"Auto-compound check: {positions_checked} positions, "
            f"{len(opportunities)} harvest opportunities, "
            f"${total_harvestable:.2f} total harvestable"
        )

        return {
            'total_positions_checked': positions_checked,
            'harvest_opportunities': opportunities,
            'total_harvestable_usd': round(total_harvestable, 2),
        }

    except Exception as e:
        logger.error(f"Error in auto-compound check: {e}", exc_info=True)
        return {
            'total_positions_checked': 0,
            'harvest_opportunities': [],
            'total_harvestable_usd': 0,
        }


def apply_rotation(user, position_id: int, new_pool_id: int) -> Dict:
    """
    Record a rotation intent for a user's position.

    Creates a new DeFiTransaction with action='rotate' to record the user's
    decision to move funds from one pool to another. The actual on-chain
    execution (withdraw from old pool + deposit to new pool) is handled
    by the mobile app via WalletConnect.

    This function:
    1. Validates the position belongs to the user and is active
    2. Validates the target pool exists and is active
    3. Runs the standard transaction validation pipeline
    4. Creates a pending DeFiTransaction with action='rotate'

    Args:
        user: Django User instance
        position_id: ID of the UserDeFiPosition to rotate
        new_pool_id: ID of the target DeFiPool

    Returns:
        dict with:
            - success: bool
            - message: str
            - transaction_id: str (if successful)
            - validation_warnings: list of str
    """
    models = _get_models()
    if not models:
        return {
            'success': False,
            'message': 'DeFi models not available',
            'transaction_id': None,
            'validation_warnings': [],
        }

    UserDeFiPosition = models['UserDeFiPosition']
    DeFiPool = models['DeFiPool']
    DeFiTransaction = models['DeFiTransaction']

    try:
        # 1. Validate the position
        try:
            position = UserDeFiPosition.objects.select_related(
                'pool', 'pool__protocol'
            ).get(
                id=position_id,
                user=user,
                is_active=True,
            )
        except UserDeFiPosition.DoesNotExist:
            return {
                'success': False,
                'message': (
                    f'Position {position_id} not found, does not belong to you, '
                    f'or is no longer active.'
                ),
                'transaction_id': None,
                'validation_warnings': [],
            }

        # 2. Validate the target pool
        try:
            new_pool = DeFiPool.objects.select_related('protocol').get(
                id=new_pool_id,
                is_active=True,
            )
        except DeFiPool.DoesNotExist:
            return {
                'success': False,
                'message': f'Target pool {new_pool_id} not found or inactive.',
                'transaction_id': None,
                'validation_warnings': [],
            }

        # 3. Run validation pipeline
        validation_warnings = []
        validation_svc = _get_validation_service()
        if validation_svc:
            validate_fn = validation_svc['validate_transaction']
            result = validate_fn(
                user=user,
                tx_type='withdraw',
                wallet_address=position.wallet_address,
                symbol=position.pool.symbol,
                amount_human=str(position.staked_amount),
                chain_id=position.pool.chain_id,
                pool_id=str(position.pool_id),
            )
            if not result.is_valid:
                return {
                    'success': False,
                    'message': f'Validation failed: {result.reason}',
                    'transaction_id': None,
                    'validation_warnings': result.warnings,
                }
            validation_warnings = result.warnings

        # 4. Create rotation transaction record
        tx_record = DeFiTransaction.objects.create(
            user=user,
            position=position,
            pool=new_pool,
            action='rotate',
            tx_hash=f'rotate_intent_{timezone.now().timestamp():.0f}',
            chain_id=position.pool.chain_id,
            amount=position.staked_amount,
            amount_usd=position.staked_value_usd,
            status='pending',
        )

        logger.info(
            f"Rotation intent recorded: user={user.id} "
            f"position={position_id} "
            f"from_pool={position.pool_id} to_pool={new_pool_id} "
            f"amount={position.staked_amount} tx_id={tx_record.id}"
        )

        return {
            'success': True,
            'message': (
                f'Rotation from {position.pool.symbol} to {new_pool.symbol} '
                f'({new_pool.protocol.name}) recorded. '
                f'Complete the on-chain transaction in your wallet.'
            ),
            'transaction_id': str(tx_record.id),
            'validation_warnings': validation_warnings,
        }

    except Exception as e:
        logger.error(
            f"Error applying rotation for user {user.id}: {e}",
            exc_info=True,
        )
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}',
            'transaction_id': None,
            'validation_warnings': [],
        }


# ---- Celery Task ----

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed, strategy rotation task will not be scheduled")

    def shared_task(*args, **kwargs):
        """Fallback decorator when Celery is not installed."""
        def decorator(func):
            return func
        return decorator


@shared_task(bind=True, max_retries=2)
def evaluate_strategy_rotations_task(self):
    """
    Periodic Celery task (runs every 30 minutes).

    Evaluates all users who have active DeFi positions and generates
    rotation and harvest suggestions. Results are logged and can be
    surfaced via GraphQL queries or push notifications.

    Steps:
    1. Query distinct users with active positions
    2. Run StrategyEvaluation for each user
    3. Run auto_compound_check for global harvest scan
    4. Log summary metrics

    Returns:
        dict with evaluation summary
    """
    try:
        models = _get_models()
        if not models:
            logger.error("DeFi models not available, skipping strategy rotation evaluation")
            return {'status': 'error', 'message': 'Models not available'}

        UserDeFiPosition = models['UserDeFiPosition']

        # Get distinct users with active positions
        user_ids = UserDeFiPosition.objects.filter(
            is_active=True,
        ).values_list('user_id', flat=True).distinct()

        total_users = len(user_ids)
        total_suggestions = 0
        total_rotations = 0
        total_harvests = 0
        errors = 0

        engine = StrategyEvaluation()

        for user_id in user_ids:
            try:
                # Resolve user object
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)

                suggestions = engine.evaluate_positions(user)
                total_suggestions += len(suggestions)

                for s in suggestions:
                    if s.get('suggestion_type') == 'rotate':
                        total_rotations += 1
                    elif s.get('suggestion_type') == 'harvest':
                        total_harvests += 1

            except Exception as e:
                logger.warning(
                    f"Error evaluating strategies for user {user_id}: {e}"
                )
                errors += 1

        # Global auto-compound scan
        compound_result = auto_compound_check()

        summary = {
            'status': 'success',
            'users_evaluated': total_users,
            'total_suggestions': total_suggestions,
            'rotation_suggestions': total_rotations,
            'harvest_suggestions': total_harvests,
            'compound_opportunities': len(
                compound_result.get('harvest_opportunities', [])
            ),
            'total_harvestable_usd': compound_result.get(
                'total_harvestable_usd', 0
            ),
            'errors': errors,
        }

        logger.info(f"Strategy rotation evaluation complete: {summary}")
        return summary

    except Exception as e:
        logger.error(
            f"Error in strategy rotation task: {e}", exc_info=True
        )
        if CELERY_AVAILABLE and hasattr(self, 'request') and self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))
        return {'status': 'failed', 'error': str(e)}
