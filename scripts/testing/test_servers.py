#!/usr/bin/env python3
"""
Test both servers to see which one is working
"""
import requests
import time

def test_server(ip, name):
    print(f"🔍 Testing {name} at {ip}...")
    
    try:
        # Test health endpoint
        response = requests.get(f"http://{ip}:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} is healthy!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  {name} responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is not responding")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ {name} timed out")
        return False
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return False

def test_servers():
    print("🚀 Testing RichesReach servers...")
    
    servers = [
        ("18.217.92.158", "Original Server"),
        ("3.21.164.228", "New Simple Server")
    ]
    
    working_servers = []
    
    for ip, name in servers:
        if test_server(ip, name):
            working_servers.append((ip, name))
        print()
    
    if working_servers:
        print("🎉 Working servers:")
        for ip, name in working_servers:
            print(f"   ✅ {name}: http://{ip}:8000")
    else:
        print("❌ No servers are currently responding")
        print("💡 The applications may still be starting up. Try again in a few minutes.")

if __name__ == "__main__":
    test_servers()
