"""
Edge Factory Health Alerting Engine

Translates HealthStatus alerts into actionable notifications:
- Slack alerts for ops team (#ops-alerts, #ops-monitor)
- Email summaries for admins
- System-wide broadcast warnings for users

This closes the loop: Detection → Alert → User Notification
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import asdict

from .options_health_monitor import HealthStatus
from .alert_notifications import (
    send_slack_alert,
    send_email_alert,
    send_push_notification,
)

logger = logging.getLogger(__name__)


class EdgeFactoryAlerter:
    """Routes HealthStatus alerts to appropriate notification channels"""

    # Alert severity mapping
    ALERT_SEVERITY = {
        "SKEW_STALE": "warning",
        "LIQUIDITY_SHOCK": "critical",
        "REGIME_STUCK": "warning",
        "POP_DRIFT": "info",
    }

    # Slack channel routing
    ALERT_CHANNELS = {
        "LIQUIDITY_SHOCK": "#ops-alerts",  # Critical - immediate attention
        "REGIME_STUCK": "#ops-monitor",    # Monitoring - investigation needed
        "SKEW_STALE": "#ops-monitor",      # Data quality - caution mode
        "POP_DRIFT": "#ops-monitor",       # Edge decay - track for tuning
    }

    @staticmethod
    def process_health_status(
        ticker: str,
        health: HealthStatus,
        timestamp: Optional[datetime] = None,
        user_count_affected: int = 0,
    ) -> Dict[str, bool]:
        """
        Process a health status and trigger appropriate alerts.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            health: HealthStatus object from run_pre_flight_check()
            timestamp: Event time (defaults to now)
            user_count_affected: Number of users affected by this issue

        Returns:
            Dict with keys: slack_sent, email_sent, push_sent, broadcast_sent
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        result = {
            "slack_sent": False,
            "email_sent": False,
            "push_sent": False,
            "broadcast_sent": False,
        }

        if health.is_healthy:
            # No alerts needed for healthy status
            logger.debug(f"✓ Health check passed for {ticker}")
            return result

        logger.warning(
            f"⚠️ Health check FAILED for {ticker}: {health.active_alerts}"
        )

        # Process each alert
        for alert in health.active_alerts:
            severity = EdgeFactoryAlerter.ALERT_SEVERITY.get(alert.split(":")[0], "info")
            channel = EdgeFactoryAlerter.ALERT_CHANNELS.get(
                alert.split(":")[0], "#ops-monitor"
            )

            # Alert 1: Slack to ops team
            slack_result = EdgeFactoryAlerter._send_slack_alert(
                ticker=ticker,
                alert=alert,
                severity=severity,
                channel=channel,
                timestamp=timestamp,
            )
            result["slack_sent"] = result["slack_sent"] or slack_result

            # Alert 2: Email to admin (batch of critical + warning only)
            if severity in ["critical", "warning"]:
                email_result = EdgeFactoryAlerter._send_email_alert(
                    ticker=ticker,
                    alert=alert,
                    severity=severity,
                    timestamp=timestamp,
                    health_status=health,
                )
                result["email_sent"] = result["email_sent"] or email_result

            # Alert 3: System broadcast (users)
            # Only broadcast critical issues that affect active traders
            if severity == "critical" and user_count_affected > 0:
                broadcast_result = EdgeFactoryAlerter._broadcast_safe_mode(
                    ticker=ticker,
                    alert=alert,
                    user_count_affected=user_count_affected,
                    timestamp=timestamp,
                )
                result["broadcast_sent"] = result["broadcast_sent"] or broadcast_result

        # Alert 4: Daily health summary email (async - batched)
        # This would be triggered by a cron job, not here
        logger.info(
            f"Health alerts processed for {ticker}: "
            f"slack={result['slack_sent']}, "
            f"email={result['email_sent']}, "
            f"broadcast={result['broadcast_sent']}"
        )

        return result

    @staticmethod
    def _send_slack_alert(
        ticker: str,
        alert: str,
        severity: str,
        channel: str,
        timestamp: datetime,
    ) -> bool:
        """Send alert to Slack ops channel"""
        try:
            alert_type = alert.split(":")[0]
            alert_detail = alert.split(":", 1)[1].strip() if ":" in alert else alert

            # Map alert types to emoji
            emoji_map = {
                "SKEW_STALE": "⏰",
                "LIQUIDITY_SHOCK": "🚨",
                "REGIME_STUCK": "🔒",
                "POP_DRIFT": "📊",
            }
            emoji = emoji_map.get(alert_type, "⚠️")

            # Build Slack message
            title = f"{emoji} Edge Factory Alert [{ticker}]"
            message = f"**{alert_type}**: {alert_detail}"

            details = {
                "ticker": ticker,
                "alert_type": alert_type,
                "severity": severity.upper(),
                "timestamp": timestamp.isoformat(),
            }

            result = send_slack_alert(
                alert_level=severity,
                metric_name=f"Edge Factory Health: {alert_type}",
                message=message,
                timestamp=timestamp,
                details=details,
            )

            if result:
                logger.info(f"✓ Slack alert sent to {channel} for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to send Slack alert for {ticker}: {e}")
            return False

    @staticmethod
    def _send_email_alert(
        ticker: str,
        alert: str,
        severity: str,
        timestamp: datetime,
        health_status: HealthStatus,
    ) -> bool:
        """Send detailed email to admin with context"""
        try:
            alert_type = alert.split(":")[0]

            # Build detailed email
            title = f"[{severity.upper()}] Edge Factory Health Alert: {ticker}"
            
            # Build detailed message with remediation
            remediation_map = {
                "SKEW_STALE": (
                    "- Check Polygon data feed status\n"
                    "- Verify CBOE SKEW index availability\n"
                    "- Consider switching to conservative routing"
                ),
                "LIQUIDITY_SHOCK": (
                    "- Check option chain bid/ask spreads\n"
                    "- Monitor trading volume\n"
                    "- Consider holding open positions\n"
                    "- Pause new entry recommendations"
                ),
                "REGIME_STUCK": (
                    "- Review regime indicators\n"
                    "- Check for market discontinuities\n"
                    "- May indicate regime model drift"
                ),
                "POP_DRIFT": (
                    "- PoP (Probability of Profit) deviating from historical\n"
                    "- Review option pricing vs. model\n"
                    "- May indicate market shift or data error"
                ),
            }

            remediation = remediation_map.get(alert_type, "- Investigate manually")

            message = f"""
Edge Factory Health Monitor Alert

**Ticker:** {ticker}
**Alert Type:** {alert_type}
**Severity:** {severity.upper()}
**Timestamp:** {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

**Issue:**
{alert.split(':', 1)[1].strip() if ':' in alert else alert}

**Data Freshness:** {health_status.data_freshness}
**Logic Confidence:** {health_status.logic_confidence:.0%}

**Recommended Actions:**
{remediation}

**Active Alerts:**
{chr(10).join(f'  • {a}' for a in health_status.active_alerts)}

---
This is an automated alert from the Edge Factory Health Monitor.
Log in to the admin console to take further action.
            """

            result = send_email_alert(
                alert_level=severity,
                metric_name=f"Edge Factory Health Alert: {alert_type}",
                message=message,
                timestamp=timestamp,
                details={
                    "ticker": ticker,
                    "alert_type": alert_type,
                    "data_freshness": health_status.data_freshness,
                    "logic_confidence": health_status.logic_confidence,
                    "all_alerts": health_status.active_alerts,
                },
            )

            if result:
                logger.info(f"✓ Email alert sent for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to send email alert for {ticker}: {e}")
            return False

    @staticmethod
    def _broadcast_safe_mode(
        ticker: str,
        alert: str,
        user_count_affected: int,
        timestamp: datetime,
    ) -> bool:
        """
        Broadcast system-wide notice to users when critical issues detected.
        
        Example: "Market liquidity is currently low for AAPL. 
                 Strategy routing is in Conservative Mode."
        """
        try:
            alert_type = alert.split(":")[0]

            # Map alert types to user-friendly messages
            user_messages = {
                "LIQUIDITY_SHOCK": (
                    f"Market liquidity is currently low for {ticker}. "
                    "Strategy routing is in Conservative Mode. "
                    "Wider spreads than usual are expected."
                ),
                "SKEW_STALE": (
                    f"Data freshness issue detected for {ticker}. "
                    "Recommendations are in Caution Mode. "
                    "Consider reviewing market conditions."
                ),
                "REGIME_STUCK": (
                    f"Market regime detector may be recalibrating for {ticker}. "
                    "Recommendations updated with increased caution."
                ),
                "POP_DRIFT": (
                    f"Profit probability models are recalibrating for {ticker}. "
                    "Edge thresholds have been raised."
                ),
            }

            user_message = user_messages.get(
                alert_type,
                f"System is operating in Conservative Mode for {ticker} due to data quality concerns.",
            )

            # Send push notification to all affected users
            result = send_push_notification(
                title=f"⚠️ {ticker} Safety Alert",
                body=user_message,
                priority="high",
                data={
                    "ticker": ticker,
                    "alert_type": alert_type,
                    "mode": "conservative",
                    "timestamp": timestamp.isoformat(),
                },
            )

            logger.info(
                f"✓ Broadcast safe-mode notice for {ticker} "
                f"({user_count_affected} users affected)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to broadcast safe-mode for {ticker}: {e}")
            return False

    @staticmethod
    def generate_daily_health_summary(
        health_checks: List[Dict],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Generate and send daily health summary email to admins.
        
        This would be called by a scheduled cron job once per day.
        
        Args:
            health_checks: List of dicts with ticker, status, timestamp
            timestamp: Report date (defaults to today)
            
        Returns:
            True if email sent successfully
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        try:
            healthy_count = sum(
                1 for check in health_checks if check.get("is_healthy", True)
            )
            unhealthy_count = len(health_checks) - healthy_count
            alert_summary = {}

            # Aggregate alerts
            for check in health_checks:
                for alert in check.get("alerts", []):
                    alert_type = alert.split(":")[0]
                    alert_summary[alert_type] = alert_summary.get(alert_type, 0) + 1

            # Build summary table
            alert_table = "\n".join(
                f"  {alert_type}: {count} occurrence(s)"
                for alert_type, count in sorted(alert_summary.items())
            )

            message = f"""
Daily Edge Factory Health Summary
Report Date: {timestamp.strftime('%Y-%m-%d')}

**Overall Status:**
  ✓ Healthy: {healthy_count}/{len(health_checks)} tickers
  ⚠️ Unhealthy: {unhealthy_count}/{len(health_checks)} tickers

**Alert Breakdown:**
{alert_table if alert_summary else "  No alerts - all systems green ✓"}

**Action Required:**
{f"Review {unhealthy_count} unhealthy ticker(s) in the admin console." if unhealthy_count > 0 else "All systems operating normally."}

---
This is an automated report from the Edge Factory Health Monitor.
            """

            result = send_email_alert(
                alert_level="info",
                metric_name="Daily Edge Factory Health Summary",
                message=message,
                timestamp=timestamp,
                details={
                    "healthy_count": healthy_count,
                    "unhealthy_count": unhealthy_count,
                    "alert_summary": alert_summary,
                },
            )

            if result:
                logger.info(f"✓ Daily health summary sent")
            return result

        except Exception as e:
            logger.error(f"Failed to generate daily health summary: {e}")
            return False
