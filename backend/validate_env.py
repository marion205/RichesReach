#!/usr/bin/env python3
"""
Environment Validation Script
Validates that all required environment variables are set
"""

import os
import sys
from dotenv import load_dotenv

def validate_environment():
    """Validate that all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        'SECRET_KEY',
        'DB_NAME',
        'DB_USER', 
        'DB_PASSWORD',
        'DB_HOST',
        'ALPHA_VANTAGE_API_KEY',
        'NEWS_API_KEY',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    if validate_environment():
        sys.exit(0)
    else:
        sys.exit(1)
