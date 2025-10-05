#!/usr/bin/env python3
"""
Dependency Checker for Phase 3 Components
Checks if all required dependencies are installed
"""

import sys
import importlib
import subprocess
from typing import Dict, List, Tuple

def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        return True, "✅ Installed"
    except ImportError:
        return False, "❌ Not installed"

def install_package(package_name: str) -> bool:
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main dependency checker"""
    print("🔍 Checking Phase 3 Dependencies")
    print("=" * 50)
    
    # Required packages for Phase 3
    required_packages = [
        # Core dependencies
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("requests", "requests"),
        ("asyncio", "asyncio"),
        
        # Security dependencies
        ("cryptography", "cryptography"),
        ("bcrypt", "bcrypt"),
        ("pyjwt", "jwt"),
        ("geoip2", "geoip2"),
        
        # AI dependencies
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("google-generativeai", "google.generativeai"),
        
        # Analytics dependencies
        ("plotly", "plotly"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        
        # Performance dependencies
        ("aioredis", "aioredis"),
        ("redis", "redis"),
        ("psycopg2-binary", "psycopg2"),
        
        # Monitoring dependencies
        ("prometheus-client", "prometheus_client"),
        ("structlog", "structlog"),
        
        # ML dependencies
        ("xgboost", "xgboost"),
        ("mlflow", "mlflow"),
        ("onnx", "onnx"),
        
        # Other dependencies
        ("python-multipart", "multipart"),
        ("python-jose", "jose"),
        ("passlib", "passlib"),
        ("python-dotenv", "dotenv"),
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package_name, import_name in required_packages:
        is_installed, message = check_package(package_name, import_name)
        print(f"{package_name}: {message}")
        
        if is_installed:
            installed_packages.append(package_name)
        else:
            missing_packages.append(package_name)
    
    print("\n" + "=" * 50)
    print(f"✅ Installed: {len(installed_packages)}")
    print(f"❌ Missing: {len(missing_packages)}")
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        
        response = input("\n🤔 Would you like to install missing packages? (y/n): ")
        if response.lower() == 'y':
            print("\n📥 Installing missing packages...")
            for package in missing_packages:
                print(f"Installing {package}...")
                if install_package(package):
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}")
        else:
            print("⚠️ Some packages are missing. Phase 3 components may not work properly.")
    else:
        print("\n🎉 All required packages are installed!")
    
    print("\n" + "=" * 50)
    print("Dependency check complete!")

if __name__ == "__main__":
    main()
