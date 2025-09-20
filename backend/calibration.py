# Calibration and drift detection system for ML models
import numpy as np
from sklearn.isotonic import IsotonicRegression
from dataclasses import dataclass
from typing import Dict, Any, Optional
from scipy.stats import ks_2samp
import logging

logger = logging.getLogger(__name__)

@dataclass
class Calibrator:
    """Isotonic probability calibration for model outputs in [0,1]."""
    iso: IsotonicRegression
    is_fitted: bool = False

    @classmethod
    def fit(cls, raw_probs: np.ndarray, outcomes: np.ndarray) -> "Calibrator":
        """Fit calibrator on validation data"""
        if len(raw_probs) != len(outcomes):
            raise ValueError("raw_probs and outcomes must have same length")
        
        # Ensure inputs are numpy arrays
        raw_probs = np.asarray(raw_probs)
        outcomes = np.asarray(outcomes)
        
        # Check for valid probability range
        if np.any(raw_probs < 0) or np.any(raw_probs > 1):
            logger.warning("Raw probabilities outside [0,1] range, clipping")
            raw_probs = np.clip(raw_probs, 0, 1)
        
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(raw_probs, outcomes)
        return cls(iso, is_fitted=True)

    def predict(self, raw_probs: np.ndarray) -> np.ndarray:
        """Calibrate raw probabilities"""
        if not self.is_fitted:
            raise ValueError("Calibrator must be fitted before prediction")
        
        raw_probs = np.asarray(raw_probs)
        raw_probs = np.clip(raw_probs, 0, 1)  # Ensure valid range
        return self.iso.predict(raw_probs)

    def calibration_error(self, raw_probs: np.ndarray, outcomes: np.ndarray) -> float:
        """Calculate Expected Calibration Error (ECE)"""
        if not self.is_fitted:
            raise ValueError("Calibrator must be fitted before calculating ECE")
        
        raw_probs = np.asarray(raw_probs)
        outcomes = np.asarray(outcomes)
        
        # Bin probabilities
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (raw_probs > bin_lower) & (raw_probs <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = outcomes[in_bin].mean()
                avg_confidence_in_bin = raw_probs[in_bin].mean()
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return float(ece)

def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Population Stability Index as a simple drift signal over probabilities.
    """
    # Ensure inputs are numpy arrays
    expected = np.asarray(expected)
    actual = np.asarray(actual)
    
    # Create bins based on quantiles
    cuts = np.quantile(np.concatenate([expected, actual]), np.linspace(0, 1, bins + 1))
    cuts[0] = -np.inf  # Ensure all values are included
    cuts[-1] = np.inf
    
    e_hist, _ = np.histogram(expected, bins=cuts)
    a_hist, _ = np.histogram(actual, bins=cuts)
    
    # Normalize to probabilities
    e = np.clip(e_hist / max(1, e_hist.sum()), 1e-6, 1)
    a = np.clip(a_hist / max(1, a_hist.sum()), 1e-6, 1)
    
    # Calculate PSI
    psi_val = np.sum((a - e) * np.log(a / e))
    return float(psi_val)

def ks_stat(expected: np.ndarray, actual: np.ndarray) -> float:
    """Two-sample KS test for quick drift check."""
    expected = np.asarray(expected)
    actual = np.asarray(actual)
    return float(ks_2samp(expected, actual).statistic)

@dataclass
class DriftPolicy:
    psi_warn: float = 0.1
    psi_alert: float = 0.25
    ks_warn: float = 0.15
    ks_alert: float = 0.25
    ece_warn: float = 0.05
    ece_alert: float = 0.10

@dataclass
class SafeModeDecision:
    drift_level: str          # "OK" | "WARN" | "ALERT"
    size_multiplier: float    # 1.0 normal; <1.0 clamp orders/signals
    notes: str
    psi_value: float
    ks_value: float
    ece_value: float

def evaluate_drift_and_safemode(
    ref_probs: np.ndarray,
    live_probs: np.ndarray,
    live_outcomes: Optional[np.ndarray] = None,
    calibrator: Optional[Calibrator] = None,
    policy: DriftPolicy = DriftPolicy()
) -> SafeModeDecision:
    """Evaluate drift and determine safe mode settings"""
    ref_probs = np.asarray(ref_probs)
    live_probs = np.asarray(live_probs)
    
    psi_val = psi(ref_probs, live_probs)
    ks_val = ks_stat(ref_probs, live_probs)
    
    # Calculate ECE if outcomes are available
    ece_val = 0.0
    if live_outcomes is not None and calibrator is not None:
        ece_val = calibrator.calibration_error(live_probs, live_outcomes)
    
    # Determine drift level
    if (psi_val >= policy.psi_alert or 
        ks_val >= policy.ks_alert or 
        ece_val >= policy.ece_alert):
        return SafeModeDecision(
            "ALERT", 
            0.25, 
            f"High drift detected (PSI={psi_val:.3f}, KS={ks_val:.3f}, ECE={ece_val:.3f}) → clamp to 25% size, require human review.",
            psi_val, ks_val, ece_val
        )
    elif (psi_val >= policy.psi_warn or 
          ks_val >= policy.ks_warn or 
          ece_val >= policy.ece_warn):
        return SafeModeDecision(
            "WARN", 
            0.5, 
            f"Elevated drift (PSI={psi_val:.3f}, KS={ks_val:.3f}, ECE={ece_val:.3f}) → clamp to 50% size.",
            psi_val, ks_val, ece_val
        )
    else:
        return SafeModeDecision(
            "OK", 
            1.0, 
            f"Drift normal (PSI={psi_val:.3f}, KS={ks_val:.3f}, ECE={ece_val:.3f}).",
            psi_val, ks_val, ece_val
        )

class DriftMonitor:
    """Continuous drift monitoring with rolling windows"""
    
    def __init__(self, window_size: int = 1000, policy: DriftPolicy = DriftPolicy()):
        self.window_size = window_size
        self.policy = policy
        self.reference_window = None
        self.current_window = []
        self.decisions = []
    
    def add_reference_data(self, probs: np.ndarray):
        """Set reference window for drift comparison"""
        self.reference_window = np.asarray(probs)
        logger.info(f"Reference window set with {len(self.reference_window)} samples")
    
    def add_live_data(self, probs: np.ndarray, outcomes: Optional[np.ndarray] = None):
        """Add live data point and check for drift"""
        self.current_window.append(probs)
        
        # Keep only recent data
        if len(self.current_window) > self.window_size:
            self.current_window = self.current_window[-self.window_size:]
        
        # Need minimum data for drift check
        if len(self.current_window) < 100:
            return SafeModeDecision("OK", 1.0, "Insufficient data for drift check", 0, 0, 0)
        
        if self.reference_window is None:
            return SafeModeDecision("OK", 1.0, "No reference data available", 0, 0, 0)
        
        # Convert to numpy arrays
        live_probs = np.array(self.current_window)
        if outcomes is not None:
            live_outcomes = np.array(outcomes[-len(live_probs):])
        else:
            live_outcomes = None
        
        # Evaluate drift
        decision = evaluate_drift_and_safemode(
            self.reference_window, 
            live_probs, 
            live_outcomes, 
            policy=self.policy
        )
        
        self.decisions.append(decision)
        return decision
    
    def get_drift_history(self) -> list:
        """Get history of drift decisions"""
        return self.decisions
    
    def reset(self):
        """Reset monitor state"""
        self.reference_window = None
        self.current_window = []
        self.decisions = []

# Example usage functions
def create_calibrated_predictor(raw_probs: np.ndarray, outcomes: np.ndarray) -> Calibrator:
    """Create a calibrated predictor from training data"""
    return Calibrator.fit(raw_probs, outcomes)

def monitor_model_drift(
    reference_probs: np.ndarray,
    live_probs: np.ndarray,
    live_outcomes: Optional[np.ndarray] = None,
    calibrator: Optional[Calibrator] = None
) -> SafeModeDecision:
    """Monitor drift between reference and live model outputs"""
    return evaluate_drift_and_safemode(
        reference_probs, 
        live_probs, 
        live_outcomes, 
        calibrator
    )
