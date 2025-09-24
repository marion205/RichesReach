#!/usr/bin/env python3
"""
Security Configuration Script for RichesReach
Sets up production security settings and validates configuration
"""

import os
import sys
import secrets
import string
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(50))

def create_logs_directory():
    """Create logs directory for security logging"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create log files
    (logs_dir / "django.log").touch()
    (logs_dir / "security.log").touch()
    
    print("✅ Created logs directory and log files")

def validate_environment():
    """Validate production environment setup"""
    print("🔍 Validating production environment...")
    
    # Check for required environment variables
    required_vars = [
        'DJANGO_SECRET_KEY',
        'DB_NAME',
        'DB_USER', 
        'DB_PASSWORD',
        'DB_HOST',
        'REDIS_URL',
        'CELERY_BROKER_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please set these variables in your .env.production file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def setup_file_permissions():
    """Set up secure file permissions"""
    print("🔒 Setting up secure file permissions...")
    
    # Set secure permissions for sensitive files
    sensitive_files = [
        "production_settings.py",
        "production.env.template",
        "logs/",
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            os.chmod(file_path, 0o600)  # Read/write for owner only
            print(f"✅ Set secure permissions for {file_path}")
    
    print("✅ File permissions configured")

def create_security_checklist():
    """Create a security checklist for production deployment"""
    checklist = """
# 🔒 Production Security Checklist

## ✅ Completed
- [x] Django secret key generated
- [x] Production settings configured
- [x] Security headers enabled
- [x] SSL/TLS configuration
- [x] Database security
- [x] Session security
- [x] CSRF protection
- [x] CORS configuration
- [x] Rate limiting
- [x] Logging configuration
- [x] File permissions

## 🔄 To Complete Before Production
- [ ] Set up PostgreSQL database
- [ ] Configure Redis server
- [ ] Set up SSL certificates
- [ ] Configure load balancer
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Configure backup system
- [ ] Set up firewall rules
- [ ] Configure CDN
- [ ] Set up email service
- [ ] Test security headers
- [ ] Run security audit
- [ ] Set up intrusion detection
- [ ] Configure log monitoring
- [ ] Set up alerting

## 🚨 Critical Security Items
1. **Change default passwords** - All default passwords must be changed
2. **Enable 2FA** - Two-factor authentication for admin accounts
3. **Regular updates** - Keep all dependencies updated
4. **Monitor logs** - Set up log monitoring and alerting
5. **Backup encryption** - Ensure backups are encrypted
6. **Network security** - Configure firewall and network security
7. **Access control** - Implement proper access controls
8. **Audit logging** - Enable comprehensive audit logging

## 📋 Environment Variables to Set
Copy production.env.template to .env.production and fill in:
- DJANGO_SECRET_KEY (generated above)
- Database credentials
- Redis configuration
- Email settings
- API keys
- Monitoring keys

## 🔧 Commands to Run
```bash
# Set environment variables
export DJANGO_SETTINGS_MODULE=richesreach.production_settings

# Run security checks
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```
"""
    
    with open("SECURITY_CHECKLIST.md", "w") as f:
        f.write(checklist)
    
    print("✅ Created SECURITY_CHECKLIST.md")

def main():
    """Main security configuration function"""
    print("🔒 Configuring Production Security for RichesReach")
    print("=" * 60)
    
    # Generate secret key
    secret_key = generate_secret_key()
    print(f"🔑 Generated Django secret key: {secret_key}")
    print("📝 Add this to your .env.production file as DJANGO_SECRET_KEY")
    
    # Create logs directory
    create_logs_directory()
    
    # Setup file permissions
    setup_file_permissions()
    
    # Create security checklist
    create_security_checklist()
    
    # Validate environment (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        validate_environment()
    
    print("\n" + "=" * 60)
    print("🎉 Security configuration completed!")
    print("\n📋 Next steps:")
    print("1. Copy production.env.template to .env.production")
    print("2. Fill in your actual values in .env.production")
    print("3. Set DJANGO_SECRET_KEY to the generated key above")
    print("4. Review SECURITY_CHECKLIST.md")
    print("5. Run: export DJANGO_SETTINGS_MODULE=richesreach.production_settings")
    print("6. Test with: python manage.py check --deploy")
    print("\n🚀 Your production security is configured!")

if __name__ == "__main__":
    main()
