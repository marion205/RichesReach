"""
HMM Regime Detector - Hidden Markov Model for probabilistic regime detection.

Uses Gaussian HMM to learn regime transitions from historical market data.
Complements the rule-based RegimeDetector by providing:
1. Probabilistic regime classification (not binary)
2. Regime durability estimates via transition matrix
3. Data-driven regime boundaries (not hand-tuned thresholds)
"""
import os
import logging
from typing import Dict, Optional, Tuple, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from hmmlearn.hmm import GaussianHMM
    import joblib
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    logger.warning("hmmlearn not installed. Install with: pip install hmmlearn")

# HMM configuration
N_HIDDEN_STATES = 5
HMM_FEATURES = [
    'returns_5d',
    'rv_z',
    'iv_z',
    'adx_normalized',
    'price_dist_sma20',
    'momentum',
]

# Semantic regime labels (mapped post-training from emission means)
HMM_REGIMES = ['CRASH', 'TREND_UP', 'TREND_DOWN', 'VOLATILE', 'CALM']


class HMMRegimeDetector:
    """
    Gaussian HMM for market regime detection.
    Learns regime structure from historical data and provides
    probabilistic regime classifications with transition probabilities.
    """

    def __init__(self):
        self.model = None
        self.state_mapping = {}  # {hidden_state_idx: regime_label}
        self.model_path = os.path.join(
            os.path.dirname(__file__), 'ml_models', 'hmm_regime_model.pkl'
        )
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self._load_model()

    def _load_model(self):
        """Load trained HMM from disk."""
        if not HMM_AVAILABLE:
            return

        try:
            if os.path.exists(self.model_path):
                saved = joblib.load(self.model_path)
                self.model = saved['model']
                self.state_mapping = saved['state_mapping']
                logger.info(f"Loaded HMM regime model: {len(self.state_mapping)} states")
        except Exception as e:
            logger.warning(f"Error loading HMM model: {e}")

    def is_available(self) -> bool:
        """Check if HMM model is trained and ready."""
        return HMM_AVAILABLE and self.model is not None

    def train(self, historical_df: pd.DataFrame, min_days: int = 252) -> Dict:
        """
        Train HMM on historical market data.

        Args:
            historical_df: DataFrame with columns including close, high, low, iv, rv, volume.
                           Must have calculate_indicators() already applied.
            min_days: Minimum number of days required

        Returns:
            Dict with training metrics
        """
        if not HMM_AVAILABLE:
            return {'success': False, 'error': 'hmmlearn not installed'}

        if len(historical_df) < min_days:
            return {
                'success': False,
                'error': f'Need {min_days} days, have {len(historical_df)}',
            }

        # Extract observable features
        features = self._extract_features(historical_df)
        if features is None:
            return {'success': False, 'error': 'Feature extraction failed'}

        # Remove any rows with NaN
        valid_mask = ~np.isnan(features).any(axis=1)
        features = features[valid_mask]

        if len(features) < min_days:
            return {'success': False, 'error': f'Only {len(features)} valid rows after NaN removal'}

        try:
            # Fit Gaussian HMM
            model = GaussianHMM(
                n_components=N_HIDDEN_STATES,
                covariance_type='full',
                n_iter=200,
                random_state=42,
                verbose=False,
            )
            model.fit(features)

            self.model = model

            # Map hidden states to semantic regime labels
            self.state_mapping = self._map_states_to_regimes(model, features)

            # Compute model selection criteria
            log_likelihood = model.score(features)
            n_params = N_HIDDEN_STATES ** 2 + N_HIDDEN_STATES * len(HMM_FEATURES) * 2
            n_samples = len(features)
            bic = -2 * log_likelihood + n_params * np.log(n_samples)
            aic = -2 * log_likelihood + 2 * n_params

            # Save model
            joblib.dump({
                'model': model,
                'state_mapping': self.state_mapping,
            }, self.model_path)

            # Save training record to DB
            self._save_training_record(
                n_states=N_HIDDEN_STATES,
                log_likelihood=log_likelihood,
                bic=bic,
                aic=aic,
                training_days=len(features),
            )

            logger.info(
                f"HMM trained: {N_HIDDEN_STATES} states, {len(features)} days, "
                f"LL={log_likelihood:.2f}, BIC={bic:.2f}"
            )

            return {
                'success': True,
                'n_states': N_HIDDEN_STATES,
                'log_likelihood': float(log_likelihood),
                'bic': float(bic),
                'aic': float(aic),
                'training_days': len(features),
                'state_mapping': self.state_mapping,
            }

        except Exception as e:
            logger.error(f"HMM training failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def predict_regime(
        self, features: np.ndarray
    ) -> Tuple[str, Dict[str, float], Dict[str, float]]:
        """
        Predict current regime from observable features.

        Args:
            features: 1D or 2D array of observable features (last row used)

        Returns:
            Tuple of:
            - regime: Semantic regime label
            - probabilities: Dict of {regime: probability}
            - transition_probs: Dict of {regime: transition probability from current state}
        """
        if not self.is_available():
            return 'NEUTRAL', {}, {}

        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)

            # Get state probabilities for the last observation
            state_probs = self.model.predict_proba(features)[-1]
            most_likely_state = np.argmax(state_probs)

            # Map to semantic labels
            regime = self.state_mapping.get(most_likely_state, 'NEUTRAL')
            probabilities = {
                self.state_mapping.get(i, f'STATE_{i}'): float(p)
                for i, p in enumerate(state_probs)
            }

            # Get transition probabilities from current state
            transition_row = self.model.transmat_[most_likely_state]
            transition_probs = {
                self.state_mapping.get(i, f'STATE_{i}'): float(p)
                for i, p in enumerate(transition_row)
            }

            return regime, probabilities, transition_probs

        except Exception as e:
            logger.error(f"HMM prediction failed: {e}")
            return 'NEUTRAL', {}, {}

    def get_regime_durability(self, regime: str) -> float:
        """
        Get the self-transition probability for a regime.
        Higher = regime is more likely to persist.
        """
        if not self.is_available():
            return 0.5

        # Find the state index for this regime
        for state_idx, label in self.state_mapping.items():
            if label == regime:
                return float(self.model.transmat_[state_idx][state_idx])
        return 0.5

    def _extract_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """Extract HMM observable features from market data DataFrame."""
        try:
            features = np.column_stack([
                df['returns_5d'].fillna(0).values if 'returns_5d' in df else df['close'].pct_change(5).fillna(0).values,
                df['rv_z'].fillna(0).values if 'rv_z' in df else np.zeros(len(df)),
                df['iv_z'].fillna(0).values if 'iv_z' in df else np.zeros(len(df)),
                (df['adx'].fillna(25).values / 100.0) if 'adx' in df else np.full(len(df), 0.25),
                df['price_dist_sma20'].fillna(0).values if 'price_dist_sma20' in df else np.zeros(len(df)),
                df['returns'].fillna(0).values if 'returns' in df else df['close'].pct_change().fillna(0).values,
            ])
            return features
        except Exception as e:
            logger.error(f"HMM feature extraction failed: {e}", exc_info=True)
            return None

    def _map_states_to_regimes(
        self, model: 'GaussianHMM', features: np.ndarray
    ) -> Dict[int, str]:
        """
        Map hidden states to semantic regime labels by examining emission means.

        Strategy:
        - CRASH: lowest returns_5d mean + highest rv_z
        - TREND_UP: highest returns_5d mean + positive momentum
        - TREND_DOWN: negative returns + moderate rv_z
        - VOLATILE: highest rv_z but mixed returns
        - CALM: lowest rv_z + low adx
        """
        means = model.means_  # Shape: (n_states, n_features)
        # Feature indices: returns_5d=0, rv_z=1, iv_z=2, adx_norm=3, price_dist=4, momentum=5

        mapping = {}
        used_labels = set()

        # Score each state for each regime
        state_scores = {}
        for i in range(N_HIDDEN_STATES):
            returns = means[i][0]
            rv_z = means[i][1]
            iv_z = means[i][2]
            adx_norm = means[i][3]
            momentum = means[i][5]

            state_scores[i] = {
                'CRASH': -returns * 10 + rv_z * 5 + iv_z * 3,
                'TREND_UP': returns * 10 + momentum * 5 - rv_z * 2,
                'TREND_DOWN': -returns * 8 - momentum * 3 + rv_z * 1,
                'VOLATILE': rv_z * 8 + iv_z * 5 + abs(returns) * 2,
                'CALM': -rv_z * 8 - iv_z * 5 - adx_norm * 5,
            }

        # Greedily assign labels to states (highest score first)
        assignments = []
        for i in range(N_HIDDEN_STATES):
            for label in HMM_REGIMES:
                if label not in used_labels:
                    assignments.append((state_scores[i][label], i, label))

        assignments.sort(reverse=True)

        used_states = set()
        for score, state_idx, label in assignments:
            if state_idx not in used_states and label not in used_labels:
                mapping[state_idx] = label
                used_states.add(state_idx)
                used_labels.add(label)

        # Fill any unmapped states
        for i in range(N_HIDDEN_STATES):
            if i not in mapping:
                mapping[i] = 'NEUTRAL'

        logger.info(f"HMM state mapping: {mapping}")
        return mapping

    def _save_training_record(self, **kwargs):
        """Save training metadata to DB."""
        try:
            from .hmm_regime_models import HMMTrainingRecord

            # Deactivate old records
            HMMTrainingRecord.objects.filter(is_active=True).update(is_active=False)

            HMMTrainingRecord.objects.create(
                symbol='SPY',
                model_path=self.model_path,
                is_active=True,
                state_mapping={str(k): v for k, v in self.state_mapping.items()},
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Could not save HMM training record: {e}")
