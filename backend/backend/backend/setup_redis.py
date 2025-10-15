#!/usr/bin/env python3
"""
Redis Setup Script for RichesReach
Configures Redis for Celery and caching
"""

import os
import sys
import subprocess
import redis
from pathlib import Path

def check_redis_installed():
    """Check if Redis is installed"""
    try:
        result = subprocess.run(['redis-server', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Redis is installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Redis is not installed")
            return False
    except FileNotFoundError:
        print("❌ Redis is not installed")
        return False

def install_redis_macos():
    """Install Redis on macOS using Homebrew"""
    print("🍺 Installing Redis on macOS using Homebrew...")
    
    try:
        # Check if Homebrew is installed
        subprocess.run(['brew', '--version'], check=True, capture_output=True)
        
        # Install Redis
        subprocess.run(['brew', 'install', 'redis'], check=True)
        
        # Start Redis service
        subprocess.run(['brew', 'services', 'start', 'redis'], check=True)
        
        print("✅ Redis installed and started successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Redis: {e}")
        return False
    except FileNotFoundError:
        print("❌ Homebrew is not installed")
        print("📝 Please install Homebrew first: https://brew.sh/")
        return False

def install_redis_ubuntu():
    """Install Redis on Ubuntu/Debian"""
    print("🐧 Installing Redis on Ubuntu/Debian...")
    
    try:
        # Update package list
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        
        # Install Redis
        subprocess.run(['sudo', 'apt', 'install', '-y', 'redis-server'], check=True)
        
        # Start Redis service
        subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'redis-server'], check=True)
        
        print("✅ Redis installed and started successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Redis: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.ping()
        print("✅ Redis connection test successful")
        
        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        if value == b'test_value':
            print("✅ Redis read/write test successful")
            r.delete('test_key')
            return True
        else:
            print("❌ Redis read/write test failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        return False

def configure_redis():
    """Configure Redis for production use"""
    print("🔧 Configuring Redis for production...")
    
    # Redis configuration recommendations
    config = """
# Redis Configuration for RichesReach
# Add these settings to your redis.conf file

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
requirepass your_redis_password_here

# Network
bind 127.0.0.1
port 6379
timeout 300

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Performance
tcp-keepalive 300
tcp-backlog 511
"""
    
    config_file = Path("redis_production.conf")
    with open(config_file, "w") as f:
        f.write(config)
    
    print(f"✅ Redis configuration saved to {config_file}")
    print("📝 Review and customize the configuration as needed")
    print("📝 Use this config file when starting Redis in production")

def create_redis_management_script():
    """Create Redis management script"""
    script = """#!/bin/bash
# Redis Management Script for RichesReach

case "$1" in
    start)
        echo "Starting Redis..."
        redis-server redis_production.conf
        ;;
    stop)
        echo "Stopping Redis..."
        redis-cli shutdown
        ;;
    restart)
        echo "Restarting Redis..."
        redis-cli shutdown
        sleep 2
        redis-server redis_production.conf
        ;;
    status)
        echo "Redis status:"
        redis-cli ping
        ;;
    monitor)
        echo "Monitoring Redis..."
        redis-cli monitor
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor}"
        exit 1
        ;;
esac
"""
    
    script_file = Path("manage_redis.sh")
    with open(script_file, "w") as f:
        f.write(script)
    
    # Make script executable
    os.chmod(script_file, 0o755)
    
    print(f"✅ Redis management script created: {script_file}")
    print("📝 Usage: ./manage_redis.sh {start|stop|restart|status|monitor}")

def main():
    """Main Redis setup function"""
    print("🔴 Redis Setup for RichesReach")
    print("=" * 40)
    
    # Check if Redis is already installed
    if check_redis_installed():
        if test_redis_connection():
            print("✅ Redis is already running and working")
            configure_redis()
            create_redis_management_script()
            return
    
    # Detect operating system and install Redis
    if sys.platform == "darwin":  # macOS
        if install_redis_macos():
            if test_redis_connection():
                configure_redis()
                create_redis_management_script()
                print("\n🎉 Redis setup completed successfully!")
            else:
                print("❌ Redis installation failed")
    elif sys.platform.startswith("linux"):  # Linux
        if install_redis_ubuntu():
            if test_redis_connection():
                configure_redis()
                create_redis_management_script()
                print("\n🎉 Redis setup completed successfully!")
            else:
                print("❌ Redis installation failed")
    else:
        print(f"❌ Unsupported operating system: {sys.platform}")
        print("📝 Please install Redis manually for your system")
        print("📝 Visit: https://redis.io/download")
    
    print("\n📋 Next steps:")
    print("1. Start Redis: redis-server")
    print("2. Test connection: redis-cli ping")
    print("3. Start Celery worker: python start_celery_worker.py worker")
    print("4. Start Celery beat: python start_celery_worker.py beat")

if __name__ == "__main__":
    main()
