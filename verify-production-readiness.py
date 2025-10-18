#!/usr/bin/env python3
"""
🚀 RichesReach Production Readiness Verification Script
This script checks if the application is ready for production deployment.
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message, color=Colors.BLUE):
    print(f"{color}[INFO]{Colors.NC} {message}")

def print_success(message):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def check_file_exists(file_path, description):
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print_success(f"✓ {description}: {file_path}")
        return True
    else:
        print_error(f"✗ {description}: {file_path}")
        return False

def check_directory_exists(dir_path, description):
    """Check if a directory exists and report status."""
    if os.path.isdir(dir_path):
        print_success(f"✓ {description}: {dir_path}")
        return True
    else:
        print_error(f"✗ {description}: {dir_path}")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    print_status("Checking Python packages...")
    
    # Set Django settings to avoid configuration errors
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    
    required_packages = [
        'django',
        'graphene_django',
        'psycopg2',
        'redis',
        'requests',
        'celery'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"✓ {package}")
        except ImportError:
            print_error(f"✗ {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_node_packages():
    """Check if required Node.js packages are installed."""
    print_status("Checking Node.js packages...")
    
    mobile_dir = Path("mobile")
    if not mobile_dir.exists():
        print_error("Mobile directory not found")
        return False
    
    package_json = mobile_dir / "package.json"
    if not package_json.exists():
        print_error("package.json not found in mobile directory")
        return False
    
    try:
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        required_packages = [
            'expo',
            'react-native',
            '@apollo/client',
            'react-native-wagmi-charts',
            'react-native-svg',
            'react-native-vector-icons'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package in all_deps:
                print_success(f"✓ {package}")
            else:
                print_error(f"✗ {package}")
                missing_packages.append(package)
        
        return len(missing_packages) == 0
        
    except Exception as e:
        print_error(f"Error reading package.json: {e}")
        return False

def check_backend_structure():
    """Check backend directory structure and key files."""
    print_status("Checking backend structure...")
    
    backend_files = [
        ("backend/backend/backend/backend/manage.py", "Django manage.py"),
        ("backend/backend/backend/backend/richesreach/settings.py", "Django settings"),
        ("backend/backend/backend/backend/core/schema.py", "GraphQL schema"),
        ("backend/backend/backend/backend/core/stock_comprehensive.py", "Stock comprehensive resolver"),
        ("backend/requirements.txt", "Python requirements"),
    ]
    
    all_exist = True
    for file_path, description in backend_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_mobile_structure():
    """Check mobile app structure and key files."""
    print_status("Checking mobile app structure...")
    
    mobile_files = [
        ("mobile/package.json", "Package.json"),
        ("mobile/app.json", "Expo app.json"),
        ("mobile/src/App.tsx", "Main App component"),
        ("mobile/src/features/stocks/screens/StockDetailScreen.tsx", "Stock detail screen"),
        ("mobile/src/components/forms/StockTradingModal.tsx", "Stock trading modal"),
        ("mobile/src/services/stockDataService.ts", "Stock data service"),
    ]
    
    all_exist = True
    for file_path, description in mobile_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_environment_files():
    """Check if environment configuration files exist."""
    print_status("Checking environment files...")
    
    env_files = [
        (".env.production", "Production environment template"),
        ("mobile/env.production", "Mobile production environment"),
    ]
    
    all_exist = True
    for file_path, description in env_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_git_status():
    """Check git status and ensure all changes are committed."""
    print_status("Checking git status...")
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print_warning("Uncommitted changes detected:")
            print(result.stdout)
            return False
        else:
            print_success("All changes committed")
            return True
            
    except subprocess.CalledProcessError as e:
        print_error(f"Git command failed: {e}")
        return False

def check_backend_health():
    """Check if backend is running and healthy."""
    print_status("Checking backend health...")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print_success("Backend health check passed")
            return True
        else:
            print_warning(f"Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print_warning("Backend not running or not accessible")
        return False

def main():
    """Main verification function."""
    print("🚀 RichesReach Production Readiness Verification")
    print("=" * 50)
    
    checks = [
        ("Backend Structure", check_backend_structure),
        ("Mobile Structure", check_mobile_structure),
        ("Python Packages", check_python_packages),
        ("Node.js Packages", check_node_packages),
        ("Environment Files", check_environment_files),
        ("Git Status", check_git_status),
        ("Backend Health", check_backend_health),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PRODUCTION READINESS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("🎉 Application is ready for production deployment!")
        return 0
    else:
        print_warning(f"⚠️  {total - passed} checks failed. Please address these issues before production deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())