"""
Convert Models to ONNX Format
Convert LSTM and XGBoost models to ONNX for faster inference.
"""
from django.core.management.base import BaseCommand
from core.model_optimization import get_model_optimizer
import os


class Command(BaseCommand):
    help = 'Convert models to ONNX format for faster inference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lstm-model',
            type=str,
            help='Path to LSTM model (Keras .h5 file)'
        )
        parser.add_argument(
            '--xgboost-model',
            type=str,
            help='Path to XGBoost model (.pkl or .json file)'
        )
        parser.add_argument(
            '--n-features',
            type=int,
            default=20,
            help='Number of input features for XGBoost (default: 20)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Convert all available models'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 Model Optimization: Converting to ONNX")
        self.stdout.write("=" * 60)
        
        optimizer = get_model_optimizer()
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        success_count = 0
        
        # Convert LSTM if specified or --all
        if options['all'] or options.get('lstm_model'):
            lstm_path = options.get('lstm_model')
            if not lstm_path and options['all']:
                # Try to find default LSTM model
                default_lstm = os.path.join(models_dir, 'lstm_extractor_model.h5')
                if os.path.exists(default_lstm):
                    lstm_path = default_lstm
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  LSTM model not found. Specify --lstm-model")
                    )
            
            if lstm_path:
                if os.path.exists(lstm_path):
                    self.stdout.write(f"\n📦 Converting LSTM model: {lstm_path}")
                    success = optimizer.convert_lstm_to_onnx(lstm_path)
                    if success:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS("   ✅ LSTM converted to ONNX")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR("   ❌ LSTM conversion failed")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ LSTM model not found: {lstm_path}")
                    )
        
        # Convert XGBoost if specified or --all
        if options['all'] or options.get('xgboost_model'):
            xgb_path = options.get('xgboost_model')
            if not xgb_path and options['all']:
                # Try to find default XGBoost model
                default_xgb = os.path.join(models_dir, 'xgboost_model.pkl')
                if os.path.exists(default_xgb):
                    xgb_path = default_xgb
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  XGBoost model not found. Specify --xgboost-model")
                    )
            
            if xgb_path:
                if os.path.exists(xgb_path):
                    self.stdout.write(f"\n📦 Converting XGBoost model: {xgb_path}")
                    success = optimizer.convert_xgboost_to_onnx(
                        xgb_path,
                        n_features=options['n_features']
                    )
                    if success:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS("   ✅ XGBoost converted to ONNX")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR("   ❌ XGBoost conversion failed")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ XGBoost model not found: {xgb_path}")
                    )
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully converted {success_count} model(s) to ONNX")
            )
            self.stdout.write("\n💡 Next steps:")
            self.stdout.write("   1. Test ONNX models: python manage.py activate_speed_optimizations --check-only")
            self.stdout.write("   2. Models will be automatically used if available")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  No models converted. Check paths and dependencies.")
            )
            self.stdout.write("\n📋 Dependencies:")
            self.stdout.write("   pip install onnx onnxruntime tf2onnx onnxmltools")

