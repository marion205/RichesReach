"""
Ensemble Regime Detector - Combines rule-based and HMM regime detection.

Voting logic:
1. If both agree → high confidence, use the agreed regime
2. If rule-based says CRASH_PANIC → always use CRASH_PANIC (safety override)
3. If they disagree → use HMM if its confidence > 0.7, else use rule-based
4. Maps HMM's 5-state output to the existing 7-regime system
"""
import logging
from typing import Dict, Tuple, Optional, Any

import numpy as np
import pandas as pd
from django.utils import timezone

from .options_regime_detector import RegimeDetector
from .hmm_regime_detector import HMMRegimeDetector

logger = logging.getLogger(__name__)


class EnsembleRegimeDetector:
    """
    Ensemble that combines rule-based and HMM regime detectors.
    Preserves the RegimeDetector interface (detect_regime returns same tuple)
    while adding probabilistic confidence and transition durability metadata.
    """

    def __init__(self, lookback_period: int = 20, confirmation_bars: int = 3):
        self.rule_detector = RegimeDetector(
            lookback_period=lookback_period,
            confirmation_bars=confirmation_bars,
        )
        self.hmm_detector = HMMRegimeDetector()
        logger.info(
            f"EnsembleRegimeDetector initialized "
            f"(HMM available: {self.hmm_detector.is_available()})"
        )

    # Expose state for regime integration compatibility
    @property
    def previous_regime(self):
        return self.rule_detector.previous_regime

    @property
    def current_regime(self):
        return self.rule_detector.current_regime

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Delegate to rule-based detector's indicator calculation."""
        return self.rule_detector.calculate_indicators(df)

    def detect_regime(self, df: pd.DataFrame) -> Tuple[str, bool, str]:
        """
        Detect regime using ensemble of rule-based + HMM detectors.
        Returns the same (regime, is_shift, description) tuple as RegimeDetector.
        """
        # 1. Rule-based detection (includes hysteresis)
        rule_regime, is_shift, description = self.rule_detector.detect_regime(df)

        # 2. HMM detection (if model available)
        if not self.hmm_detector.is_available():
            return rule_regime, is_shift, description

        try:
            hmm_features = self.hmm_detector._extract_features(df)
            if hmm_features is None or len(hmm_features) == 0:
                return rule_regime, is_shift, description

            hmm_regime, probabilities, transition_probs = self.hmm_detector.predict_regime(
                hmm_features
            )

            # 3. Ensemble voting
            final_regime = self._ensemble_vote(
                rule_regime, hmm_regime, probabilities, df
            )

            # If ensemble changed the regime, check for shift
            if final_regime != rule_regime:
                # Only override if HMM is very confident
                hmm_confidence = probabilities.get(hmm_regime, 0)
                if hmm_confidence <= 0.7:
                    final_regime = rule_regime

            # Record snapshot for analysis
            self._record_snapshot(
                df, hmm_regime, probabilities, rule_regime,
                final_regime, transition_probs
            )

            # Use rule-based description (it matches the 7-regime system)
            description = RegimeDetector.REGIME_DESCRIPTIONS.get(
                final_regime, description
            )

            return final_regime, is_shift, description

        except Exception as e:
            logger.debug(f"HMM ensemble failed, using rule-based: {e}")
            return rule_regime, is_shift, description

    def _ensemble_vote(
        self,
        rule_regime: str,
        hmm_regime: str,
        probabilities: Dict[str, float],
        df: pd.DataFrame,
    ) -> str:
        """
        Combine rule-based and HMM predictions.
        """
        # Map HMM 5-state to 7-state system
        mapped_hmm = self._map_to_seven_regimes(hmm_regime, probabilities, df)

        # Agreement → high confidence
        if rule_regime == mapped_hmm:
            return rule_regime

        # Safety: CRASH_PANIC from rule-based always wins
        if rule_regime == 'CRASH_PANIC':
            return 'CRASH_PANIC'

        # Disagreement: use HMM if highly confident
        hmm_confidence = probabilities.get(hmm_regime, 0)
        if hmm_confidence > 0.7:
            return mapped_hmm

        # Default to rule-based
        return rule_regime

    def _map_to_seven_regimes(
        self,
        hmm_regime: str,
        probabilities: Dict[str, float],
        df: pd.DataFrame,
    ) -> str:
        """
        Map HMM's 5-state output to the existing 7-regime system.

        HMM 5 states → 7 regimes:
        - CRASH → CRASH_PANIC
        - TREND_UP → TREND_UP (or BREAKOUT_EXPANSION if rv_z high)
        - TREND_DOWN → TREND_DOWN
        - VOLATILE → BREAKOUT_EXPANSION (if directional) or MEAN_REVERSION (if choppy)
        - CALM → POST_EVENT_CRUSH (if IV declining) or NEUTRAL
        """
        if hmm_regime == 'CRASH':
            return 'CRASH_PANIC'

        if hmm_regime == 'TREND_UP':
            # Check if it's more of a breakout
            latest = df.iloc[-1] if len(df) > 0 else None
            if latest is not None:
                rv_z = latest.get('rv_z', 0)
                if rv_z > 1.0:
                    return 'BREAKOUT_EXPANSION'
            return 'TREND_UP'

        if hmm_regime == 'TREND_DOWN':
            return 'TREND_DOWN'

        if hmm_regime == 'VOLATILE':
            latest = df.iloc[-1] if len(df) > 0 else None
            if latest is not None:
                returns_5d = abs(latest.get('returns_5d', 0))
                if returns_5d > 0.03:
                    return 'BREAKOUT_EXPANSION'
            return 'MEAN_REVERSION'

        if hmm_regime == 'CALM':
            latest = df.iloc[-1] if len(df) > 0 else None
            if latest is not None:
                iv_accel = latest.get('iv_accel', 1.0)
                if iv_accel < 0.95:
                    return 'POST_EVENT_CRUSH'
            return 'NEUTRAL'

        return 'NEUTRAL'

    def _record_snapshot(
        self,
        df: pd.DataFrame,
        hmm_regime: str,
        probabilities: Dict,
        rule_regime: str,
        ensemble_regime: str,
        transition_probs: Dict,
    ):
        """Record regime detection snapshot for analysis."""
        try:
            from .hmm_regime_models import HMMRegimeSnapshot

            # Determine symbol from context (if available)
            symbol = 'SPY'  # Default

            HMMRegimeSnapshot.objects.create(
                symbol=symbol,
                hmm_regime=hmm_regime,
                hmm_probabilities=probabilities,
                rule_regime=rule_regime,
                ensemble_regime=ensemble_regime,
                transition_probs=transition_probs,
                detected_at=timezone.now(),
            )
        except Exception as e:
            logger.debug(f"Could not record HMM snapshot: {e}")

    def get_regime_state(self) -> Dict:
        """Return combined state for diagnostics."""
        state = self.rule_detector.get_regime_state()
        state['hmm_available'] = self.hmm_detector.is_available()
        if self.hmm_detector.is_available():
            state['hmm_state_mapping'] = self.hmm_detector.state_mapping
        return state

    def reset_regime(self):
        """Reset internal state."""
        self.rule_detector.reset_regime()
