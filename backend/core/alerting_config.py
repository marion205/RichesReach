"""
Alerting Configuration for RichesReach
Supports email and Slack notifications
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AlertingConfig:
    """Configuration for alerting channels"""
    
    def __init__(self):
        self.email_config = {
            'enabled': os.getenv('ALERTING_EMAIL_ENABLED', 'False').lower() == 'true',
            'smtp_host': os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_PORT', '587')),
            'username': os.getenv('EMAIL_HOST_USER', ''),
            'password': os.getenv('EMAIL_HOST_PASSWORD', ''),
            'from_email': os.getenv('DEFAULT_FROM_EMAIL', ''),
            'to_emails': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
        }
        
        self.slack_config = {
            'enabled': os.getenv('ALERTING_SLACK_ENABLED', 'False').lower() == 'true',
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
            'channel': os.getenv('SLACK_CHANNEL', '#alerts'),
            'username': os.getenv('SLACK_USERNAME', 'RichesReach Bot')
        }
    
    def send_email_alert(self, subject: str, message: str, priority: str = 'INFO') -> bool:
        """Send email alert"""
        if not self.email_config['enabled']:
            logger.info("Email alerting disabled")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            msg['Subject'] = f"[{priority}] {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_host'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], self.email_config['to_emails'], text)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def send_slack_alert(self, message: str, priority: str = 'INFO') -> bool:
        """Send Slack alert"""
        if not self.slack_config['enabled']:
            logger.info("Slack alerting disabled")
            return False
        
        try:
            # Color coding based on priority
            color_map = {
                'INFO': '#36a64f',      # Green
                'WARNING': '#ff9500',   # Orange
                'ERROR': '#ff0000',     # Red
                'CRITICAL': '#8b0000'   # Dark red
            }
            
            payload = {
                'channel': self.slack_config['channel'],
                'username': self.slack_config['username'],
                'attachments': [{
                    'color': color_map.get(priority, '#36a64f'),
                    'fields': [{
                        'title': f"RichesReach Alert - {priority}",
                        'value': message,
                        'short': False
                    }],
                    'footer': 'RichesReach Monitoring',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(
                self.slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {priority}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def send_alert(self, subject: str, message: str, priority: str = 'INFO') -> Dict[str, bool]:
        """Send alert to all configured channels"""
        results = {
            'email': self.send_email_alert(subject, message, priority),
            'slack': self.send_slack_alert(message, priority)
        }
        
        return results

# Global alerting instance
alerting = AlertingConfig()

def send_system_alert(subject: str, message: str, priority: str = 'INFO'):
    """Convenience function to send system alerts"""
    return alerting.send_alert(subject, message, priority)

def send_ml_alert(message: str, priority: str = 'WARNING'):
    """Send ML-specific alerts"""
    subject = f"ML Service Alert - {priority}"
    return alerting.send_alert(subject, message, priority)

def send_monitoring_alert(message: str, priority: str = 'ERROR'):
    """Send monitoring alerts"""
    subject = f"Monitoring Alert - {priority}"
    return alerting.send_alert(subject, message, priority)
