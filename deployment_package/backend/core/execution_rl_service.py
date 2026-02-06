"""
Execution RL Service - Learns optimal execution strategies from UserFill data.

Uses tabular Q-learning (effectively a contextual bandit since execution is
single-step) to learn which order type performs best in each market condition.

State space: 8 discretized features (spread, volume, time, volatility, etc.)
Action space: 4 discrete actions (MARKET_IMMEDIATE, LIMIT_TIGHT, LIMIT_LOOSE, WAIT_5MIN)
Reward: -slippage_bps + quality_bonus
"""
import logging
from decimal import Decimal
from typing import Dict, Optional, Any, List
from collections import defaultdict

import numpy as np
from django.utils import timezone

logger = logging.getLogger(__name__)

# Actions
ACTIONS = ['MARKET_IMMEDIATE', 'LIMIT_TIGHT', 'LIMIT_LOOSE', 'WAIT_5MIN']

# Q-learning hyperparameters
LEARNING_RATE = 0.1
EPSILON = 0.1           # Exploration rate
MIN_EXPERIENCES = 200   # Minimum experiences before training
REWARD_LOWER = -50.0
REWARD_UPPER = 10.0

# Discretization bins
SPREAD_BINS = [0, 5, 15, 50]          # bps: tight, normal, wide, very wide
VOLUME_BINS = [0, 0.8, 1.5, 3.0]     # ratio: low, normal, high, very high
TIME_BUCKETS = {                       # Hour ranges
    'open': (9, 10),
    'mid_morning': (10, 12),
    'midday': (12, 14),
    'afternoon': (14, 15),
    'close': (15, 16),
}
SLIPPAGE_BINS = [0, 5, 15, 50]        # bps: excellent, good, poor, terrible
SIZE_BINS = [0, 5000, 25000]          # dollars: small, medium, large


