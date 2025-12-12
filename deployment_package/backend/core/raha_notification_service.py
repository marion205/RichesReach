"""
RAHA Notification Service
Handles push notifications for high-confidence signals and backtest completion
"""
import logging
import requests
import os
from typing import Dict, Any, Optional
from datetime import datetime, time
from django.utils import timezone
from django.conf import settings

from .raha_models import NotificationPreferences, RAHASignal, RAHABacktestRun

logger = logging.getLogger(__name__)


class RAHANotificationService:
    """
    Service for sending push notifications for RAHA events.
    Uses Expo Push Notification service.
    """
    
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    
    def __init__(self):
        self.expo_push_url = os.getenv('EXPO_PUSH_URL', self.EXPO_PUSH_URL)
    
    def _get_user_preferences(self, user) -> Optional[NotificationPreferences]:
        """Get or create notification preferences for a user"""
        try:
            prefs, _ = NotificationPreferences.objects.get_or_create(user=user)
            return prefs
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return None
    
    def _is_quiet_hours(self, prefs: NotificationPreferences) -> bool:
        """Check if current time is within quiet hours"""
        if not prefs.quiet_hours_enabled:
            return False
        
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end
        
        # Handle quiet hours that span midnight (e.g., 22:00 - 08:00)
        if start > end:
            return now >= start or now <= end
        else:
            return start <= now <= end
    
    def _should_notify_signal(self, prefs: NotificationPreferences, signal: RAHASignal) -> bool:
        """Check if we should send a notification for this signal"""
        if not prefs.push_enabled or not prefs.signal_notifications_enabled:
            return False
        
        if not prefs.push_token:
            return False
        
        # Check confidence threshold
        if signal.confidence_score < prefs.signal_confidence_threshold:
            return False
        
        # Check symbol filter
        if prefs.signal_symbols and signal.symbol not in prefs.signal_symbols:
            return False
        
        # Check quiet hours
        if self._is_quiet_hours(prefs):
            return False
        
        return True
    
    def _should_notify_backtest(self, prefs: NotificationPreferences, backtest: RAHABacktestRun) -> bool:
        """Check if we should send a notification for this backtest"""
        if not prefs.push_enabled or not prefs.backtest_notifications_enabled:
            return False
        
        if not prefs.push_token:
            return False
        
        # Check if only successful backtests should be notified
        if prefs.backtest_success_only:
            results = backtest.results or {}
            win_rate = results.get('win_rate', 0)
            if win_rate < 0.5:
                return False
        
        # Check quiet hours
        if self._is_quiet_hours(prefs):
            return False
        
        return True
    
    def _send_push_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = 'default',
        sound: str = 'default'
    ) -> bool:
        """
        Send a push notification via Expo Push Notification service.
        
        Args:
            push_token: Expo push token
            title: Notification title
            body: Notification body
            data: Optional data payload
            priority: 'default' or 'high'
            sound: Sound to play ('default' or None)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                'to': push_token,
                'title': title,
                'body': body,
                'priority': priority,
                'sound': sound,
            }
            
            if data:
                payload['data'] = data
            
            response = requests.post(
                self.expo_push_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('data', {}).get('status') == 'ok':
                    logger.info(f"✅ Push notification sent: {title}")
                    return True
                else:
                    logger.warning(f"⚠️  Push notification failed: {result}")
                    return False
            else:
                logger.error(f"❌ Push notification HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending push notification: {e}", exc_info=True)
            return False
    
    def notify_signal(self, signal: RAHASignal) -> bool:
        """
        Send a push notification for a high-confidence RAHA signal.
        
        Args:
            signal: RAHASignal instance
        
        Returns:
            True if notification was sent, False otherwise
        """
        try:
            # Get user from signal (via strategy version -> user settings)
            from .raha_models import UserStrategySettings
            user_settings = UserStrategySettings.objects.filter(
                strategy_version=signal.strategy_version,
                enabled=True
            ).first()
            
            if not user_settings:
                logger.debug(f"No enabled user settings found for signal {signal.id}")
                return False
            
            user = user_settings.user
            prefs = self._get_user_preferences(user)
            
            if not prefs:
                return False
            
            if not self._should_notify_signal(prefs, signal):
                logger.debug(f"Signal notification skipped for user {user.email}")
                return False
            
            # Format notification
            strategy_name = signal.strategy_version.strategy.name
            confidence_pct = int(signal.confidence_score * 100)
            signal_type = signal.signal_type.upper()
            
            title = f"🎯 {signal.symbol} {signal_type} Signal"
            body = f"{strategy_name}: {confidence_pct}% confidence"
            
            data = {
                'type': 'raha_signal',
                'signal_id': str(signal.id),
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'confidence_score': float(signal.confidence_score),
                'strategy_name': strategy_name,
            }
            
            return self._send_push_notification(
                push_token=prefs.push_token,
                title=title,
                body=body,
                data=data,
                priority='high',
                sound='default'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in notify_signal: {e}", exc_info=True)
            return False
    
    def notify_backtest_complete(self, backtest: RAHABacktestRun) -> bool:
        """
        Send a push notification when a backtest completes.
        
        Args:
            backtest: RAHABacktestRun instance
        
        Returns:
            True if notification was sent, False otherwise
        """
        try:
            user = backtest.user
            prefs = self._get_user_preferences(user)
            
            if not prefs:
                return False
            
            if not self._should_notify_backtest(prefs, backtest):
                logger.debug(f"Backtest notification skipped for user {user.email}")
                return False
            
            # Format notification
            strategy_name = backtest.strategy_version.strategy.name
            results = backtest.metrics or {}
            win_rate = results.get('win_rate', 0)
            win_rate_pct = int(win_rate * 100) if win_rate else 0
            status = backtest.status.upper()
            
            title = f"📊 Backtest Complete: {strategy_name}"
            body = f"{backtest.symbol} - {win_rate_pct}% win rate ({status})"
            
            data = {
                'type': 'raha_backtest',
                'backtest_id': str(backtest.id),
                'symbol': backtest.symbol,
                'strategy_name': strategy_name,
                'status': backtest.status,
                'win_rate': win_rate,
            }
            
            return self._send_push_notification(
                push_token=prefs.push_token,
                title=title,
                body=body,
                data=data,
                priority='default',
                sound='default'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in notify_backtest_complete: {e}", exc_info=True)
            return False


# Global instance
_notification_service = None

def get_notification_service() -> RAHANotificationService:
    """Get or create the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = RAHANotificationService()
    return _notification_service

