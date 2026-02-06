"""
Bandit Service - Adaptive Discounted Thompson Sampling (ADTS) for strategy allocation.

Extends standard Thompson Sampling with adaptive discount rates that respond
to regime changes. When market regimes shift frequently, the system forgets
old evidence faster. When regimes are stable, it accumulates evidence slowly.
"""
import math
import logging
from datetime import timedelta
from typing import Dict, Optional, List

import numpy as np
from django.conf import settings
from django.utils import timezone

from .bandit_models import BanditArm

logger = logging.getLogger(__name__)

# Default strategies to seed if no arms exist
DEFAULT_STRATEGIES = ['breakout', 'mean_reversion', 'momentum', 'etf_rotation']

# ADTS parameters
ADTS_BASE_RATE = 0.995      # Very slow decay in stable markets
ADTS_MIN_RATE = 0.90        # Aggressive forgetting during regime turbulence
ADTS_HALFLIFE_DAYS = 7.0    # Days for discount to recover from min to base
ADTS_REWARD_WINDOW = 100    # Sliding window size for reward history


class BanditService:
    """
    Adaptive Discounted Thompson Sampling for strategy allocation.

    When ENABLE_ADAPTIVE_BANDIT is True, uses per-arm adaptive discount rates
    driven by regime change frequency. Otherwise falls back to standard decay.
    """

    def _ensure_arms_exist(self):
        """Seed default bandit arms if none exist."""
        if BanditArm.objects.count() == 0:
            for slug in DEFAULT_STRATEGIES:
                BanditArm.objects.get_or_create(
                    strategy_slug=slug,
                    defaults={'alpha': 1.0, 'beta_param': 1.0, 'current_weight': 0.25}
                )
            logger.info(f"Seeded {len(DEFAULT_STRATEGIES)} default bandit arms")

    def select_strategy(self, context: Optional[Dict] = None) -> Dict:
        """
        Sample from each arm's Beta posterior and return the strategy
        with the highest sampled value.
        """
        self._ensure_arms_exist()
        arms = BanditArm.objects.filter(enabled=True)

        if not arms.exists():
            return {'strategy': 'momentum', 'confidence': 0.5, 'source': 'fallback'}

        regime = context.get('regime') if context else None
        best_sample = -1.0
        best_arm = None

        for arm in arms:
            alpha = arm.alpha
            beta = arm.beta_param

            # Use context-specific posteriors if regime provided
            if regime and regime in arm.context_alphas and regime in arm.context_betas:
                alpha = arm.context_alphas[regime]
                beta = arm.context_betas[regime]

            sample = np.random.beta(max(alpha, 0.01), max(beta, 0.01))

            if sample > best_sample:
                best_sample = sample
                best_arm = arm

        return {
            'strategy': best_arm.strategy_slug,
            'confidence': round(best_sample, 4),
            'expected_win_rate': round(best_arm.expected_win_rate, 4),
            'alpha': best_arm.alpha,
            'beta': best_arm.beta_param,
            'total_pulls': best_arm.total_pulls,
            'discount_rate': best_arm.discount_rate,
            'source': 'adaptive_thompson_sampling',
        }

    def update_reward(
        self,
        strategy_slug: str,
        reward: float,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Update arm's posterior with a new reward.
        Also records to reward_history sliding window for ADTS.
        """
        self._ensure_arms_exist()

        try:
            arm, created = BanditArm.objects.get_or_create(
                strategy_slug=strategy_slug,
                defaults={'alpha': 1.0, 'beta_param': 1.0}
            )

            # Update global posterior
            arm.alpha += reward
            arm.beta_param += (1.0 - reward)
            arm.total_pulls += 1
            arm.total_rewards += reward

            # Update context-specific posterior if regime provided
            regime = context.get('regime') if context else None
            if regime:
                ctx_alphas = arm.context_alphas or {}
                ctx_betas = arm.context_betas or {}

                ctx_alphas[regime] = ctx_alphas.get(regime, 1.0) + reward
                ctx_betas[regime] = ctx_betas.get(regime, 1.0) + (1.0 - reward)

                arm.context_alphas = ctx_alphas
                arm.context_betas = ctx_betas

            # ADTS: append to reward history sliding window
            history = arm.reward_history or []
            history.append({
                'reward': reward,
                'timestamp': timezone.now().isoformat(),
                'regime': regime or 'UNKNOWN',
            })
            arm.reward_history = history[-ADTS_REWARD_WINDOW:]

            arm.save()

            logger.info(
                f"Bandit update: {strategy_slug} reward={reward}, "
                f"alpha={arm.alpha:.1f}, beta={arm.beta_param:.1f}, "
                f"win_rate={arm.expected_win_rate:.2%}, discount={arm.discount_rate:.4f}"
            )

            return {
                'strategy': strategy_slug,
                'alpha': arm.alpha,
                'beta': arm.beta_param,
                'win_rate': arm.expected_win_rate,
                'total_pulls': arm.total_pulls,
            }
        except Exception as e:
            logger.error(f"Error updating bandit reward for {strategy_slug}: {e}", exc_info=True)
            return {'strategy': strategy_slug, 'error': str(e)}

    def get_allocation_weights(self, n_samples: int = 10000) -> Dict[str, float]:
        """
        Run Monte Carlo Thompson Sampling to compute allocation weights.
        """
        self._ensure_arms_exist()
        arms = list(BanditArm.objects.filter(enabled=True))

        if not arms:
            return {}

        win_counts = {arm.strategy_slug: 0 for arm in arms}

        for _ in range(n_samples):
            best_sample = -1.0
            best_slug = arms[0].strategy_slug

            for arm in arms:
                sample = np.random.beta(max(arm.alpha, 0.01), max(arm.beta_param, 0.01))
                if sample > best_sample:
                    best_sample = sample
                    best_slug = arm.strategy_slug

            win_counts[best_slug] += 1

        weights = {slug: count / n_samples for slug, count in win_counts.items()}

        for arm in arms:
            arm.current_weight = weights.get(arm.strategy_slug, 0.0)
            arm.save(update_fields=['current_weight'])

        logger.info(f"Bandit allocation weights: {weights}")
        return weights

    def decay_priors(self, decay_factor: float = 0.99):
        """
        Decay old evidence to adapt to regime changes.

        When ENABLE_ADAPTIVE_BANDIT is True, computes per-arm adaptive
        discount rates based on recent regime change frequency.
        Otherwise uses the fixed decay_factor.
        """
        use_adaptive = getattr(settings, 'ENABLE_ADAPTIVE_BANDIT', False)

        if use_adaptive:
            self._compute_adaptive_discounts()

        arms = BanditArm.objects.filter(enabled=True)
        for arm in arms:
            rate = arm.discount_rate if use_adaptive else decay_factor

            arm.alpha = 1.0 + (arm.alpha - 1.0) * rate
            arm.beta_param = 1.0 + (arm.beta_param - 1.0) * rate

            if arm.context_alphas:
                arm.context_alphas = {
                    k: 1.0 + (v - 1.0) * rate
                    for k, v in arm.context_alphas.items()
                }
            if arm.context_betas:
                arm.context_betas = {
                    k: 1.0 + (v - 1.0) * rate
                    for k, v in arm.context_betas.items()
                }

            arm.save()

        logger.info(
            f"Decayed priors for {arms.count()} bandit arms "
            f"(mode={'adaptive' if use_adaptive else 'fixed'}, factor={decay_factor})"
        )

    def _compute_adaptive_discounts(self):
        """
        Compute per-arm adaptive discount rates based on regime change frequency.

        Formula:
            regime_recency = exp(-days_since_last_shift / halflife)
            discount = base_rate - (base_rate - min_rate) * regime_recency

        More recent regime shifts → lower discount → faster forgetting.
        """
        try:
            from .regime_change_models import RegimeChangeEvent

            now = timezone.now()
            recent_cutoff = now - timedelta(days=14)

            # Get recent regime changes
            recent_changes = RegimeChangeEvent.objects.filter(
                detected_at__gte=recent_cutoff
            ).order_by('-detected_at')

            if not recent_changes.exists():
                # No regime changes → use base rate (slow decay)
                BanditArm.objects.filter(enabled=True).update(
                    discount_rate=ADTS_BASE_RATE
                )
                return

            last_change = recent_changes.first()
            days_since_shift = (now - last_change.detected_at).total_seconds() / 86400.0

            # Count regime transitions in last 7 days
            week_cutoff = now - timedelta(days=7)
            transitions_7d = RegimeChangeEvent.objects.filter(
                detected_at__gte=week_cutoff
            ).count()

            # Regime recency factor: exponential decay from last shift
            regime_recency = math.exp(-days_since_shift / ADTS_HALFLIFE_DAYS)

            # Boost recency if many transitions (turbulent market)
            if transitions_7d > 2:
                regime_recency = min(1.0, regime_recency * 1.5)

            # Compute adaptive discount
            discount = ADTS_BASE_RATE - (ADTS_BASE_RATE - ADTS_MIN_RATE) * regime_recency

            # Apply to all arms
            arms = BanditArm.objects.filter(enabled=True)
            for arm in arms:
                arm.discount_rate = round(discount, 4)
                arm.regime_change_count = transitions_7d
                arm.save(update_fields=['discount_rate', 'regime_change_count'])

            logger.info(
                f"ADTS discount computed: rate={discount:.4f}, "
                f"days_since_shift={days_since_shift:.1f}, "
                f"transitions_7d={transitions_7d}, recency={regime_recency:.3f}"
            )

        except Exception as e:
            logger.error(f"Error computing adaptive discounts: {e}", exc_info=True)

    def get_all_arms_status(self) -> List[Dict]:
        """Return status of all arms for dashboard display."""
        self._ensure_arms_exist()
        arms = BanditArm.objects.all().order_by('-current_weight')
        return [
            {
                'strategy': arm.strategy_slug,
                'alpha': arm.alpha,
                'beta': arm.beta_param,
                'win_rate': arm.expected_win_rate,
                'weight': arm.current_weight,
                'total_pulls': arm.total_pulls,
                'enabled': arm.enabled,
                'discount_rate': arm.discount_rate,
                'regime_change_count': arm.regime_change_count,
            }
            for arm in arms
        ]
