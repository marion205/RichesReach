"""
DeFi Achievement Service for RichesReach

Tracks and evaluates user milestones in their DeFi journey, provides
portfolio analytics, and powers the "Ghost Whisper DeFi" recommendation engine.

Achievements are designed around the BIPOC wealth-building mission:
building a financial fortress, step by step.

Part of Phase 5: Community Vanguard
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg, F

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Achievement Definitions
# ---------------------------------------------------------------------------

ACHIEVEMENTS: Dict[str, dict] = {
    'first_deposit': {
        'id': 'first_deposit',
        'title': 'First Fortress Stone',
        'description': 'Make your first DeFi deposit.',
        'icon': 'shield',
        'color': '#4CAF50',
        'threshold': 1,
        'category': 'milestone',
    },
    'yield_earner': {
        'id': 'yield_earner',
        'title': 'Yield Harvester',
        'description': 'Earn your first yield reward.',
        'icon': 'zap',
        'color': '#FF9800',
        'threshold': 1,
        'category': 'milestone',
    },
    'multi_chain': {
        'id': 'multi_chain',
        'title': 'Chain Explorer',
        'description': 'Deposit on 2+ different chains.',
        'icon': 'globe',
        'color': '#2196F3',
        'threshold': 2,
        'category': 'milestone',
    },
    'diamond_hands': {
        'id': 'diamond_hands',
        'title': 'Diamond Hands',
        'description': 'Hold a position for 30+ days.',
        'icon': 'award',
        'color': '#00BCD4',
        'threshold': 30,
        'category': 'mastery',
    },
    'diversified': {
        'id': 'diversified',
        'title': 'Diversified Fortress',
        'description': 'Hold 3+ active positions simultaneously.',
        'icon': 'layers',
        'color': '#9C27B0',
        'threshold': 3,
        'category': 'mastery',
    },
    'yield_master': {
        'id': 'yield_master',
        'title': 'Yield Master',
        'description': 'Earn $100+ total in DeFi rewards.',
        'icon': 'star',
        'color': '#FFD700',
        'threshold': 100,
        'category': 'mastery',
    },
    'protocol_explorer': {
        'id': 'protocol_explorer',
        'title': 'Protocol Explorer',
        'description': 'Use 3+ different protocols.',
        'icon': 'compass',
        'color': '#795548',
        'threshold': 3,
        'category': 'milestone',
    },
    'community_builder': {
        'id': 'community_builder',
        'title': 'Community Builder',
        'description': 'Share a strategy with your tribe.',
        'icon': 'users',
        'color': '#E91E63',
        'threshold': 1,
        'category': 'community',
    },
    'risk_manager': {
        'id': 'risk_manager',
        'title': 'Risk Manager',
        'description': 'Successfully avoid a liquidation (health factor recovered).',
        'icon': 'shield',
        'color': '#607D8B',
        'threshold': 1,
        'category': 'mastery',
    },
    'thousand_club': {
        'id': 'thousand_club',
        'title': 'The $1,000 Club',
        'description': 'Total DeFi deposits exceed $1,000.',
        'icon': 'trending-up',
        'color': '#8BC34A',
        'threshold': 1000,
        'category': 'milestone',
    },
}


# ---------------------------------------------------------------------------
# Lazy model imports
# ---------------------------------------------------------------------------

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
    except Exception as e:
        logger.error(f"Failed to import DeFi models: {e}")
        return None


# ---------------------------------------------------------------------------
# check_achievements
# ---------------------------------------------------------------------------

def check_achievements(user) -> List[dict]:
    """
    Evaluate every achievement definition against the user's DeFi data.

    Returns a list of dicts, one per achievement:
        {
            id, title, description, icon, color,
            earned: bool,
            earned_at: datetime | None,
            progress: float  # 0.0 – 1.0
        }
    """
    models = _get_models()
    if models is None:
        logger.error("Cannot check achievements — models unavailable")
        return []

    UserDeFiPosition = models['UserDeFiPosition']
    DeFiTransaction = models['DeFiTransaction']

    now = timezone.now()
    results: List[dict] = []

    # ---- Pre-fetch user data (guarded) ----
    try:
        positions = UserDeFiPosition.objects.filter(user=user).select_related(
            'pool', 'pool__protocol'
        )
        active_positions = positions.filter(is_active=True)
        transactions = DeFiTransaction.objects.filter(
            user=user, status='confirmed'
        )
    except Exception as e:
        logger.error(f"Error fetching data for achievements (user={user}): {e}")
        return []

    # ---- Derived metrics (computed once) ----
    try:
        deposit_count = transactions.filter(action='deposit').count()
    except Exception:
        deposit_count = 0

    try:
        harvest_count = transactions.filter(action='harvest').count()
    except Exception:
        harvest_count = 0

    try:
        distinct_chains = (
            active_positions.values_list('pool__chain', flat=True)
            .distinct()
        )
        chain_count = len(set(distinct_chains))
    except Exception:
        chain_count = 0

    try:
        active_count = active_positions.count()
    except Exception:
        active_count = 0

    try:
        total_rewards = float(
            active_positions.aggregate(total=Sum('rewards_earned'))['total'] or 0
        )
    except Exception:
        total_rewards = 0.0

    try:
        distinct_protocols = (
            active_positions.values_list('pool__protocol__slug', flat=True)
            .distinct()
        )
        protocol_count = len(set(distinct_protocols))
    except Exception:
        protocol_count = 0

    try:
        total_deposited = float(
            active_positions.aggregate(total=Sum('staked_value_usd'))['total'] or 0
        )
    except Exception:
        total_deposited = 0.0

    # Oldest active position for diamond_hands
    try:
        oldest_position = active_positions.order_by('created_at').first()
        if oldest_position:
            days_held = (now - oldest_position.created_at).days
        else:
            days_held = 0
    except Exception:
        days_held = 0

    # ---- Evaluate each achievement ----

    def _build(achievement: dict, earned: bool, progress: float,
               earned_at=None) -> dict:
        return {
            'id': achievement['id'],
            'title': achievement['title'],
            'description': achievement['description'],
            'icon': achievement['icon'],
            'color': achievement['color'],
            'earned': earned,
            'earned_at': earned_at,
            'progress': min(1.0, max(0.0, progress)),
        }

    # first_deposit
    ach = ACHIEVEMENTS['first_deposit']
    earned = deposit_count >= ach['threshold']
    progress = min(deposit_count / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    earned_at = None
    if earned:
        try:
            first_tx = transactions.filter(action='deposit').order_by('created_at').first()
            earned_at = first_tx.created_at if first_tx else None
        except Exception:
            pass
    results.append(_build(ach, earned, progress, earned_at))

    # yield_earner
    ach = ACHIEVEMENTS['yield_earner']
    earned = harvest_count >= ach['threshold']
    progress = min(harvest_count / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    earned_at = None
    if earned:
        try:
            first_harvest = transactions.filter(action='harvest').order_by('created_at').first()
            earned_at = first_harvest.created_at if first_harvest else None
        except Exception:
            pass
    results.append(_build(ach, earned, progress, earned_at))

    # multi_chain
    ach = ACHIEVEMENTS['multi_chain']
    earned = chain_count >= ach['threshold']
    progress = min(chain_count / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    results.append(_build(ach, earned, progress))

    # diamond_hands
    ach = ACHIEVEMENTS['diamond_hands']
    earned = days_held >= ach['threshold']
    progress = min(days_held / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    earned_at = None
    if earned and oldest_position:
        earned_at = oldest_position.created_at + timedelta(days=ach['threshold'])
    results.append(_build(ach, earned, progress, earned_at))

    # diversified
    ach = ACHIEVEMENTS['diversified']
    earned = active_count >= ach['threshold']
    progress = min(active_count / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    results.append(_build(ach, earned, progress))

    # yield_master
    ach = ACHIEVEMENTS['yield_master']
    earned = total_rewards >= ach['threshold']
    progress = min(total_rewards / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    results.append(_build(ach, earned, progress))

    # protocol_explorer
    ach = ACHIEVEMENTS['protocol_explorer']
    earned = protocol_count >= ach['threshold']
    progress = min(protocol_count / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    results.append(_build(ach, earned, progress))

    # community_builder — tracked separately (placeholder progress)
    ach = ACHIEVEMENTS['community_builder']
    # Community shares are tracked outside DeFi models; default to not earned.
    results.append(_build(ach, False, 0.0))

    # risk_manager — tracked separately via alert service
    ach = ACHIEVEMENTS['risk_manager']
    # Liquidation avoidance events are tracked by the alert pipeline.
    results.append(_build(ach, False, 0.0))

    # thousand_club
    ach = ACHIEVEMENTS['thousand_club']
    earned = total_deposited >= ach['threshold']
    progress = min(total_deposited / ach['threshold'], 1.0) if ach['threshold'] else 0.0
    results.append(_build(ach, earned, progress))

    return results


# ---------------------------------------------------------------------------
# get_portfolio_analytics
# ---------------------------------------------------------------------------

def get_portfolio_analytics(user) -> dict:
    """
    Calculate portfolio-level analytics for the user's active DeFi positions.

    Returns:
        {
            total_deposited_usd, total_rewards_usd, total_positions,
            active_chains, active_protocols,
            realized_apy, sharpe_ratio, max_drawdown_estimate,
            portfolio_diversity_score,
        }
    """
    models = _get_models()
    if models is None:
        logger.error("Cannot compute portfolio analytics — models unavailable")
        return _empty_analytics()

    UserDeFiPosition = models['UserDeFiPosition']
    YieldSnapshot = models['YieldSnapshot']

    try:
        positions = UserDeFiPosition.objects.filter(
            user=user, is_active=True,
        ).select_related('pool', 'pool__protocol')
    except Exception as e:
        logger.error(f"Error fetching positions for analytics (user={user}): {e}")
        return _empty_analytics()

    if not positions.exists():
        return _empty_analytics()

    # ---- Basic aggregates ----
    total_deposited_usd = 0.0
    total_rewards_usd = 0.0
    weighted_apy_sum = 0.0
    weight_sum = 0.0
    chains = set()
    protocols = set()
    pool_types = set()
    max_risk_score = 0.0
    risk_scores: List[float] = []

    for pos in positions:
        staked = float(pos.staked_value_usd)
        rewards = float(pos.rewards_earned)
        total_deposited_usd += staked
        total_rewards_usd += rewards

        chains.add(pos.pool.chain)
        protocols.add(pos.pool.protocol.slug)
        pool_types.add(pos.pool.pool_type)

        apy = pos.realized_apy if pos.realized_apy is not None else 0.0
        weighted_apy_sum += apy * staked
        weight_sum += staked

        # Fetch latest risk score for the pool
        try:
            latest_snap = YieldSnapshot.objects.filter(
                pool=pos.pool,
            ).order_by('-timestamp').first()
            if latest_snap:
                rs = latest_snap.risk_score
            else:
                rs = pos.pool.protocol.risk_score
        except Exception:
            rs = 0.5

        risk_scores.append(rs)
        if rs > max_risk_score:
            max_risk_score = rs

    total_positions = positions.count()
    active_chains = sorted(chains)
    active_protocols = sorted(protocols)

    # ---- Realized APY (weighted average) ----
    realized_apy = (weighted_apy_sum / weight_sum) if weight_sum > 0 else 0.0

    # ---- Sharpe Ratio approximation ----
    risk_free_rate = 0.05  # 5%
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5
    # Use average risk score as a proxy for volatility (scaled to typical DeFi range)
    volatility_estimate = max(avg_risk * 0.5, 0.01)  # floor at 1% to avoid div/0
    sharpe_ratio = (realized_apy / 100.0 - risk_free_rate) / volatility_estimate

    # ---- Max drawdown estimate ----
    max_drawdown_estimate = round(max_risk_score * 100, 2)

    # ---- Portfolio diversity score (0–100) ----
    # Scoring: chains (max 30), protocols (max 40), pool types (max 30)
    chain_score = min(len(chains) / 4, 1.0) * 30          # 4 chains = full marks
    protocol_score = min(len(protocols) / 5, 1.0) * 40    # 5 protocols = full marks
    type_score = min(len(pool_types) / 3, 1.0) * 30       # 3 pool types = full marks
    portfolio_diversity_score = round(chain_score + protocol_score + type_score, 1)

    return {
        'total_deposited_usd': round(total_deposited_usd, 2),
        'total_rewards_usd': round(total_rewards_usd, 2),
        'total_positions': total_positions,
        'active_chains': active_chains,
        'active_protocols': active_protocols,
        'realized_apy': round(realized_apy, 2),
        'sharpe_ratio': round(sharpe_ratio, 4),
        'max_drawdown_estimate': max_drawdown_estimate,
        'portfolio_diversity_score': portfolio_diversity_score,
    }


def _empty_analytics() -> dict:
    """Return an analytics dict with zero / empty defaults."""
    return {
        'total_deposited_usd': 0.0,
        'total_rewards_usd': 0.0,
        'total_positions': 0,
        'active_chains': [],
        'active_protocols': [],
        'realized_apy': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown_estimate': 0.0,
        'portfolio_diversity_score': 0.0,
    }


# ---------------------------------------------------------------------------
# get_ghost_whisper_recommendation  (Ghost Whisper DeFi)
# ---------------------------------------------------------------------------

def get_ghost_whisper_recommendation(user) -> dict:
    """
    Ghost Whisper DeFi — AI-driven, personalised recommendation engine.

    Analyses the user's current positions, risk exposure, and available
    market yields to return a single actionable recommendation.

    Returns:
        {
            message: str,
            action: 'deposit' | 'rotate' | 'harvest' | 'diversify' | 'hold',
            confidence: float,   # 0.0 – 1.0
            reasoning: str,
            suggested_pool: dict | None,
        }
    """
    models = _get_models()
    if models is None:
        logger.error("Cannot generate Ghost Whisper — models unavailable")
        return _hold_recommendation("System is initialising. Check back shortly.")

    UserDeFiPosition = models['UserDeFiPosition']
    YieldSnapshot = models['YieldSnapshot']

    # ---- Fetch cached yields (optional dependency) ----
    available_yields: List[dict] = []
    try:
        from .defi_data_service import get_cached_yields
        available_yields = get_cached_yields(chain='all', limit=50)
    except Exception as e:
        logger.warning(f"Could not load cached yields for Ghost Whisper: {e}")

    # ---- Fetch user positions ----
    try:
        positions = UserDeFiPosition.objects.filter(
            user=user, is_active=True,
        ).select_related('pool', 'pool__protocol')
    except Exception as e:
        logger.error(f"Error fetching positions for Ghost Whisper (user={user}): {e}")
        return _hold_recommendation("Unable to read your positions right now.")

    position_list = list(positions)

    # ---- Rule 1: No positions → recommend first deposit ----
    if not position_list:
        suggested = _find_lowest_risk_pool(available_yields)
        msg = (
            "Welcome to DeFi! Start building your fortress with a low-risk "
            "deposit. We found a safe pool to get you started."
        )
        return {
            'message': msg,
            'action': 'deposit',
            'confidence': 0.85,
            'reasoning': (
                'New user with no active positions. Recommending the lowest-risk '
                'pool available to begin the wealth-building journey safely.'
            ),
            'suggested_pool': suggested,
        }

    # ---- Rule 2: All positions on one chain → diversify ----
    chains_in_use = set(pos.pool.chain for pos in position_list)
    if len(chains_in_use) == 1:
        current_chain = next(iter(chains_in_use))
        suggested = _find_pool_on_different_chain(available_yields, current_chain)
        msg = (
            f"All your positions are on {current_chain.title()}. "
            "Spreading across chains reduces risk and unlocks new yield."
        )
        return {
            'message': msg,
            'action': 'diversify',
            'confidence': 0.75,
            'reasoning': (
                f'User has {len(position_list)} position(s) all on {current_chain}. '
                'Cross-chain diversification reduces smart-contract and bridge risk.'
            ),
            'suggested_pool': suggested,
        }

    # ---- Rule 3: Unharvested rewards > $10 → harvest ----
    for pos in position_list:
        rewards = float(pos.rewards_earned)
        if rewards > 10.0:
            msg = (
                f"You have ${rewards:.2f} in unclaimed rewards on your "
                f"{pos.pool.symbol} position. Time to harvest!"
            )
            return {
                'message': msg,
                'action': 'harvest',
                'confidence': 0.90,
                'reasoning': (
                    f'Position {pos.pool.symbol} on {pos.pool.protocol.name} '
                    f'has ${rewards:.2f} in unharvested rewards exceeding the '
                    f'$10 threshold.'
                ),
                'suggested_pool': None,
            }

    # ---- Rule 4: Better pool available (20%+ APY improvement) → rotate ----
    rotation = _find_rotation_candidate(position_list, available_yields)
    if rotation:
        current_pool, target_pool, improvement = rotation
        msg = (
            f"We found a pool with {improvement:.0f}% higher APY than your "
            f"{current_pool.pool.symbol} position. Consider rotating for better yield."
        )
        return {
            'message': msg,
            'action': 'rotate',
            'confidence': 0.70,
            'reasoning': (
                f'{target_pool["symbol"]} on {target_pool["protocol"]} offers '
                f'{target_pool["apy"]:.1f}% APY vs your current '
                f'{current_pool.realized_apy or 0:.1f}%. '
                f'That is a {improvement:.0f}% relative improvement.'
            ),
            'suggested_pool': target_pool,
        }

    # ---- Default: fortress is strong ----
    return _hold_recommendation("Your fortress is strong. Keep earning yield!")


# ---------------------------------------------------------------------------
# Ghost Whisper helpers
# ---------------------------------------------------------------------------

def _hold_recommendation(message: str) -> dict:
    """Return a neutral 'hold' recommendation."""
    return {
        'message': message,
        'action': 'hold',
        'confidence': 0.60,
        'reasoning': 'No immediate action needed. Positions are healthy and yields are stable.',
        'suggested_pool': None,
    }


def _find_lowest_risk_pool(yields: List[dict]) -> Optional[dict]:
    """Pick the pool with the lowest risk score from the available yields."""
    if not yields:
        return None
    try:
        sorted_pools = sorted(yields, key=lambda y: y.get('risk', 1.0))
        return sorted_pools[0] if sorted_pools else None
    except Exception:
        return None


def _find_pool_on_different_chain(
    yields: List[dict], current_chain: str
) -> Optional[dict]:
    """Find the best pool on a chain different from *current_chain*."""
    if not yields:
        return None
    try:
        candidates = [
            y for y in yields
            if y.get('chain', '') != current_chain
        ]
        if not candidates:
            return None
        # Prefer low risk, then high APY
        candidates.sort(key=lambda y: (y.get('risk', 1.0), -y.get('apy', 0)))
        return candidates[0]
    except Exception:
        return None


def _find_rotation_candidate(
    positions, yields: List[dict]
) -> Optional[tuple]:
    """
    Check whether any available pool offers 20%+ APY improvement over the
    user's current positions (with similar or lower risk).

    Returns (current_position, target_pool_dict, relative_improvement_pct) or None.
    """
    if not yields:
        return None

    try:
        for pos in positions:
            current_apy = pos.realized_apy if pos.realized_apy is not None else 0.0
            if current_apy <= 0:
                continue

            current_risk = pos.pool.protocol.risk_score
            current_chain = pos.pool.chain
            current_protocol = pos.pool.protocol.slug

            for pool in yields:
                pool_apy = pool.get('apy', 0)
                pool_risk = pool.get('risk', 1.0)

                # Skip same pool / same protocol-chain combo
                if (pool.get('chain') == current_chain
                        and pool.get('protocol', '').lower() == current_protocol):
                    continue

                # Risk guard: don't suggest meaningfully riskier pools
                if pool_risk > current_risk + 0.20:
                    continue

                improvement = (pool_apy - current_apy) / current_apy
                if improvement >= 0.20:
                    return (pos, pool, improvement * 100)
    except Exception as e:
        logger.warning(f"Error searching rotation candidate: {e}")

    return None
