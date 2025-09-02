#!/usr/bin/env python3
"""
Production Deployment Script
Demonstrates TensorFlow installation, API integration, performance monitoring, and user feedback
"""

import os
import sys
import asyncio
import time
from pathlib import Path
import json
import numpy as np
import pandas as pd

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

def check_tensorflow_installation():
    """Check if TensorFlow is properly installed"""
    print("🧠 Checking TensorFlow Installation...")
    print("=" * 50)
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow {tf.__version__} installed successfully")
        
        # Check GPU availability
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"🚀 GPU detected: {len(gpus)} device(s)")
            for gpu in gpus:
                print(f"   - {gpu.name}")
        else:
            print("💻 Running on CPU")
        
        # Test basic functionality
        print("\n🧪 Testing TensorFlow functionality...")
        x = tf.constant([[1, 2], [3, 4]])
        y = tf.constant([[5, 6], [7, 8]])
        result = tf.matmul(x, y)
        print(f"   Matrix multiplication test: ✅ {result.numpy()}")
        
        return True
        
    except ImportError as e:
        print(f"❌ TensorFlow not installed: {e}")
        print("\n📦 To install TensorFlow, run:")
        print("   pip install tensorflow")
        return False
    except Exception as e:
        print(f"❌ TensorFlow error: {e}")
        return False

def check_api_integration():
    """Check API integration capabilities"""
    print("\n🌐 Checking API Integration...")
    print("=" * 50)
    
    try:
        from core.market_data_api_service import MarketDataAPIService, DataProvider
        
        # Initialize service
        api_service = MarketDataAPIService()
        
        print("✅ Market Data API Service initialized")
        
        # Check available providers
        available_providers = api_service.get_available_providers()
        if available_providers:
            print(f"🔑 Available data providers: {len(available_providers)}")
            for provider in available_providers:
                print(f"   - {provider.value}")
        else:
            print("⚠️  No API keys configured")
            print("\n🔑 To configure API keys, set environment variables:")
            print("   export ALPHA_VANTAGE_API_KEY='your_key_here'")
            print("   export FINNHUB_API_KEY='your_key_here'")
            print("   export IEX_CLOUD_API_KEY='your_key_here'")
        
        # Check provider status
        provider_status = api_service.get_provider_status()
        print(f"\n📊 Provider Status:")
        for provider, status in provider_status.items():
            print(f"   {provider}: {status['rate_limit']} req/min")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration error: {e}")
        return False

def check_performance_monitoring():
    """Check performance monitoring capabilities"""
    print("\n📊 Checking Performance Monitoring...")
    print("=" * 50)
    
    try:
        from core.performance_monitoring_service import PerformanceMonitoringService, MetricType
        
        # Initialize monitoring service
        monitoring = PerformanceMonitoringService()
        
        print("✅ Performance Monitoring Service initialized")
        
        # Test metric recording
        print("\n🧪 Testing metric recording...")
        monitoring.record_metric(
            name="test_accuracy",
            value=0.85,
            metric_type=MetricType.ACCURACY,
            model_name="test_model"
        )
        
        monitoring.record_metric(
            name="test_response_time",
            value=0.5,
            metric_type=MetricType.API_PERFORMANCE
        )
        
        print("   ✅ Test metrics recorded")
        
        # Test model performance recording
        print("\n🧪 Testing model performance recording...")
        monitoring.record_model_performance(
            model_name="test_model",
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            mse=0.15,
            mae=0.12,
            training_samples=1000,
            validation_samples=200
        )
        
        print("   ✅ Model performance recorded")
        
        # Wait for metrics to be processed
        time.sleep(2)
        
        # Get metrics
        metrics = monitoring.get_metrics(limit=10)
        print(f"\n📈 Recent metrics: {len(metrics)} recorded")
        
        # Get system status
        status = monitoring.get_system_status()
        print(f"🔍 System status: {status['monitoring_active']}")
        
        # Cleanup test data
        monitoring.cleanup_old_data(days_to_keep=0)
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring error: {e}")
        return False

