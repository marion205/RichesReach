#!/usr/bin/env python3
"""
Benchmark test for voice streaming endpoint.
Tests latency improvements: streaming vs non-streaming.
"""
__test__ = False

import asyncio
import aiohttp
import time
import json
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TRANSCRIPTS = [
    "What should I invest in today?",
    "Show me the best crypto opportunity",
    "What's my portfolio performance?",
    "Buy one Bitcoin",
    "Execute the trade",
]

async def test_streaming_endpoint(transcript: str, history: List = None) -> Dict:
    """Test the streaming endpoint and measure latency."""
    url = f"{BASE_URL}/api/voice/stream"
    payload = {
        "transcript": transcript,
        "history": history or [],
        "last_trade": None,
    }
    
    start_time = time.time()
    first_token_time = None
    full_response_time = None
    tokens_received = 0
    full_text = ""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    return {
                        "error": f"HTTP {response.status}",
                        "status": response.status,
                    }
                
                # Read streaming response
                async for line in response.content:
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line.decode('utf-8').strip())
                        
                        if data.get("type") == "ack":
                            # Acknowledgment received
                            pass
                        elif data.get("type") == "token":
                            if first_token_time is None:
                                first_token_time = time.time()
                            tokens_received += 1
                            full_text += data.get("text", "")
                        elif data.get("type") == "done":
                            full_response_time = time.time()
                            full_text = data.get("full_text", full_text)
                            break
                        elif data.get("type") == "error":
                            return {
                                "error": data.get("text", "Unknown error"),
                            }
                    except json.JSONDecodeError:
                        continue
        
        return {
            "status": "success",
            "first_token_latency_ms": (first_token_time - start_time) * 1000 if first_token_time else None,
            "full_response_latency_ms": (full_response_time - start_time) * 1000 if full_response_time else None,
            "tokens_received": tokens_received,
            "response_length": len(full_text),
            "full_text": full_text[:100] + "..." if len(full_text) > 100 else full_text,
        }
    except Exception as e:
        return {
            "error": str(e),
        }

async def test_non_streaming_endpoint(transcript: str, history: List = None) -> Dict:
    """Test the non-streaming endpoint (old way) for comparison."""
    url = f"{BASE_URL}/api/voice/process/"
    
    # Create a mock audio file (multipart form data)
    form_data = aiohttp.FormData()
    form_data.add_field('audio', b'fake_audio_data', filename='test.wav', content_type='audio/wav')
    form_data.add_field('transcript', transcript)  # Simulate already transcribed
    if history:
        form_data.add_field('history', json.dumps(history))
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                if response.status != 200:
                    return {
                        "error": f"HTTP {response.status}",
                        "status": response.status,
                    }
                
                data = await response.json()
                end_time = time.time()
                
                return {
                    "status": "success",
                    "latency_ms": (end_time - start_time) * 1000,
                    "response_length": len(data.get("response", {}).get("text", "")),
                    "full_text": data.get("response", {}).get("text", "")[:100] + "..." if len(data.get("response", {}).get("text", "")) > 100 else data.get("response", {}).get("text", ""),
                }
    except Exception as e:
        return {
            "error": str(e),
        }

async def run_benchmark():
    """Run benchmark tests."""
    print("=" * 80)
    print("🚀 Voice Endpoint Benchmark Test")
    print("=" * 80)
    print()
    
    streaming_results = []
    non_streaming_results = []
    
    for i, transcript in enumerate(TEST_TRANSCRIPTS, 1):
        print(f"Test {i}/{len(TEST_TRANSCRIPTS)}: '{transcript}'")
        print("-" * 80)
        
        # Test streaming endpoint
        print("📡 Testing streaming endpoint...")
        streaming_result = await test_streaming_endpoint(transcript)
        streaming_results.append(streaming_result)
        
        if "error" in streaming_result:
            print(f"  ❌ Error: {streaming_result['error']}")
        else:
            print(f"  ✅ First token: {streaming_result.get('first_token_latency_ms', 0):.0f}ms")
            print(f"  ✅ Full response: {streaming_result.get('full_response_latency_ms', 0):.0f}ms")
            print(f"  ✅ Tokens received: {streaming_result.get('tokens_received', 0)}")
        
        # Wait a bit between requests
        await asyncio.sleep(0.5)
        
        # Test non-streaming endpoint (skip for now - requires actual audio file)
        # print("📡 Testing non-streaming endpoint...")
        # non_streaming_result = await test_non_streaming_endpoint(transcript)
        # non_streaming_results.append(non_streaming_result)
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 Benchmark Summary")
    print("=" * 80)
    
    successful_streaming = [r for r in streaming_results if "error" not in r]
    
    if successful_streaming:
        first_token_times = [r.get("first_token_latency_ms", 0) for r in successful_streaming if r.get("first_token_latency_ms")]
        full_response_times = [r.get("full_response_latency_ms", 0) for r in successful_streaming if r.get("full_response_latency_ms")]
        
        if first_token_times:
            avg_first_token = sum(first_token_times) / len(first_token_times)
            min_first_token = min(first_token_times)
            max_first_token = max(first_token_times)
            
            print(f"\n🎯 First Token Latency (Streaming):")
            print(f"   Average: {avg_first_token:.0f}ms")
            print(f"   Min: {min_first_token:.0f}ms")
            print(f"   Max: {max_first_token:.0f}ms")
            print(f"   Target: <450ms ✅" if avg_first_token < 450 else f"   Target: <450ms ⚠️")
        
        if full_response_times:
            avg_full = sum(full_response_times) / len(full_response_times)
            min_full = min(full_response_times)
            max_full = max(full_response_times)
            
            print(f"\n🎯 Full Response Latency (Streaming):")
            print(f"   Average: {avg_full:.0f}ms")
            print(f"   Min: {min_full:.0f}ms")
            print(f"   Max: {max_full:.0f}ms")
    
    errors = [r for r in streaming_results if "error" in r]
    if errors:
        print(f"\n❌ Errors: {len(errors)}/{len(streaming_results)}")
        for error in errors:
            print(f"   - {error.get('error')}")
    else:
        print(f"\n✅ All tests passed! ({len(successful_streaming)}/{len(streaming_results)})")
    
    print()

if __name__ == "__main__":
    asyncio.run(run_benchmark())

