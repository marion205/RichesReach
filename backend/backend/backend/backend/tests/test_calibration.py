# Unit tests for calibration and drift detection
import pytest
import numpy as np
from calibration import (
    Calibrator, psi, ks_stat, DriftPolicy, SafeModeDecision,
    evaluate_drift_and_safemode, DriftMonitor
)

class TestCalibration:
    def test_calibrator_fit_and_predict(self):
        """Test calibrator fitting and prediction"""
        # Create synthetic data
        np.random.seed(42)
        raw_probs = np.random.uniform(0, 1, 1000)
        outcomes = (raw_probs > 0.5).astype(int)  # Perfect calibration
        
        calibrator = Calibrator.fit(raw_probs, outcomes)
        
        # Test prediction
        test_probs = np.array([0.1, 0.5, 0.9])
        calibrated = calibrator.predict(test_probs)
        
        assert len(calibrated) == 3
        assert np.all(calibrated >= 0)
        assert np.all(calibrated <= 1)
        
    def test_calibrator_calibration_error(self):
        """Test calibration error calculation"""
        # Create poorly calibrated data
        raw_probs = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        outcomes = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1])  # Perfect step function
        
        calibrator = Calibrator.fit(raw_probs, outcomes)
        ece = calibrator.calibration_error(raw_probs, outcomes)
        
        assert ece >= 0
        assert ece <= 1
        
    def test_psi_calculation(self):
        """Test PSI calculation"""
        # Create two similar distributions
        expected = np.random.normal(0.5, 0.1, 1000)
        actual = np.random.normal(0.5, 0.1, 1000)
        
        psi_val = psi(expected, actual)
        assert psi_val >= 0
        assert psi_val < 1  # Should be small for similar distributions
        
        # Test with very different distributions
        expected = np.random.normal(0.5, 0.1, 1000)
        actual = np.random.normal(0.8, 0.1, 1000)
        
        psi_val = psi(expected, actual)
        assert psi_val > 0.1  # Should be larger for different distributions
        
    def test_ks_stat_calculation(self):
        """Test KS statistic calculation"""
        # Create two similar distributions
        expected = np.random.normal(0.5, 0.1, 1000)
        actual = np.random.normal(0.5, 0.1, 1000)
        
        ks_val = ks_stat(expected, actual)
        assert ks_val >= 0
        assert ks_val <= 1
        
        # Test with very different distributions
        expected = np.random.normal(0.5, 0.1, 1000)
        actual = np.random.normal(0.8, 0.1, 1000)
        
        ks_val = ks_stat(expected, actual)
        assert ks_val > 0.1  # Should be larger for different distributions
        
    def test_drift_evaluation_ok(self):
        """Test drift evaluation when drift is normal"""
        ref_probs = np.random.uniform(0, 1, 1000)
        live_probs = np.random.uniform(0, 1, 1000)
        
        decision = evaluate_drift_and_safemode(ref_probs, live_probs)
        
        assert decision.drift_level == "OK"
        assert decision.size_multiplier == 1.0
        assert "normal" in decision.notes.lower()
        
    def test_drift_evaluation_warn(self):
        """Test drift evaluation when drift is elevated"""
        ref_probs = np.random.normal(0.5, 0.1, 1000)
        live_probs = np.random.normal(0.6, 0.1, 1000)  # Shifted distribution
        
        decision = evaluate_drift_and_safemode(ref_probs, live_probs)
        
        assert decision.drift_level in ["WARN", "ALERT"]
        assert decision.size_multiplier <= 0.5
        
    def test_drift_evaluation_alert(self):
        """Test drift evaluation when drift is high"""
        ref_probs = np.random.normal(0.5, 0.1, 1000)
        live_probs = np.random.normal(0.8, 0.1, 1000)  # Very shifted distribution
        
        decision = evaluate_drift_and_safemode(ref_probs, live_probs)
        
        assert decision.drift_level in ["WARN", "ALERT"]
        assert decision.size_multiplier <= 0.5
        
    def test_drift_monitor(self):
        """Test drift monitor functionality"""
        monitor = DriftMonitor(window_size=100)
        
        # Add reference data
        ref_probs = np.random.uniform(0, 1, 500)
        monitor.add_reference_data(ref_probs)
        
        # Add live data
        live_probs = np.random.uniform(0, 1, 200)
        for prob in live_probs:
            decision = monitor.add_live_data(prob)
            assert isinstance(decision, SafeModeDecision)
            
        # Check history
        history = monitor.get_drift_history()
        assert len(history) == 200
        
    def test_drift_monitor_with_outcomes(self):
        """Test drift monitor with outcomes"""
        monitor = DriftMonitor(window_size=100)
        
        # Add reference data
        ref_probs = np.random.uniform(0, 1, 500)
        monitor.add_reference_data(ref_probs)
        
        # Add live data with outcomes
        live_probs = np.random.uniform(0, 1, 200)
        live_outcomes = (live_probs > 0.5).astype(int)
        
        for i, (prob, outcome) in enumerate(zip(live_probs, live_outcomes)):
            decision = monitor.add_live_data(prob, outcome)
            assert isinstance(decision, SafeModeDecision)
            
    def test_drift_policy_customization(self):
        """Test custom drift policy"""
        policy = DriftPolicy(psi_warn=0.05, psi_alert=0.15)
        
        ref_probs = np.random.normal(0.5, 0.1, 1000)
        live_probs = np.random.normal(0.6, 0.1, 1000)
        
        decision = evaluate_drift_and_safemode(ref_probs, live_probs, policy=policy)
        
        # Should trigger warning earlier with lower thresholds
        assert decision.drift_level in ["WARN", "ALERT"]
        
    def test_edge_cases(self):
        """Test edge cases"""
        # Test with empty arrays
        with pytest.raises(ValueError):
            Calibrator.fit(np.array([]), np.array([]))
            
        # Test with mismatched lengths
        with pytest.raises(ValueError):
            Calibrator.fit(np.array([0.1, 0.2]), np.array([0, 1, 0]))
            
        # Test with invalid probabilities
        raw_probs = np.array([-0.1, 0.5, 1.1])
        outcomes = np.array([0, 1, 0])
        calibrator = Calibrator.fit(raw_probs, outcomes)
        
        # Should handle clipping gracefully
        calibrated = calibrator.predict(np.array([-0.1, 1.1]))
        assert np.all(calibrated >= 0)
        assert np.all(calibrated <= 1)
        
    def test_calibrator_not_fitted(self):
        """Test error when using unfitted calibrator"""
        calibrator = Calibrator(None, is_fitted=False)
        
        with pytest.raises(ValueError):
            calibrator.predict(np.array([0.5]))
            
        with pytest.raises(ValueError):
            calibrator.calibration_error(np.array([0.5]), np.array([1]))
            
    def test_drift_monitor_reset(self):
        """Test drift monitor reset functionality"""
        monitor = DriftMonitor()
        
        # Add some data
        ref_probs = np.random.uniform(0, 1, 100)
        monitor.add_reference_data(ref_probs)
        
        for _ in range(50):
            monitor.add_live_data(np.random.uniform(0, 1))
            
        # Reset
        monitor.reset()
        
        # Should be empty after reset
        assert len(monitor.events) == 0
        assert len(monitor.venue_stats) == 0
        assert monitor.reference_window is None
