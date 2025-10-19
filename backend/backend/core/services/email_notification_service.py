"""
Email Notification Service
Handles workflow step notifications and trading alerts
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service for sending email notifications for KYC workflows and trading activities"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@richesreach.com')
        self.support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@richesreach.com')
        self.app_name = "RichesReach"
        self.base_url = getattr(settings, 'FRONTEND_URL', 'https://app.richesreach.com')
    
    def _send_email(self, subject: str, to_emails: List[str], html_content: str, text_content: str = None) -> bool:
        """Send email with HTML and text content"""
        try:
            if not to_emails:
                logger.warning("No email addresses provided")
                return False
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content or self._html_to_text(html_content),
                from_email=self.from_email,
                to=to_emails
            )
            
            # Attach HTML content
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            result = msg.send()
            logger.info(f"Email sent successfully to {to_emails}: {subject}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {e}")
            return False
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text"""
        import re
        # Simple HTML to text conversion
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _get_user_context(self, user: User) -> Dict[str, Any]:
        """Get user context for email templates"""
        return {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'user_email': user.email,
            'app_name': self.app_name,
            'base_url': self.base_url,
            'support_email': self.support_email,
            'current_year': datetime.now().year,
        }
    
    # =============================================================================
    # KYC WORKFLOW NOTIFICATIONS
    # =============================================================================
    
    def send_kyc_workflow_started(self, user: User, workflow_type: str) -> bool:
        """Send notification when KYC workflow is started"""
        try:
            context = self._get_user_context(user)
            context.update({
                'workflow_type': workflow_type,
                'workflow_name': 'Brokerage Account' if workflow_type == 'brokerage' else 'Crypto Account',
                'estimated_time': '3-5 business days',
                'next_steps': self._get_kyc_next_steps(workflow_type)
            })
            
            subject = f"🎯 {self.app_name} - {context['workflow_name']} KYC Started"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .step {{ background: #F8FAFC; border-left: 4px solid #007AFF; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
                    .cta {{ background: #007AFF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 KYC Process Started</h1>
                        <p>Welcome to {context['workflow_name']} verification</p>
                    </div>
                    <div class="content">
                        <h2>Hello {context['user_name']}!</h2>
                        <p>Your {context['workflow_name']} KYC (Know Your Customer) verification process has been initiated. This is a required step to enable real money trading on our platform.</p>
                        
                        <h3>📋 What's Next?</h3>
                        {self._render_kyc_steps(context['next_steps'])}
                        
                        <h3>⏱️ Timeline</h3>
                        <p>We estimate the verification process will take <strong>{context['estimated_time']}</strong>. You'll receive email updates as you progress through each step.</p>
                        
                        <div style="text-align: center;">
                            <a href="{context['base_url']}/kyc" class="cta">Continue KYC Process</a>
                        </div>
                        
                        <h3>📞 Need Help?</h3>
                        <p>If you have any questions during the process, our support team is here to help:</p>
                        <ul>
                            <li>Email: <a href="mailto:{context['support_email']}">{context['support_email']}</a></li>
                            <li>Response time: Within 24 hours</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>&copy; {context['current_year']} {self.app_name}. All rights reserved.</p>
                        <p>This email was sent to {context['user_email']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(subject, [user.email], html_content)
            
        except Exception as e:
            logger.error(f"Failed to send KYC workflow started email: {e}")
            return False
    
    def send_kyc_step_completed(self, user: User, step_name: str, step_number: int, total_steps: int, workflow_type: str) -> bool:
        """Send notification when a KYC step is completed"""
        try:
            context = self._get_user_context(user)
            context.update({
                'step_name': step_name,
                'step_number': step_number,
                'total_steps': total_steps,
                'progress_percentage': int((step_number / total_steps) * 100),
                'workflow_type': workflow_type,
                'is_final_step': step_number == total_steps
            })
            
            if context['is_final_step']:
                subject = f"🎉 {self.app_name} - KYC Process Complete!"
            else:
                subject = f"✅ {self.app_name} - Step {step_number} Complete: {step_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .progress {{ background: #F3F4F6; border-radius: 10px; height: 20px; margin: 20px 0; }}
                    .progress-bar {{ background: linear-gradient(90deg, #22C55E 0%, #16A34A 100%); height: 100%; border-radius: 10px; width: {context['progress_percentage']}%; transition: width 0.3s ease; }}
                    .cta {{ background: #007AFF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{"🎉 KYC Complete!" if context['is_final_step'] else "✅ Step Complete"}</h1>
                        <p>{"Your verification is ready for review" if context['is_final_step'] else f"Step {step_number} of {total_steps} completed"}</p>
                    </div>
                    <div class="content">
                        <h2>Hello {context['user_name']}!</h2>
                        
                        {"<p><strong>Congratulations!</strong> You've successfully completed all KYC verification steps. Your application is now being reviewed by our compliance team.</p>" if context['is_final_step'] else f"<p>Great progress! You've successfully completed: <strong>{step_name}</strong></p>"}
                        
                        <div class="progress">
                            <div class="progress-bar"></div>
                        </div>
                        <p style="text-align: center; margin: 0;"><strong>{context['progress_percentage']}% Complete</strong></p>
                        
                        {"<h3>📋 What Happens Next?</h3><p>Our compliance team will review your application within 1-2 business days. You'll receive an email notification once your account is approved and ready for trading.</p>" if context['is_final_step'] else "<h3>📋 Next Step</h3><p>Continue with the next step in your KYC process to complete your account verification.</p>"}
                        
                        <div style="text-align: center;">
                            <a href="{context['base_url']}/kyc" class="cta">{"View Status" if context['is_final_step'] else "Continue KYC"}</a>
                        </div>
                    </div>
                    <div class="footer">
                        <p>&copy; {context['current_year']} {self.app_name}. All rights reserved.</p>
                        <p>This email was sent to {context['user_email']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(subject, [user.email], html_content)
            
        except Exception as e:
            logger.error(f"Failed to send KYC step completed email: {e}")
            return False
    
    def send_kyc_approval_notification(self, user: User, account_type: str, account_id: str) -> bool:
        """Send notification when KYC is approved"""
        try:
            context = self._get_user_context(user)
            context.update({
                'account_type': account_type,
                'account_id': account_id,
                'trading_enabled': True
            })
            
            subject = f"🎉 {self.app_name} - Account Approved! Start Trading Now"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .feature {{ background: #F8FAFC; border-left: 4px solid #22C55E; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
                    .cta {{ background: #007AFF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Account Approved!</h1>
                        <p>Your {account_type} account is ready for trading</p>
                    </div>
                    <div class="content">
                        <h2>Congratulations {context['user_name']}!</h2>
                        <p>Your {account_type} account has been approved and is now active. You can start trading with real money!</p>
                        
                        <h3>🚀 What You Can Do Now</h3>
                        <div class="feature">
                            <strong>📈 Stock & ETF Trading</strong><br>
                            Buy and sell stocks, ETFs, and other securities
                        </div>
                        <div class="feature">
                            <strong>💰 Cryptocurrency Trading</strong><br>
                            Trade popular crypto pairs like BTC/USD, ETH/USD
                        </div>
                        <div class="feature">
                            <strong>📊 Portfolio Management</strong><br>
                            Track your investments and performance
                        </div>
                        <div class="feature">
                            <strong>🤖 AI Recommendations</strong><br>
                            Get personalized investment suggestions
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{context['base_url']}/trading" class="cta">Start Trading Now</a>
                        </div>
                        
                        <h3>📞 Need Help Getting Started?</h3>
                        <p>Our support team is here to help you make your first trade:</p>
                        <ul>
                            <li>Email: <a href="mailto:{context['support_email']}">{context['support_email']}</a></li>
                            <li>Live chat available in the app</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>&copy; {context['current_year']} {self.app_name}. All rights reserved.</p>
                        <p>This email was sent to {context['user_email']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(subject, [user.email], html_content)
            
        except Exception as e:
            logger.error(f"Failed to send KYC approval email: {e}")
            return False
    
    # =============================================================================
    # TRADING NOTIFICATIONS
    # =============================================================================
    
    def send_order_confirmation(self, user: User, order_data: Dict[str, Any]) -> bool:
        """Send order confirmation email"""
        try:
            context = self._get_user_context(user)
            context.update({
                'order': order_data,
                'order_type': order_data.get('type', 'Unknown'),
                'symbol': order_data.get('symbol', 'Unknown'),
                'side': order_data.get('side', 'Unknown'),
                'quantity': order_data.get('qty', order_data.get('quantity', 0)),
                'price': order_data.get('price', order_data.get('limit_price', 'Market')),
                'status': order_data.get('status', 'Unknown')
            })
            
            subject = f"📈 {self.app_name} - Order Confirmation: {context['side']} {context['symbol']}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .order-details {{ background: #F8FAFC; border: 1px solid #E5E7EB; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .order-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #E5E7EB; }}
                    .order-row:last-child {{ border-bottom: none; }}
                    .cta {{ background: #007AFF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📈 Order Confirmation</h1>
                        <p>Your trade order has been placed</p>
                    </div>
                    <div class="content">
                        <h2>Hello {context['user_name']}!</h2>
                        <p>Your trading order has been successfully placed and is being processed.</p>
                        
                        <div class="order-details">
                            <h3>Order Details</h3>
                            <div class="order-row">
                                <span><strong>Symbol:</strong></span>
                                <span>{context['symbol']}</span>
                            </div>
                            <div class="order-row">
                                <span><strong>Side:</strong></span>
                                <span>{context['side']}</span>
                            </div>
                            <div class="order-row">
                                <span><strong>Type:</strong></span>
                                <span>{context['order_type']}</span>
                            </div>
                            <div class="order-row">
                                <span><strong>Quantity:</strong></span>
                                <span>{context['quantity']}</span>
                            </div>
                            <div class="order-row">
                                <span><strong>Price:</strong></span>
                                <span>{context['price']}</span>
                            </div>
                            <div class="order-row">
                                <span><strong>Status:</strong></span>
                                <span>{context['status']}</span>
                            </div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{context['base_url']}/trading/orders" class="cta">View Order Status</a>
                        </div>
                        
                        <h3>📞 Questions?</h3>
                        <p>If you have any questions about your order, contact our support team:</p>
                        <ul>
                            <li>Email: <a href="mailto:{context['support_email']}">{context['support_email']}</a></li>
                            <li>Response time: Within 2 hours during market hours</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>&copy; {context['current_year']} {self.app_name}. All rights reserved.</p>
                        <p>This email was sent to {context['user_email']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(subject, [user.email], html_content)
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {e}")
            return False
    
    def send_order_filled_notification(self, user: User, order_data: Dict[str, Any]) -> bool:
        """Send notification when order is filled"""
        try:
            context = self._get_user_context(user)
            context.update({
                'order': order_data,
                'symbol': order_data.get('symbol', 'Unknown'),
                'side': order_data.get('side', 'Unknown'),
                'filled_quantity': order_data.get('filled_qty', order_data.get('quantity', 0)),
                'filled_price': order_data.get('filled_avg_price', order_data.get('price', 0)),
                'total_value': float(order_data.get('filled_qty', 0)) * float(order_data.get('filled_avg_price', 0))
            })
            
            subject = f"✅ {self.app_name} - Order Filled: {context['side']} {context['symbol']}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .fill-details {{ background: #F0FDF4; border: 1px solid #22C55E; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .fill-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #D1FAE5; }}
                    .fill-row:last-child {{ border-bottom: none; }}
                    .cta {{ background: #007AFF; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Order Filled!</h1>
                        <p>Your trade has been executed</p>
                    </div>
                    <div class="content">
                        <h2>Great news {context['user_name']}!</h2>
                        <p>Your {context['side']} order for {context['symbol']} has been successfully filled.</p>
                        
                        <div class="fill-details">
                            <h3>Fill Details</h3>
                            <div class="fill-row">
                                <span><strong>Symbol:</strong></span>
                                <span>{context['symbol']}</span>
                            </div>
                            <div class="fill-row">
                                <span><strong>Side:</strong></span>
                                <span>{context['side']}</span>
                            </div>
                            <div class="fill-row">
                                <span><strong>Quantity Filled:</strong></span>
                                <span>{context['filled_quantity']}</span>
                            </div>
                            <div class="fill-row">
                                <span><strong>Average Price:</strong></span>
                                <span>${context['filled_price']:.2f}</span>
                            </div>
                            <div class="fill-row">
                                <span><strong>Total Value:</strong></span>
                                <span>${context['total_value']:.2f}</span>
                            </div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{context['base_url']}/portfolio" class="cta">View Portfolio</a>
                        </div>
                        
                        <h3>📊 Track Your Performance</h3>
                        <p>Monitor your investment performance and get AI-powered insights to optimize your portfolio.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {context['current_year']} {self.app_name}. All rights reserved.</p>
                        <p>This email was sent to {context['user_email']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(subject, [user.email], html_content)
            
        except Exception as e:
            logger.error(f"Failed to send order filled email: {e}")
            return False
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _get_kyc_next_steps(self, workflow_type: str) -> List[Dict[str, str]]:
        """Get next steps for KYC workflow"""
        if workflow_type == 'brokerage':
            return [
                {'name': 'Personal Information', 'description': 'Provide your basic personal details'},
                {'name': 'Identity Verification', 'description': 'Upload government-issued ID'},
                {'name': 'Address Verification', 'description': 'Confirm your residential address'},
                {'name': 'Tax Information', 'description': 'Provide tax identification details'},
                {'name': 'Disclosures', 'description': 'Answer regulatory compliance questions'},
                {'name': 'Document Upload', 'description': 'Upload required verification documents'},
                {'name': 'Review & Approval', 'description': 'Final review and approval process'}
            ]
        else:
            return [
                {'name': 'State Eligibility', 'description': 'Verify crypto trading eligibility in your state'},
                {'name': 'Identity Verification', 'description': 'Upload government-issued ID'},
                {'name': 'Crypto Disclosures', 'description': 'Acknowledge crypto trading risks'},
                {'name': 'Document Upload', 'description': 'Upload required verification documents'},
                {'name': 'Review & Approval', 'description': 'Final review and approval process'}
            ]
    
    def _render_kyc_steps(self, steps: List[Dict[str, str]]) -> str:
        """Render KYC steps as HTML"""
        html = ""
        for i, step in enumerate(steps, 1):
            html += f"""
            <div class="step">
                <strong>Step {i}: {step['name']}</strong><br>
                <span style="color: #666;">{step['description']}</span>
            </div>
            """
        return html
