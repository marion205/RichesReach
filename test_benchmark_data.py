#!/usr/bin/env python3
"""
Test script to verify benchmark data is working correctly
"""
import requests
import json

# GraphQL query to test benchmark data
QUERY = """
query TestBenchmarkData {
  benchmarkSeries(symbol: "SPY", timeframe: "1Y") {
    symbol
    name
    timeframe
    totalReturnPercent
    dataPoints {
      timestamp
      value
      change
      changePercent
    }
    startValue
    endValue
    totalReturn
    volatility
  }
}
"""

def test_benchmark_data():
    """Test if benchmark data is working"""
    try:
        # Make request to GraphQL endpoint
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': QUERY},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GraphQL Response Status: 200")
            print("📊 Response Data:")
            print(json.dumps(data, indent=2))
            
            # Check if we got benchmark data
            if 'data' in data and data['data'] and data['data']['benchmarkSeries']:
                benchmark = data['data']['benchmarkSeries']
                print(f"\n🎯 Benchmark Data Found:")
                print(f"   Symbol: {benchmark.get('symbol')}")
                print(f"   Name: {benchmark.get('name')}")
                print(f"   Timeframe: {benchmark.get('timeframe')}")
                print(f"   Total Return: {benchmark.get('totalReturnPercent')}%")
                print(f"   Data Points: {len(benchmark.get('dataPoints', []))}")
                print(f"   Start Value: ${benchmark.get('startValue')}")
                print(f"   End Value: ${benchmark.get('endValue')}")
                return True
            else:
                print("❌ No benchmark data found in response")
                return False
        else:
            print(f"❌ GraphQL Request Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing benchmark data: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Benchmark Data Integration...")
    print("=" * 50)
    
    success = test_benchmark_data()
    
    print("=" * 50)
    if success:
        print("✅ Benchmark data is working correctly!")
    else:
        print("❌ Benchmark data test failed!")
