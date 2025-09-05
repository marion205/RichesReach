#!/usr/bin/env python3
"""
Update Email Configuration Script
Updates the .env file with your email credentials
"""

import os
import sys

def update_email_config():
    """Update email configuration in .env file"""
    print("📧 Updating Email Configuration")
    print("=" * 35)
    
    # Your email configuration
    email_config = {
        'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'EMAIL_HOST': 'smtp.gmail.com',
        'EMAIL_PORT': '587',
        'EMAIL_USE_TLS': 'True',
        'EMAIL_HOST_USER': 'mcollins205@gmail.com',
        'EMAIL_HOST_PASSWORD': 'your_app_password_here',  # You'll need to replace this
        'DEFAULT_FROM_EMAIL': 'mcollins205@gmail.com',
        'FRONTEND_URL': 'http://localhost:3000'
    }
    
    env_file = '.env'
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        print("📝 Creating .env file...")
        
        # Create .env file from env.example if it exists
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
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update email configuration
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
    
    # Show the configuration
    print("📧 Current Email Configuration:")
    print("=" * 35)
    for key, value in email_config.items():
        if 'PASSWORD' in key:
            print(f"{key}=***hidden***")
        else:
            print(f"{key}={value}")
    
    print()
    print("🔐 IMPORTANT: Gmail Setup Required!")
    print("=" * 40)
    print("To use Gmail, you need to:")
    print("1. Enable 2-Factor Authentication on your Google account")
    print("2. Generate an App Password:")
    print("   • Go to https://myaccount.google.com/")
    print("   • Security → 2-Step Verification → App passwords")
    print("   • Generate a password for 'Mail'")
    print("   • Replace 'your_app_password_here' with the generated password")
    print()
    print("3. Update the EMAIL_HOST_PASSWORD in your .env file")
    print()
    
    return True

def test_email_config():
    """Test the email configuration"""
    print("🧪 Testing Email Configuration")
    print("=" * 32)
    
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        
        from django.conf import settings
        from django.core.mail import send_mail
        
        print(f"✅ Email backend: {settings.EMAIL_BACKEND}")
        print(f"✅ Email host: {settings.EMAIL_HOST}")
        print(f"✅ Email port: {settings.EMAIL_PORT}")
        print(f"✅ Email use TLS: {settings.EMAIL_USE_TLS}")
        print(f"✅ Email user: {settings.EMAIL_HOST_USER}")
        print(f"✅ Default from: {settings.DEFAULT_FROM_EMAIL}")
        print(f"✅ Frontend URL: {settings.FRONTEND_URL}")
        
        # Check if password is still placeholder
        if settings.EMAIL_HOST_PASSWORD == 'your_app_password_here':
            print("⚠️ EMAIL_HOST_PASSWORD still has placeholder value")
            print("Please update it with your Gmail App Password")
            return False
        
        print("✅ Email configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔐 RichesReach Email Configuration Setup")
    print("=" * 45)
    print()
    
    # Update email configuration
    success = update_email_config()
    
    if success:
        # Test the configuration
        test_success = test_email_config()
        
        if test_success:
            print("\n🎉 Email configuration setup complete!")
            print("✅ Your enhanced authentication system is ready to send emails")
        else:
            print("\n⚠️ Email configuration updated but needs Gmail App Password")
            print("Please follow the Gmail setup instructions above")
    else:
        print("\n❌ Failed to update email configuration")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
