"""
Test LSTM Integration
Tests the hybrid LSTM → Tree pipeline for day trading
"""
import os
import sys
import django
import logging
from django.core.management.base import BaseCommand
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.lstm_feature_extractor import get_lstm_feature_extractor
from core.day_trading_ml_scorer import DayTradingMLScorer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test LSTM integration with day trading scorer'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing LSTM Integration for Day Trading")
        self.stdout.write("=" * 60)
        
        # Test 1: Check if LSTM extractor is available
        self.stdout.write("\n1. Checking LSTM Feature Extractor...")
        lstm_extractor = get_lstm_feature_extractor()
        
        if lstm_extractor.is_available():
            self.stdout.write(self.style.SUCCESS("   ✅ LSTM Feature Extractor is available"))
            self.stdout.write(f"   - Deep learning available: {lstm_extractor.lstm_available}")
        else:
            self.stdout.write(self.style.WARNING("   ⚠️ LSTM Feature Extractor not available (TensorFlow may not be installed)"))
            self.stdout.write("   - This is OK - system will fall back to tree-only models")
        
        # Test 2: Create sample price data
        self.stdout.write("\n2. Creating sample price data...")
        sample_data = self._create_sample_price_data()
        self.stdout.write(f"   ✅ Created {len(sample_data)} time steps of sample data")
        
        # Test 3: Extract LSTM features
        self.stdout.write("\n3. Extracting LSTM features...")
        try:
            lstm_features = lstm_extractor.extract_features(
                price_data=sample_data,
                symbol='AAPL',
                lookback_minutes=60
            )
            
            self.stdout.write(self.style.SUCCESS("   ✅ LSTM features extracted successfully"))
            self.stdout.write("   Features:")
            for key, value in lstm_features.items():
                self.stdout.write(f"     - {key}: {value:.4f}")
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ LSTM feature extraction failed: {e}"))
            self.stdout.write("   - This is expected if TensorFlow/LSTM model not trained")
            lstm_features = {}
        
        # Test 4: Test day trading scorer with LSTM features
        self.stdout.write("\n4. Testing Day Trading Scorer with LSTM features...")
        scorer = DayTradingMLScorer()
        
        # Create sample features
        sample_features = {
            'momentum_15m': 0.05,
            'rvol_10m': 1.2,
            'vwap_dist': 0.02,
            'breakout_pct': 0.03,
            'spread_bps': 5.0,
            'catalyst_score': 0.7,
            'volume_ratio': 1.5,
            'rsi_14': 65.0,
        }
        
        # Merge LSTM features if available
        if lstm_features:
            sample_features.update(lstm_features)
            self.stdout.write("   ✅ LSTM features merged into feature set")
        
        # Score with and without price data
        try:
            score_without_lstm = scorer.score(
                features=sample_features.copy(),
                mode='SAFE',
                side='LONG'
            )
            
            score_with_lstm = scorer.score(
                features=sample_features.copy(),
                mode='SAFE',
                side='LONG',
                price_data=sample_data,
                symbol='AAPL'
            )
            
            self.stdout.write(self.style.SUCCESS("   ✅ Scoring successful"))
            self.stdout.write(f"   - Score without LSTM data: {score_without_lstm:.2f}")
            self.stdout.write(f"   - Score with LSTM data: {score_with_lstm:.2f}")
            
            if abs(score_with_lstm - score_without_lstm) > 0.1:
                self.stdout.write(self.style.SUCCESS("   ✅ LSTM features are affecting the score (hybrid working!)"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️ LSTM features not significantly affecting score (may need training)"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Scoring failed: {e}"))
        
        # Test 5: Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 Test Summary:")
        self.stdout.write(f"   - LSTM Extractor Available: {lstm_extractor.is_available()}")
        self.stdout.write(f"   - LSTM Features Extracted: {len(lstm_features) > 0}")
        self.stdout.write(f"   - Hybrid Pipeline Working: {lstm_extractor.is_available() and len(lstm_features) > 0}")
        
        if lstm_extractor.is_available():
            self.stdout.write(self.style.SUCCESS("\n✅ LSTM integration is ready!"))
            self.stdout.write("   Next steps:")
            self.stdout.write("   1. Train LSTM models on historical data")
            self.stdout.write("   2. A/B test LSTM-enhanced vs tree-only")
            self.stdout.write("   3. Monitor performance improvement")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ LSTM integration needs TensorFlow"))
            self.stdout.write("   To enable:")
            self.stdout.write("   1. Install TensorFlow: pip install tensorflow")
            self.stdout.write("   2. Train LSTM models")
            self.stdout.write("   3. System will automatically use LSTM features")
    
    def _create_sample_price_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for testing"""
        # Generate 60 time steps (1 hour of 1-min bars)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='1min')
        
        # Generate realistic price data (random walk with trend)
        np.random.seed(42)
        base_price = 150.0
        returns = np.random.normal(0.0001, 0.002, 60)  # Small positive drift, 0.2% volatility
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLCV
        data = {
            'Open': prices * (1 + np.random.normal(0, 0.0005, 60)),
            'High': prices * (1 + abs(np.random.normal(0, 0.001, 60))),
            'Low': prices * (1 - abs(np.random.normal(0, 0.001, 60))),
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, 60)
        }
        
        df = pd.DataFrame(data, index=dates)
        # Ensure High >= Close >= Low, etc.
        df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
        df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
        
        return df

