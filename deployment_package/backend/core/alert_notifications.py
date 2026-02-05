"""
Alert Notification System
Sends email and Slack notifications for performance monitoring alerts

Includes Regime Shift Alerts: When market regime changes (e.g., Trend Up → Crash Panic),
broadcasts high-priority notifications to all users so they can adjust strategy selection.
"""
import os
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .options_regime_detector import get_flight_manual_for_regime

logger = logging.getLogger(__name__)


def send_email_alert(alert_level: str, metric_name: str, message: str, 
                     timestamp: Any, details: Dict[str, Any] = None) -> bool:
    """Send email alert notification"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    alert_email_to = os.getenv('ALERT_EMAIL_TO')
    
    if not all([smtp_host, smtp_user, smtp_password, alert_email_to]):
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{alert_level.upper()}] Performance Alert: {metric_name}"
        msg['From'] = smtp_user
        msg['To'] = alert_email_to
        
        # Create email body
        text = f"""
Performance Monitoring Alert

Level: {alert_level.upper()}
Metric: {metric_name}
Message: {message}
Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)}

Additional Details:
{json.dumps(details, indent=2) if details else 'N/A'}
        """
        
        html = f"""
<html>
  <body>
    <h2 style="color: {'red' if alert_level == 'critical' else 'orange'}">
      [{alert_level.upper()}] Performance Alert
    </h2>
    <p><strong>Metric:</strong> {metric_name}</p>
    <p><strong>Message:</strong> {message}</p>
    <p><strong>Time:</strong> {timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)}</p>
    {f'<p><strong>Details:</strong><pre>{json.dumps(details, indent=2)}</pre></p>' if details else ''}
  </body>
</html>
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email alert sent to {alert_email_to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def send_slack_alert(alert_level: str, metric_name: str, message: str, 
                     timestamp: Any, details: Dict[str, Any] = None) -> bool:
    """Send Slack alert notification"""
    if not REQUESTS_AVAILABLE:
        return False
        
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not slack_webhook_url:
        return False
    
    try:
        color = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'error': '#ff0000',
            'critical': '#8b0000'
        }.get(alert_level.lower(), '#808080')
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f":warning: Performance Alert: {metric_name}",
                "text": message,
                "fields": [
                    {
                        "title": "Level",
                        "value": alert_level.upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp),
                        "short": True
                    }
                ],
                "footer": "Performance Monitoring Service",
                "ts": int(timestamp.timestamp()) if hasattr(timestamp, 'timestamp') else None
            }]
        }
        
        if details:
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": f"```{json.dumps(details, indent=2)}```",
                "short": False
            })
        
        response = requests.post(
            slack_webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info("Slack alert sent successfully")
            return True
        else:
            logger.error(f"Slack alert failed: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False

def send_regime_shift_alert(new_regime: str, previous_regime: Optional[str],
                            description: str, timestamp: Optional[datetime] = None) -> bool:
    """
    Send high-priority alert when market regime changes.
    
    Example: "Market Regime Shift: TREND_UP → CRASH_PANIC"
    
    This triggers updates to:
    - Mobile: Pushes Flight Manual for new regime
    - Web: Shows banner with strategy recommendations
    - API: Updates active_regime cache for router
    
    Args:
        new_regime: New regime string (e.g., "CRASH_PANIC")
        previous_regime: Prior regime (for context)
        description: Human-friendly description from RegimeDetector
        timestamp: Event time (defaults to now)
    
    Returns:
        True if alert sent successfully
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Get Flight Manual context for this regime
    flight_manual = get_flight_manual_for_regime(new_regime)
    
    # Determine priority based on regime severity
    alert_level = "critical" if new_regime == "CRASH_PANIC" else "warning"
    action_required = new_regime in ["CRASH_PANIC", "BREAKOUT_EXPANSION"]
    
    # Build alert message
    prev_str = f" (from {previous_regime})" if previous_regime else ""
    title = f"⚠️ MARKET REGIME SHIFT: {new_regime}{prev_str}"
    
    message = f"""
{description}

**Active Strategies:** {', '.join(flight_manual['active_strategies']) or 'None (apply fundamentals)'}
**Action:** {flight_manual['action']}

This regime change may require adjusting your strategy selection. Review active trades for compatibility.
    """
    
    # Send notifications
    details = {
        "new_regime": new_regime,
        "previous_regime": previous_regime,
        "description": description,
        "flight_manual": flight_manual,
        "action_required": action_required,
        "timestamp": timestamp.isoformat(),
    }
    
    # Email
    email_sent = send_email_alert(
        alert_level=alert_level,
        metric_name="Market Regime Shift",
        message=title,
        timestamp=timestamp,
        details=details
    )
    
    # Slack
    slack_sent = send_slack_alert(
        alert_level=alert_level,
        metric_name="Market Regime Shift",
        message=title,
        timestamp=timestamp,
        details=details
    )
    
    # Push notification (for mobile app)
    push_sent = send_push_notification(
        title=title,
        body=flight_manual['summary'],
        priority="high" if action_required else "normal",
        data={
            "regime": new_regime,
            "action_required": action_required,
            "flight_manual": json.dumps(flight_manual)
        }
    )
    
    logger.info(f"Regime shift alert sent: {new_regime} "
               f"(email={email_sent}, slack={slack_sent}, push={push_sent})")
    
    return any([email_sent, slack_sent, push_sent])


def send_push_notification(title: str, body: str, priority: str = "normal",
                          data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send push notification to mobile app (Firebase Cloud Messaging or equivalent).
    
    Args:
        title: Notification title
        body: Notification body
        priority: "high" or "normal"
        data: Optional additional data payload
    
    Returns:
        True if sent successfully
    """
    # Implementation depends on your push notification service
    # This is a placeholder that logs the notification
    
    logger.info(f"📱 PUSH: [{priority}] {title} — {body}")
    
    # TODO: Integrate with Firebase FCM or equivalent
    # fcm_client.send_multicast_message(...)
    
    return True