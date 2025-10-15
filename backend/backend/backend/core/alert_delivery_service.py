import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models_smart_alerts import SmartAlert, AlertDeliveryHistory, AlertDeliveryPreference
from .alert_config_service import alert_config_service

logger = logging.getLogger(__name__)

class AlertDeliveryService:
    """Service for multi-channel alert delivery (push, email, SMS, in-app)"""
    
    def __init__(self):
        self.config_service = alert_config_service
    
    async def deliver_alert(self, alert: SmartAlert, delivery_methods: List[str] = None) -> Dict[str, bool]:
        """Deliver an alert through specified channels"""
        try:
            if not delivery_methods:
                delivery_methods = self._get_preferred_delivery_methods(alert)
            
            delivery_results = {}
            
            for method in delivery_methods:
                try:
                    success = await self._deliver_via_method(alert, method)
                    delivery_results[method] = success
                    
                    # Record delivery attempt
                    self._record_delivery_attempt(alert, method, success)
                    
                except Exception as e:
                    logger.error(f"Error delivering alert {alert.id} via {method}: {e}")
                    delivery_results[method] = False
                    self._record_delivery_attempt(alert, method, False, str(e))
            
            return delivery_results
            
        except Exception as e:
            logger.error(f"Error in deliver_alert: {e}")
            return {}
    
    def _get_preferred_delivery_methods(self, alert: SmartAlert) -> List[str]:
        """Get preferred delivery methods based on user preferences and alert urgency"""
        try:
            user = alert.user
            category = alert.category
            urgency_level = alert.urgency_level
            
            # Get user delivery preferences
            preferences = self.config_service.get_user_delivery_preferences(
                user, category, urgency_level
            )
            
            delivery_method = preferences.get('delivery_method', 'in_app')
            
            # Map delivery method to actual channels
            if delivery_method == 'all':
                return ['in_app', 'push', 'email']
            elif delivery_method == 'push':
                return ['in_app', 'push']
            elif delivery_method == 'email':
                return ['in_app', 'email']
            else:
                return ['in_app']
                
        except Exception as e:
            logger.error(f"Error getting delivery methods: {e}")
            return ['in_app']
    
    async def _deliver_via_method(self, alert: SmartAlert, method: str) -> bool:
        """Deliver alert via specific method"""
        try:
            if method == 'in_app':
                return await self._deliver_in_app(alert)
            elif method == 'push':
                return await self._deliver_push(alert)
            elif method == 'email':
                return await self._deliver_email(alert)
            elif method == 'sms':
                return await self._deliver_sms(alert)
            else:
                logger.warning(f"Unknown delivery method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Error delivering via {method}: {e}")
            return False
    
    async def _deliver_in_app(self, alert: SmartAlert) -> bool:
        """Deliver alert in-app (mark as delivered)"""
        try:
            alert.delivered_in_app = True
            alert.save(update_fields=['delivered_in_app'])
            return True
        except Exception as e:
            logger.error(f"Error delivering in-app: {e}")
            return False
    
    async def _deliver_push(self, alert: SmartAlert) -> bool:
        """Deliver alert via push notification"""
        try:
            # Check if user has push notifications enabled
            if not self._user_has_push_enabled(alert.user):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(alert.user, alert.category, alert.urgency_level):
                # Schedule for later delivery
                await self._schedule_delivery(alert, 'push', self._get_next_delivery_time(alert.user))
                return True
            
            # Send push notification
            push_data = {
                'title': alert.title,
                'body': alert.message,
                'data': {
                    'alert_id': alert.alert_id,
                    'category': alert.category,
                    'urgency': alert.urgency_level,
                    'actionable': alert.actionable,
                }
            }
            
            # Here you would integrate with your push notification service
            # (Firebase, OneSignal, etc.)
            success = await self._send_push_notification(alert.user, push_data)
            
            if success:
                alert.delivered_push = True
                alert.save(update_fields=['delivered_push'])
            
            return success
            
        except Exception as e:
            logger.error(f"Error delivering push notification: {e}")
            return False
    
    async def _deliver_email(self, alert: SmartAlert) -> bool:
        """Deliver alert via email"""
        try:
            # Check if user has email notifications enabled
            if not self._user_has_email_enabled(alert.user):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(alert.user, alert.category, alert.urgency_level):
                # Schedule for later delivery
                await self._schedule_delivery(alert, 'email', self._get_next_delivery_time(alert.user))
                return True
            
            # Prepare email content
            subject = f"🚨 {alert.title}" if alert.urgency_level == 'critical' else f"📊 {alert.title}"
            
            html_content = self._generate_email_html(alert)
            text_content = self._generate_email_text(alert)
            
            # Send email
            success = send_mail(
                subject=subject,
                message=text_content,
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.user.email],
                fail_silently=False,
            )
            
            if success:
                alert.delivered_email = True
                alert.save(update_fields=['delivered_email'])
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Error delivering email: {e}")
            return False
    
    async def _deliver_sms(self, alert: SmartAlert) -> bool:
        """Deliver alert via SMS (for critical alerts only)"""
        try:
            # Only send SMS for critical alerts
            if alert.urgency_level != 'critical':
                return False
            
            # Check if user has SMS enabled
            if not self._user_has_sms_enabled(alert.user):
                return False
            
            # Check quiet hours (but allow critical SMS)
            if self._is_quiet_hours(alert.user, alert.category, alert.urgency_level) and alert.urgency_level != 'critical':
                return False
            
            # Prepare SMS content
            sms_content = f"{alert.title}: {alert.message[:100]}..."
            
            # Here you would integrate with your SMS service (Twilio, etc.)
            success = await self._send_sms(alert.user, sms_content)
            
            if success:
                alert.delivered_sms = True
                alert.save(update_fields=['delivered_sms'])
            
            return success
            
        except Exception as e:
            logger.error(f"Error delivering SMS: {e}")
            return False
    
    def _user_has_push_enabled(self, user: User) -> bool:
        """Check if user has push notifications enabled"""
        # This would check user preferences, device tokens, etc.
        # For now, return True as a placeholder
        return True
    
    def _user_has_email_enabled(self, user: User) -> bool:
        """Check if user has email notifications enabled"""
        return bool(user.email)
    
    def _user_has_sms_enabled(self, user: User) -> bool:
        """Check if user has SMS notifications enabled"""
        # This would check user's phone number and SMS preferences
        # For now, return False as a placeholder
        return False
    
    def _is_quiet_hours(self, user: User, category: str, urgency_level: str) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            preferences = self.config_service.get_user_delivery_preferences(
                user, category, urgency_level
            )
            
            if not preferences.get('quiet_hours_enabled', True):
                return False
            
            now = timezone.now().time()
            start_time = preferences.get('quiet_hours_start', '22:00')
            end_time = preferences.get('quiet_hours_end', '08:00')
            
            # Convert string times to time objects
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            
            # Handle overnight quiet hours
            if start <= end:
                return start <= now <= end
            else:
                return now >= start or now <= end
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def _get_next_delivery_time(self, user: User) -> datetime:
        """Get next appropriate delivery time (after quiet hours)"""
        try:
            # Get user's quiet hours end time
            preferences = self.config_service.get_user_delivery_preferences(
                user, 'general', 'informational'
            )
            
            end_time = preferences.get('quiet_hours_end', '08:00')
            end = datetime.strptime(end_time, '%H:%M').time()
            
            # Calculate next delivery time
            now = timezone.now()
            next_delivery = now.replace(
                hour=end.hour,
                minute=end.minute,
                second=0,
                microsecond=0
            )
            
            # If the time has already passed today, schedule for tomorrow
            if next_delivery <= now:
                next_delivery += timedelta(days=1)
            
            return next_delivery
            
        except Exception as e:
            logger.error(f"Error calculating next delivery time: {e}")
            return timezone.now() + timedelta(hours=1)
    
    async def _send_push_notification(self, user: User, push_data: Dict[str, Any]) -> bool:
        """Send push notification to user's devices"""
        try:
            # This is where you'd integrate with your push notification service
            # For now, we'll simulate success
            logger.info(f"Would send push notification to {user.username}: {push_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def _send_sms(self, user: User, content: str) -> bool:
        """Send SMS to user's phone"""
        try:
            # This is where you'd integrate with your SMS service (Twilio, etc.)
            # For now, we'll simulate success
            logger.info(f"Would send SMS to {user.username}: {content}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    def _generate_email_html(self, alert: SmartAlert) -> str:
        """Generate HTML email content for alert"""
        urgency_color = {
            'critical': '#EF4444',
            'important': '#F59E0B',
            'informational': '#06B6D4'
        }.get(alert.urgency_level, '#6B7280')
        
        urgency_icon = {
            'critical': '🚨',
            'important': '⚠️',
            'informational': 'ℹ️'
        }.get(alert.urgency_level, '📊')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{alert.title}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 24px; }}
                .alert-title {{ font-size: 20px; font-weight: 600; margin-bottom: 8px; }}
                .alert-message {{ font-size: 16px; line-height: 1.5; color: #374151; margin-bottom: 20px; }}
                .suggested-actions {{ background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 20px; }}
                .coaching-tip {{ background-color: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; }}
                .footer {{ background-color: #f9fafb; padding: 16px; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{urgency_icon} {alert.title}</h1>
                </div>
                <div class="content">
                    <p class="alert-message">{alert.message}</p>
                    
                    {f'<div class="suggested-actions"><h3>Suggested Actions:</h3><ul>' + ''.join(f'<li>{action}</li>' for action in alert.suggested_actions) + '</ul></div>' if alert.suggested_actions else ''}
                    
                    <div class="coaching-tip">
                        <strong>💡 Coaching Tip:</strong> {alert.coaching_tip}
                    </div>
                </div>
                <div class="footer">
                    <p>This alert was generated by your RichesReach portfolio analysis.</p>
                    <p>You can manage your notification preferences in the app.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_email_text(self, alert: SmartAlert) -> str:
        """Generate plain text email content for alert"""
        urgency_icon = {
            'critical': '🚨',
            'important': '⚠️',
            'informational': 'ℹ️'
        }.get(alert.urgency_level, '📊')
        
        text = f"""
{urgency_icon} {alert.title}

{alert.message}

"""
        
        if alert.suggested_actions:
            text += "Suggested Actions:\n"
            for i, action in enumerate(alert.suggested_actions, 1):
                text += f"{i}. {action}\n"
            text += "\n"
        
        text += f"💡 Coaching Tip: {alert.coaching_tip}\n\n"
        text += "This alert was generated by your RichesReach portfolio analysis.\n"
        text += "You can manage your notification preferences in the app."
        
        return text
    
    def _record_delivery_attempt(self, alert: SmartAlert, method: str, success: bool, error_message: str = None):
        """Record delivery attempt in database"""
        try:
            AlertDeliveryHistory.objects.create(
                alert=alert,
                delivery_method=method,
                status='delivered' if success else 'failed',
                delivery_confirmed_at=timezone.now() if success else None,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Error recording delivery attempt: {e}")
    
    async def _schedule_delivery(self, alert: SmartAlert, method: str, scheduled_time: datetime):
        """Schedule alert for later delivery"""
        try:
            # This would integrate with a task queue (Celery, etc.)
            # For now, we'll just log it
            logger.info(f"Scheduled {method} delivery for alert {alert.id} at {scheduled_time}")
        except Exception as e:
            logger.error(f"Error scheduling delivery: {e}")
    
    async def process_delivery_queue(self):
        """Process scheduled deliveries (called by background task)"""
        try:
            # This would process any scheduled deliveries
            # For now, it's a placeholder
            logger.info("Processing delivery queue...")
        except Exception as e:
            logger.error(f"Error processing delivery queue: {e}")
    
    async def send_digest_email(self, user: User, timeframe: str = 'daily'):
        """Send digest email with multiple alerts"""
        try:
            # Get recent alerts for user
            since = timezone.now() - timedelta(days=1 if timeframe == 'daily' else 7)
            alerts = SmartAlert.objects.filter(
                user=user,
                triggered_at__gte=since,
                delivered_email=False
            ).order_by('-triggered_at')
            
            if not alerts.exists():
                return False
            
            # Generate digest email
            subject = f"📊 Your {timeframe.title()} Portfolio Digest"
            html_content = self._generate_digest_html(alerts, timeframe)
            text_content = self._generate_digest_text(alerts, timeframe)
            
            # Send email
            success = send_mail(
                subject=subject,
                message=text_content,
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            if success:
                # Mark alerts as delivered via email
                alerts.update(delivered_email=True)
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Error sending digest email: {e}")
            return False
    
    def _generate_digest_html(self, alerts: List[SmartAlert], timeframe: str) -> str:
        """Generate HTML digest email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your {timeframe.title()} Portfolio Digest</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .alert-item {{ padding: 16px; border-bottom: 1px solid #e5e7eb; }}
                .alert-item:last-child {{ border-bottom: none; }}
                .alert-title {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; }}
                .alert-message {{ font-size: 14px; color: #6b7280; }}
                .footer {{ background-color: #f9fafb; padding: 16px; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Your {timeframe.title()} Portfolio Digest</h1>
                    <p>{len(alerts)} alerts from the past {timeframe}</p>
                </div>
        """
        
        for alert in alerts:
            html += f"""
                <div class="alert-item">
                    <div class="alert-title">{alert.title}</div>
                    <div class="alert-message">{alert.message}</div>
                </div>
            """
        
        html += """
                <div class="footer">
                    <p>View all alerts and manage preferences in the RichesReach app.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_digest_text(self, alerts: List[SmartAlert], timeframe: str) -> str:
        """Generate plain text digest email"""
        text = f"Your {timeframe.title()} Portfolio Digest\n"
        text += f"{len(alerts)} alerts from the past {timeframe}\n\n"
        
        for alert in alerts:
            text += f"{alert.title}\n"
            text += f"{alert.message}\n\n"
        
        text += "View all alerts and manage preferences in the RichesReach app."
        
        return text

# Global instance
alert_delivery_service = AlertDeliveryService()
