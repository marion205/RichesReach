"""
Train Ensemble Model
Trains the ensemble predictor (LSTM + XGBoost + Random Forest) with collected data.
"""
from django.core.management.base import BaseCommand
from core.ensemble_predictor import get_ensemble_predictor
from core.lstm_feature_extractor import get_lstm_feature_extractor
from core.hybrid_lstm_xgboost_trainer import get_hybrid_trainer
from core.enhanced_alternative_data_service import get_enhanced_alternative_data_service
import os
import pandas as pd
import numpy as np
from pathlib import Path
import asyncio


class Command(BaseCommand):
    help = 'Train ensemble model (LSTM + XGBoost + Random Forest)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['SPY', 'AAPL', 'MSFT', 'GOOGL'],
            help='Symbols to train on (default: SPY AAPL MSFT GOOGL)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=730,
            help='Days of historical data (default: 730)'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='training_data/price_data',
            help='Directory with training data (default: training_data/price_data)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🤖 Training Ensemble Model")
        self.stdout.write("=" * 60)
        
        symbols = options['symbols']
        days = options['days']
        data_dir = options['data_dir']
        
        self.stdout.write(f"\n📊 Configuration:")
        self.stdout.write(f"   Symbols: {', '.join(symbols)}")
        self.stdout.write(f"   Days: {days}")
        self.stdout.write(f"   Data Directory: {data_dir}")
        
        # Get services
        ensemble_predictor = get_ensemble_predictor()
        lstm_extractor = get_lstm_feature_extractor()
        hybrid_trainer = get_hybrid_trainer()
        enhanced_alt_data = get_enhanced_alternative_data_service()
        
        # Step 1: Load training data
        self.stdout.write(f"\n📂 Loading training data...")
        training_data = self._load_training_data(data_dir, symbols)
        
        if training_data is None or training_data.empty:
            self.stdout.write(self.style.ERROR("❌ No training data found!"))
            self.stdout.write("   Run: python manage.py collect_training_data --symbols SPY AAPL MSFT GOOGL --days 730")
            return
        
        self.stdout.write(f"   ✅ Loaded {len(training_data)} samples")
        
        # Step 2: Prepare features
        self.stdout.write(f"\n🔧 Preparing features...")
        
        # Run async preparation
        async def prepare_features():
            # Get LSTM features
            lstm_features_list = []
            alt_data_features_list = []
            technical_features_list = []
            targets = []
            
            for idx, row in training_data.iterrows():
                symbol = row.get('symbol', 'SPY')
                
                # LSTM features (temporal momentum)
                try:
                    # Use price sequence for LSTM
                    price_seq = row.get('price_sequence', [])
                    if price_seq and len(price_seq) > 0:
                        lstm_feat = np.mean(price_seq[-60:]) if len(price_seq) >= 60 else np.mean(price_seq)
                    else:
                        lstm_feat = 0.0
                except:
                    lstm_feat = 0.0
                
                # Alternative data features (use defaults to avoid slow API calls)
                # Skip live API calls during training - use default features
                alt_data_features_list.append({
                    'social_sentiment': 0.0,
                    'social_volume': 0.0,
                    'unusual_volume_pct': 0.0,
                    'call_bias': 0.5,
                    'put_call_ratio': 1.0,
                })
                
                # Technical features (simplified)
                technical_features = {
                    'rsi': row.get('rsi', 50.0),
                    'sma_ratio': row.get('sma_ratio', 1.0),
                    'volume_ratio': row.get('volume_ratio', 1.0),
                }
                technical_features_list.append(technical_features)
                
                # Target (1 = buy, 0 = sell/abstain)
                target = 1 if row.get('return', 0) > 0.001 else 0  # 0.1% threshold
                targets.append(target)
                
                lstm_features_list.append(lstm_feat)
            
            return lstm_features_list, alt_data_features_list, technical_features_list, targets
        
        # Run async preparation
        try:
            lstm_features, alt_data_features, technical_features, targets = asyncio.run(prepare_features())
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error preparing features: {e}"))
            return
        
        self.stdout.write(f"   ✅ Prepared features for {len(targets)} samples")
        
        # Step 3: Convert to arrays
        self.stdout.write(f"\n🔄 Converting to arrays...")
        
        # Convert alt data to array
        if alt_data_features:
            # Get all unique keys
            all_keys = set()
            for feat_dict in alt_data_features:
                all_keys.update(feat_dict.keys())
            
            # Create DataFrame
            alt_data_df = pd.DataFrame(alt_data_features)
            alt_data_array = alt_data_df.values
        else:
            alt_data_array = np.zeros((len(targets), 10))  # Default size
        
        # Convert technical features to array
        technical_df = pd.DataFrame(technical_features)
        technical_array = technical_df.values
        
        # Convert LSTM features
        lstm_array = np.array(lstm_features).reshape(-1, 1)
        
        # Combine all features
        X_combined = np.hstack([lstm_array, alt_data_array, technical_array])
        y = np.array(targets)
        
        self.stdout.write(f"   ✅ Combined features: {X_combined.shape}")
        
        # Step 4: Train ensemble
        self.stdout.write(f"\n🎓 Training ensemble model...")
        
        try:
            results = ensemble_predictor.train_ensemble(
                X_lstm=lstm_array,
                X_alt_data=pd.DataFrame(alt_data_array),
                X_technical=pd.DataFrame(technical_array),
                y=y
            )
            
            self.stdout.write(self.style.SUCCESS("\n✅ Ensemble training complete!"))
            self.stdout.write(f"\n📊 Results:")
            self.stdout.write(f"   XGBoost Accuracy: {results.get('xgb_accuracy', 0):.3f}")
            self.stdout.write(f"   Random Forest Accuracy: {results.get('rf_accuracy', 0):.3f}")
            self.stdout.write(f"   Ensemble Accuracy: {results.get('ensemble_accuracy', 0):.3f}")
            self.stdout.write(f"   Ensemble F1: {results.get('ensemble_f1', 0):.3f}")
            self.stdout.write(f"\n📈 Model Weights:")
            weights = results.get('model_weights', {})
            for model, weight in weights.items():
                self.stdout.write(f"   {model}: {weight:.2%}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Training failed: {e}"))
            import traceback
            traceback.print_exc()
            return
        
        self.stdout.write(self.style.SUCCESS("\n✅ Ensemble model trained and ready!"))
        self.stdout.write("   The model will be used automatically in live inference.")

    def _load_training_data(self, data_dir: str, symbols: list) -> pd.DataFrame:
        """Load training data from CSV files"""
        try:
            data_path = Path(data_dir)
            if not data_path.exists():
                return None
            
            all_data = []
            for symbol in symbols:
                # Try multiple filename patterns
                patterns = [
                    f"{symbol}_price_data.csv",
                    f"{symbol}_1min_*.csv",  # Pattern with timestamp
                    f"{symbol}.csv"
                ]
                
                found = False
                for pattern in patterns:
                    if '*' in pattern:
                        # Glob pattern
                        matches = list(data_path.glob(pattern))
                        if matches:
                            csv_file = matches[0]  # Use first match
                        else:
                            continue
                    else:
                        csv_file = data_path / pattern
                    
                    if csv_file.exists():
                        df = pd.read_csv(csv_file)
                        df['symbol'] = symbol
                        all_data.append(df)
                        found = True
                        break
                
                if not found:
                    self.stdout.write(self.style.WARNING(f"   ⚠️  No data file found for {symbol}"))
            
            if not all_data:
                return None
            
            combined = pd.concat(all_data, ignore_index=True)
            return combined
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error loading training data: {e}"))
            return None

