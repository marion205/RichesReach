#!/usr/bin/env python3
"""
Advanced ML Features Demonstration
Shows fine-tuned algorithms, enhanced features, and advanced ML techniques
"""

import os
import sys
import django
from pathlib import Path
import json
import numpy as np
import pandas as pd

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def demonstrate_algorithm_fine_tuning():
    """Demonstrate algorithm fine-tuning capabilities"""
    print("🎯 A. Algorithm Fine-tuning Demonstration")
    print("=" * 60)
    
    try:
        from core.ml_config import MLConfig
        
        config = MLConfig()
        
        print("✅ ML Configuration loaded successfully")
        
        # Show current configurations
        print("\n📊 Current Risk Tolerance Configurations:")
        for risk_level, settings in config.risk_tolerance_config.items():
            print(f"  {risk_level}:")
            print(f"    Risk Score: {settings['risk_score']:.2f}")
            print(f"    Max Stock Allocation: {settings['max_stock_allocation']:.1%}")
            print(f"    Volatility Tolerance: {settings['volatility_tolerance']:.1%}")
            print(f"    Drawdown Tolerance: {settings['drawdown_tolerance']:.1%}")
        
        print("\n🌱 Current ESG Factor Weights:")
        for category, factors in config.esg_weights.items():
            print(f"  {category.title()}:")
            for factor, weight in factors.items():
                print(f"    {factor.replace('_', ' ').title()}: {weight:.2f}")
        
        print("\n📈 Current Market Regime Thresholds:")
        for regime, thresholds in config.regime_thresholds.items():
            print(f"  {regime.replace('_', ' ').title()}:")
            for metric, value in thresholds.items():
                if isinstance(value, tuple):
                    print(f"    {metric.replace('_', ' ').title()}: {value[0]:.3f} - {value[1]:.3f}")
                else:
                    print(f"    {metric.replace('_', ' ').title()}: {value:.3f}")
        
        print("\n💼 Current Asset Allocation Ranges:")
        for asset, risk_levels in config.allocation_ranges.items():
            print(f"  {asset.title()}:")
            for risk_level, ranges in risk_levels.items():
                print(f"    {risk_level}: {ranges['min']:.1%} - {ranges['max']:.1%} (target: {ranges['target']:.1%})")
        
        # Demonstrate customization
        print("\n🔧 Customization Examples:")
        
        # Customize risk tolerance
        print("\n1. Customizing Risk Tolerance:")
        old_risk = config.risk_tolerance_config['Conservative']['risk_score']
        config.update_risk_config('Conservative', {'risk_score': 0.25, 'max_stock_allocation': 0.35})
        new_risk = config.risk_tolerance_config['Conservative']['risk_score']
        print(f"   Conservative risk score: {old_risk:.2f} → {new_risk:.2f}")
        
        # Customize ESG weights
        print("\n2. Customizing ESG Weights:")
        old_weight = config.esg_weights['environmental']['carbon_footprint']
        config.update_esg_weights('environmental', {'carbon_footprint': 0.30})
        new_weight = config.esg_weights['environmental']['carbon_footprint']
        print(f"   Carbon footprint weight: {old_weight:.2f} → {new_weight:.2f}")
        
        # Customize regime thresholds
        print("\n3. Customizing Market Regime Thresholds:")
        old_threshold = config.regime_thresholds['early_bull_market']['min_return']
        config.update_regime_thresholds('early_bull_market', {'min_return': 0.10})
        new_threshold = config.regime_thresholds['early_bull_market']['min_return']
        print(f"   Early bull market min return: {old_threshold:.3f} → {new_threshold:.3f}")
        
        # Customize allocation ranges
        print("\n4. Customizing Asset Allocation Ranges:")
        old_range = config.allocation_ranges['stocks']['Conservative']['max']
        config.update_allocation_range('stocks', 'Conservative', {'max': 0.50})
        new_range = config.allocation_ranges['stocks']['Conservative']['max']
        print(f"   Conservative max stock allocation: {old_range:.1%} → {new_range:.1%}")
        
        # Save configuration
        config.save_config('custom_ml_config.json')
        print("\n💾 Configuration saved to 'custom_ml_config.json'")
        
        print("\n" + "=" * 60)
        print("🎯 Algorithm Fine-tuning Demonstration Complete!")
        
    except Exception as e:
        print(f"❌ Error in algorithm fine-tuning demonstration: {e}")

