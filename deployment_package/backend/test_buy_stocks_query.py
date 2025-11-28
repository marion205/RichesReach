#!/usr/bin/env python3
"""
Test script to simulate: "buy three stocks that will make me money this week"
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_buy_stocks_query():
    """Test the voice streaming endpoint with a buy stocks query"""
    url = f"{BASE_URL}/api/voice/stream"
    payload = {
        "transcript": "buy three stocks that will make me money this week",
        "history": [],
        "last_trade": None,
    }
    
    print("🧪 Testing Voice Query: 'buy three stocks that will make me money this week'")
    print("=" * 70)
    print(f"📤 Sending request to: {url}")
    print(f"📝 Transcript: {payload['transcript']}\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return
        
        print("✅ Connected to streaming endpoint")
        print("📥 Receiving stream...\n")
        print("-" * 70)
        
        full_text = ""
        tokens_received = 0
        first_token_time = None
        
        for line in response.iter_lines():
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
                        print(f"\n🎯 First token received: {latency_ms:.0f}ms\n")
                    
                    token_text = data.get("text", "")
                    full_text += token_text
                    tokens_received += 1
                    print(token_text, end="", flush=True)
                
                elif data.get("type") == "done":
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
        
        total_time = (time.time() - start_time) * 1000
        first_token_latency = (first_token_time - start_time) * 1000 if first_token_time else None
        
        print("\n" + "-" * 70)
        print("\n📊 TEST RESULTS")
        print("=" * 70)
        print(f"⚡ First token latency: {first_token_latency:.0f}ms" if first_token_latency else "⚡ First token: N/A")
        print(f"⏱️  Total response time: {total_time:.0f}ms")
        print(f"📝 Tokens received: {tokens_received}")
        print(f"📏 Response length: {len(full_text)} chars")
        print(f"\n💬 Full Response:")
        print("=" * 70)
        print(full_text)
        print("=" * 70)
        
        # Analysis
        print(f"\n🔍 ANALYSIS:")
        if "buy" in full_text.lower() and "stock" in full_text.lower():
            print("✅ Mentions buying stocks")
        if "can't" in full_text.lower() or "cannot" in full_text.lower() or "unable" in full_text.lower():
            print("⚠️  Contains negative language (can't/cannot/unable)")
        if "three" in full_text.lower() or "3" in full_text:
            print("✅ Mentions 'three' or '3'")
        if any(word in full_text.lower() for word in ["recommend", "suggest", "opportunity", "trade"]):
            print("✅ Provides recommendations/suggestions")
        
        return {
            "success": True,
            "response": full_text,
            "first_token_latency_ms": first_token_latency,
            "total_time_ms": total_time,
        }
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Is it running?")
        print("   Start with: cd deployment_package/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return {"error": "connection_failed"}
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30s)")
        return {"error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_buy_stocks_query()
    if result and result.get("success"):
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")

