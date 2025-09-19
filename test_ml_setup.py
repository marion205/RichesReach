#!/usr/bin/env python3
"""
Test script to verify ML mutations setup and functionality
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def test_django_setup():
    """Test Django setup and models"""
    print("🔧 Testing Django Setup...")
    
    try:
        from django.conf import settings
        print(f"✅ Django settings loaded: {settings.SETTINGS_MODULE}")
        
        # Test ML settings
        ml_config = getattr(settings, 'ML_SERVICE_CONFIG', {})
        print(f"✅ ML Service Config: {ml_config.get('enabled', False)}")
        
        # Test models
        from core.models import User, StockPriceSnapshot, AuditLog
        print("✅ Core models imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_ml_mutations():
    """Test ML mutations functionality"""
    print("\n🤖 Testing ML Mutations...")
    
    try:
        from core.ml_mutations import (
            GenerateMLPortfolioRecommendation,
            GetMLMarketAnalysis,
            GetMLServiceStatus,
            GenerateInstitutionalPortfolioRecommendation
        )
        print("✅ ML mutations imported successfully")
        
        # Test service status
        status_mutation = GetMLServiceStatus()
        print("✅ ML Service Status mutation available")
        
        return True
    except Exception as e:
        print(f"❌ ML mutations test failed: {e}")
        return False

def test_authentication():
    """Test authentication utilities"""
    print("\n🔐 Testing Authentication...")
    
    try:
        from core.auth_utils import RateLimiter, SecurityUtils, get_ml_mutation_context
        print("✅ Authentication utilities imported successfully")
        
        # Test rate limiter
        rate_limiter = RateLimiter()
        print("✅ Rate limiter initialized")
        
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_monitoring():
    """Test monitoring services"""
    print("\n📊 Testing Monitoring...")
    
    try:
        from core.monitoring_service import MonitoringService
        from core.monitoring_types import MonitoringMutations
        print("✅ Monitoring services imported successfully")
        
        # Test monitoring service
        monitoring = MonitoringService()
        print("✅ Monitoring service initialized")
        
        return True
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

def test_point_in_time_data():
    """Test point-in-time data services"""
    print("\n📅 Testing Point-in-Time Data...")
    
    try:
        from core.pit_data_service import PointInTimeDataService
        print("✅ Point-in-time data service imported successfully")
        
        # Test PIT service
        pit_service = PointInTimeDataService()
        print("✅ PIT data service initialized")
        
        return True
    except Exception as e:
        print(f"❌ Point-in-time data test failed: {e}")
        return False

def test_backend_server():
    """Test if backend server is running"""
    print("\n🌐 Testing Backend Server...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"❌ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend server not accessible: {e}")
        return False

def test_graphql_endpoint():
    """Test GraphQL endpoint"""
    print("\n🔗 Testing GraphQL Endpoint...")
    
    try:
        # Test GraphQL endpoint
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ GraphQL endpoint is working")
                return True
            else:
                print(f"❌ GraphQL returned errors: {data.get('errors', [])}")
                return False
        else:
            print(f"❌ GraphQL endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ GraphQL endpoint not accessible: {e}")
        return False

def test_ml_mutations_endpoint():
    """Test ML mutations via GraphQL"""
    print("\n🧠 Testing ML Mutations Endpoint...")
    
    try:
        # Test ML service status
        query = """
        mutation {
            getMLServiceStatus {
                status
                message
                services {
                    name
                    status
                    lastChecked
                }
            }
        }
        """
        
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'getMLServiceStatus' in data['data']:
                print("✅ ML mutations endpoint is working")
                print(f"   Status: {data['data']['getMLServiceStatus']['status']}")
                return True
            else:
                print(f"❌ ML mutations returned errors: {data.get('errors', [])}")
                return False
        else:
            print(f"❌ ML mutations endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ ML mutations endpoint not accessible: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RichesReach ML Setup Test Suite")
    print("=" * 50)
    
    tests = [
        test_django_setup,
        test_ml_mutations,
        test_authentication,
        test_monitoring,
        test_point_in_time_data,
        test_backend_server,
        test_graphql_endpoint,
        test_ml_mutations_endpoint,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! ML setup is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