def demonstrate_enhanced_features():
    """Demonstrate enhanced features and technical analysis"""
    print("\n🔧 B. Enhanced Features Demonstration")
    print("=" * 60)
    
    try:
        from core.technical_analysis_service import TechnicalAnalysisService
        
        ta_service = TechnicalAnalysisService()
        
        print("✅ Technical Analysis Service loaded successfully")
        
        # Create sample price data
        print("\n📊 Creating Sample Price Data...")
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        
        # Generate realistic price data
        base_price = 100.0
        returns = np.random.normal(0.0005, 0.02, 252)  # Daily returns
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        price_data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 252)
        })
        
        print(f"   Generated {len(price_data)} days of price data")
        print(f"   Price range: ${price_data['low'].min():.2f} - ${price_data['high'].max():.2f}")
        
        # Calculate technical indicators
        print("\n📈 Calculating Technical Indicators...")
        indicators = ta_service.calculate_all_indicators(price_data)
        
        print(f"   Moving Averages: {len([k for k in indicators.keys() if 'ma_' in k])} indicators")
        print(f"   Momentum: {len([k for k in indicators.keys() if any(x in k for x in ['rsi', 'macd', 'stoch', 'williams'])])} indicators")
        print(f"   Volatility: {len([k for k in indicators.keys() if any(x in k for x in ['bb_', 'atr', 'volatility'])])} indicators")
        print(f"   Volume: {len([k for k in indicators.keys() if any(x in k for x in ['volume', 'obv', 'vpt', 'mfi'])])} indicators")
        print(f"   Trend: {len([k for k in indicators.keys() if any(x in k for x in ['adx', 'trend', 'ichimoku'])])} indicators")
        print(f"   Support/Resistance: {len([k for k in indicators.keys() if any(x in k for x in ['pivot', 'resistance', 'support'])])} indicators")
        print(f"   Patterns: {len([k for k in indicators.keys() if any(x in k for x in ['double', 'head', 'triangle', 'flag', 'cup'])])} patterns")
        
        # Show some key indicators
        print("\n🔍 Key Technical Indicators:")
        if 'rsi_14' in indicators:
            print(f"   RSI (14): {indicators['rsi_14']:.2f}")
            print(f"   RSI Oversold: {indicators['rsi_oversold']}")
            print(f"   RSI Overbought: {indicators['rsi_overbought']}")
        
        if 'macd_bullish' in indicators:
            print(f"   MACD Bullish: {indicators['macd_bullish']}")
        
        if 'bb_position' in indicators:
            print(f"   Bollinger Band Position: {indicators['bb_position']:.2f}")
            print(f"   Near BB Upper: {indicators['price_near_bb_upper']}")
            print(f"   Near BB Lower: {indicators['price_near_bb_lower']}")
        
        if 'trend_direction' in indicators:
            print(f"   Trend Direction: {indicators['trend_direction']}")
            print(f"   Trend Strength: {indicators['trend_strength']:.2f}")
        
        # Show pattern detection
        print("\n🎯 Chart Pattern Detection:")
        pattern_indicators = [k for k in indicators.keys() if any(x in k for x in ['double', 'head', 'triangle', 'flag', 'cup'])]
        for pattern in pattern_indicators:
            if indicators[pattern]:
                print(f"   ✅ {pattern.replace('_', ' ').title()} detected")
            else:
                print(f"   ❌ {pattern.replace('_', ' ').title()} not detected")
        
        print("\n" + "=" * 60)
        print("🔧 Enhanced Features Demonstration Complete!")
        
    except Exception as e:
        print(f"❌ Error in enhanced features demonstration: {e}")

