"""
Autopilot Notification Service

Handles push notifications for DeFi Auto-Pilot repair events.
Uses Expo Push Notification service, same pattern as RAHANotificationService.

Notification types:
  - repair_available: New repair suggested by risk scoring or strategy engine
  - repair_executed: AUTO_BOUNDED mode prepared a repair (user must sign)
  - revert_expiring: 24h revert window closing in <2 hours
  - policy_breach: Position drifted outside user's policy guardrails
"""
import logging
import os
from typing import Dict, Any, Optional

from django.utils import timezone

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AutopilotNotificationService:
    """
    Push notification service for DeFi Auto-Pilot events.
    Uses Expo Push Notification service.
    """

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self):
        self.expo_push_url = os.getenv('EXPO_PUSH_URL', self.EXPO_PUSH_URL)

    def _get_user_preferences(self, user):
        """Get or create DeFi notification preferences for a user."""
        try:
            from .defi_models import DeFiNotificationPreferences
            prefs, _ = DeFiNotificationPreferences.objects.get_or_create(user=user)
            return prefs
        except Exception as e:
            logger.error(f"Error getting DeFi notification preferences: {e}")
            return None

    def _is_quiet_hours(self, prefs) -> bool:
        """Check if current time is within quiet hours."""
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

    def _should_notify(self, prefs, notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences."""
        if not prefs or not prefs.push_enabled or not prefs.push_token:
            return False
        if self._is_quiet_hours(prefs):
            return False

        # Check category-specific preference flags
        category_map = {
            'repair_available': prefs.repair_alerts_enabled,
            'repair_executed': prefs.repair_alerts_enabled,
            'revert_expiring': prefs.revert_reminder_enabled,
            'policy_breach': prefs.autopilot_alerts_enabled,
            'health_warning': prefs.health_alerts_enabled,
            'health_critical': prefs.health_alerts_enabled,
            'health_danger': prefs.health_alerts_enabled,
            'apy_change': prefs.apy_alerts_enabled,
            'harvest_ready': prefs.harvest_alerts_enabled,
        }
        return category_map.get(notification_type, prefs.autopilot_alerts_enabled)

    def _send_push_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = 'default',
        sound: str = 'default',
    ) -> bool:
        """
        Send a push notification via Expo Push Notification service.

        Args:
            push_token: Expo push token (ExponentPushToken[...])
            title: Notification title
            body: Notification body text
            data: Optional data payload for mobile routing
            priority: 'default' or 'high'
            sound: Sound to play ('default' or None)

        Returns:
            True if successful, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available, cannot send push notification")
            return False

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
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('data', {}).get('status') == 'ok':
                    logger.info(f"Autopilot push sent: {title}")
                    return True
                else:
                    logger.warning(f"Autopilot push failed: {result}")
                    return False
            else:
                logger.error(f"Autopilot push HTTP error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending autopilot push: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Public notification methods
    # ------------------------------------------------------------------

    def notify_repair_available(self, user, repair: Dict[str, Any]) -> bool:
        """
        Notify user that a new repair action is available.
        Sent when risk scoring or strategy engine identifies a better vault.
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'repair_available'):
            return False

        from_vault = repair.get('from_vault', '?')
        to_vault = repair.get('to_vault', '?')
        apy_delta = repair.get('estimated_apy_delta', 0)
        apy_pct = apy_delta * 100 if abs(apy_delta) < 1 else apy_delta

        title = "Auto-Pilot: Repair Available"
        body = f"Move from {from_vault} to {to_vault} ({apy_pct:+.1f}% APY)"

        data = {
            'type': 'autopilot_repair_available',
            'repair_id': repair.get('id', ''),
            'screen': 'DeFiAutopilot',
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
        )

    def notify_repair_executed(self, user, repair: Dict[str, Any]) -> bool:
        """
        Notify user that Auto-Pilot prepared a repair in AUTO_BOUNDED mode.
        User still needs to sign the on-chain transaction via wallet.
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'repair_executed'):
            return False

        from_vault = repair.get('from_vault', '?')
        to_vault = repair.get('to_vault', '?')

        title = "Auto-Pilot Prepared a Move"
        body = f"{from_vault} -> {to_vault}. Approve in your wallet within 24h."

        data = {
            'type': 'autopilot_repair_executed',
            'repair_id': repair.get('id', ''),
            'screen': 'DeFiAutopilot',
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
        )

    def notify_funds_moved(
        self,
        user,
        repair_id: str,
        from_vault: str,
        to_vault: str,
        amount_usd: Optional[float] = None,
        tx_hash: Optional[str] = None,
    ) -> bool:
        """
        Notify user that their funds were moved to a safer vault (on-chain execution done).
        Message: "We moved your funds to a safer vault (Saves $X in potential drawdown). Tap to see the proof."
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'repair_executed'):
            return False

        if amount_usd is not None and amount_usd > 0:
            try:
                savings_str = f"${amount_usd:,.0f}"
            except (TypeError, ValueError):
                savings_str = None
        else:
            savings_str = None

        title = "Funds moved to safer vault"
        if savings_str:
            body = f"We moved your funds to a safer vault (Saves {savings_str} in potential drawdown). Tap to see the proof."
        else:
            body = f"We moved your funds from {from_vault} to {to_vault}. Tap to see the proof."

        data = {
            'type': 'autopilot_funds_moved',
            'repair_id': repair_id,
            'screen': 'DeFiAutopilot',
            'tx_hash': tx_hash or '',
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
        )

    def notify_revert_window_expiring(self, user, last_move: Dict[str, Any]) -> bool:
        """
        Notify user that the 24h revert window is expiring soon (<2 hours left).
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'revert_expiring'):
            return False

        from_vault = last_move.get('from_vault', '?')
        to_vault = last_move.get('to_vault', '?')

        title = "Revert Window Expiring Soon"
        body = f"Your move {from_vault} -> {to_vault} can be reverted for less than 2 hours."

        data = {
            'type': 'autopilot_revert_expiring',
            'move_id': last_move.get('id', ''),
            'screen': 'DeFiAutopilot',
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
        )

    def notify_portfolio_drawdown(self, user, drawdown_data: Dict[str, Any]) -> bool:
        """
        Notify user that their portfolio drawdown has exceeded the limit.
        Part of Trust-First Framework: Gap 1 — Portfolio Stop-Loss.
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'policy_breach'):
            return False

        drawdown_pct = drawdown_data.get('drawdown_pct', 0)
        limit = drawdown_data.get('max_drawdown_limit', 0.08)
        current_value = drawdown_data.get('current_value', 0)
        hwm = drawdown_data.get('high_water_mark', 0)

        title = "Portfolio Drawdown Alert"
        body = (
            f"Your portfolio has drawn down {drawdown_pct:.1%} "
            f"from its peak of ${hwm:,.0f}. "
            f"This exceeds your {limit:.0%} safety limit. "
            f"Auto-Pilot is evaluating protective actions."
        )

        data = {
            'type': 'portfolio_drawdown',
            'screen': 'DeFiAutopilot',
            'drawdown_pct': drawdown_pct,
            'current_value': current_value,
            'high_water_mark': hwm,
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
            sound='default',
        )

    def notify_policy_breach(self, user, breach_details: Dict[str, Any]) -> bool:
        """
        Notify user of a policy guardrail breach (position drifted outside limits).
        """
        prefs = self._get_user_preferences(user)
        if not self._should_notify(prefs, 'policy_breach'):
            return False

        title = "Auto-Pilot: Policy Alert"
        body = breach_details.get(
            'message',
            'A position has breached your policy guardrails.',
        )

        data = {
            'type': 'autopilot_policy_breach',
            'screen': 'DeFiAutopilot',
            **{k: v for k, v in breach_details.items() if k != 'message'},
        }

        return self._send_push_notification(
            push_token=prefs.push_token,
            title=title,
            body=body,
            data=data,
            priority='high',
            sound='default',
        )


# ------------------------------------------------------------------
# Global singleton (same pattern as raha_notification_service)
# ------------------------------------------------------------------

_autopilot_notification_service = None


def get_autopilot_notification_service() -> AutopilotNotificationService:
    """Get or create the global autopilot notification service instance."""
    global _autopilot_notification_service
    if _autopilot_notification_service is None:
        _autopilot_notification_service = AutopilotNotificationService()
    return _autopilot_notification_service