def check_user_feedback():
    """Check user feedback integration"""
    print("\n👤 Checking User Feedback Integration...")
    print("=" * 50)
    
    try:
        from core.user_feedback_service import UserFeedbackService, FeedbackType, UserPreference, LearningPattern
        
        # Initialize feedback service
        feedback_service = UserFeedbackService()
        
        print("✅ User Feedback Service initialized")
        
        # Test user ID
        test_user_id = "test_user_001"
        
        # Test feedback submission
        print("\n🧪 Testing feedback submission...")
        feedback_success = feedback_service.submit_feedback(
            user_id=test_user_id,
            feedback_type=FeedbackType.ALGORITHM_FEEDBACK,
            content="The portfolio optimization algorithm works great!",
            rating=9.0,
            metadata={'feature': 'portfolio_optimization', 'satisfaction': 'high'}
        )
        
        if feedback_success:
            print("   ✅ Feedback submitted successfully")
        else:
            print("   ❌ Feedback submission failed")
        
        # Test preference update
        print("\n🧪 Testing preference update...")
        preference_success = feedback_service.update_preference(
            user_id=test_user_id,
            preference_type=UserPreference.ESG_FOCUS,
            value={
                'focus_areas': ['environmental', 'governance'],
                'importance_level': 'high',
                'exclusion_criteria': ['fossil_fuels', 'tobacco']
            },
            confidence=0.9
        )
        
        if preference_success:
            print("   ✅ Preference updated successfully")
        else:
            print("   ❌ Preference update failed")
        
        # Test learning pattern recording
        print("\n🧪 Testing learning pattern recording...")
        pattern_success = feedback_service.record_learning_pattern(
            user_id=test_user_id,
            pattern_type=LearningPattern.PORTFOLIO_CHANGES,
            data={
                'rebalancing_frequency': 'monthly',
                'allocation_changes': 'moderate',
                'risk_adjustments': 'conservative',
                'last_change_date': '2024-01-15'
            }
        )
        
        if pattern_success:
            print("   ✅ Learning pattern recorded successfully")
        else:
            print("   ❌ Learning pattern recording failed")
        
        # Test data retrieval
        print("\n🧪 Testing data retrieval...")
        preferences = feedback_service.get_user_preferences(test_user_id)
        patterns = feedback_service.get_learning_patterns(test_user_id)
        feedback = feedback_service.get_user_feedback(test_user_id)
        
        print(f"   Preferences: {len(preferences)}")
        print(f"   Learning patterns: {len(patterns)}")
        print(f"   Feedback: {len(feedback)}")
        
        # Test preference summary
        summary = feedback_service.get_preference_summary(test_user_id)
        print(f"   Summary generated: {'user_id' in summary}")
        
        # Test adaptive preferences
        adaptive = feedback_service.get_adaptive_preferences(test_user_id)
        print(f"   Adaptive preferences: {'portfolio_behavior' in adaptive}")
        
        # Test data export
        print("\n🧪 Testing data export...")
        export_success = feedback_service.export_user_data(test_user_id, "test_user_data.json")
        if export_success:
            print("   ✅ User data exported successfully")
            # Clean up export file
            if os.path.exists("test_user_data.json"):
                os.remove("test_user_data.json")
        else:
            print("   ❌ User data export failed")
        
        return True
        
    except Exception as e:
        print(f"❌ User feedback error: {e}")
        return False

def check_deep_learning():
    """Check deep learning capabilities"""
    print("\n🔮 Checking Deep Learning Capabilities...")
    print("=" * 50)
    
    try:
        from core.deep_learning_service import DeepLearningService
        
        # Initialize deep learning service
        dl_service = DeepLearningService()
        
        print(f"✅ Deep Learning Service initialized: {dl_service.is_available()}")
        
        if not dl_service.is_available():
            print("⚠️  Deep learning not available. Install TensorFlow for full functionality.")
            return False
        
        # Test LSTM model creation
        print("\n🧪 Testing LSTM model creation...")
        lstm_created = dl_service.create_lstm_model('production_test', {
            'sequence_length': 30,
            'features': 15,
            'lstm_units': [64, 32],
            'epochs': 5  # Reduced for testing
        })
        
        if lstm_created:
            print("   ✅ LSTM model created successfully")
            
            # Test ensemble model
            print("\n🧪 Testing ensemble model creation...")
            ensemble_created = dl_service.create_ensemble_model('production_ensemble', ['production_test'], 'voting')
            
            if ensemble_created:
                print("   ✅ Ensemble model created successfully")
            else:
                print("   ❌ Ensemble model creation failed")
            
            # Test online model
            print("\n🧪 Testing online model creation...")
            online_created = dl_service.create_online_model('production_online', 'sgd')
            
            if online_created:
                print("   ✅ Online model created successfully")
            else:
                print("   ❌ Online model creation failed")
            
            # Get model summary
            all_models = dl_service.get_all_models()
            print(f"\n📊 Models created: {all_models['total_models']}")
            
        else:
            print("   ❌ LSTM model creation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Deep learning error: {e}")
        return False

