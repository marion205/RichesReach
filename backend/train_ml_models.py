#!/usr/bin/env python3
"""
ML Model Training Script for RichesReach
Trains machine learning models with real market data for swing trading signals
"""

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import joblib
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import OHLCV, Signal
from core.swing_trading.ml_scoring import SwingTradingML
from core.swing_trading.indicators import TechnicalIndicators
from django.db import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLModelTrainer:
    """Train ML models for swing trading signal generation"""
    
    def __init__(self, model_dir="ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.ml_system = SwingTradingML(model_dir=str(self.model_dir))
        self.ti = TechnicalIndicators()
        
    def prepare_training_data(self, symbols=None, min_records=100):
        """Prepare training data from OHLCV records"""
        logger.info("Preparing training data...")
        
        if symbols is None:
            # Get all symbols with sufficient data
            symbol_counts = OHLCV.objects.values('symbol').annotate(
                count=models.Count('id')
            ).filter(count__gte=min_records, timeframe='1d')
            symbols = [item['symbol'] for item in symbol_counts]
        
        logger.info(f"Training on symbols: {symbols}")
        
        all_data = []
        for symbol in symbols:
            logger.info(f"Processing {symbol}...")
            
            # Get OHLCV data
            ohlcv_records = OHLCV.objects.filter(
                symbol=symbol,
                timeframe='1d'
            ).order_by('timestamp')
            
            if ohlcv_records.count() < min_records:
                logger.warning(f"Insufficient data for {symbol}: {ohlcv_records.count()} records")
                continue
            
            # Convert to DataFrame
            df_data = []
            for record in ohlcv_records:
                df_data.append({
                    'timestamp': record.timestamp,
                    'open': float(record.open_price),
                    'high': float(record.high_price),
                    'low': float(record.low_price),
                    'close': float(record.close_price),
                    'volume': record.volume,
                    'ema_12': float(record.ema_12) if record.ema_12 else None,
                    'ema_26': float(record.ema_26) if record.ema_26 else None,
                    'rsi_14': float(record.rsi_14) if record.rsi_14 else None,
                    'atr_14': float(record.atr_14) if record.atr_14 else None,
                    'volume_sma_20': record.volume_sma_20 if record.volume_sma_20 else None,
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Add symbol column
            df['symbol'] = symbol
            
            all_data.append(df)
        
        if not all_data:
            logger.error("No training data available")
            return None
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=False)
        combined_df.sort_index(inplace=True)
        
        logger.info(f"Combined training data: {len(combined_df)} records from {len(symbols)} symbols")
        return combined_df
    
    def train_models(self, df):
        """Train ML models with the prepared data"""
        logger.info("Training ML models...")
        
        try:
            # Train the ML system
            self.ml_system.train(df)
            
            # Save model artifacts
            self.save_model_artifacts()
            
            logger.info("ML models trained successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def save_model_artifacts(self):
        """Save trained model artifacts"""
        logger.info("Saving model artifacts...")
        
        try:
            # Save the ML system
            model_path = self.model_dir / "swing_trading_ml.pkl"
            joblib.dump(self.ml_system, model_path)
            
            # Save feature schema
            if self.ml_system._schema:
                schema_path = self.model_dir / "feature_schema.json"
                import json
                with open(schema_path, 'w') as f:
                    json.dump({
                        'feature_names': self.ml_system._schema.feature_names,
                        'lookforward_days': self.ml_system._schema.lookforward_days,
                        'long_profit_threshold': self.ml_system._schema.long_profit_threshold,
                        'short_profit_threshold': self.ml_system._schema.short_profit_threshold,
                    }, f, indent=2)
            
            # Save model reports
            if self.ml_system._reports:
                reports_path = self.model_dir / "model_reports.json"
                import json
                reports_data = {}
                for name, report in self.ml_system._reports.items():
                    reports_data[name] = {
                        'accuracy': report.accuracy,
                        'precision': report.precision,
                        'recall': report.recall,
                        'f1': report.f1,
                        'roc_auc': report.roc_auc,
                    }
                
                with open(reports_path, 'w') as f:
                    json.dump(reports_data, f, indent=2)
            
            logger.info("Model artifacts saved successfully!")
            
        except Exception as e:
            logger.error(f"Error saving model artifacts: {e}")
    
    def test_model_prediction(self, symbol='AAPL'):
        """Test model prediction on a sample symbol"""
        logger.info(f"Testing model prediction on {symbol}...")
        
        try:
            # Get recent data for the symbol
            recent_data = OHLCV.objects.filter(
                symbol=symbol,
                timeframe='1d'
            ).order_by('-timestamp')[:50]
            
            if recent_data.count() < 50:
                logger.warning(f"Insufficient recent data for {symbol}")
                return None
            
            # Convert to DataFrame
            df_data = []
            for record in recent_data:
                df_data.append({
                    'timestamp': record.timestamp,
                    'open': float(record.open_price),
                    'high': float(record.high_price),
                    'low': float(record.low_price),
                    'close': float(record.close_price),
                    'volume': record.volume,
                    'ema_12': float(record.ema_12) if record.ema_12 else None,
                    'ema_26': float(record.ema_26) if record.ema_26 else None,
                    'rsi_14': float(record.rsi_14) if record.rsi_14 else None,
                    'atr_14': float(record.atr_14) if record.atr_14 else None,
                    'volume_sma_20': record.volume_sma_20 if record.volume_sma_20 else None,
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Test prediction
            features = self.ml_system.extract_features(df)
            feature_row = features.iloc[-1].to_dict()
            proba = self.ml_system.predict_proba_row(feature_row)
            score = proba.get('positive', 0.5)
            thesis = f"ML prediction with {score:.3f} confidence"
            
            logger.info(f"Prediction for {symbol}: Score={score:.3f}, Thesis='{thesis}'")
            return score, thesis
            
        except Exception as e:
            logger.error(f"Error testing model prediction: {e}")
            return None
    
    def generate_sample_signals(self, symbols=None, min_score=0.6):
        """Generate sample trading signals using trained models"""
        logger.info("Generating sample trading signals...")
        
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
        signals_created = 0
        
        for symbol in symbols:
            try:
                # Get recent data
                recent_data = OHLCV.objects.filter(
                    symbol=symbol,
                    timeframe='1d'
                ).order_by('-timestamp')[:100]
                
                if recent_data.count() < 50:
                    continue
                
                # Convert to DataFrame
                df_data = []
                for record in recent_data:
                    df_data.append({
                        'timestamp': record.timestamp,
                        'open': float(record.open_price),
                        'high': float(record.high_price),
                        'low': float(record.low_price),
                        'close': float(record.close_price),
                        'volume': record.volume,
                        'ema_12': float(record.ema_12) if record.ema_12 else None,
                        'ema_26': float(record.ema_26) if record.ema_26 else None,
                        'rsi_14': float(record.rsi_14) if record.rsi_14 else None,
                        'atr_14': float(record.atr_14) if record.atr_14 else None,
                        'volume_sma_20': record.volume_sma_20 if record.volume_sma_20 else None,
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
                # Get the latest record
                latest = df.iloc[-1]
                
                # Generate prediction
                features = self.ml_system.extract_features(df)
                feature_row = features.iloc[-1].to_dict()
                proba = self.ml_system.predict_proba_row(feature_row)
                score = proba.get('positive', 0.5)
                thesis = f"ML prediction with {score:.3f} confidence"
                
                if score >= min_score:
                    # Create signal
                    signal = Signal.objects.create(
                        symbol=symbol,
                        timeframe='1d',
                        triggered_at=latest.name,
                        signal_type='ml_generated',
                        features={
                            'rsi_14': float(latest.rsi_14) if latest.rsi_14 else 0,
                            'ema_12': float(latest.ema_12) if latest.ema_12 else 0,
                            'ema_26': float(latest.ema_26) if latest.ema_26 else 0,
                            'atr_14': float(latest.atr_14) if latest.atr_14 else 0,
                            'volume_surge': float(latest.volume) / float(latest.volume_sma_20) if latest.volume_sma_20 else 1.0,
                        },
                        ml_score=score,
                        thesis=thesis,
                        entry_price=latest.close,
                        stop_price=latest.close * 0.95,  # 5% stop
                        target_price=latest.close * 1.10,  # 10% target
                        is_active=True
                    )
                    signals_created += 1
                    logger.info(f"Created signal for {symbol}: Score={score:.3f}")
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        logger.info(f"Generated {signals_created} trading signals")
        return signals_created

def main():
    """Main function to train ML models"""
    print("🤖 ML Model Training for RichesReach")
    print("=" * 50)
    
    # Create trainer
    trainer = MLModelTrainer()
    
    # Prepare training data
    print("📊 Preparing training data...")
    df = trainer.prepare_training_data()
    
    if df is None:
        print("❌ No training data available")
        return
    
    print(f"✅ Training data prepared: {len(df)} records")
    
    # Train models
    print("🧠 Training ML models...")
    success = trainer.train_models(df)
    
    if not success:
        print("❌ Model training failed")
        return
    
    print("✅ ML models trained successfully!")
    
    # Test model prediction
    print("🔍 Testing model prediction...")
    result = trainer.test_model_prediction('AAPL')
    
    if result:
        score, thesis = result
        print(f"✅ Test prediction: Score={score:.3f}, Thesis='{thesis}'")
    else:
        print("❌ Model prediction test failed")
    
    # Generate sample signals
    print("📡 Generating sample trading signals...")
    signals_created = trainer.generate_sample_signals()
    
    print(f"✅ Generated {signals_created} sample trading signals")
    
    # Summary
    print("\n🎉 ML Model Training Complete!")
    print("=" * 50)
    print("✅ Models trained with real market data")
    print("✅ Model artifacts saved")
    print("✅ Sample signals generated")
    print("\n🚀 Your ML-powered swing trading system is ready!")
    print("\nNext steps:")
    print("- Use the trained models for signal generation")
    print("- Run backtests with ML-generated signals")
    print("- Monitor model performance and retrain as needed")

if __name__ == "__main__":
    main()
