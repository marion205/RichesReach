#!/usr/bin/env python3
"""
Local development server that connects to production database
Run this to test fixes locally before deploying to production
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local_prod')

def main():
    print("🚀 Starting local development server with production database...")
    print("📊 This will connect to your production database for testing")
    print("🔧 Debug mode enabled for better error messages")
    print("")
    
    # Check if environment file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env.local')
    if not os.path.exists(env_file):
        print("⚠️  Warning: .env.local file not found!")
        print("   Please copy env.local.template to .env.local and fill in your database credentials")
        print("")
    
    # Run Django development server
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n👋 Local development server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