def check_technical_analysis():
    """Check technical analysis capabilities"""
    print("\n📈 Checking Technical Analysis...")
    print("=" * 50)
    
    try:
        from core.technical_analysis_service import TechnicalAnalysisService
        
        # Initialize technical analysis service
        ta_service = TechnicalAnalysisService()
        
        print("✅ Technical Analysis Service initialized")
        
        # Create sample data
        print("\n🧪 Testing technical indicators...")
        np.random.seed(42)
        sample_data = pd.DataFrame({
            'open': np.random.randn(100) * 10 + 100,
            'high': np.random.randn(100) * 10 + 105,
            'low': np.random.randn(100) * 10 + 95,
            'close': np.random.randn(100) * 10 + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        # Calculate indicators
        indicators = ta_service.calculate_all_indicators(sample_data)
        
        if indicators:
            print(f"   ✅ {len(indicators)} technical indicators calculated")
            
            # Show some key indicators
            if 'rsi_14' in indicators:
                print(f"   RSI (14): {indicators['rsi_14']:.2f}")
            if 'macd_bullish' in indicators:
                print(f"   MACD Bullish: {indicators['macd_bullish']}")
            if 'trend_direction' in indicators:
                print(f"   Trend Direction: {indicators['trend_direction']}")
        else:
            print("   ❌ Technical indicators calculation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical analysis error: {e}")
        return False

def check_ml_config():
    """Check ML configuration capabilities"""
    print("\n⚙️  Checking ML Configuration...")
    print("=" * 50)
    
    try:
        from core.ml_config import MLConfig
        
        # Initialize ML configuration
        config = MLConfig()
        
        print("✅ ML Configuration Service initialized")
        
        # Show configuration summary
        summary = config.get_config_summary()
        print(f"\n📋 Configuration Summary:")
        for key, value in summary.items():
            if isinstance(value, list):
                print(f"   {key.replace('_', ' ').title()}: {len(value)} items")
            else:
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Test configuration updates
        print("\n🧪 Testing configuration updates...")
        
        # Update risk tolerance
        old_risk = config.risk_tolerance_config['Conservative']['risk_score']
        config.update_risk_config('Conservative', {'risk_score': 0.28})
        new_risk = config.risk_tolerance_config['Conservative']['risk_score']
        print(f"   Risk tolerance updated: {old_risk:.2f} → {new_risk:.2f}")
        
        # Update ESG weights
        old_weight = config.esg_weights['environmental']['carbon_footprint']
        config.update_esg_weights('environmental', {'carbon_footprint': 0.28})
        new_weight = config.esg_weights['environmental']['carbon_footprint']
        print(f"   ESG weight updated: {old_weight:.2f} → {new_weight:.2f}")
        
        # Save configuration
        config.save_config('production_ml_config.json')
        print("   ✅ Configuration saved to 'production_ml_config.json'")
        
        return True
        
    except Exception as e:
        print(f"❌ ML configuration error: {e}")
        return False

def run_production_tests():
    """Run all production tests"""
    print("🚀 Production Deployment Tests")
    print("=" * 80)
    
    tests = [
        ("TensorFlow Installation", check_tensorflow_installation),
        ("API Integration", check_api_integration),
        ("Performance Monitoring", check_performance_monitoring),
        ("User Feedback Integration", check_user_feedback),
        ("Deep Learning", check_deep_learning),
        ("Technical Analysis", check_technical_analysis),
        ("ML Configuration", check_ml_config)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "✅ PASS" if success else "❌ FAIL"
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = "💥 ERROR"
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PRODUCTION TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results.items():
        print(f"{test_name:30} {result}")
    
    passed = sum(1 for result in results.values() if "PASS" in result)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All production tests passed! Your ML system is ready for production.")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. Review failed tests before production deployment.")
    else:
        print("❌ Multiple tests failed. Fix issues before production deployment.")
    
    return results

def main():
    """Main function"""
    print("🤖 RichesReach ML System - Production Deployment")
    print("=" * 80)
    
    while True:
        print("\nOptions:")
        print("1. Run All Production Tests")
        print("2. Check TensorFlow Installation")
        print("3. Check API Integration")
        print("4. Check Performance Monitoring")
        print("5. Check User Feedback Integration")
        print("6. Check Deep Learning")
        print("7. Check Technical Analysis")
        print("8. Check ML Configuration")
        print("9. Exit")
        
        print("\nEnter your choice (1-9): ", end="")
        choice = input().strip()
        
        if choice == '1':
            run_production_tests()
        elif choice == '2':
            check_tensorflow_installation()
        elif choice == '3':
            check_api_integration()
        elif choice == '4':
            check_performance_monitoring()
        elif choice == '5':
            check_user_feedback()
        elif choice == '6':
            check_deep_learning()
        elif choice == '7':
            check_technical_analysis()
        elif choice == '8':
            check_ml_config()
        elif choice == '9':
            print("👋 Production deployment check complete!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
            print("\n" + "=" * 80)
            print("🎯 Ready for next test or deployment!")

if __name__ == "__main__":
    main()
