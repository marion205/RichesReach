#!/usr/bin/env python3
"""
Quick test script to verify Bitcoin price fetching for voice queries
"""
import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"

async def test_bitcoin_voice_query():
    """Test the voice streaming endpoint with a Bitcoin query"""
    url = f"{BASE_URL}/api/voice/stream"
    payload = {
        "transcript": "What's Bitcoin doing?",
        "history": [],
        "last_trade": None,
    }
    
    print("🧪 Testing Bitcoin voice query...")
    print(f"📤 Sending: {payload['transcript']}")
    print(f"🔗 URL: {url}\n")
    
    start_time = time.time()
    first_token_time = None
    full_response_time = None
    tokens_received = 0
    full_text = ""
    price_mentioned = False
    fresh_data_mentioned = False
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    print(f"❌ HTTP {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:200]}")
                    return
                
                print("✅ Connected to streaming endpoint")
                print("📥 Receiving stream...\n")
                
                async for line in response.content:
                    if not line:
                        continue
                    try:
                        line_text = line.decode('utf-8').strip()
                        if not line_text:
                            continue
                        
                        data = json.loads(line_text)
                        
                        if data.get("type") == "ack":
                            print(f"⚡ ACK: {data.get('text', '')}")
                        
                        elif data.get("type") == "token":
                            if first_token_time is None:
                                first_token_time = time.time()
                                latency_ms = (first_token_time - start_time) * 1000
                                print(f"🎯 First token received: {latency_ms:.0f}ms\n")
                            
                            token_text = data.get("text", "")
                            full_text += token_text
                            tokens_received += 1
                            
                            # Check for price mentions
                            if "$" in token_text or "price" in token_text.lower():
                                price_mentioned = True
                            
                            # Check for freshness indicators
                            if any(word in token_text.lower() for word in ["current", "real-time", "just now", "as of", "fresh"]):
                                fresh_data_mentioned = True
                            
                            # Print tokens as they arrive (first 200 chars)
                            if len(full_text) <= 200:
                                print(token_text, end="", flush=True)
                        
                        elif data.get("type") == "done":
                            full_response_time = time.time()
                            full_text = data.get("full_text", full_text)
                            break
                        
                        elif data.get("type") == "error":
                            print(f"\n❌ Error: {data.get('text', 'Unknown error')}")
                            return
                    
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"\n⚠️ Error parsing line: {e}")
                        continue
                
                # Final results
                total_time = (full_response_time - start_time) * 1000 if full_response_time else None
                first_token_latency = (first_token_time - start_time) * 1000 if first_token_time else None
                
                print("\n\n" + "="*60)
                print("📊 TEST RESULTS")
                print("="*60)
                print(f"✅ Query: '{payload['transcript']}'")
                print(f"⚡ First token latency: {first_token_latency:.0f}ms" if first_token_latency else "⚡ First token: N/A")
                print(f"⏱️  Total response time: {total_time:.0f}ms" if total_time else "⏱️  Total: N/A")
                print(f"📝 Tokens received: {tokens_received}")
                print(f"📏 Response length: {len(full_text)} chars")
                print(f"\n💬 Full response:")
                print("-" * 60)
                print(full_text)
                print("-" * 60)
                
                # Analysis
                print(f"\n🔍 ANALYSIS:")
                if price_mentioned:
                    print("✅ Price mentioned in response")
                else:
                    print("⚠️  No price mentioned")
                
                if fresh_data_mentioned:
                    print("✅ Freshness indicators found (current/real-time/etc)")
                else:
                    print("⚠️  No freshness indicators found")
                
                # Check for actual price numbers
                import re
                price_pattern = r'\$[\d,]+\.?\d*'
                prices_found = re.findall(price_pattern, full_text)
                if prices_found:
                    print(f"💰 Prices found: {', '.join(prices_found)}")
                else:
                    print("⚠️  No price format ($XX,XXX) found in response")
                
                return {
                    "success": True,
                    "first_token_latency_ms": first_token_latency,
                    "total_time_ms": total_time,
                    "tokens": tokens_received,
                    "response": full_text,
                    "price_mentioned": price_mentioned,
                    "fresh_data_mentioned": fresh_data_mentioned,
                    "prices_found": prices_found,
                }
    
    except asyncio.TimeoutError:
        print("❌ Request timed out (>30s)")
        return {"error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_bitcoin_voice_query())
    if result:
        print(f"\n✅ Test completed")
    else:
        print(f"\n❌ Test failed")

