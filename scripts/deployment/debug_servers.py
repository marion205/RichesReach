#!/usr/bin/env python3
"""
Debug servers - check what's happening with the applications
"""
import requests
import socket
import time

def test_port(ip, port):
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_http(ip, port, path="/"):
    """Test HTTP endpoint"""
    try:
        response = requests.get(f"http://{ip}:{port}{path}", timeout=5)
        return response.status_code, response.text[:200]
    except requests.exceptions.ConnectionError:
        return None, "Connection refused"
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def debug_server(ip, name):
    print(f"\n🔍 Debugging {name} at {ip}")
    print("=" * 50)
    
    # Test port 8000
    port_open = test_port(ip, 8000)
    print(f"Port 8000 open: {'✅' if port_open else '❌'}")
    
    if port_open:
        # Test HTTP endpoints
        for path in ["/", "/health", "/api/test"]:
            status, response = test_http(ip, 8000, path)
            if status:
                print(f"GET {path}: ✅ {status} - {response}")
            else:
                print(f"GET {path}: ❌ {response}")
    else:
        print("Port 8000 is not accessible")
    
    # Test other common ports
    for port in [22, 80, 443, 3000, 5000]:
        if test_port(ip, port):
            print(f"Port {port}: ✅ Open")

def main():
    print("🚀 Debugging RichesReach Servers")
    print("=" * 50)
    
    servers = [
        ("18.217.92.158", "Original Server"),
        ("3.21.164.228", "New Simple Server")
    ]
    
    for ip, name in servers:
        debug_server(ip, name)
        time.sleep(1)
    
    print("\n💡 Recommendations:")
    print("- If ports are closed, the application isn't running")
    print("- If ports are open but HTTP fails, there's an app issue")
    print("- Check AWS console for instance logs")

if __name__ == "__main__":
    main()
