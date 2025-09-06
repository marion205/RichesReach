#!/usr/bin/env python3
"""
Test Integrated ML System
Tests the complete system with alternative data, deep learning, and real-time pipeline
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

from core.integrated_ml_system import IntegratedMLSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_integrated_system():
    """Test the integrated ML system"""
    print("\n" + "="*70)
    print("TESTING INTEGRATED ML SYSTEM - TARGETING R² = 0.1")
    print("="*70)
    
    # Initialize system
    system = IntegratedMLSystem()
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
    
    try:
        print("✅ Initializing integrated ML system...")
        await system.initialize_system(symbols)
        
        print("✅ Training models with real data...")
        results = await system.train_models_with_real_data(symbols, days=400)
        
        print(f"\n📊 MODEL PERFORMANCE (Cross-Validation R²):")
        best_cv_r2 = -999
        best_model = None
        
        for model_name, model_results in results.items():
            if 'cv_mean' in model_results:
                cv_r2 = model_results['cv_mean']
                cv_std = model_results.get('cv_std', 0)
                print(f"   {model_name}: CV R² = {cv_r2:.3f} ± {cv_std:.3f}")
                
                if cv_r2 > best_cv_r2:
                    best_cv_r2 = cv_r2
                    best_model = model_name
            elif 'r2' in model_results:
                r2 = model_results['r2']
                print(f"   {model_name}: R² = {r2:.3f}")
                
                if r2 > best_cv_r2:
                    best_cv_r2 = r2
                    best_model = model_name
        
        if best_model:
            print(f"\n🏆 BEST MODEL: {best_model.upper()} with R² = {best_cv_r2:.3f}")
            
            # Improvement analysis
            original_r2 = -0.003
            improvement = ((best_cv_r2 - original_r2) / abs(original_r2)) * 100 if original_r2 != 0 else 0
            
            print(f"\n📈 IMPROVEMENT ANALYSIS:")
            print(f"   Previous R²: {original_r2:.3f}")
            print(f"   Integrated R²: {best_cv_r2:.3f}")
            print(f"   Improvement: {improvement:+.1f}%")
            
            if best_cv_r2 > 0.1:
                print("   🎉 EXCELLENT: Target achieved! R² > 0.1")
            elif best_cv_r2 > 0.05:
                print("   ✅ GOOD: Significant improvement achieved!")
            elif best_cv_r2 > 0.02:
                print("   📈 POSITIVE: Meaningful improvement achieved!")
            elif best_cv_r2 > 0:
                print("   📈 POSITIVE: Better than random!")
            else:
                print("   ⚠️  CHALLENGING: Financial prediction is inherently difficult")
        
        # Test real-time predictions
        print(f"\n🔮 REAL-TIME PREDICTIONS:")
        for symbol in symbols[:5]:
            prediction = await system.get_real_time_prediction(symbol)
            print(f"   {symbol}: Prediction={prediction['prediction']:.3f}, Confidence={prediction['confidence']:.3f}")
        
        # Get system status
        status = system.get_system_status()
        print(f"\n🔧 SYSTEM STATUS:")
        print(f"   Initialized: {status['is_initialized']}")
        print(f"   Alternative Data: {status['alternative_data_available']}")
        print(f"   Deep Learning: {status['deep_learning_available']}")
        print(f"   Real-time Pipeline: {status['realtime_pipeline_running']}")
        print(f"   Model Version: {status['current_model_version']}")
        
        # Performance summary
        performance = system.get_performance_summary()
        print(f"\n📋 PERFORMANCE SUMMARY:")
        for model_name, metrics in performance.get('models', {}).items():
            if 'cv_r2_mean' in metrics:
                print(f"   {model_name}: CV R² = {metrics['cv_r2_mean']:.3f} ± {metrics['cv_r2_std']:.3f}")
            elif 'r2' in metrics:
                print(f"   {model_name}: R² = {metrics['r2']:.3f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing integrated system: {e}")
        logger.error(f"Error testing integrated system: {e}")
        return None

def main():
    """Main test function"""
    try:
        results = asyncio.run(test_integrated_system())
        
        if results:
            print("\n" + "="*70)
            print("INTEGRATED ML SYSTEM TEST COMPLETE")
            print("="*70)
            
            print("\n💡 NEXT STEPS FOR R² > 0.1:")
            print("   1. Integrate real API keys for alternative data sources")
            print("   2. Implement model retraining pipeline with new data")
            print("   3. Add performance monitoring and alerting")
            print("   4. Implement user feedback learning system")
            print("   5. Add model ensemble optimization")
            print("   6. Implement A/B testing for model versions")
            print("   7. Add real-time model performance tracking")
        else:
            print("❌ Test failed")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
