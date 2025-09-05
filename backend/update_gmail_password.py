#!/usr/bin/env python3
"""
Update Gmail App Password
Simple script to update just the EMAIL_HOST_PASSWORD
"""

import os
import getpass

def update_gmail_password():
    """Update Gmail App Password in .env file"""
    print("🔐 Gmail App Password Update")
    print("=" * 30)
    print()
    
    # Get the App Password from user
    print("Please enter your Gmail App Password:")
    print("(The 16-character password from Google Account settings)")
    print()
    
    app_password = getpass.getpass("Gmail App Password: ").strip()
    
    if not app_password:
        print("❌ No password entered")
        return False
    
    if len(app_password) < 16:
        print("⚠️ Warning: App Password should be 16 characters long")
        print("Are you sure this is correct? (y/n): ", end="")
        confirm = input().strip().lower()
        if confirm != 'y':
            return False
    
    # Update .env file
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update EMAIL_HOST_PASSWORD
    updated_lines = []
    password_updated = False
    
    for line in lines:
        if line.startswith('EMAIL_HOST_PASSWORD='):
            updated_lines.append(f'EMAIL_HOST_PASSWORD={app_password}\n')
            password_updated = True
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    if password_updated:
        print("✅ Gmail App Password updated successfully!")
    else:
        print("❌ Could not find EMAIL_HOST_PASSWORD in .env file")
        return False
    
    return True

def test_email_sending():
    """Test sending an email"""
    print("\n🧪 Testing Email Sending")
    print("=" * 25)
    
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        
        from django.core.mail import send_mail
        from django.conf import settings
        
        print("Sending test email...")
        
        send_mail(
            subject='RichesReach Email Test',
            message='This is a test email from your enhanced authentication system. If you receive this, your email configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        
        print("✅ Test email sent successfully!")
        print(f"📧 Check your inbox at {settings.EMAIL_HOST_USER}")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("• Check your Gmail App Password")
        print("• Make sure 2-Factor Authentication is enabled")
        print("• Check your internet connection")
        print("• Verify the SMTP settings")
        return False

def main():
    """Main function"""
    print("📧 Gmail App Password Configuration")
    print("=" * 35)
    print()
    
    # Update password
    success = update_gmail_password()
    
    if success:
        # Test email sending
        test_success = test_email_sending()
        
        if test_success:
            print("\n🎉 Gmail configuration complete!")
            print("✅ Your enhanced authentication system can now send emails")
            print("\n📋 What's working now:")
            print("• Password reset emails")
            print("• Email verification")
            print("• Account security notifications")
        else:
            print("\n⚠️ Password updated but email test failed")
            print("Please check the troubleshooting tips above")
    else:
        print("\n❌ Failed to update Gmail password")
    
    return success

if __name__ == "__main__":
    main()
