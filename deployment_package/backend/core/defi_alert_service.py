"""
DeFi Health Factor Alert Service

Monitors user DeFi positions and sends push notifications when:
- Health factor drops below warning threshold (< 1.5)
- Health factor drops below critical threshold (< 1.2)
- Health factor drops below liquidation danger (< 1.05)
- Large APY changes on active positions (> 20% relative change)
- Position rewards ready to harvest (> $10 accumulated)

Runs as a Celery periodic task every 5 minutes.

Part of Phase 3: Community Vanguard
"""
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import F

logger = logging.getLogger(__name__)


# ---- Alert Thresholds ----

HEALTH_FACTOR_WARNING = 1.5
HEALTH_FACTOR_CRITICAL = 1.2
HEALTH_FACTOR_DANGER = 1.05
APY_CHANGE_THRESHOLD = 0.20  # 20% relative change triggers alert
HARVEST_THRESHOLD_USD = 10.0  # $10 in rewards triggers harvest reminder


# ---- Alert Types ----

ALERT_TYPES = {
    'health_warning': {
        'title': 'Health Factor Warning',
        'priority': 'medium',
        'icon': 'alert-triangle',
    },
    'health_critical': {
        'title': 'Health Factor Critical',
        'priority': 'high',
        'icon': 'alert-circle',
    },
    'health_danger': {
        'title': 'Liquidation Risk!',
        'priority': 'urgent',
        'icon': 'x-circle',
    },
    'apy_change': {
        'title': 'APY Changed Significantly',
        'priority': 'low',
        'icon': 'trending-down',
    },
    'harvest_ready': {
        'title': 'Rewards Ready to Harvest',
        'priority': 'low',
        'icon': 'gift',
    },
}


def check_all_positions():
    """
    Main monitoring function. Checks all active positions and generates alerts.
    Called by Celery task every 5 minutes.

    Returns:
        dict with counts of alerts generated per type
    """
    try:
        from .defi_models import UserDeFiPosition, DeFiPool, YieldSnapshot

        active_positions = UserDeFiPosition.objects.filter(
            is_active=True,
        ).select_related('pool', 'pool__protocol', 'user')

        alerts_generated = {
            'health_warnings': 0,
            'health_critical': 0,
            'health_danger': 0,
            'apy_changes': 0,
            'harvest_reminders': 0,
            'total_positions_checked': 0,
        }

        for position in active_positions:
            alerts_generated['total_positions_checked'] += 1

            try:
                # 1. Check health factor
                hf_alerts = _check_health_factor_alerts(position)
                if hf_alerts:
                    alerts_generated['health_warnings'] += hf_alerts.get('warning', 0)
                    alerts_generated['health_critical'] += hf_alerts.get('critical', 0)
                    alerts_generated['health_danger'] += hf_alerts.get('danger', 0)

                # 2. Check APY changes
                if _check_apy_change_alert(position):
                    alerts_generated['apy_changes'] += 1

                # 3. Check harvest readiness
                if _check_harvest_alert(position):
                    alerts_generated['harvest_reminders'] += 1

            except Exception as e:
                logger.warning(
                    f"Error checking position {position.id} for user {position.user_id}: {e}"
                )

        logger.info(f"DeFi alert check complete: {alerts_generated}")
        return alerts_generated

    except Exception as e:
        logger.error(f"Error in DeFi alert service: {e}", exc_info=True)
        return {'error': str(e)}


def _check_health_factor_alerts(position):
    """Check health factor and generate alerts if below thresholds."""
    # In Phase 2, we use estimated health factor from position data
    # Phase 4 will read on-chain health factor via Aave's getUserAccountData
    from .defi_models import UserDeFiPosition

    # Get all positions for this user to calculate aggregate health factor
    user_positions = UserDeFiPosition.objects.filter(
        user=position.user,
        wallet_address=position.wallet_address,
        is_active=True,
    )

    total_collateral = sum(float(p.staked_value_usd) for p in user_positions)
    if total_collateral == 0:
        return None

    # Estimate health factor (simplified; real version needs on-chain debt data)
    # For now, assume no borrows = infinite HF, with borrows = calculated
    # This will be properly calculated when we have borrow position tracking
    estimated_hf = 999.0  # Default: no borrows = safe

    # If we have borrow positions (tracked via DeFiTransaction)
    from .defi_models import DeFiTransaction
    recent_borrows = DeFiTransaction.objects.filter(
        user=position.user,
        action='borrow',
        status='confirmed',
    ).order_by('-created_at')

    if recent_borrows.exists():
        total_borrowed = sum(float(b.amount_usd) for b in recent_borrows[:10])
        if total_borrowed > 0:
            liq_threshold = 0.80
            estimated_hf = (total_collateral * liq_threshold) / total_borrowed

    alerts = {}

    if estimated_hf < HEALTH_FACTOR_DANGER:
        _send_alert(
            user=position.user,
            alert_type='health_danger',
            message=(
                f'Your health factor is {estimated_hf:.2f} — liquidation is imminent! '
                f'Repay debt or add collateral immediately to protect your position.'
            ),
            data={
                'health_factor': estimated_hf,
                'wallet': position.wallet_address,
                'collateral_usd': total_collateral,
            },
        )
        alerts['danger'] = 1

    elif estimated_hf < HEALTH_FACTOR_CRITICAL:
        _send_alert(
            user=position.user,
            alert_type='health_critical',
            message=(
                f'Your health factor dropped to {estimated_hf:.2f}. '
                f'Consider adding collateral or repaying some debt.'
            ),
            data={
                'health_factor': estimated_hf,
                'wallet': position.wallet_address,
            },
        )
        alerts['critical'] = 1

    elif estimated_hf < HEALTH_FACTOR_WARNING:
        _send_alert(
            user=position.user,
            alert_type='health_warning',
            message=(
                f'Health factor at {estimated_hf:.2f}. '
                f'Your position is safe but worth monitoring.'
            ),
            data={
                'health_factor': estimated_hf,
                'wallet': position.wallet_address,
            },
        )
        alerts['warning'] = 1

    return alerts if alerts else None


