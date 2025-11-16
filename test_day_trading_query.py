"""
Simple test script to verify day trading GraphQL query works
"""
import requests
import json

# GraphQL endpoint
# Try Django GraphQL endpoint first, fallback to FastAPI
GRAPHQL_URL = "http://localhost:8000/graphql/"  # Django
# Alternative: "http://localhost:8000/graphql"  # FastAPI

# Test query
query = """
query GetDayTradingPicks($mode: String!) {
  dayTradingPicks(mode: $mode) {
    asOf
    mode
    picks {
      symbol
      side
      score
      features {
        momentum15m
        rvol10m
        vwapDist
        breakoutPct
        spreadBps
        catalystScore
      }
      risk {
        atr5m
        sizeShares
        stop
        targets
        timeStopMin
      }
      notes
    }
    universeSize
    qualityThreshold
  }
}
"""

def test_day_trading_query(mode="SAFE"):
    """Test the day trading picks query"""
    variables = {"mode": mode}
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🧪 Testing dayTradingPicks query with mode: {mode}")
        print(f"📡 Sending request to {GRAPHQL_URL}")
        
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL Errors:")
                for error in data["errors"]:
                    print(f"   - {error.get('message', error)}")
                return False
            
            if "data" in data and data["data"]:
                result = data["data"].get("dayTradingPicks", {})
                picks = result.get("picks", [])
                
                print(f"✅ Query successful!")
                print(f"   Mode: {result.get('mode')}")
                print(f"   As Of: {result.get('asOf')}")
                print(f"   Universe Size: {result.get('universeSize')}")
                print(f"   Quality Threshold: {result.get('qualityThreshold')}")
                print(f"   Picks Found: {len(picks)}")
                
                if picks:
                    print(f"\n📊 Top 5 Picks:")
                    for i, pick in enumerate(picks[:5], 1):
                        print(f"   {i}. {pick['symbol']} ({pick['side']}) - Score: {pick['score']:.2f}")
                        print(f"      Momentum: {pick['features']['momentum15m']:.4f}")
                        print(f"      Breakout: {pick['features']['breakoutPct']:.4f}")
                        print(f"      Notes: {pick['notes']}")
                
                return True
            else:
                print(f"⚠️ No data returned")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {GRAPHQL_URL}")
        print(f"   Make sure the backend server is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Day Trading GraphQL Query Test")
    print("=" * 60)
    print()
    
    # Test SAFE mode
    print("Testing SAFE mode...")
    safe_success = test_day_trading_query("SAFE")
    print()
    
    # Test AGGRESSIVE mode
    print("Testing AGGRESSIVE mode...")
    aggressive_success = test_day_trading_query("AGGRESSIVE")
    print()
    
    # Summary
    print("=" * 60)
    if safe_success and aggressive_success:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed - check output above")
    print("=" * 60)

