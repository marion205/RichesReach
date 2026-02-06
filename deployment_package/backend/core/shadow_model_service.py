"""
Shadow Model Service - Evolutionary model promotion system.

Trains candidate models nightly with diverse algorithms. Each shadow model
runs in parallel with the incumbent for 72 hours. If a shadow outperforms
the incumbent on out-of-sample predictions, it gets promoted.

This prevents catastrophic model regressions and enables continuous
algorithm exploration without risking production quality.
"""
import os
import shutil
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Any

import numpy as np
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Shadow model configurations
SHADOW_CONFIGS = [
    {
        'algorithm': 'gradient_boosting',
        'model_class': 'GradientBoostingRegressor',
        'hyperparameters': {
            'n_estimators': 200,
            'learning_rate': 0.05,
            'max_depth': 3,
            'random_state': 42,
        },
    },
    {
        'algorithm': 'random_forest',
        'model_class': 'RandomForestRegressor',
        'hyperparameters': {
            'n_estimators': 200,
            'max_depth': 8,
            'random_state': 42,
            'n_jobs': -1,
        },
    },
    {
        'algorithm': 'mlp',
        'model_class': 'MLPRegressor',
        'hyperparameters': {
            'hidden_layer_sizes': (64, 32),
            'max_iter': 500,
            'learning_rate': 'adaptive',
            'random_state': 42,
        },
    },
]

VALIDATION_HOURS = 72
MIN_PREDICTIONS_FOR_EVAL = 20