class ExecutionRLService:
    """Q-learning based execution optimizer."""

    def __init__(self):
        self._policy = None

    def _get_active_policy(self):
        """Load the active policy from DB."""
        if self._policy is not None:
            return self._policy

        from .execution_rl_models import ExecutionPolicy
        policy = ExecutionPolicy.objects.filter(is_active=True).first()
        if policy:
            self._policy = policy.policy_data or {}
        else:
            self._policy = {}
        return self._policy

    def get_recommendation(self, state_features: Dict) -> Dict[str, Any]:
        """
        Get execution recommendation for current market conditions.
        Uses epsilon-greedy policy from Q-table.

        Args:
            state_features: Dict with spread_bps, volume_ratio, etc.

        Returns:
            Dict with action, confidence, and q_values
        """
        q_table = self._get_active_policy()
        state_key = self._discretize_state(state_features)

        if not q_table or state_key not in q_table:
            # No data for this state — default to LIMIT_TIGHT
            return {
                'action': 'LIMIT_TIGHT',
                'confidence': 0.5,
                'q_values': {},
                'source': 'default',
            }

        q_values = q_table[state_key]
        best_action = max(q_values, key=q_values.get)
        best_q = q_values[best_action]

        # Confidence based on how much better best is vs others
        q_range = max(q_values.values()) - min(q_values.values())
        confidence = min(1.0, 0.5 + q_range / 20.0)  # Scale by q-value spread

        return {
            'action': best_action,
            'confidence': round(confidence, 3),
            'q_values': q_values,
            'source': 'q_table',
        }

    def build_state_from_features(self, features: Dict, symbol: str = None) -> Dict:
        """
        Build state features dict from signal features for recommendation.
        Used during scoring to get execution advice.
        """
        hour = timezone.now().hour

        state = {
            'spread_bps': features.get('spread_bps', features.get('spreadBps', 5.0)),
            'volume_ratio': features.get('volume_ratio', features.get('volumeRatio', 1.0)),
            'hour': hour,
            'momentum': abs(features.get('momentum_15m', features.get('momentum15m', 0.0))),
        }

        # Add symbol-level execution stats if available
        if symbol:
            try:
                from .signal_performance_models import SymbolExecutionProfile
                profile = SymbolExecutionProfile.objects.filter(symbol=symbol.upper()).first()
                if profile:
                    state['recent_slippage_avg'] = float(profile.avg_slippage_bps)
                    state['symbol_liquidity'] = 2 if profile.fill_count > 50 else (1 if profile.fill_count > 10 else 0)
                else:
                    state['recent_slippage_avg'] = 5.0
                    state['symbol_liquidity'] = 1
            except Exception:
                state['recent_slippage_avg'] = 5.0
                state['symbol_liquidity'] = 1
        else:
            state['recent_slippage_avg'] = 5.0
            state['symbol_liquidity'] = 1

        return state

    def record_experience(self, user_fill) -> Optional[Dict]:
        """
        Record an execution experience from a completed UserFill.
        Extracts state, infers action, computes reward.

        Args:
            user_fill: UserFill model instance
        """
        from .execution_rl_models import ExecutionExperience

        try:
            # Extract state features from the fill context
            state = self._extract_state_from_fill(user_fill)

            # Infer action from fill characteristics
            action = self._infer_action_from_fill(user_fill)

            # Compute reward: negative slippage + quality bonus
            slippage_bps = float(user_fill.slippage_bps or 0)
            quality_score = float(user_fill.execution_quality_score or 5.0)
            quality_bonus = 2.0 if quality_score >= 8.0 else 0.0
            reward = max(REWARD_LOWER, min(REWARD_UPPER, -slippage_bps + quality_bonus))

            experience = ExecutionExperience.objects.create(
                user_fill=user_fill,
                state_features=state,
                action_taken=action,
                reward=reward,
            )

            logger.debug(
                f"RL experience recorded: state={self._discretize_state(state)}, "
                f"action={action}, reward={reward:.1f}"
            )

            return {
                'state': state,
                'action': action,
                'reward': reward,
                'experience_id': experience.id,
            }
        except Exception as e:
            logger.debug(f"Could not record RL experience: {e}")
            return None

    def train_policy(self, min_experiences: int = MIN_EXPERIENCES) -> Dict[str, Any]:
        """
        Train Q-table from accumulated ExecutionExperience records.
        Uses batch Q-learning updates (single-step, so effectively contextual bandit).
        """
        from .execution_rl_models import ExecutionExperience, ExecutionPolicy

        experiences = ExecutionExperience.objects.all()
        total = experiences.count()

        if total < min_experiences:
            logger.info(f"Not enough experiences for RL training: {total}/{min_experiences}")
            return {'error': f'Need {min_experiences} experiences, have {total}'}

        # Build Q-table from experiences
        q_table = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
        state_action_counts = defaultdict(lambda: defaultdict(int))

        for exp in experiences.iterator():
            state_key = self._discretize_state(exp.state_features)
            action = exp.action_taken
            reward = exp.reward

            # Q-learning update (single-step, no next state)
            old_q = q_table[state_key].get(action, 0.0)
            q_table[state_key][action] = old_q + LEARNING_RATE * (reward - old_q)
            state_action_counts[state_key][action] += 1

        # Convert to serializable dict
        q_dict = {k: dict(v) for k, v in q_table.items()}

        # Compute average reward
        avg_reward = sum(e.reward for e in experiences.iterator()) / total

        # Deactivate old policies
        ExecutionPolicy.objects.filter(is_active=True).update(is_active=False)

        # Create new active policy
        version = ExecutionPolicy.objects.count() + 1
        policy = ExecutionPolicy.objects.create(
            version=version,
            policy_type='q_table',
            policy_data=q_dict,
            is_active=True,
            train_episodes=total,
            avg_reward=avg_reward,
        )

        # Reset cached policy
        self._policy = q_dict

        logger.info(
            f"Execution RL policy trained: v{version}, "
            f"{len(q_dict)} states, {total} experiences, avg_reward={avg_reward:.2f}"
        )

        return {
            'version': version,
            'states': len(q_dict),
            'experiences': total,
            'avg_reward': avg_reward,
            'policy_id': str(policy.id),
        }

    def get_policy_stats(self) -> Dict[str, Any]:
        """Return summary of current Q-table for dashboard."""
        q_table = self._get_active_policy()
        if not q_table:
            return {'states': 0, 'message': 'No policy trained yet'}

        # Find best action per state
        best_actions = {}
        for state_key, q_values in q_table.items():
            best = max(q_values, key=q_values.get)
            best_actions[best] = best_actions.get(best, 0) + 1

        return {
            'states': len(q_table),
            'action_distribution': best_actions,
            'total_q_entries': sum(len(v) for v in q_table.values()),
        }

    def _discretize_state(self, state: Dict) -> str:
        """Convert continuous state features to a discrete state key."""
        spread = state.get('spread_bps', 5.0)
        volume = state.get('volume_ratio', 1.0)
        hour = state.get('hour', 12)
        slippage = state.get('recent_slippage_avg', 5.0)
        momentum = state.get('momentum', 0.0)
        liquidity = state.get('symbol_liquidity', 1)

        spread_bin = self._bin_value(spread, SPREAD_BINS)
        volume_bin = self._bin_value(volume, VOLUME_BINS)
        time_bin = self._get_time_bucket(hour)
        slippage_bin = self._bin_value(slippage, SLIPPAGE_BINS)
        momentum_bin = 0 if momentum < 0.01 else (1 if momentum < 0.03 else 2)

        return f"s{spread_bin}_v{volume_bin}_t{time_bin}_sl{slippage_bin}_m{momentum_bin}_l{liquidity}"

    def _bin_value(self, value: float, bins: List[float]) -> int:
        """Discretize a value into bin index."""
        for i, threshold in enumerate(bins):
            if value <= threshold:
                return i
        return len(bins)

    def _get_time_bucket(self, hour: int) -> int:
        """Map hour to time bucket index."""
        if hour < 10:
            return 0  # open
        elif hour < 12:
            return 1  # mid-morning
        elif hour < 14:
            return 2  # midday
        elif hour < 15:
            return 3  # afternoon
        else:
            return 4  # close

    def _extract_state_from_fill(self, fill) -> Dict:
        """Extract state features from a UserFill for experience recording."""
        signal = fill.signal
        features = {}

        if signal and signal.features:
            feat = signal.features if isinstance(signal.features, dict) else {}
            features['spread_bps'] = float(feat.get('spreadBps', feat.get('spread_bps', 5.0)))
            features['volume_ratio'] = float(feat.get('volumeRatio', feat.get('volume_ratio', 1.0)))
            features['momentum'] = abs(float(feat.get('momentum15m', feat.get('momentum_15m', 0.0))))
        else:
            features['spread_bps'] = 5.0
            features['volume_ratio'] = 1.0
            features['momentum'] = 0.0

        features['hour'] = fill.entry_time.hour if fill.entry_time else 12
        features['recent_slippage_avg'] = float(fill.slippage_bps or 5.0)

        # Estimate order size bucket
        entry = float(fill.entry_price or 100)
        shares = fill.shares or 100
        order_value = entry * shares
        features['order_size_bucket'] = 0 if order_value < 5000 else (1 if order_value < 25000 else 2)
        features['symbol_liquidity'] = 1  # Default

        return features

    def _infer_action_from_fill(self, fill) -> str:
        """
        Infer which action was taken based on fill characteristics.
        Since we don't know the actual order type, we infer from slippage patterns.
        """
        slippage = float(fill.slippage_bps or 0)
        quality = float(fill.execution_quality_score or 5.0)

        # Heuristic mapping based on execution characteristics
        if quality >= 8.0 and slippage < 3:
            return 'LIMIT_TIGHT'    # Very good execution → likely limit order
        elif quality >= 6.0 and slippage < 10:
            return 'LIMIT_LOOSE'    # Good execution → probably limit
        elif slippage > 20:
            return 'MARKET_IMMEDIATE'  # High slippage → market order
        elif fill.entry_time and fill.signal:
            # Check if there was a delay between signal and fill
            signal_time = fill.signal.generated_at
            fill_time = fill.entry_time
            if signal_time and fill_time:
                delay = (fill_time - signal_time).total_seconds()
                if delay > 300:
                    return 'WAIT_5MIN'
        return 'MARKET_IMMEDIATE'
