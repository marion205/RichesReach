"""
Regime Learning Service - Learns optimal regime detection thresholds
from historical performance data using Optuna.

Objective: Find thresholds that maximize the correlation between
regime classifications and subsequent strategy performance.
"""
import logging
from typing import Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    import optuna
    import numpy as np
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available for regime learning")


# Search space for regime thresholds
THRESHOLD_SPACE = {
    'rv_spike_threshold': {'low': 0.8, 'high': 2.0},
    'price_crash_threshold': {'low': -0.06, 'high': -0.01},
    'trend_strength_threshold': {'low': 0.01, 'high': 0.05},
    'iv_expansion_threshold': {'low': 0.9, 'high': 1.5},
    'iv_rank_high': {'low': 0.5, 'high': 0.9},
    'iv_rank_low': {'low': 0.1, 'high': 0.4},
    'price_flat_threshold': {'low': 0.005, 'high': 0.03},
}


class RegimeLearningService:
    """Learns optimal regime detection thresholds from historical performance."""

    def optimize_thresholds(self, n_trials: int = 100, timeout_seconds: int = 300) -> Dict[str, Any]:
        """
        Use Optuna to find thresholds that maximize regime-strategy alignment.

        For each historical day, classify regime with candidate thresholds,
        then check if the recommended strategy type actually performed well.
        """
        if not OPTUNA_AVAILABLE:
            return {'success': False, 'error': 'Optuna not installed'}

        # Load historical data for evaluation
        historical_data = self._load_historical_regime_data()
        if not historical_data or len(historical_data) < 30:
            return {
                'success': False,
                'error': f'Insufficient historical data ({len(historical_data) if historical_data else 0} records, need 30+)',
            }

        def objective(trial):
            thresholds = {}
            for name, spec in THRESHOLD_SPACE.items():
                thresholds[name] = trial.suggest_float(name, spec['low'], spec['high'])

            # Evaluate thresholds against historical data
            score = self._evaluate_thresholds(thresholds, historical_data)
            return score

        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=n_trials, timeout=timeout_seconds)

        logger.info(
            f"Regime threshold optimization complete: "
            f"best_score={study.best_value:.4f}, thresholds={study.best_params}"
        )

        return {
            'success': True,
            'best_thresholds': study.best_params,
            'best_score': study.best_value,
            'n_trials': len(study.trials),
        }

    def _load_historical_regime_data(self):
        """
        Load historical data needed for regime evaluation.
        Returns list of dicts with market indicators and strategy performance.
        """
        try:
            from .signal_performance_models import SignalPerformance
            from datetime import timedelta

            cutoff = timezone.now() - timedelta(days=180)

            # Get historical signal performances with outcomes
            perfs = SignalPerformance.objects.filter(
                signal__isnull=False,
                horizon='EOD',
                evaluated_at__gte=cutoff,
                outcome__in=['WIN', 'LOSS', 'BREAKEVEN'],
            ).select_related('signal').order_by('evaluated_at')

            if not perfs.exists():
                return []

            records = []
            for perf in perfs[:500]:  # Cap for performance
                signal = perf.signal
                features = signal.features or {}
                records.append({
                    'pnl_percent': float(perf.pnl_percent or 0),
                    'outcome': perf.outcome,
                    'mode': signal.mode,
                    # Market indicators from signal features
                    'momentum': features.get('momentum_15m', 0),
                    'volume_ratio': features.get('volume_ratio', 1.0),
                    'rsi': features.get('rsi_14', 50),
                    'vwap_dist': features.get('vwap_dist_pct', 0),
                    'is_trend': features.get('is_trend_regime', 0),
                    'is_range': features.get('is_range_regime', 0),
                    'is_chop': features.get('is_high_vol_chop', 0),
                    'bb_position': features.get('bb_position', 0.5),
                    'trend_strength': features.get('trend_strength', 0),
                })

            return records
        except Exception as e:
            logger.error(f"Error loading historical regime data: {e}", exc_info=True)
            return []

    def _evaluate_thresholds(self, thresholds: Dict, historical_data: list) -> float:
        """
        Score a set of thresholds by checking how well they predict
        which signals will be profitable.

        Higher score = better regime classification → better strategy selection.
        """
        if not historical_data:
            return 0.0

        correct_predictions = 0
        total_predictions = 0

        trend_threshold = thresholds.get('trend_strength_threshold', 0.02)
        flat_threshold = thresholds.get('price_flat_threshold', 0.015)
        crash_threshold = thresholds.get('price_crash_threshold', -0.03)

        for record in historical_data:
            total_predictions += 1
            trend_strength = record.get('trend_strength', 0)
            momentum = record.get('momentum', 0)
            is_chop = record.get('is_chop', 0)
            pnl = record.get('pnl_percent', 0)

            # Classify regime with candidate thresholds
            if momentum < crash_threshold:
                regime = 'CRASH'
            elif abs(trend_strength) > trend_threshold:
                regime = 'TRENDING'
            elif abs(trend_strength) < flat_threshold:
                regime = 'RANGE'
            else:
                regime = 'NEUTRAL'

            # Check if regime classification predicted outcome correctly
            # TRENDING regime should predict wins for momentum trades
            if regime == 'TRENDING' and pnl > 0:
                correct_predictions += 1
            elif regime == 'RANGE' and abs(pnl) < 0.5:
                correct_predictions += 1  # Range = small moves expected
            elif regime == 'CRASH' and pnl < 0:
                correct_predictions += 1  # Crash = losses expected
            elif regime == 'NEUTRAL' and abs(pnl) < 1.0:
                correct_predictions += 1

        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        return accuracy

    def apply_thresholds(self, thresholds: Dict) -> bool:
        """
        Apply learned thresholds to RegimeDetector and save as active threshold set.
        """
        try:
            from .regime_learning_models import RegimeThresholdSet

            # Deactivate current active set
            RegimeThresholdSet.objects.filter(is_active=True).update(is_active=False)

            # Create new active set
            version = RegimeThresholdSet.objects.count() + 1
            RegimeThresholdSet.objects.create(
                version=version,
                is_active=True,
                thresholds=thresholds,
            )

            # Apply to detector class
            self._apply_to_detector(thresholds)

            logger.info(f"Applied regime thresholds v{version}: {thresholds}")
            return True
        except Exception as e:
            logger.error(f"Error applying regime thresholds: {e}", exc_info=True)
            return False

    def _apply_to_detector(self, thresholds: Dict):
        """Override RegimeDetector class constants with learned values."""
        try:
            from .options_regime_detector import RegimeDetector

            mapping = {
                'rv_spike_threshold': 'RV_SPIKE_THRESHOLD',
                'price_crash_threshold': 'PRICE_CRASH_THRESHOLD',
                'trend_strength_threshold': 'TREND_STRENGTH_THRESHOLD',
                'iv_expansion_threshold': 'IV_EXPANSION_THRESHOLD',
                'iv_rank_high': 'IV_RANK_HIGH',
                'iv_rank_low': 'IV_RANK_LOW',
                'price_flat_threshold': 'PRICE_FLAT_THRESHOLD',
            }

            for param_key, class_attr in mapping.items():
                if param_key in thresholds:
                    setattr(RegimeDetector, class_attr, thresholds[param_key])
        except Exception as e:
            logger.error(f"Error applying thresholds to detector: {e}", exc_info=True)
