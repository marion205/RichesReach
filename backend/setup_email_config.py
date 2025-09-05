#!/usr/bin/env python3
"""
Email Configuration Setup Script for RichesReach
This script helps you set up email configuration for the enhanced authentication system.
"""

import os
import sys

def setup_email_config():
    """Setup email configuration for enhanced authentication"""
    
    print("🔐 RichesReach Email Configuration Setup")
    print("=" * 50)
    print()
    
    # Check if .env file exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        print("📝 Creating .env file from env.example...")
        
        # Copy from env.example if it exists
        if os.path.exists('env.example'):
            with open('env.example', 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created from env.example")
        else:
            print("❌ env.example not found either!")
            return False
    else:
        print("✅ .env file found")
    
    print()
    print("📧 Email Configuration Setup")
    print("=" * 30)
    print()
    print("For the enhanced authentication system to work, you need to configure email settings.")
    print("This is required for:")
    print("  • Password reset emails")
    print("  • Email verification")
    print("  • Account security notifications")
    print()
    
    # Get email configuration from user
    print("Please provide your email configuration:")
    print()
    
    email_host = input("Email Host (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    email_port = input("Email Port (default: 587): ").strip() or "587"
    email_use_tls = input("Use TLS? (y/n, default: y): ").strip().lower() or "y"
    email_user = input("Your Email Address: ").strip()
    email_password = input("Your Email Password/App Password: ").strip()
    default_from = input("Default From Email (default: noreply@richesreach.com): ").strip() or "noreply@richesreach.com"
    frontend_url = input("Frontend URL (default: http://localhost:3000): ").strip() or "http://localhost:3000"
    
    print()
    print("📝 Updating .env file...")
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update email configuration
    email_config = {
        'EMAIL_HOST': email_host,
        'EMAIL_PORT': email_port,
        'EMAIL_USE_TLS': 'True' if email_use_tls in ['y', 'yes', 'true'] else 'False',
        'EMAIL_HOST_USER': email_user,
        'EMAIL_HOST_PASSWORD': email_password,
        'DEFAULT_FROM_EMAIL': default_from,
        'FRONTEND_URL': frontend_url,
    }
    
    # Update or add email configuration lines
    updated_lines = []
    email_keys = set(email_config.keys())
    
    for line in lines:
        line_stripped = line.strip()
        if '=' in line_stripped:
            key = line_stripped.split('=')[0].strip()
            if key in email_keys:
                # Update existing line
                updated_lines.append(f"{key}={email_config[key]}\n")
                email_keys.remove(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add any missing email configuration
    for key in email_keys:
        updated_lines.append(f"{key}={email_config[key]}\n")
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ Email configuration updated!")
    print()
    
    # Gmail specific instructions
    if email_host == "smtp.gmail.com":
        print("📧 Gmail Setup Instructions:")
        print("=" * 25)
        print("If you're using Gmail, you need to:")
        print("1. Enable 2-Factor Authentication on your Google account")
        print("2. Generate an App Password:")
        print("   • Go to Google Account settings")
        print("   • Security → 2-Step Verification → App passwords")
        print("   • Generate a password for 'Mail'")
        print("   • Use this password (not your regular Gmail password)")
        print()
    
    print("🧪 Testing Email Configuration...")
    print("=" * 35)
    
    # Test email configuration
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Load Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        
        # Test email sending
        print("Sending test email...")
        send_mail(
            subject='RichesReach Email Test',
            message='This is a test email from RichesReach. If you receive this, your email configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_user],
            fail_silently=False,
        )
        print("✅ Test email sent successfully!")
        print(f"📧 Check your inbox at {email_user}")
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("• Check your email credentials")
        print("• For Gmail, make sure you're using an App Password")
        print("• Check your internet connection")
        print("• Verify the SMTP settings")
        return False
    
    print()
    print("🎉 Email configuration setup complete!")
    print("Your enhanced authentication system is now ready to send emails.")
    return True

if __name__ == "__main__":
    setup_email_config()
