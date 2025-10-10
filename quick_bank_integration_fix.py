#!/usr/bin/env python3
"""
Quick Bank Integration Fix for Production
This script helps you quickly enable and test bank integration features
"""

import os
import sys
import json
import requests
from typing import Dict, Any

def update_production_config():
    """Update production configuration to enable bank integration"""
    
    config_file = "backend/backend/production_config.py"
    
    print("🔧 Updating production configuration...")
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Update USE_YODLEE to True
    content = content.replace("'USE_YODLEE': False", "'USE_YODLEE': True")
    
    # Add SBLOC settings if not present
    if "'USE_SBLOC_AGGREGATOR'" not in content:
        # Find the end of PRODUCTION_SETTINGS and add SBLOC config
        settings_end = content.find("}")
        if settings_end != -1:
            sbloc_config = """
    'USE_SBLOC_AGGREGATOR': True,
    'USE_SBLOC_MOCK': False,"""
            content = content[:settings_end] + sbloc_config + "\n" + content[settings_end:]
    
    # Write updated config
    with open(config_file, 'w') as f:
        f.write(content)
    
    print("✅ Production configuration updated!")

def create_environment_template():
    """Create environment variables template for bank integration"""
    
    env_template = """# Bank Integration Environment Variables
# Copy these to your production environment

# Yodlee Configuration
export USE_YODLEE=true
export YODLEE_ENV=production
export YODLEE_CLIENT_ID=your_yodlee_client_id_here
export YODLEE_SECRET=your_yodlee_client_secret_here
export YODLEE_LOGIN_NAME=your_yodlee_login_name_here
export YODLEE_BASE_URL=https://api.yodlee.com/ysl
export YODLEE_FASTLINK_URL=https://fastlink.yodlee.com/apps

# SBLOC Configuration
export USE_SBLOC_AGGREGATOR=true
export USE_SBLOC_MOCK=false
export SBLOC_AGGREGATOR_BASE_URL=https://api.your-sbloc-provider.com
export SBLOC_AGGREGATOR_API_KEY=your_sbloc_api_key_here
export SBLOC_WEBHOOK_SECRET=your_webhook_secret_here
export SBLOC_REDIRECT_URI=https://app.richesreach.net/sbloc/callback
"""
    
    with open("bank_integration.env", "w") as f:
        f.write(env_template)
    
    print("✅ Environment template created: bank_integration.env")

def test_bank_endpoints():
    """Test bank integration endpoints"""
    
    base_url = "https://app.richesreach.net"
    
    endpoints = [
        "/api/yodlee/fastlink/start",
        "/api/sbloc/health",
        "/api/sbloc/banks",
        "/health/"
    ]
    
    print("🧪 Testing bank integration endpoints...")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")

def create_mock_enhancement():
    """Create enhanced mock data for better user experience"""
    
    enhanced_mock = {
        "banks": [
            {
                "id": "chase",
                "name": "Chase Bank",
                "logo": "https://logo.clearbit.com/chase.com",
                "popular": True
            },
            {
                "id": "bankofamerica", 
                "name": "Bank of America",
                "logo": "https://logo.clearbit.com/bankofamerica.com",
                "popular": True
            },
            {
                "id": "wellsfargo",
                "name": "Wells Fargo",
                "logo": "https://logo.clearbit.com/wellsfargo.com",
                "popular": True
            },
            {
                "id": "citi",
                "name": "Citibank",
                "logo": "https://logo.clearbit.com/citi.com",
                "popular": False
            }
        ],
        "sbloc_banks": [
            {
                "id": "ibkr",
                "name": "Interactive Brokers",
                "min_apr": 0.0599,
                "max_apr": 0.0999,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 5000,
                "popular": True
            },
            {
                "id": "schwab",
                "name": "Charles Schwab",
                "min_apr": 0.0699,
                "max_apr": 0.1099,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 25000,
                "popular": True
            },
            {
                "id": "fidelity",
                "name": "Fidelity",
                "min_apr": 0.0699,
                "max_apr": 0.1099,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 25000,
                "popular": True
            }
        ]
    }
    
    with open("enhanced_mock_data.json", "w") as f:
        json.dump(enhanced_mock, f, indent=2)
    
    print("✅ Enhanced mock data created: enhanced_mock_data.json")

def create_test_script():
    """Create a test script for bank integration"""
    
    test_script = """#!/bin/bash
# Bank Integration Test Script

echo "🧪 Testing Bank Integration..."

# Test Yodlee endpoints
echo "Testing Yodlee integration..."
curl -X POST https://app.richesreach.net/api/yodlee/fastlink/start \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer test_token" \\
  -d '{"userId": "test_user"}' \\
  --max-time 10

echo "\\n"

# Test SBLOC endpoints
echo "Testing SBLOC integration..."
curl -X GET https://app.richesreach.net/api/sbloc/health \\
  --max-time 10

echo "\\n"

# Test bank listing
echo "Testing bank listing..."
curl -X GET https://app.richesreach.net/api/sbloc/banks \\
  --max-time 10

echo "\\n✅ Bank integration tests completed!"
"""
    
    with open("test_bank_integration.sh", "w") as f:
        f.write(test_script)
    
    # Make it executable
    os.chmod("test_bank_integration.sh", 0o755)
    
    print("✅ Test script created: test_bank_integration.sh")

def main():
    """Main function to set up bank integration"""
    
    print("🚀 Bank Integration Quick Fix")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("backend/backend/production_config.py"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    print("\\n1. Updating production configuration...")
    update_production_config()
    
    print("\\n2. Creating environment template...")
    create_environment_template()
    
    print("\\n3. Creating enhanced mock data...")
    create_mock_enhancement()
    
    print("\\n4. Creating test script...")
    create_test_script()
    
    print("\\n" + "=" * 50)
    print("✅ Bank Integration Setup Complete!")
    print("\\n📋 Next Steps:")
    print("1. Get Yodlee credentials from https://developer.yodlee.com/")
    print("2. Choose a SBLOC aggregator provider")
    print("3. Update your production environment with the variables in bank_integration.env")
    print("4. Run ./test_bank_integration.sh to test the integration")
    print("5. Deploy to production")
    print("\\n🚨 IMPORTANT: Update your production environment variables before deploying!")
    
    print("\\n📁 Files created:")
    print("- bank_integration.env (environment variables template)")
    print("- enhanced_mock_data.json (better mock data)")
    print("- test_bank_integration.sh (test script)")

if __name__ == "__main__":
    main()
