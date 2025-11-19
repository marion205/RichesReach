"""
Django management command to train the spending-based predictive model
Run: python manage.py train_spending_predictor
"""
from django.core.management.base import BaseCommand
import asyncio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train the spending-based predictive model (Week 1 baseline)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lookback-months',
            type=int,
            default=36,
            help='Number of months of historical data to use (default: 36)'
        )
        parser.add_argument(
            '--min-transactions',
            type=int,
            default=1000,
            help='Minimum number of transactions required (default: 1000)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Training Spending-Based Predictive Model'))
        self.stdout.write('=' * 80)
        
        lookback_months = options['lookback_months']
        min_transactions = options['min_transactions']
        
        # Run async training
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            from core.spending_trend_predictor import spending_predictor
            
            self.stdout.write(f'📊 Using {lookback_months} months of historical data')
            self.stdout.write('Training baseline XGBoost model with spending features only...')
            
            results = loop.run_until_complete(
                spending_predictor.train_baseline_model(lookback_months)
            )
            
            if 'error' in results:
                self.stdout.write(self.style.ERROR(f'❌ Error: {results["error"]}'))
                return
            
            self.stdout.write(self.style.SUCCESS('\n✅ Model Training Complete!'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'📈 Cross-Validation R²: {results["cv_r2"]:.4f}')
            self.stdout.write(f'📉 RMSE: {results["cv_rmse"]:.4f}')
            self.stdout.write(f'📊 MAE: {results["cv_mae"]:.4f}')
            self.stdout.write(f'🔢 Features: {results["n_features"]}')
            self.stdout.write(f'📦 Training Samples: {results["n_samples"]}')
            
            if results["cv_r2"] > 0.12:
                self.stdout.write(self.style.SUCCESS('\n🎯 EXCELLENT! R² > 0.12 - Model is ready for production!'))
            elif results["cv_r2"] > 0.05:
                self.stdout.write(self.style.WARNING('\n⚠️  Good start! R² > 0.05 - Continue improving with more data'))
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  Low R² - May need more transaction data or feature engineering'))
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('Next Steps:')
            self.stdout.write('1. Review feature importance')
            self.stdout.write('2. Integrate into stock scoring (already done in ml_service.py)')
            self.stdout.write('3. Add options flow features (Week 2)')
            self.stdout.write('4. Add SHAP explainability (Week 3)')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error training model: {e}'))
            import traceback
            traceback.print_exc()
        finally:
            loop.close()

