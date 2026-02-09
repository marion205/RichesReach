#!/usr/bin/env python3
"""
Quick test to verify voice endpoints are working.
Tests for 404s and basic functionality.
"""
__test__ = False

import asyncio
import aiohttp
import json
import sys

BASE_URL = "http://localhost:8000"

async def test_endpoint(url, method="GET", **kwargs):
    """Test an endpoint and return status."""
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status, await response.text()
            elif method == "POST":
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=10), **kwargs) as response:
                    return response.status, await response.text()
    except aiohttp.ClientError as e:
        return None, str(e)
    except asyncio.TimeoutError:
        return None, "Timeout"

async def test_streaming():
    """Test streaming endpoint."""
    print("📡 Testing /api/voice/stream...")
    url = f"{BASE_URL}/api/voice/stream"
    payload = {
        "transcript": "What should I invest in today?",
        "history": [],
    }
    
    status, response = await test_endpoint(url, method="POST", json=payload)
    
    if status is None:
        print(f"   ❌ Error: {response}")
        return False
    
    if status == 404:
        print(f"   ❌ 404 Not Found - endpoint doesn't exist!")
        return False
    
    if status != 200:
        print(f"   ⚠️  Status {status}: {response[:100]}")
        return False
    
    # Try to read at least one chunk
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                chunk_count = 0
                async for line in resp.content:
                    if line:
                        chunk_count += 1
                        try:
                            data = json.loads(line.decode('utf-8').strip())
                            if data.get("type") == "token":
                                print(f"   ✅ Streaming working! First token: '{data.get('text', '')[:20]}...'")
                                return True
                        except:
                            pass
                        if chunk_count > 10:  # Don't wait forever
                            break
    except Exception as e:
        print(f"   ⚠️  Couldn't read stream: {e}")
        return status == 200  # At least endpoint exists
    
    print(f"   ✅ Endpoint exists and responds (status {status})")
    return True

async def test_process():
    """Test process endpoint."""
    print("📡 Testing /api/voice/process/...")
    url = f"{BASE_URL}/api/voice/process/"
    
    form_data = aiohttp.FormData()
    form_data.add_field('audio', b'fake_audio_data', filename='test.wav', content_type='audio/wav')
    
    status, response = await test_endpoint(url, method="POST", data=form_data)
    
    if status is None:
        print(f"   ❌ Error: {response}")
        return False
    
    if status == 404:
        print(f"   ❌ 404 Not Found - endpoint doesn't exist!")
        return False
    
    print(f"   ✅ Endpoint exists (status {status})")
    return True

async def main():
    """Run all quick tests."""
    print("=" * 60)
    print("🧪 Quick Voice Endpoint Test")
    print("=" * 60)
    print()
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    status, _ = await test_endpoint(f"{BASE_URL}/health")
    if status is None or status != 200:
        print(f"   ⚠️  Server may not be running (status: {status})")
        print(f"   💡 Make sure your backend is running on {BASE_URL}")
        print()
        return
    
    print("   ✅ Server is running")
    print()
    
    # Test endpoints
    results = []
    
    results.append(await test_streaming())
    print()
    
    results.append(await test_process())
    print()
    
    # Summary
    print("=" * 60)
    if all(results):
        print("✅ All endpoints working!")
        print()
        print("Next steps:")
        print("  1. Run full benchmark: python3 test_voice_benchmark.py")
        print("  2. Run unit tests: pytest test_voice_endpoints.py -v")
    else:
        print("❌ Some tests failed")
        print()
        print("Check:")
        print("  1. Backend server is running")
        print("  2. OPENAI_API_KEY is set (for streaming)")
        print("  3. No syntax errors in main.py")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)

