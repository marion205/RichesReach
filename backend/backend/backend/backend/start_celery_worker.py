#!/usr/bin/env python3
"""
Start Celery worker for real-time data updates
"""
import os
import sys
import subprocess

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery worker for real-time data updates...")
    
    try:
        # Start Celery worker
        cmd = [
            'celery', '-A', 'richesreach', 'worker',
            '--loglevel=info',
            '--concurrency=2'
        ]
        
        subprocess.run(cmd, cwd='/Users/marioncollins/RichesReach/backend/backend')
        
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped")
    except Exception as e:
        print(f"❌ Error starting Celery worker: {e}")

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("🚀 Starting Celery beat scheduler...")
    
    try:
        # Start Celery beat
        cmd = [
            'celery', '-A', 'richesreach', 'beat',
            '--loglevel=info'
        ]
        
        subprocess.run(cmd, cwd='/Users/marioncollins/RichesReach/backend/backend')
        
    except KeyboardInterrupt:
        print("\n🛑 Celery beat stopped")
    except Exception as e:
        print(f"❌ Error starting Celery beat: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'beat':
        start_celery_beat()
    else:
        start_celery_worker()
