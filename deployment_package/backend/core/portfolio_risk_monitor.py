"""
Portfolio-Level Risk Monitor

Enforces aggregate portfolio drawdown limits as a hard guardrail.
Individual vaults are monitored by risk_scoring_service.py; this module
monitors the WHOLE portfolio and triggers de-risk actions when the
aggregate drawdown exceeds the user's max_drawdown_limit.

Uses a high-water-mark (HWM) approach:
    drawdown = 1 - (current_value / peak_value)

Part of Trust-First Framework: Gap 1 — Bounded Losses
"""
import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key formats
HWM_KEY = 'defi:hwm:{user_id}'
SNAPSHOT_KEY = 'defi:portfolio_snapshot:{user_id}'
DRAWDOWN_ALERT_KEY = 'defi:drawdown_alert:{user_id}'

# Drawdown alert cooldown (don't re-alert within this window)
DRAWDOWN_ALERT_COOLDOWN_SECONDS = 1800  # 30 minutes


class PortfolioRiskMonitor:
    """
    Monitors aggregate portfolio value against a rolling high-water mark.
    Triggers alerts and de-risk actions when drawdown exceeds policy limits.
    """

    def get_portfolio_value(self, user) -> float:
        """
        Aggregate all active DeFi positions for a user.
        Returns total portfolio value in USD.
        """
        try:
            from .defi_models import UserDeFiPosition

            positions = UserDeFiPosition.objects.filter(
                user=user,
                is_active=True,
            )
            total = sum(float(p.staked_value_usd) for p in positions)
            return total
        except Exception as e:
            logger.warning(f"Error getting portfolio value for user {user.id}: {e}")
            return 0.0

    def get_high_water_mark(self, user) -> float:
        """
        Get the portfolio's peak value (high water mark) from cache.
        If no HWM exists, initialize with current value.
        """
        key = HWM_KEY.format(user_id=user.id)
        hwm = cache.get(key)
        if hwm is not None:
            return float(hwm)
        return 0.0

    def update_high_water_mark(self, user, current_value: float) -> float:
        """
        Update HWM if current value exceeds the stored peak.
        Returns the (possibly updated) HWM.
        """
        key = HWM_KEY.format(user_id=user.id)
        current_hwm = self.get_high_water_mark(user)

        if current_value > current_hwm:
            cache.set(key, current_value, timeout=None)  # Persistent
            return current_value
        return current_hwm

    def calculate_drawdown(self, user) -> Dict[str, Any]:
        """
        Calculate current portfolio drawdown from peak.

        Returns:
            dict with: current_value, high_water_mark, drawdown_pct, breached (bool)
        """
        from .policy_engine import get_policy

        current_value = self.get_portfolio_value(user)

        if current_value <= 0:
            return {
                'current_value': 0.0,
                'high_water_mark': 0.0,
                'drawdown_pct': 0.0,
                'breached': False,
                'max_drawdown_limit': 0.08,
            }

        # Update HWM (will only increase)
        hwm = self.update_high_water_mark(user, current_value)

        # If HWM is 0 (first run), no drawdown
        if hwm <= 0:
            return {
                'current_value': current_value,
                'high_water_mark': current_value,
                'drawdown_pct': 0.0,
                'breached': False,
                'max_drawdown_limit': 0.08,
            }

        drawdown_pct = 1.0 - (current_value / hwm)
        drawdown_pct = max(0.0, drawdown_pct)  # Can't be negative

        # Get policy limit
        policy = get_policy()
        max_drawdown_limit = float(
            policy.get('risk_thresholds', {}).get('max_drawdown_limit', 0.08)
        )

        breached = drawdown_pct > max_drawdown_limit

        return {
            'current_value': round(current_value, 2),
            'high_water_mark': round(hwm, 2),
            'drawdown_pct': round(drawdown_pct, 4),
            'breached': breached,
            'max_drawdown_limit': max_drawdown_limit,
        }

    def check_and_enforce(self, user) -> Dict[str, Any]:
        """
        Check portfolio drawdown and take action if breached.

        Actions on breach:
        1. Create urgent DeFiAlert
        2. Send push notification
        3. Return action signal for crisis de-risk engine (Gap 4)

        Returns:
            dict with: action ('none' or 'derisk'), drawdown data, alert_created (bool)
        """
        drawdown = self.calculate_drawdown(user)

        if not drawdown['breached']:
            return {
                'action': 'none',
                **drawdown,
                'alert_created': False,
            }

        # Check cooldown: don't spam alerts
        cooldown_key = DRAWDOWN_ALERT_KEY.format(user_id=user.id)
        if cache.get(cooldown_key):
            return {
                'action': 'derisk',
                **drawdown,
                'alert_created': False,
            }

        # 1. Create urgent alert
        alert_created = False
        try:
            from .defi_models import DeFiAlert

            DeFiAlert.objects.create(
                user=user,
                alert_type='portfolio_drawdown',
                severity='urgent',
                title='Portfolio Drawdown Limit Breached',
                message=(
                    f'Your portfolio has drawn down {drawdown["drawdown_pct"]:.1%} '
                    f'from its peak of ${drawdown["high_water_mark"]:,.0f}. '
                    f'This exceeds your {drawdown["max_drawdown_limit"]:.0%} limit. '
                    f'Auto-Pilot is evaluating protective actions.'
                ),
                data=drawdown,
            )
            alert_created = True
        except Exception as e:
            logger.error(f"Failed to create drawdown alert for user {user.id}: {e}")

        # 2. Send push notification
        try:
            from .autopilot_notification_service import get_autopilot_notification_service
            service = get_autopilot_notification_service()
            service.notify_portfolio_drawdown(user, drawdown)
        except Exception as e:
            logger.warning(f"Drawdown push notification failed for user {user.id}: {e}")

        # 3. Set cooldown
        cache.set(cooldown_key, True, timeout=DRAWDOWN_ALERT_COOLDOWN_SECONDS)

        # 4. Trigger crisis de-risk engine if available
        try:
            from .crisis_derisk_engine import CrisisDeriskEngine
            engine = CrisisDeriskEngine()
            engine.evaluate_crisis_response('portfolio_drawdown', user=user)
        except ImportError:
            logger.debug("Crisis de-risk engine not yet available")
        except Exception as e:
            logger.warning(f"Crisis de-risk evaluation failed for user {user.id}: {e}")

        logger.critical(
            f"PORTFOLIO DRAWDOWN BREACHED: user={user.id} "
            f"drawdown={drawdown['drawdown_pct']:.2%} "
            f"limit={drawdown['max_drawdown_limit']:.2%} "
            f"value=${drawdown['current_value']:,.0f} "
            f"hwm=${drawdown['high_water_mark']:,.0f}"
        )

        return {
            'action': 'derisk',
            **drawdown,
            'alert_created': alert_created,
        }

    def snapshot_portfolio_value(self, user) -> Dict[str, Any]:
        """
        Store a portfolio value snapshot in cache for historical tracking.
        Called periodically by the monitor task.
        """
        current_value = self.get_portfolio_value(user)
        hwm = self.update_high_water_mark(user, current_value)

        snapshot = {
            'value_usd': round(current_value, 2),
            'high_water_mark': round(hwm, 2),
            'timestamp': timezone.now().isoformat(),
        }

        key = SNAPSHOT_KEY.format(user_id=user.id)
        cache.set(key, snapshot, timeout=86400 * 7)  # Keep for 7 days

        return snapshot


