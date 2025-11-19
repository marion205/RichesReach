"""
Django management command to train the Week 2 hybrid ensemble model
Run: python manage.py train_hybrid_predictor
"""
from django.core.management.base import BaseCommand
import asyncio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train the Week 2 hybrid ensemble model (spending + options + earnings + insider)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lookback-months',
            type=int,
            default=36,
            help='Number of months of historical data to use (default: 36)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Training Week 2 Hybrid Ensemble Model'))
        self.stdout.write('=' * 80)
        
        lookback_months = options['lookback_months']
        
        # Run async training
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            from core.hybrid_ml_predictor import hybrid_predictor
            
            self.stdout.write(f'📊 Using {lookback_months} months of historical data')
            self.stdout.write('Training two-stage ensemble:')
            self.stdout.write('  Stage 1: Spending + Options + Earnings + Insider models')
            self.stdout.write('  Stage 2: LightGBM meta-learner')
            self.stdout.write('')
            self.stdout.write('This may take 10-20 minutes (fetching real options/earnings/insider data)...')
            
            results = loop.run_until_complete(
                hybrid_predictor.train_hybrid_model(lookback_months)
            )
            
            if 'error' in results:
                self.stdout.write(self.style.ERROR(f'❌ Error: {results["error"]}'))
                return
            
            self.stdout.write(self.style.SUCCESS('\n✅ Hybrid Model Training Complete!'))
            self.stdout.write('=' * 80)
            
            # Stage 1 scores
            self.stdout.write('\n📈 Stage 1 Model Performance:')
            for model_name, score in results.get('stage1_scores', {}).items():
                self.stdout.write(f'  {model_name.capitalize()} Model R²: {score:.4f}')
            
            # Meta-learner
            meta_r2 = results.get('meta_learner_r2')
            if meta_r2:
                self.stdout.write(f'\n🎯 Meta-Learner R²: {meta_r2:.4f}')
            
            # Feature groups
            self.stdout.write('\n🔢 Feature Groups:')
            for group, count in results.get('feature_groups', {}).items():
                self.stdout.write(f'  {group.capitalize()}: {count} features')
            
            self.stdout.write(f'\n📦 Total Training Samples: {results["n_samples"]}')
            self.stdout.write(f'📊 Total Features: {results["n_features"]}')
            
            if meta_r2 and meta_r2 > 0.12:
                self.stdout.write(self.style.SUCCESS('\n🎯 EXCELLENT! R² > 0.12 - Model is ready for production!'))
            elif meta_r2 and meta_r2 > 0.08:
                self.stdout.write(self.style.WARNING('\n⚠️  Good progress! R² > 0.08 - Continue improving'))
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  May need more data or feature engineering'))
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('Next Steps:')
            self.stdout.write('1. Model is automatically integrated into stock scoring')
            self.stdout.write('2. Add SHAP explainability (Week 3)')
            self.stdout.write('3. Create UI charts (Week 3)')
            self.stdout.write('4. Launch beta for premium users (Week 4)')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error training model: {e}'))
            import traceback
            traceback.print_exc()
        finally:
            loop.close()

