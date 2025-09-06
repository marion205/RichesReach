#!/usr/bin/env python3
"""
Test ML Improvements
Tests the three high-impact improvements: alternative data, deep learning, and real-time pipeline
"""

import os
import sys
import django
import logging
import asyncio
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_alternative_data():
    """Test alternative data service"""
    print("\n🔍 TESTING ALTERNATIVE DATA SERVICE")
    print("="*50)
    
    try:
        from core.alternative_data_service import AlternativeDataService
        
        service = AlternativeDataService()
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        print(f"Fetching alternative data for {symbols}...")
        alternative_data = await service.get_alternative_data(symbols)
        
        for symbol, data_point in alternative_data.items():
            print(f"\n{symbol}:")
            print(f"  News Sentiment: {data_point.news_sentiment:.3f}")
            print(f"  Social Sentiment: {data_point.social_sentiment:.3f}")
            print(f"  Analyst Sentiment: {data_point.analyst_sentiment:.3f}")
            print(f"  Market Sentiment: {data_point.market_sentiment:.3f}")
            print(f"  VIX: {data_point.volatility_index:.1f}")
            print(f"  Fear & Greed: {data_point.fear_greed_index:.3f}")
            
            features = service.to_feature_vector(data_point)
            print(f"  Feature Vector: {len(features)} features")
        
        print("✅ Alternative data service working!")
        return True
        
    except Exception as e:
        print(f"❌ Alternative data service error: {e}")
        return False

def test_deep_learning():
    """Test deep learning service"""
    print("\n🧠 TESTING DEEP LEARNING SERVICE")
    print("="*50)
    
    try:
        from core.deep_learning_service import DeepLearningService
        
        service = DeepLearningService()
        
        if not service.deep_learning_available:
            print("❌ Deep learning libraries not available")
            return False
        
        print("Creating sample data...")
        n_samples = 500
        n_features = 50
        
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        
        print("Training LSTM model...")
        lstm_results = service.train_lstm_model(X, y)
        print(f"  LSTM CV R²: {lstm_results['cv_mean']:.3f} ± {lstm_results['cv_std']:.3f}")
        
        print("Training Transformer model...")
        transformer_results = service.train_transformer_model(X, y)
        print(f"  Transformer CV R²: {transformer_results['cv_mean']:.3f} ± {transformer_results['cv_std']:.3f}")
        
        print("Testing ensemble prediction...")
        test_X = np.random.randn(10, n_features)
        ensemble_pred = service.ensemble_predict(test_X)
        print(f"  Ensemble predictions: {ensemble_pred[:3]}")
        
        print("✅ Deep learning service working!")
        return True
        
    except Exception as e:
        print(f"❌ Deep learning service error: {e}")
        return False

async def test_integrated_system():
    """Test integrated ML system"""
    print("\n🚀 TESTING INTEGRATED ML SYSTEM")
    print("="*50)
    
    try:
        from core.integrated_ml_system import IntegratedMLSystem
        
        system = IntegratedMLSystem()
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        print("Initializing system...")
        await system.initialize_system(symbols)
        
        print("Training models with real data...")
        results = await system.train_models_with_real_data(symbols, days=300)
        
        print("\n📊 MODEL PERFORMANCE:")
        best_r2 = -999
        best_model = None
        
        for model_name, model_results in results.items():
            if 'cv_mean' in model_results:
                r2 = model_results['cv_mean']
                std = model_results.get('cv_std', 0)
                print(f"  {model_name}: CV R² = {r2:.3f} ± {std:.3f}")
                
                if r2 > best_r2:
                    best_r2 = r2
                    best_model = model_name
            elif 'r2' in model_results:
                r2 = model_results['r2']
                print(f"  {model_name}: R² = {r2:.3f}")
                
                if r2 > best_r2:
                    best_r2 = r2
                    best_model = model_name
        
        if best_model:
            print(f"\n🏆 BEST MODEL: {best_model.upper()} with R² = {best_r2:.3f}")
            
            # Improvement analysis
            original_r2 = -0.003
            improvement = ((best_r2 - original_r2) / abs(original_r2)) * 100 if original_r2 != 0 else 0
            
            print(f"\n📈 IMPROVEMENT ANALYSIS:")
            print(f"  Previous R²: {original_r2:.3f}")
            print(f"  Integrated R²: {best_r2:.3f}")
            print(f"  Improvement: {improvement:+.1f}%")
            
            if best_r2 > 0.1:
                print("  🎉 EXCELLENT: Target achieved! R² > 0.1")
            elif best_r2 > 0.05:
                print("  ✅ GOOD: Significant improvement achieved!")
            elif best_r2 > 0.02:
                print("  📈 POSITIVE: Meaningful improvement achieved!")
            elif best_r2 > 0:
                print("  📈 POSITIVE: Better than random!")
            else:
                print("  ⚠️  CHALLENGING: Financial prediction is inherently difficult")
        
        # Test real-time predictions
        print(f"\n🔮 REAL-TIME PREDICTIONS:")
        for symbol in symbols[:3]:
            prediction = await system.get_real_time_prediction(symbol)
            print(f"  {symbol}: Prediction={prediction['prediction']:.3f}, Confidence={prediction['confidence']:.3f}")
        
        print("✅ Integrated ML system working!")
        return True
        
    except Exception as e:
        print(f"❌ Integrated ML system error: {e}")
        return False

async def main():
    """Main test function"""
    print("\n" + "="*70)
    print("TESTING HIGH-IMPACT ML IMPROVEMENTS")
    print("="*70)
    
    results = {}
    
    # Test alternative data service
    results['alternative_data'] = await test_alternative_data()
    
    # Test deep learning service
    results['deep_learning'] = test_deep_learning()
    
    # Test integrated system
    results['integrated_system'] = await test_integrated_system()
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your integrated ML system is ready for production!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please check the error messages above.")
    
    print("\n💡 NEXT STEPS FOR R² > 0.1:")
    print("   1. Integrate real API keys for alternative data sources")
    print("   2. Implement model retraining pipeline with new data")
    print("   3. Add performance monitoring and alerting")
    print("   4. Implement user feedback learning system")
    print("   5. Add model ensemble optimization")
    print("   6. Implement A/B testing for model versions")
    print("   7. Add real-time model performance tracking")

if __name__ == "__main__":
    asyncio.run(main())
