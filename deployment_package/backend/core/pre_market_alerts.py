"""
Pre-Market Alert System - Email, Push Notifications, and Webhooks
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PreMarketAlertService:
    """
    Service for sending pre-market alerts via email and push notifications.
    """
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', '')
        self.push_notification_key = os.getenv('PUSH_NOTIFICATION_KEY', '')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK', '').strip()
        self.slack_webhook = os.getenv('SLACK_WEBHOOK', '').strip()
    
    def send_email_alert(self, setups: List[Dict], subject: str = None) -> bool:
        """
        Send email alert with pre-market setups.
        
        Args:
            setups: List of pre-market setups
            subject: Email subject (optional)
        
        Returns:
            bool: True if sent successfully
        """
        if not self.alert_email:
            logger.warning("No ALERT_EMAIL configured - skipping email alert")
            return False
        
        try:
            # Generate email content
            html_content = self._generate_email_html(setups)
            text_content = self._generate_email_text(setups)
            
            # Use Django's email backend if configured
            if hasattr(settings, 'EMAIL_BACKEND'):
                send_mail(
                    subject=subject or f"🔔 Pre-Market Alert: {len(setups)} Quality Setups",
                    message=text_content,
                    from_email=self.smtp_user or settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.alert_email],
                    html_message=html_content,
                    fail_silently=False,
                )
                logger.info(f"✅ Email alert sent to {self.alert_email}")
                return True
            else:
                # Fallback: direct SMTP
                return self._send_smtp_email(setups, subject)
                
        except Exception as e:
            logger.error(f"Error sending email alert: {e}", exc_info=True)
            return False
    
    def _send_smtp_email(self, setups: List[Dict], subject: str = None) -> bool:
        """Send email via direct SMTP"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject or f"🔔 Pre-Market Alert: {len(setups)} Quality Setups"
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email
            
            # Add text and HTML parts
            text_part = MIMEText(self._generate_email_text(setups), 'plain')
            html_part = MIMEText(self._generate_email_html(setups), 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email alert sent via SMTP to {self.alert_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMTP email: {e}", exc_info=True)
            return False
    
    def _generate_email_html(self, setups: List[Dict], top_3_only: bool = True) -> str:
        """
        Generate HTML email content with "Top 3 Only" format.
        Top 3 ML-ranked plays (big bold), then collapsible "All others" section.
        """
        top_3 = setups[:3]
        others = setups[3:] if len(setups) > 3 else []
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #007AFF; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .top-3 {{ margin-bottom: 30px; }}
                .setup {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .setup.top-3-setup {{ border: 3px solid #007AFF; background-color: #f0f8ff; }}
                .symbol {{ font-size: 24px; font-weight: bold; color: #007AFF; }}
                .top-3 .symbol {{ font-size: 28px; }}
                .metrics {{ margin: 10px 0; }}
                .metric {{ display: inline-block; margin-right: 20px; }}
                .label {{ font-weight: bold; }}
                .long {{ color: green; }}
                .short {{ color: red; }}
                .others-section {{ margin-top: 30px; }}
                .others-toggle {{ cursor: pointer; color: #007AFF; text-decoration: underline; }}
                .others-content {{ display: none; }}
                .others-content.show {{ display: block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔔 Pre-Market Alert</h1>
                <p>{len(setups)} Quality Setups Found</p>
            </div>
            <div class="content">
                <div class="top-3">
                    <h2 style="font-size: 22px; color: #007AFF; margin-bottom: 20px;">🎯 TOP 3 ML-RANKED PLAYS</h2>
        """
        
        # Top 3 (big and bold)
        for i, setup in enumerate(top_3, 1):
            symbol = setup.get('symbol', 'N/A')
            side = setup.get('side', 'N/A')
            change = setup.get('pre_market_change_pct', 0)
            price = setup.get('pre_market_price', 0)
            score = setup.get('score', 0)
            ml_prob = setup.get('ml_success_probability')
            
            side_class = 'long' if side == 'LONG' else 'short'
            
            is_top_3 = i <= 3
            setup_class = "setup top-3-setup" if is_top_3 else "setup"
            
            html += f"""
                <div class="setup top-3-setup">
                    <div class="symbol">{i}. {symbol} - <span class="{side_class}">{side}</span></div>
                    <div class="metrics">
                        <div class="metric">
                            <span class="label">Pre-Market Move:</span> {change:+.2%}
                        </div>
                        <div class="metric">
                            <span class="label">Price:</span> ${price:.2f}
                        </div>
                        <div class="metric">
                            <span class="label">Score:</span> {score:.2f}
                        </div>
            """
            
            if ml_prob is not None:
                html += f"""
                        <div class="metric">
                            <span class="label">ML Success Prob:</span> <strong>{ml_prob:.1%}</strong>
                        </div>
                """
            
            html += f"""
                    </div>
                    <p>{setup.get('notes', '')}</p>
                </div>
            """
        
        # Add "All others" collapsible section
        if others and top_3_only:
            html += """
                </div>
                <div class="others-section">
                    <h3 class="others-toggle" onclick="document.getElementById('others-content').classList.toggle('show')">
                        📋 View All {len(others)} Other Setups (Click to expand)
                    </h3>
                    <div id="others-content" class="others-content">
            """
            
            for i, setup in enumerate(others, 4):
                symbol = setup.get('symbol', 'N/A')
                side = setup.get('side', 'N/A')
                change = setup.get('pre_market_change_pct', 0)
                price = setup.get('pre_market_price', 0)
                score = setup.get('score', 0)
                ml_prob = setup.get('ml_success_probability')
                side_class = 'long' if side == 'LONG' else 'short'
                
                html += f"""
                    <div class="setup">
                        <div class="symbol">{i}. {symbol} - <span class="{side_class}">{side}</span></div>
                        <div class="metrics">
                            <div class="metric">Move: {change:+.2%}</div>
                            <div class="metric">Price: ${price:.2f}</div>
                            <div class="metric">Score: {score:.2f}</div>
                """
                
                if ml_prob is not None:
                    html += f'<div class="metric">ML Prob: {ml_prob:.1%}</div>'
                
                html += f"""
                        </div>
                        <p>{setup.get('notes', '')}</p>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        else:
            html += "</div>"
        
        html += """
            <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
                <p><strong>⚠️ Risk Warning:</strong> Pre-market moves can reverse at open. Use proper risk management.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_email_text(self, setups: List[Dict]) -> str:
        """Generate plain text email content"""
        text = f"🔔 PRE-MARKET ALERT - {len(setups)} Quality Setups Found\n"
        text += "=" * 80 + "\n\n"
        
        for i, setup in enumerate(setups[:10], 1):
            symbol = setup.get('symbol', 'N/A')
            side = setup.get('side', 'N/A')
            change = setup.get('pre_market_change_pct', 0)
            price = setup.get('pre_market_price', 0)
            score = setup.get('score', 0)
            ml_prob = setup.get('ml_success_probability')
            
            text += f"{i}. {symbol} - {side}\n"
            text += f"   Pre-market: {change:+.2%} | Price: ${price:.2f} | Score: {score:.2f}"
            
            if ml_prob is not None:
                text += f" | ML Prob: {ml_prob:.1%}"
            
            text += f"\n   {setup.get('notes', '')}\n\n"
        
        text += "=" * 80 + "\n"
        text += "⚠️  Risk Warning: Pre-market moves can reverse at open. Use proper risk management.\n"
        
        return text
    
    def send_push_notification(self, setups: List[Dict]) -> bool:
        """
        Send push notification (mobile app integration).
        This would integrate with your mobile app's push notification service.
        """
        if not self.push_notification_key:
            logger.warning("No push notification key configured")
            return False
        try:
            # Placeholder for push notification logic
            # You would send to your mobile app's push notification endpoint
            
            notification_data = {
                'title': f'Pre-Market Alert: {len(setups)} Setups',
                'body': f"Top pick: {setups[0].get('symbol')} - {setups[0].get('side')}",
                'data': {
                    'type': 'pre_market_alert',
                    'setups_count': len(setups),
                    'top_pick': setups[0].get('symbol') if setups else None,
                }
            }
            
            logger.info(f"📱 Push notification prepared: {notification_data['title']}")
            # Deferred: send via FCM/APNs when notification service is integrated
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return False


# Global instance
_alert_service_instance = None

def get_alert_service() -> PreMarketAlertService:
    """Get or create global alert service instance"""
    global _alert_service_instance
    if _alert_service_instance is None:
        _alert_service_instance = PreMarketAlertService()
    return _alert_service_instance

