"""
Alert Notification System
Sends email and Slack notifications for performance monitoring alerts
"""
import os
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

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
