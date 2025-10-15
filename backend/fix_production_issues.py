#!/usr/bin/env python3
"""
Fix Production Issues - Automated Production System Repair
This script identifies and fixes common production issues
"""

import os
import sys
import json
import subprocess
import requests
import time
from typing import Dict, List, Any
from datetime import datetime

class ProductionFixer:
    def __init__(self):
        self.fixes_applied = []
        self.errors_found = []
        self.base_url = "https://app.richesreach.net"
    
    def check_and_fix_environment(self):
        """Check and fix environment configuration"""
        print("🔧 Checking environment configuration...")
        
        # Check if production config exists
        config_files = [
            "backend/backend/production_config.py",
            "backend/backend/richesreach/settings.py",
            "mobile/src/config/production.ts"
        ]
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                self.errors_found.append(f"Missing config file: {config_file}")
                print(f"  ❌ Missing: {config_file}")
            else:
                print(f"  ✅ Found: {config_file}")
        
        # Check environment variables
        required_env_vars = [
            "FINNHUB_API_KEY",
            "POLYGON_API_KEY", 
            "OPENAI_API_KEY",
            "SECRET_KEY"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                self.errors_found.append(f"Missing environment variable: {var}")
                print(f"  ❌ Missing: {var}")
            else:
                print(f"  ✅ Found: {var}")
    
    def fix_bank_integration_config(self):
        """Fix bank integration configuration"""
        print("🏦 Fixing bank integration configuration...")
        
        # Update production config to enable bank features
        config_file = "backend/backend/production_config.py"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Enable Yodlee if not already enabled
            if "'USE_YODLEE': False" in content:
                content = content.replace("'USE_YODLEE': False", "'USE_YODLEE': True")
                self.fixes_applied.append("Enabled Yodlee in production config")
                print("  ✅ Enabled Yodlee integration")
            
            # Enable SBLOC if not already enabled
            if "'USE_SBLOC_AGGREGATOR'" not in content:
                # Add SBLOC configuration
                settings_end = content.find("}")
                if settings_end != -1:
                    sbloc_config = """
    'USE_SBLOC_AGGREGATOR': True,
    'USE_SBLOC_MOCK': False,"""
                    content = content[:settings_end] + sbloc_config + "\n" + content[settings_end:]
                    self.fixes_applied.append("Added SBLOC configuration")
                    print("  ✅ Added SBLOC configuration")
            
            # Write updated config
            with open(config_file, 'w') as f:
                f.write(content)
        else:
            self.errors_found.append("Production config file not found")
    
    def fix_database_migrations(self):
        """Fix database migration issues"""
        print("🗄️ Checking database migrations...")
        
        try:
            # Check if we're in the backend directory
            if os.path.exists("backend/backend/manage.py"):
                os.chdir("backend/backend")
            
            # Run migrations
            result = subprocess.run(
                ["python3", "manage.py", "migrate", "--check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print("  ⚠️ Migration issues detected, running migrations...")
                result = subprocess.run(
                    ["python3", "manage.py", "migrate"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.fixes_applied.append("Applied database migrations")
                    print("  ✅ Database migrations applied")
                else:
                    self.errors_found.append(f"Migration failed: {result.stderr}")
                    print(f"  ❌ Migration failed: {result.stderr}")
            else:
                print("  ✅ Database migrations up to date")
                
        except subprocess.TimeoutExpired:
            self.errors_found.append("Database migration timeout")
            print("  ❌ Database migration timeout")
        except Exception as e:
            self.errors_found.append(f"Database check failed: {str(e)}")
            print(f"  ❌ Database check failed: {str(e)}")
    
    def fix_static_files(self):
        """Fix static files collection"""
        print("📁 Checking static files...")
        
        try:
            if os.path.exists("backend/backend/manage.py"):
                os.chdir("backend/backend")
            
            # Collect static files
            result = subprocess.run(
                ["python3", "manage.py", "collectstatic", "--noinput"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.fixes_applied.append("Collected static files")
                print("  ✅ Static files collected")
            else:
                self.errors_found.append(f"Static files collection failed: {result.stderr}")
                print(f"  ❌ Static files collection failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.errors_found.append("Static files collection timeout")
            print("  ❌ Static files collection timeout")
        except Exception as e:
            self.errors_found.append(f"Static files check failed: {str(e)}")
            print(f"  ❌ Static files check failed: {str(e)}")
    
    def fix_permissions(self):
        """Fix file permissions"""
        print("🔐 Checking file permissions...")
        
        # Check and fix permissions for key files
        key_files = [
            "backend/backend/manage.py",
            "backend/backend/final_complete_server.py",
            "mobile/src/config/production.ts"
        ]
        
        for file_path in key_files:
            if os.path.exists(file_path):
                # Make executable if it's a Python file
                if file_path.endswith('.py'):
                    os.chmod(file_path, 0o755)
                    self.fixes_applied.append(f"Fixed permissions for {file_path}")
                    print(f"  ✅ Fixed permissions: {file_path}")
                else:
                    print(f"  ✅ Permissions OK: {file_path}")
    
    def fix_docker_config(self):
        """Fix Docker configuration"""
        print("🐳 Checking Docker configuration...")
        
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "Dockerfile.prod"
        ]
        
        for docker_file in docker_files:
            if os.path.exists(docker_file):
                print(f"  ✅ Found: {docker_file}")
            else:
                self.errors_found.append(f"Missing Docker file: {docker_file}")
                print(f"  ❌ Missing: {docker_file}")
    
    def fix_nginx_config(self):
        """Fix Nginx configuration"""
        print("🌐 Checking Nginx configuration...")
        
        nginx_files = [
            "nginx/nginx.production.conf",
            "nginx/nginx.conf"
        ]
        
        for nginx_file in nginx_files:
            if os.path.exists(nginx_file):
                print(f"  ✅ Found: {nginx_file}")
            else:
                self.errors_found.append(f"Missing Nginx config: {nginx_file}")
                print(f"  ❌ Missing: {nginx_file}")
    
    def test_critical_endpoints(self):
        """Test critical endpoints"""
        print("🧪 Testing critical endpoints...")
        
        critical_endpoints = [
            "/health/",
            "/graphql/",
            "/api/ai-options/recommendations"
        ]
        
        for endpoint in critical_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"  ✅ {endpoint}: OK")
                else:
                    self.errors_found.append(f"Endpoint {endpoint} returned {response.status_code}")
                    print(f"  ❌ {endpoint}: Status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.errors_found.append(f"Endpoint {endpoint} failed: {str(e)}")
                print(f"  ❌ {endpoint}: {str(e)}")
    
    def create_environment_template(self):
        """Create environment template with all required variables"""
        print("📝 Creating environment template...")
        
        env_template = """# RichesReach Production Environment Variables
# Copy these to your production environment and fill in actual values

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=app.richesreach.net,localhost

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# API Keys
FINNHUB_API_KEY=your-finnhub-key-here
POLYGON_API_KEY=your-polygon-key-here
OPENAI_API_KEY=your-openai-key-here
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here
NEWS_API_KEY=your-news-api-key-here

# Yodlee Bank Integration
USE_YODLEE=true
YODLEE_ENV=production
YODLEE_CLIENT_ID=your-yodlee-client-id
YODLEE_SECRET=your-yodlee-secret
YODLEE_LOGIN_NAME=your-yodlee-login-name
YODLEE_BASE_URL=https://api.yodlee.com/ysl
YODLEE_FASTLINK_URL=https://fastlink.yodlee.com/apps

# SBLOC Integration
USE_SBLOC_AGGREGATOR=true
USE_SBLOC_MOCK=false
SBLOC_AGGREGATOR_BASE_URL=https://api.your-sbloc-provider.com
SBLOC_AGGREGATOR_API_KEY=your-sbloc-api-key
SBLOC_WEBHOOK_SECRET=your-webhook-secret
SBLOC_REDIRECT_URI=https://app.richesreach.net/sbloc/callback

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS Configuration (if using)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True

# Logging
LOG_LEVEL=INFO
"""
        
        with open("production.env.template", "w") as f:
            f.write(env_template)
        
        self.fixes_applied.append("Created environment template")
        print("  ✅ Created production.env.template")
    
    def create_deployment_script(self):
        """Create deployment script"""
        print("🚀 Creating deployment script...")
        
        deploy_script = """#!/bin/bash
# RichesReach Production Deployment Script

set -e

echo "🚀 Starting RichesReach Production Deployment..."

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/backend/manage.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Load environment variables
if [ -f ".env.production" ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    print_status "Environment variables loaded"
else
    print_warning "No .env.production file found. Using system environment variables."
fi

# Navigate to backend
cd backend/backend

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
print_status "Running database migrations..."
python3 manage.py migrate

# Collect static files
print_status "Collecting static files..."
python3 manage.py collectstatic --noinput

# Create superuser if needed
print_status "Checking for superuser..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@richesreach.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start the server
print_status "Starting production server..."
python3 final_complete_server.py

print_status "Deployment completed successfully!"
"""
        
        with open("deploy-production.sh", "w") as f:
            f.write(deploy_script)
        
        # Make it executable
        os.chmod("deploy-production.sh", 0o755)
        
        self.fixes_applied.append("Created deployment script")
        print("  ✅ Created deploy-production.sh")
    
    def run_all_fixes(self):
        """Run all fixes"""
        print("🔧 Starting production system fixes...")
        print("=" * 60)
        
        # Run all fix functions
        self.check_and_fix_environment()
        self.fix_bank_integration_config()
        self.fix_database_migrations()
        self.fix_static_files()
        self.fix_permissions()
        self.fix_docker_config()
        self.fix_nginx_config()
        self.test_critical_endpoints()
        self.create_environment_template()
        self.create_deployment_script()
        
        # Print summary
        self.print_summary()
        
        return {
            "fixes_applied": self.fixes_applied,
            "errors_found": self.errors_found,
            "timestamp": datetime.now().isoformat()
        }
    
    def print_summary(self):
        """Print fix summary"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION FIX SUMMARY")
        print("=" * 60)
        
        print(f"Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"  ✅ {fix}")
        
        print(f"\nErrors Found: {len(self.errors_found)}")
        for error in self.errors_found:
            print(f"  ❌ {error}")
        
        if self.errors_found:
            print("\n🚨 CRITICAL ISSUES REMAINING:")
            print("Please address these issues before deploying to production:")
            for error in self.errors_found:
                print(f"  - {error}")
        else:
            print("\n✅ All critical issues resolved!")
        
        print("\n📁 Files Created:")
        print("  - production.env.template (environment variables)")
        print("  - deploy-production.sh (deployment script)")
        
        print("\n🚀 Next Steps:")
        print("1. Fill in actual values in production.env.template")
        print("2. Copy to .env.production")
        print("3. Run ./deploy-production.sh")
        print("4. Test all endpoints")
        print("5. Monitor system health")

def main():
    """Main function"""
    fixer = ProductionFixer()
    results = fixer.run_all_fixes()
    
    # Save results
    with open("production_fix_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Fix report saved to: production_fix_report.json")
    
    # Exit with appropriate code
    if results["errors_found"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