class ShadowModelService:
    """Manages the shadow model lifecycle: train → validate → promote."""

    def __init__(self):
        self.models_dir = os.path.join(
            os.path.dirname(__file__), 'ml_models'
        )
        os.makedirs(self.models_dir, exist_ok=True)

    def train_shadow_models(self) -> List[Dict[str, Any]]:
        """
        Train candidate models with diverse algorithms.
        Uses the same training data as the incumbent ML learner.
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available for shadow model training")
            return []

        from .day_trading_ml_learner import get_day_trading_ml_learner
        from .shadow_model_models import ShadowModel

        learner = get_day_trading_ml_learner()
        X_dicts, y = learner.load_training_data_from_database(days_back=30, min_records=50)

        if len(X_dicts) < 50:
            logger.warning(f"Not enough data for shadow training: {len(X_dicts)} records")
            return []

        # Convert to arrays using the same feature order as the learner
        feature_names = [
            'momentum_15m', 'rvol_10m', 'vwap_dist', 'breakout_pct', 'spread_bps',
            'catalyst_score', 'volume_ratio', 'volume_zscore', 'rsi_14',
            'is_trend_regime', 'is_range_regime', 'is_high_vol_chop', 'regime_confidence',
            'is_vol_expansion', 'is_breakout', 'is_three_white_soldiers',
            'is_engulfing_bull', 'is_engulfing_bear', 'is_hammer', 'is_doji',
            'vwap_dist_pct', 'macd_hist', 'bb_position', 'trend_strength',
            'price_above_sma20', 'price_above_sma50', 'sma20_above_sma50',
            'is_opening_hour', 'is_closing_hour', 'is_midday',
            'sentiment_score', 'sentiment_volume', 'sentiment_divergence',
            'score', 'mode_safe', 'side_long', 'hour_of_day', 'day_of_week',
        ]

        X = np.array([
            [d.get(name, 0.0) for name in feature_names]
            for d in X_dicts
        ])
        y = np.array(y)

        # Split data
        if len(X) > 100:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        else:
            X_train, X_test, y_train, y_test = X, X, y, y

        # Expire old validating shadows
        ShadowModel.objects.filter(
            status='VALIDATING',
            validation_start__lt=timezone.now() - timedelta(hours=VALIDATION_HOURS * 2),
        ).update(status='EXPIRED')

        results = []
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        for config in SHADOW_CONFIGS:
            try:
                result = self._train_single_shadow(
                    config, X_train, X_test, y_train, y_test, timestamp
                )
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to train shadow {config['algorithm']}: {e}", exc_info=True)

        logger.info(f"Trained {len(results)} shadow models")
        return results

    def _train_single_shadow(
        self, config: Dict, X_train, X_test, y_train, y_test, timestamp: str
    ) -> Optional[Dict]:
        """Train a single shadow model and save to disk + DB."""
        from .shadow_model_models import ShadowModel

        algorithm = config['algorithm']
        hyperparams = config['hyperparameters']

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Build model
        model_classes = {
            'gradient_boosting': GradientBoostingRegressor,
            'random_forest': RandomForestRegressor,
            'mlp': MLPRegressor,
        }
        model_class = model_classes[algorithm]
        model = model_class(**hyperparams)
        model.fit(X_train_scaled, y_train)

        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)

        # Check for overfit
        if train_score - test_score > 0.25:
            logger.warning(f"Shadow {algorithm} overfit: train={train_score:.3f} test={test_score:.3f}")
            return None

        # Save to disk
        model_path = os.path.join(self.models_dir, f'shadow_{algorithm}_{timestamp}.pkl')
        scaler_path = os.path.join(self.models_dir, f'shadow_{algorithm}_{timestamp}_scaler.pkl')
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        # Create DB record
        shadow = ShadowModel.objects.create(
            algorithm=algorithm,
            hyperparameters=hyperparams,
            model_path=model_path,
            scaler_path=scaler_path,
            status='VALIDATING',
            train_score=train_score,
            test_score=test_score,
            validation_start=timezone.now(),
        )

        logger.info(
            f"Shadow model trained: {algorithm} "
            f"train={train_score:.3f} test={test_score:.3f} id={shadow.id}"
        )

        return {
            'id': str(shadow.id),
            'algorithm': algorithm,
            'train_score': train_score,
            'test_score': test_score,
        }

    def record_predictions_for_signal(
        self, signal_id: str, features: Dict, incumbent_score: float
    ):
        """
        Run all validating shadow models on a signal and record predictions.
        Called from the scorer during production scoring.
        """
        if not ML_AVAILABLE:
            return

        from .shadow_model_models import ShadowModel, ShadowPrediction
        from .signal_performance_models import DayTradingSignal

        shadows = ShadowModel.objects.filter(status='VALIDATING')
        if not shadows.exists():
            return

        try:
            signal = DayTradingSignal.objects.get(signal_id=signal_id)
        except DayTradingSignal.DoesNotExist:
            return

        feature_names = [
            'momentum_15m', 'rvol_10m', 'vwap_dist', 'breakout_pct', 'spread_bps',
            'catalyst_score', 'volume_ratio', 'volume_zscore', 'rsi_14',
            'is_trend_regime', 'is_range_regime', 'is_high_vol_chop', 'regime_confidence',
            'is_vol_expansion', 'is_breakout', 'is_three_white_soldiers',
            'is_engulfing_bull', 'is_engulfing_bear', 'is_hammer', 'is_doji',
            'vwap_dist_pct', 'macd_hist', 'bb_position', 'trend_strength',
            'price_above_sma20', 'price_above_sma50', 'sma20_above_sma50',
            'is_opening_hour', 'is_closing_hour', 'is_midday',
            'sentiment_score', 'sentiment_volume', 'sentiment_divergence',
            'score', 'mode_safe', 'side_long', 'hour_of_day', 'day_of_week',
        ]

        feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])

        for shadow in shadows:
            try:
                model = joblib.load(shadow.model_path)
                scaler = joblib.load(shadow.scaler_path)
                scaled = scaler.transform(feature_vector)
                shadow_score = float(model.predict(scaled)[0])
                shadow_score = max(0.0, min(1.0, shadow_score))

                ShadowPrediction.objects.create(
                    shadow_model=shadow,
                    signal=signal,
                    shadow_score=shadow_score * 10.0,
                    incumbent_score=incumbent_score,
                )
            except Exception as e:
                logger.debug(f"Shadow prediction failed for {shadow.algorithm}: {e}")

    def evaluate_shadow_models(self) -> List[Dict[str, Any]]:
        """
        Evaluate shadow models that have completed their 72-hour validation window.
        Promote any shadow that beats the incumbent on prediction accuracy.
        """
        from .shadow_model_models import ShadowModel, ShadowPrediction
        from .signal_performance_models import SignalPerformance

        cutoff = timezone.now() - timedelta(hours=VALIDATION_HOURS)
        candidates = ShadowModel.objects.filter(
            status='VALIDATING',
            validation_start__lte=cutoff,
        )

        results = []
        for shadow in candidates:
            predictions = ShadowPrediction.objects.filter(shadow_model=shadow)
            if predictions.count() < MIN_PREDICTIONS_FOR_EVAL:
                logger.info(
                    f"Shadow {shadow.algorithm} has only {predictions.count()} predictions, "
                    f"need {MIN_PREDICTIONS_FOR_EVAL}. Expiring."
                )
                shadow.status = 'EXPIRED'
                shadow.validation_end = timezone.now()
                shadow.save()
                continue

            # Fill in actual outcomes from SignalPerformance
            shadow_correct = 0
            incumbent_correct = 0
            total_evaluated = 0

            for pred in predictions:
                try:
                    perf = SignalPerformance.objects.filter(
                        signal=pred.signal, horizon='EOD'
                    ).first()
                    if not perf or perf.pnl_percent is None:
                        continue

                    actual_win = 1.0 if float(perf.pnl_percent) > 0 else 0.0
                    pred.actual_outcome = actual_win
                    pred.save(update_fields=['actual_outcome'])

                    total_evaluated += 1

                    # Shadow predicted win (score > 5.0) and actual was win
                    shadow_predicted_win = pred.shadow_score > 5.0
                    incumbent_predicted_win = pred.incumbent_score > 5.0

                    if shadow_predicted_win == (actual_win > 0.5):
                        shadow_correct += 1
                    if incumbent_predicted_win == (actual_win > 0.5):
                        incumbent_correct += 1
                except Exception:
                    continue

            if total_evaluated < 10:
                shadow.status = 'EXPIRED'
                shadow.validation_end = timezone.now()
                shadow.save()
                continue

            shadow_accuracy = shadow_correct / total_evaluated
            incumbent_accuracy = incumbent_correct / total_evaluated

            shadow.validation_accuracy = shadow_accuracy
            shadow.incumbent_accuracy = incumbent_accuracy
            shadow.validation_end = timezone.now()

            result = {
                'id': str(shadow.id),
                'algorithm': shadow.algorithm,
                'shadow_accuracy': shadow_accuracy,
                'incumbent_accuracy': incumbent_accuracy,
                'total_evaluated': total_evaluated,
                'promoted': False,
            }

            # Promote if shadow beats incumbent by at least 2%
            if shadow_accuracy > incumbent_accuracy + 0.02:
                self._promote_shadow(shadow)
                result['promoted'] = True
                logger.info(
                    f"Shadow {shadow.algorithm} PROMOTED: "
                    f"shadow={shadow_accuracy:.2%} > incumbent={incumbent_accuracy:.2%}"
                )
            else:
                shadow.status = 'EXPIRED'
                logger.info(
                    f"Shadow {shadow.algorithm} expired: "
                    f"shadow={shadow_accuracy:.2%} vs incumbent={incumbent_accuracy:.2%}"
                )

            shadow.save()
            results.append(result)

        return results

    def _promote_shadow(self, shadow):
        """Atomically swap shadow model into the incumbent position."""
        from .day_trading_ml_learner import get_day_trading_ml_learner

        learner = get_day_trading_ml_learner()

        # Backup current incumbent
        if os.path.exists(learner.model_path):
            shutil.copy(learner.model_path, learner.model_path + '.pre_shadow_backup')
        if os.path.exists(learner.scaler_path):
            shutil.copy(learner.scaler_path, learner.scaler_path + '.pre_shadow_backup')

        # Copy shadow into incumbent position
        shutil.copy(shadow.model_path, learner.model_path)
        shutil.copy(shadow.scaler_path, learner.scaler_path)

        # Reload the learner
        learner._load_model()

        shadow.status = 'PROMOTED'
        shadow.promoted_at = timezone.now()
        shadow.save()

        logger.info(f"Promoted shadow {shadow.algorithm} ({shadow.id}) to production")

    def cleanup_old_shadows(self, max_age_days: int = 14):
        """Remove expired shadow model files and records older than max_age_days."""
        from .shadow_model_models import ShadowModel

        cutoff = timezone.now() - timedelta(days=max_age_days)
        old_shadows = ShadowModel.objects.filter(
            status__in=['EXPIRED', 'FAILED'],
            created_at__lt=cutoff,
        )

        cleaned = 0
        for shadow in old_shadows:
            for path in [shadow.model_path, shadow.scaler_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            shadow.delete()
            cleaned += 1

        if cleaned:
            logger.info(f"Cleaned up {cleaned} old shadow models")
