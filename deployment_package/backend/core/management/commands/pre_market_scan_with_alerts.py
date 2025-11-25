"""
Django management command to run pre-market scanner with alerts and ML
Usage: python manage.py pre_market_scan_with_alerts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.pre_market_scanner import PreMarketScanner
from core.pre_market_ml_learner import get_ml_learner
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scan pre-market movers, enhance with ML, and send alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='AGGRESSIVE',
            choices=['SAFE', 'AGGRESSIVE'],
            help='Trading mode (SAFE or AGGRESSIVE)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of setups to return'
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send email alert'
        )
        parser.add_argument(
            '--send-push',
            action='store_true',
            help='Send push notification'
        )
        parser.add_argument(
            '--train-ml',
            action='store_true',
            help='Train ML model on historical data'
        )
        parser.add_argument(
            '--ml-insights',
            action='store_true',
            help='Show ML learning insights'
        )

    def handle(self, *args, **options):
        mode = options['mode']
        limit = options['limit']
        send_email = options.get('send_email', False)
        send_push = options.get('send_push', False)
        train_ml = options.get('train_ml', False)
        ml_insights = options.get('ml_insights', False)
        
        scanner = PreMarketScanner()
        
        # Check if we're in pre-market hours
        if not scanner.is_pre_market_hours():
            et_hour = scanner._get_et_hour()
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Not in pre-market hours (current ET hour: {et_hour})"
                )
            )
            self.stdout.write("Pre-market hours: 4:00 AM - 9:30 AM ET")
            
            # Still allow ML training/insights outside pre-market hours
            if train_ml or ml_insights:
                pass  # Continue to ML section
            else:
                return
        
        # Train ML model if requested
        if train_ml:
            self.stdout.write(self.style.SUCCESS("🤖 Training ML model on historical data..."))
            ml_learner = get_ml_learner()
            metrics = ml_learner.train_model()
            
            if 'error' in metrics:
                if metrics.get('error') == 'overfit_detected':
                    self.stdout.write(
                        self.style.ERROR("🚨 OVERFIT DETECTED - Model reverted to previous version")
                    )
                    self.stdout.write(f"   Train Score: {metrics.get('train_score', 0):.3f}")
                    self.stdout.write(f"   Test Score: {metrics.get('test_score', 0):.3f}")
                    self.stdout.write(f"   Delta: {metrics.get('delta', 0):.3f} (> 0.20 threshold)")
                    self.stdout.write("   ⚠️  Emergency alert should be sent!")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ ML training failed: {metrics['error']}")
                    )
            else:
                self.stdout.write(self.style.SUCCESS("✅ ML model trained successfully"))
                self.stdout.write(f"   Train Score: {metrics.get('train_score', 0):.3f}")
                self.stdout.write(f"   Test Score: {metrics.get('test_score', 0):.3f}")
                self.stdout.write(f"   Records Used: {metrics.get('records_used', 0)}")
                self.stdout.write(f"   Success Rate: {metrics.get('success_rate', 0):.1%}")
                
                if metrics.get('overfit_detected'):
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️  Overfit detected (delta: {metrics.get('overfit_delta', 0):.3f})")
                    )
                
                if 'feature_importances' in metrics:
                    self.stdout.write("\n   Top Features:")
                    for feature, importance in list(metrics['feature_importances'].items())[:5]:
                        self.stdout.write(f"     • {feature}: {importance:.3f}")
        
        # Show ML insights if requested
        if ml_insights:
            self.stdout.write(self.style.SUCCESS("🤖 ML Learning Insights:"))
            ml_learner = get_ml_learner()
            insights = ml_learner.get_learning_insights()
            
            if 'message' in insights:
                self.stdout.write(f"   {insights['message']}")
            else:
                self.stdout.write(f"   Total Records: {insights.get('total_records', 0)}")
                self.stdout.write(f"   Model Available: {insights.get('model_available', False)}")
                
                if 'top_features' in insights:
                    self.stdout.write("\n   Top Features Learned:")
                    for feature, importance in insights['top_features']:
                        self.stdout.write(f"     • {feature}: {importance:.3f}")
        
        # Run scan
        self.stdout.write(self.style.SUCCESS(f"🔍 Starting pre-market scan (mode: {mode})"))
        self.stdout.write(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Minutes until open: {scanner._minutes_until_open()}")
        self.stdout.write("")
        
        setups = scanner.scan_pre_market_sync(mode=mode, limit=limit)
        
        if not setups:
            self.stdout.write(
                self.style.WARNING("⚠️  No quality pre-market setups found")
            )
            return
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"✅ Found {len(setups)} quality setups"))
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("PRE-MARKET QUALITY SETUPS (ML-Enhanced)")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        for i, setup in enumerate(setups, 1):
            symbol = setup['symbol']
            side = setup['side']
            change = setup['pre_market_change_pct']
            price = setup['pre_market_price']
            score = setup.get('ml_enhanced_score', setup.get('score', 0))
            ml_prob = setup.get('ml_success_probability')
            volume = setup['volume']
            
            self.stdout.write(f"{i}. {symbol} - {side}")
            self.stdout.write(f"   Pre-market move: {change:+.2%}")
            self.stdout.write(f"   Current price: ${price:.2f}")
            self.stdout.write(f"   Volume: {volume:,} shares")
            self.stdout.write(f"   Quality score: {score:.2f}")
            
            if ml_prob is not None:
                self.stdout.write(
                    self.style.SUCCESS(f"   ML Success Probability: {ml_prob:.1%}")
                )
            
            self.stdout.write(f"   Notes: {setup['notes']}")
            self.stdout.write("")
        
        # Send alerts
        if send_email or send_push:
            self.stdout.write("=" * 80)
            self.stdout.write("SENDING ALERTS")
            self.stdout.write("=" * 80)
            
            alert_results = scanner.send_alerts(setups)
            
            if alert_results.get('email_sent'):
                self.stdout.write(self.style.SUCCESS("✅ Email alert sent"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Email alert not sent (check configuration)"))
            
            if alert_results.get('push_sent'):
                self.stdout.write(self.style.SUCCESS("✅ Push notification sent"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Push notification not sent (check configuration)"))
            
            if alert_results.get('discord_sent'):
                self.stdout.write(self.style.SUCCESS("✅ Discord webhook sent"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Discord webhook not sent (set DISCORD_WEBHOOK env var)"))
            
            if alert_results.get('slack_sent'):
                self.stdout.write(self.style.SUCCESS("✅ Slack webhook sent"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  Slack webhook not sent (set SLACK_WEBHOOK env var)"))
        
        self.stdout.write(self.style.SUCCESS("✅ Pre-market scan complete"))