def check_all_portfolio_drawdowns() -> Dict[str, Any]:
    """
    Check portfolio drawdowns for all users with active DeFi positions
    and autopilot enabled. Called from the Celery monitor task.

    Returns:
        dict with stats: users_checked, breaches_detected, alerts_created
    """
    try:
        from .defi_models import UserDeFiPosition
        from .autopilot_service import is_autopilot_enabled

        monitor = PortfolioRiskMonitor()

        user_ids = UserDeFiPosition.objects.filter(
            is_active=True,
        ).values_list('user_id', flat=True).distinct()

        stats = {
            'users_checked': 0,
            'breaches_detected': 0,
            'alerts_created': 0,
        }

        from django.contrib.auth import get_user_model
        User = get_user_model()

        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)

                # Snapshot portfolio value for all users
                monitor.snapshot_portfolio_value(user)

                # Only enforce drawdown limits for autopilot users
                if not is_autopilot_enabled(user):
                    continue

                stats['users_checked'] += 1

                result = monitor.check_and_enforce(user)
                if result['action'] == 'derisk':
                    stats['breaches_detected'] += 1
                if result.get('alert_created'):
                    stats['alerts_created'] += 1

            except Exception as e:
                logger.warning(
                    f"Error checking portfolio drawdown for user {user_id}: {e}"
                )

        logger.info(f"Portfolio drawdown check complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error in portfolio drawdown check: {e}", exc_info=True)
        return {'error': str(e)}


# Singleton
_portfolio_risk_monitor = None


def get_portfolio_risk_monitor() -> PortfolioRiskMonitor:
    global _portfolio_risk_monitor
    if _portfolio_risk_monitor is None:
        _portfolio_risk_monitor = PortfolioRiskMonitor()
    return _portfolio_risk_monitor
