#!/usr/bin/env python3
"""
Production Status Checker for RichesReach
This script verifies that all production services are running correctly.
"""

import requests
import json
import subprocess
import sys
from datetime import datetime

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "SUCCESS": "\033[92m✅",
        "ERROR": "\033[91m❌", 
        "WARNING": "\033[93m⚠️",
        "INFO": "\033[94mℹ️"
    }
    print(f"{colors.get(status, '')} {message}\033[0m")

def check_service(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_graphql_endpoint():
    """Check if GraphQL endpoint is responding"""
    try:
        response = requests.post(
            'http://127.0.0.1:8001/graphql/',
            json={'query': '{ ping }'},
            timeout=10
        )
        return response.status_code == 200 and 'pong' in response.text
    except:
        return False

def check_database():
    """Check if database is accessible"""
    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        django.setup()
        
        from core.models import Stock
        count = Stock.objects.count()
        return count > 0
    except:
        return False

def check_redis():
    """Check if Redis is accessible"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def run_comprehensive_test():
    """Run the comprehensive system test"""
    try:
        result = subprocess.run(
            ['python3', 'comprehensive_system_test.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0 and '100.0%' in result.stdout
    except:
        return False

def main():
    """Main production status check"""
    print("🚀 RichesReach Production Status Check")
    print("=" * 50)
    print(f"📅 Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check systemd services
    print_status("Checking systemd services...", "INFO")
    services = [
        'richesreach-django',
        'richesreach-celery', 
        'richesreach-celery-beat',
        'redis-server',
        'postgresql',
        'nginx'
    ]
    
    service_status = {}
    for service in services:
        if check_service(service):
            print_status(f"{service}: Running", "SUCCESS")
            service_status[service] = True
        else:
            print_status(f"{service}: Not running", "ERROR")
            service_status[service] = False
    
    print()
    
    # Check GraphQL endpoint
    print_status("Checking GraphQL endpoint...", "INFO")
    if check_graphql_endpoint():
        print_status("GraphQL API: Responding", "SUCCESS")
    else:
        print_status("GraphQL API: Not responding", "ERROR")
    
    # Check database
    print_status("Checking database...", "INFO")
    if check_database():
        print_status("Database: Accessible with data", "SUCCESS")
    else:
        print_status("Database: Not accessible or empty", "ERROR")
    
    # Check Redis
    print_status("Checking Redis...", "INFO")
    if check_redis():
        print_status("Redis: Accessible", "SUCCESS")
    else:
        print_status("Redis: Not accessible", "ERROR")
    
    print()
    
    # Run comprehensive test
    print_status("Running comprehensive system test...", "INFO")
    if run_comprehensive_test():
        print_status("System test: All endpoints working", "SUCCESS")
    else:
        print_status("System test: Some endpoints failing", "ERROR")
    
    print()
    print("=" * 50)
    
    # Overall status
    all_services_running = all(service_status.values())
    graphql_working = check_graphql_endpoint()
    database_working = check_database()
    redis_working = check_redis()
    tests_passing = run_comprehensive_test()
    
    if all_services_running and graphql_working and database_working and redis_working and tests_passing:
        print_status("🎉 PRODUCTION STATUS: FULLY OPERATIONAL", "SUCCESS")
        print_status("Your RichesReach API is ready for production use!", "SUCCESS")
        return 0
    else:
        print_status("⚠️ PRODUCTION STATUS: ISSUES DETECTED", "WARNING")
        print_status("Please check the failed components above", "WARNING")
        return 1

if __name__ == "__main__":
    sys.exit(main())
