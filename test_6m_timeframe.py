#!/usr/bin/env python3
"""
Test script to debug 6M timeframe issue
"""
import requests
import json

def test_6m_timeframe():
    """Test 6M timeframe specifically"""
    query = """
    query Test6MTimeframe {
      benchmarkSeries(symbol: "SPY", timeframe: "6M") {
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
    
    try:
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': query},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("❌ GraphQL Errors:")
                for error in data['errors']:
                    print(f"   {error}")
            elif 'data' in data and data['data'] and data['data']['benchmarkSeries']:
                benchmark = data['data']['benchmarkSeries']
                print(f"✅ 6M Data Found:")
                print(f"   Symbol: {benchmark.get('symbol')}")
                print(f"   Timeframe: {benchmark.get('timeframe')}")
                print(f"   Total Return: {benchmark.get('totalReturnPercent')}%")
                print(f"   Data Points: {len(benchmark.get('dataPoints', []))}")
                return True
            else:
                print("❌ No benchmark data in response")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing 6M Timeframe...")
    print("=" * 40)
    test_6m_timeframe()
