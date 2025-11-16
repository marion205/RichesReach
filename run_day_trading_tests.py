"""
Simple test runner for day trading features (no pytest required)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

from core.day_trading_feature_service import DayTradingFeatureService
from core.day_trading_ml_scorer import DayTradingMLScorer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data():
    """Create test OHLCV data"""
    base_price = 100.0
    timestamps_1m = [datetime.now() - timedelta(minutes=i) for i in range(390, 0, -1)]
    timestamps_5m = [datetime.now() - timedelta(minutes=i*5) for i in range(78, 0, -1)]
    
    prices_1m = [base_price]
    for i in range(1, 390):
        change = np.random.normal(0, 0.001)
        prices_1m.append(prices_1m[-1] * (1 + change))
    
    prices_5m = prices_1m[::5][:78]
    
    ohlcv_1m = pd.DataFrame({
        'timestamp': timestamps_1m,
        'open': prices_1m,
        'high': [p * 1.01 for p in prices_1m],
        'low': [p * 0.99 for p in prices_1m],
        'close': prices_1m,
        'volume': [np.random.randint(100000, 1000000) for _ in range(390)]
    })
    
    ohlcv_5m = pd.DataFrame({
        'timestamp': timestamps_5m,
        'open': prices_5m,
        'high': [p * 1.01 for p in prices_5m],
        'low': [p * 0.99 for p in prices_5m],
        'close': prices_5m,
        'volume': [np.random.randint(500000, 5000000) for _ in range(78)]
    })
    
    return ohlcv_1m, ohlcv_5m

def test_feature_extraction():
    """Test feature extraction"""
    print("🧪 Testing feature extraction...")
    service = DayTradingFeatureService()
    ohlcv_1m, ohlcv_5m = create_test_data()
    
    features = service.extract_all_features(ohlcv_1m, ohlcv_5m, "AAPL")
    
    assert len(features) > 100, f"Expected 100+ features, got {len(features)}"
    assert 'momentum_15m' in features, "Missing momentum_15m"
    assert 'rsi_14' in features, "Missing rsi_14"
    assert 'is_trend_regime' in features, "Missing is_trend_regime"
    assert 'breakout_pct' in features, "Missing breakout_pct"
    
    print("   ✅ Feature extraction: PASSED")
    return True

def test_ml_scoring():
    """Test ML scoring"""
    print("🧪 Testing ML scoring...")
    scorer = DayTradingMLScorer()
    
    features = {
        'momentum_15m': 0.02,
        'is_trend_regime': 1.0,
        'is_breakout': 1.0,
        'volume_ratio': 1.5,
        'rsi_14': 55.0
    }
    
    score = scorer.score(features)
    assert 0 <= score <= 10, f"Score should be 0-10, got {score}"
    
    print(f"   ✅ ML scoring: PASSED (score: {score:.2f})")
    return True

def test_risk_metrics():
    """Test risk metrics calculation"""
    print("🧪 Testing risk metrics...")
    service = DayTradingFeatureService()
    
    features = {
        'atr_5m': 1.0,
        'atr_5m_pct': 0.01,
        'momentum_15m': 0.02
    }
    
    risk = service.calculate_risk_metrics(features, "SAFE", 100.0)
    
    assert 'stop' in risk, "Missing stop"
    assert 'targets' in risk, "Missing targets"
    assert len(risk['targets']) == 3, "Should have 3 targets"
    assert risk['timeStopMin'] == 45, "SAFE mode should have 45min time stop"
    
    print("   ✅ Risk metrics: PASSED")
    return True

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Day Trading Features - Simple Test Runner")
    print("=" * 60)
    print()
    
    tests = [
        ("Feature Extraction", test_feature_extraction),
        ("ML Scoring", test_ml_scoring),
        ("Risk Metrics", test_risk_metrics),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {name}: FAILED - {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

