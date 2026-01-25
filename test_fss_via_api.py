#!/usr/bin/env python3
"""
Test FSS via API endpoint
Tests FSS calculation through the AI chat endpoint.
"""
import requests
import json

# Test the assistant query endpoint
url = "http://localhost:8000/assistant/query"

test_queries = [
    "Rank these stocks: AAPL, MSFT, GOOGL",
    "What are the best stocks to buy right now?",
    "Score these stocks using FSS: NVDA, TSLA",
]

print("\n" + "="*80)
print("Testing FSS v3.0 via AI Chat Endpoint")
print("="*80 + "\n")

for query in test_queries:
    print(f"Query: {query}")
    print("-" * 80)
    
    payload = {
        "user_id": "test_user",
        "prompt": query,
        "context": None,
        "market_context": None
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", data.get("response", ""))
            model = data.get("model", "unknown")
            
            print(f"Model: {model}")
            print(f"Response: {answer[:200]}...")
            print()
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Start server with: python main_server.py")
        print()
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

print("="*80)
print("✅ API Test Complete!")
print("="*80 + "\n")

