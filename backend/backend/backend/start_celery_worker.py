#!/usr/bin/env python3
"""
Celery Worker Startup Script for RichesReach
Production-ready Celery worker configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_redis_connection():
    """Check if Redis is running and accessible"""
    try:
        import redis
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("📝 Please start Redis server: redis-server")
        return False

def check_django_setup():
    """Check if Django is properly configured"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        print("✅ Django setup successful")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def start_celery_worker():
    """Start Celery worker with production settings"""
    print("🚀 Starting Celery Worker for RichesReach")
    print("=" * 50)
    
    # Check prerequisites
    if not check_redis_connection():
        return False
    
    if not check_django_setup():
        return False
    
    # Celery worker command
    cmd = [
        'celery',
        '-A', 'celery_config',
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=swing_trading,general',
        '--hostname=worker@%h',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat',
    ]
    
    print(f"🔧 Starting worker with command: {' '.join(cmd)}")
    print("📝 Press Ctrl+C to stop the worker")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery worker failed: {e}")
        return False
    
    return True

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("⏰ Starting Celery Beat Scheduler")
    print("=" * 50)
    
    # Check prerequisites
    if not check_redis_connection():
        return False
    
    if not check_django_setup():
        return False
    
    # Celery beat command
    cmd = [
        'celery',
        '-A', 'celery_config',
        'beat',
        '--loglevel=info',
        '--scheduler=django_celery_beat.schedulers:DatabaseScheduler',
    ]
    
    print(f"🔧 Starting beat scheduler with command: {' '.join(cmd)}")
    print("📝 Press Ctrl+C to stop the scheduler")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery beat stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery beat failed: {e}")
        return False
    
    return True

def start_celery_flower():
    """Start Celery Flower monitoring"""
    print("🌸 Starting Celery Flower Monitoring")
    print("=" * 50)
    
    # Check prerequisites
    if not check_redis_connection():
        return False
    
    if not check_django_setup():
        return False
    
    # Celery flower command
    cmd = [
        'celery',
        '-A', 'celery_config',
        'flower',
        '--port=5555',
        '--broker=redis://127.0.0.1:6379/0',
    ]
    
    print(f"🔧 Starting Flower with command: {' '.join(cmd)}")
    print("📝 Flower will be available at: http://localhost:5555")
    print("📝 Press Ctrl+C to stop Flower")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery Flower stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery Flower failed: {e}")
        return False
    
    return True

def main():
    """Main function to start Celery components"""
    if len(sys.argv) < 2:
        print("Usage: python start_celery_worker.py [worker|beat|flower|all]")
        print("\nOptions:")
        print("  worker  - Start Celery worker")
        print("  beat    - Start Celery beat scheduler")
        print("  flower  - Start Celery Flower monitoring")
        print("  all     - Start all components")
        return
    
    component = sys.argv[1].lower()
    
    if component == 'worker':
        start_celery_worker()
    elif component == 'beat':
        start_celery_beat()
    elif component == 'flower':
        start_celery_flower()
    elif component == 'all':
        print("🚀 Starting all Celery components")
        print("📝 This will start worker, beat, and flower")
        print("📝 Use separate terminals for each component in production")
        
        # In production, you would start these in separate processes
        # For development, we'll start them sequentially
        start_celery_worker()
    else:
        print(f"❌ Unknown component: {component}")
        print("Available components: worker, beat, flower, all")

if __name__ == "__main__":
    main()
