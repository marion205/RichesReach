"""
Management command to retrain day trading ML model from historical performance data.
Run this daily/weekly to keep the model learning from recent outcomes.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Retrain day trading ML model from historical signal performance data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of history to use for training (default: 30)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retraining even if recently trained (use for first-time bootstrap)'
        )

    def handle(self, *args, **options):
        days_back = options['days']
        force = options['force']
        
        self.stdout.write(f"🔄 Retraining day trading ML model (last {days_back} days)...")
        
        try:
            from core.day_trading_ml_learner import get_day_trading_ml_learner
            
            learner = get_day_trading_ml_learner()
            result = learner.train_model(days_back=days_back, force_retrain=force)
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f"❌ Training failed: {result['error']}"))
                if 'records' in result:
                    self.stdout.write(f"   Available records: {result['records']}")
                    self.stdout.write(f"   Need at least 50 records with performance data")
                return
            
            if 'message' in result and 'Skipped' in result['message']:
                self.stdout.write(self.style.WARNING(f"⏭️ {result['message']}"))
                if 'hours_ago' in result:
                    self.stdout.write(f"   Last trained {result['hours_ago']:.1f} hours ago")
                return
            
            # Success
            self.stdout.write(self.style.SUCCESS(f"✅ Model retrained successfully!"))
            self.stdout.write(f"   Records used: {result.get('records_used', 0)}")
            self.stdout.write(f"   Train score: {result.get('train_score', 0):.3f}")
            self.stdout.write(f"   Test score: {result.get('test_score', 0):.3f}")
            self.stdout.write(f"   Success rate: {result.get('success_rate', 0):.1%}")
            
            if result.get('overfit_detected'):
                self.stdout.write(self.style.WARNING(f"⚠️ Overfit detected (delta: {result.get('overfit_delta', 0):.3f})"))
                self.stdout.write(f"   Model reverted to previous version")
            
            # Show top features (what it learned)
            if 'feature_importances' in result:
                top_features = sorted(
                    result['feature_importances'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                self.stdout.write(f"\n🧠 Top 10 patterns learned:")
                for i, (feat, importance) in enumerate(top_features, 1):
                    self.stdout.write(f"   {i:2d}. {feat:30s} {importance:.4f}")
            
            self.stdout.write(f"\n💡 The model is now using these patterns to score new picks!")
            self.stdout.write(f"   Next picks will be enhanced with learned insights.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            logger.exception("Error retraining day trading ML model")
