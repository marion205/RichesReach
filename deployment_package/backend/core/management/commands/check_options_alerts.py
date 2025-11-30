"""
Management command to check and trigger options alerts
Run this periodically (e.g., every minute) to check alert conditions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from core.options_alert_models import OptionsAlert, OptionsAlertNotification
from core.real_options_service import RealOptionsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check options alerts and trigger notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually triggering alerts',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all active alerts
        active_alerts = OptionsAlert.objects.filter(status='ACTIVE')
        
        self.stdout.write(f"Checking {active_alerts.count()} active alerts...")
        
        options_service = RealOptionsService()
        triggered_count = 0
        
        for alert in active_alerts:
            try:
                triggered = False
                message = ""
                
                if alert.alert_type == 'PRICE':
                    # Check if option price reached target
                    # Get current option price
                    options_data = options_service.get_real_options_chain(alert.symbol)
                    chain = options_data.get('options_chain', {})
                    
                    # Find matching option
                    current_price = None
                    for call in chain.get('calls', []):
                        if (call.get('strike') == float(alert.strike) and 
                            call.get('expiration_date') == alert.expiration):
                            current_price = (call.get('bid', 0) + call.get('ask', 0)) / 2
                            break
                    
                    if not current_price:
                        for put in chain.get('puts', []):
                            if (put.get('strike') == float(alert.strike) and 
                                put.get('expiration_date') == alert.expiration):
                                current_price = (put.get('bid', 0) + put.get('ask', 0)) / 2
                                break
                    
                    if current_price:
                        target = float(alert.target_value)
                        if alert.direction == 'above' and current_price >= target:
                            triggered = True
                            message = f"{alert.symbol} {alert.option_type} ${alert.strike} price reached ${current_price:.2f} (target: ${target:.2f})"
                        elif alert.direction == 'below' and current_price <= target:
                            triggered = True
                            message = f"{alert.symbol} {alert.option_type} ${alert.strike} price reached ${current_price:.2f} (target: ${target:.2f})"
                
                elif alert.alert_type == 'IV':
                    # Check if IV reached target
                    options_data = options_service.get_real_options_chain(alert.symbol)
                    chain = options_data.get('options_chain', {})
                    
                    current_iv = None
                    for call in chain.get('calls', []):
                        if (call.get('strike') == float(alert.strike) and 
                            call.get('expiration_date') == alert.expiration):
                            current_iv = call.get('implied_volatility', 0)
                            break
                    
                    if not current_iv:
                        for put in chain.get('puts', []):
                            if (put.get('strike') == float(alert.strike) and 
                                put.get('expiration_date') == alert.expiration):
                                current_iv = put.get('implied_volatility', 0)
                                break
                    
                    if current_iv:
                        target = float(alert.target_value)
                        if alert.direction == 'above' and current_iv >= target:
                            triggered = True
                            message = f"{alert.symbol} {alert.option_type} ${alert.strike} IV reached {current_iv*100:.1f}% (target: {target*100:.1f}%)"
                        elif alert.direction == 'below' and current_iv <= target:
                            triggered = True
                            message = f"{alert.symbol} {alert.option_type} ${alert.strike} IV reached {current_iv*100:.1f}% (target: {target*100:.1f}%)"
                
                elif alert.alert_type == 'EXPIRATION':
                    # Check if expiration is within 1 day
                    if alert.expiration:
                        try:
                            from datetime import datetime
                            exp_date = datetime.strptime(alert.expiration, '%Y-%m-%d')
                            days_until = (exp_date.date() - timezone.now().date()).days
                            
                            if days_until <= 1:
                                triggered = True
                                message = f"{alert.symbol} {alert.option_type} ${alert.strike} expires in {days_until} day(s)"
                        except Exception as e:
                            logger.warning(f"Error parsing expiration date: {e}")
                
                if triggered:
                    if not dry_run:
                        # Update alert status
                        alert.status = 'TRIGGERED'
                        alert.triggered_at = timezone.now()
                        alert.save()
                        
                        # Create notification
                        OptionsAlertNotification.objects.create(
                            alert=alert,
                            notification_type='in_app',
                            message=message
                        )
                        
                        # TODO: Send push notification
                        # TODO: Send email notification
                    
                    self.stdout.write(self.style.SUCCESS(f"✓ Triggered: {message}"))
                    triggered_count += 1
                    
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}", exc_info=True)
                self.stdout.write(self.style.ERROR(f"✗ Error checking alert {alert.id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nTriggered {triggered_count} alerts"))