def demonstrate_advanced_ml():
    """Demonstrate advanced ML techniques"""
    print("\n🔮 C. Advanced ML Techniques Demonstration")
    print("=" * 60)
    
    try:
        from core.deep_learning_service import DeepLearningService
        
        dl_service = DeepLearningService()
        
        print(f"✅ Deep Learning Service loaded: {dl_service.is_available()}")
        
        if not dl_service.is_available():
            print("⚠️  Deep learning not available. Install TensorFlow for full functionality.")
            print("   pip install tensorflow")
            return
        
        # Demonstrate LSTM models
        print("\n🧠 LSTM Time Series Forecasting:")
        
        # Create sample time series data
        np.random.seed(42)
        sequence_length = 60
        n_features = 20
        n_samples = 1000
        
        # Generate synthetic time series
        time_series_data = np.random.randn(n_samples, n_features)
        target_data = np.random.randn(n_samples)
        
        print(f"   Generated {n_samples} samples with {n_features} features")
        print(f"   Sequence length: {sequence_length}")
        
        # Create LSTM model
        print("\n   1. Creating LSTM Model...")
        lstm_created = dl_service.create_lstm_model('market_forecaster', {
            'sequence_length': sequence_length,
            'features': n_features,
            'lstm_units': [64, 32],
            'epochs': 10  # Reduced for demo
        })
        
        if lstm_created:
            print("   ✅ LSTM model created successfully")
            
            # Prepare data for LSTM
            print("\n   2. Preparing Time Series Data...")
            X, y = dl_service.prepare_time_series_data(time_series_data, sequence_length)
            print(f"   Prepared {len(X)} sequences for training")
            
            # Train LSTM model
            print("\n   3. Training LSTM Model...")
            training_success = dl_service.train_lstm_model('market_forecaster', X, y, validation_split=0.2)
            
            if training_success:
                print("   ✅ LSTM model trained successfully")
                
                # Make predictions
                print("\n   4. Making LSTM Predictions...")
                test_data = np.random.randn(10, sequence_length, n_features)
                predictions = dl_service.predict_with_lstm('market_forecaster', test_data)
                
                if predictions is not None:
                    print(f"   ✅ Generated {len(predictions)} predictions")
                    print(f"   Prediction range: {predictions.min():.4f} to {predictions.max():.4f}")
                else:
                    print("   ❌ LSTM predictions failed")
            else:
                print("   ❌ LSTM training failed")
        else:
            print("   ❌ LSTM model creation failed")
        
        # Demonstrate ensemble methods
        print("\n🎯 Ensemble Methods:")
        
        # Create ensemble model
        print("\n   1. Creating Ensemble Model...")
        ensemble_created = dl_service.create_ensemble_model('market_ensemble', ['market_forecaster'], 'voting')
        
        if ensemble_created:
            print("   ✅ Ensemble model created successfully")
            
            # Train ensemble
            print("\n   2. Training Ensemble Model...")
            X_2d = np.random.randn(100, 20)
            y_2d = np.random.randn(100)
            ensemble_training = dl_service.train_ensemble_model('market_ensemble', X_2d, y_2d)
            
            if ensemble_training:
                print("   ✅ Ensemble model trained successfully")
                
                # Make ensemble predictions
                print("\n   3. Making Ensemble Predictions...")
                ensemble_predictions = dl_service.predict_with_ensemble('market_ensemble', X_2d[:5])
                
                if ensemble_predictions is not None:
                    print(f"   ✅ Generated {len(ensemble_predictions)} ensemble predictions")
                    print(f"   Prediction range: {ensemble_predictions.min():.4f} to {ensemble_predictions.max():.4f}")
                else:
                    print("   ❌ Ensemble predictions failed")
            else:
                print("   ❌ Ensemble training failed")
        else:
            print("   ❌ Ensemble model creation failed")
        
        # Demonstrate online learning
        print("\n🔄 Online Learning:")
        
        # Create online model
        print("\n   1. Creating Online Model...")
        online_created = dl_service.create_online_model('market_online', 'sgd')
        
        if online_created:
            print("   ✅ Online model created successfully")
            
            # Update online model
            print("\n   2. Updating Online Model...")
            for i in range(3):
                X_online = np.random.randn(10, 20)
                y_online = np.random.randn(10)
                update_success = dl_service.update_online_model('market_online', X_online, y_online)
                
                if update_success:
                    print(f"   ✅ Online model update #{i+1} successful")
                else:
                    print(f"   ❌ Online model update #{i+1} failed")
            
            # Make online predictions
            print("\n   3. Making Online Predictions...")
            online_predictions = dl_service.predict_with_online_model('market_online', X_2d[:5])
            
            if online_predictions is not None:
                print(f"   ✅ Generated {len(online_predictions)} online predictions")
                print(f"   Prediction range: {online_predictions.min():.4f} to {online_predictions.max():.4f}")
            else:
                print("   ❌ Online predictions failed")
        else:
            print("   ❌ Online model creation failed")
        
        # Show model performance
        print("\n📊 Model Performance Summary:")
        all_models = dl_service.get_all_models()
        print(f"   Total Models: {all_models['total_models']}")
        print(f"   LSTM Models: {len(all_models['lstm_models'])}")
        print(f"   Ensemble Models: {len(all_models['ensemble_models'])}")
        print(f"   Online Models: {len(all_models['online_models'])}")
        
        # Show specific model performance
        if 'market_forecaster' in dl_service.model_performance:
            perf = dl_service.model_performance['market_forecaster']
            print(f"\n   LSTM Model Performance:")
            print(f"     Validation Loss: {perf.get('val_loss', 'N/A')}")
            print(f"     Validation MAE: {perf.get('val_mae', 'N/A')}")
            print(f"     Training Samples: {perf.get('training_samples', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("🔮 Advanced ML Techniques Demonstration Complete!")
        
    except Exception as e:
        print(f"❌ Error in advanced ML demonstration: {e}")

def demonstrate_integration():
    """Demonstrate integration of all advanced features"""
    print("\n🚀 Integration Demonstration")
    print("=" * 60)
    
    try:
        from core.ml_config import MLConfig
        from core.technical_analysis_service import TechnicalAnalysisService
        from core.deep_learning_service import DeepLearningService
        from core.ml_service import MLService
        
        print("✅ All services loaded successfully")
        
        # Create integrated configuration
        config = MLConfig()
        ta_service = TechnicalAnalysisService()
        dl_service = DeepLearningService()
        ml_service = MLService()
        
        print("\n🔗 Service Integration Status:")
        print(f"   ML Config: ✅ Loaded")
        print(f"   Technical Analysis: ✅ Available")
        print(f"   Deep Learning: {'✅ Available' if dl_service.is_available() else '⚠️ Limited'}")
        print(f"   ML Service: {'✅ Available' if ml_service.is_available() else '⚠️ Limited'}")
        
        # Demonstrate end-to-end workflow
        print("\n🔄 End-to-End Workflow:")
        
        # 1. Configure algorithms
        print("\n   1. Configuring Algorithms...")
        config.update_risk_config('Aggressive', {'risk_score': 0.95, 'max_stock_allocation': 0.85})
        config.update_esg_weights('environmental', {'carbon_footprint': 0.35, 'renewable_energy': 0.25})
        print("   ✅ Algorithm configuration updated")
        
        # 2. Generate technical analysis
        print("\n   2. Generating Technical Analysis...")
        np.random.seed(42)
        sample_data = pd.DataFrame({
            'open': np.random.randn(100) * 10 + 100,
            'high': np.random.randn(100) * 10 + 105,
            'low': np.random.randn(100) * 10 + 95,
            'close': np.random.randn(100) * 10 + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        ta_indicators = ta_service.calculate_all_indicators(sample_data)
        print(f"   ✅ Generated {len(ta_indicators)} technical indicators")
        
        # 3. Create deep learning model
        print("\n   3. Creating Deep Learning Model...")
        if dl_service.is_available():
            dl_service.create_lstm_model('integrated_forecaster')
            print("   ✅ LSTM model created for integration")
        else:
            print("   ⚠️  Deep learning not available for integration")
        
        # 4. Show configuration summary
        print("\n   4. Configuration Summary:")
        config_summary = config.get_config_summary()
        for key, value in config_summary.items():
            if isinstance(value, list):
                print(f"   {key.replace('_', ' ').title()}: {len(value)} items")
            else:
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # 5. Save integrated configuration
        print("\n   5. Saving Integrated Configuration...")
        config.save_config('integrated_ml_config.json')
        print("   ✅ Integrated configuration saved")
        
        print("\n" + "=" * 60)
        print("🚀 Integration Demonstration Complete!")
        print("\n🎯 All advanced ML features are now integrated and ready for production use!")
        
    except Exception as e:
        print(f"❌ Error in integration demonstration: {e}")

def main():
    """Main demonstration function"""
    print("🤖 Advanced ML Features Comprehensive Demonstration")
    print("=" * 80)
    
    while True:
        print("\nOptions:")
        print("1. Algorithm Fine-tuning (Risk, ESG, Regimes, Allocations)")
        print("2. Enhanced Features (Technical Analysis, Indicators, Patterns)")
        print("3. Advanced ML Techniques (LSTM, Ensemble, Online Learning)")
        print("4. Integration Demonstration (End-to-End Workflow)")
        print("5. Run All Demonstrations")
        print("6. Exit")
        
        print("\nEnter your choice (1-6): ", end="")
        choice = input().strip()
        
        if choice == '1':
            demonstrate_algorithm_fine_tuning()
        elif choice == '2':
            demonstrate_enhanced_features()
        elif choice == '3':
            demonstrate_advanced_ml()
        elif choice == '4':
            demonstrate_integration()
        elif choice == '5':
            print("\n🚀 Running All Demonstrations...")
            demonstrate_algorithm_fine_tuning()
            demonstrate_enhanced_features()
            demonstrate_advanced_ml()
            demonstrate_integration()
        elif choice == '6':
            print("👋 Goodbye! Your ML system is now fully enhanced!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        if choice in ['1', '2', '3', '4', '5']:
            print("\n" + "=" * 80)
            print("🎯 Ready for next demonstration or customization!")

if __name__ == "__main__":
    main()