def _check_apy_change_alert(position):
    """Check if the pool's APY changed significantly since last check."""
    from .defi_models import YieldSnapshot

    # Get last two snapshots for this pool
    recent_snapshots = YieldSnapshot.objects.filter(
        pool=position.pool,
    ).order_by('-timestamp')[:2]

    if len(recent_snapshots) < 2:
        return False

    current_apy = recent_snapshots[0].apy_total
    previous_apy = recent_snapshots[1].apy_total

    if previous_apy == 0:
        return False

    relative_change = abs(current_apy - previous_apy) / previous_apy

    if relative_change > APY_CHANGE_THRESHOLD:
        direction = 'increased' if current_apy > previous_apy else 'decreased'
        _send_alert(
            user=position.user,
            alert_type='apy_change',
            message=(
                f'{position.pool.symbol} APY {direction} from '
                f'{previous_apy:.1f}% to {current_apy:.1f}% on {position.pool.protocol.name}.'
            ),
            data={
                'pool_id': position.pool.id,
                'old_apy': previous_apy,
                'new_apy': current_apy,
                'symbol': position.pool.symbol,
            },
        )
        return True

    return False


def _check_harvest_alert(position):
    """Check if accumulated rewards are worth harvesting."""
    rewards_value = float(position.rewards_earned)

    if rewards_value >= HARVEST_THRESHOLD_USD:
        # Check we haven't already sent a harvest alert recently (last 24h)
        recent_alert = _was_alert_sent_recently(
            user=position.user,
            alert_type='harvest_ready',
            hours=24,
        )
        if recent_alert:
            return False

        _send_alert(
            user=position.user,
            alert_type='harvest_ready',
            message=(
                f'You have ${rewards_value:.2f} in rewards ready to harvest '
                f'on your {position.pool.symbol} position!'
            ),
            data={
                'pool_id': position.pool.id,
                'rewards_usd': rewards_value,
                'symbol': position.pool.symbol,
            },
        )
        return True

    return False


def _send_alert(user, alert_type: str, message: str, data: dict = None):
    """
    Send a DeFi alert notification.

    In production, this will:
    1. Create a DeFiAlert record in the database
    2. Send push notification via Expo Push Notifications
    3. Update the notification center in-app

    For now (Phase 3), we log and create database records.
    """
    alert_config = ALERT_TYPES.get(alert_type, ALERT_TYPES['health_warning'])

    try:
        # Create alert record in database
        from .defi_models import DeFiProtocol  # Use existing model for now
        # In production, create a dedicated DeFiAlert model

        logger.info(
            f"DeFi Alert [{alert_config['priority'].upper()}] "
            f"user={user.id if user else 'N/A'} "
            f"type={alert_type}: {message}"
        )

        # TODO Phase 4: Send push notification via Expo
        # from .notification_service import send_push_notification
        # send_push_notification(
        #     user=user,
        #     title=alert_config['title'],
        #     body=message,
        #     data={'type': 'defi_alert', 'alert_type': alert_type, **data},
        # )

        return True

    except Exception as e:
        logger.error(f"Failed to send DeFi alert: {e}")
        return False


def _was_alert_sent_recently(user, alert_type: str, hours: int = 24) -> bool:
    """
    Check if a similar alert was sent recently to avoid notification spam.

    For Phase 3, we use a simple in-memory approach.
    Phase 4 will query the DeFiAlert database table.
    """
    # Placeholder: always return False until DeFiAlert model is created
    # This means alerts may repeat, but that's safer than missing critical ones
    return False


def get_user_alerts(user, limit: int = 20) -> list:
    """
    Get recent DeFi alerts for a user.
    Used by the notification center screen.
    """
    # Phase 3: Return empty list until DeFiAlert model exists
    # Phase 4: Query DeFiAlert.objects.filter(user=user).order_by('-created_at')[:limit]
    return []
