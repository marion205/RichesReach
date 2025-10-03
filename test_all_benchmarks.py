#!/usr/bin/env python3
"""
Test script to verify all benchmark symbols are working
"""
import requests
import json

# Test all benchmark symbols
SYMBOLS = ['SPY', 'QQQ', 'DIA', 'VTI']
TIMEFRAMES = ['1M', '3M', '6M', '1Y']

def test_benchmark_symbol(symbol, timeframe):
    """Test a specific benchmark symbol and timeframe"""
    query = f"""
    query Test{symbol}Benchmark {{
      benchmarkSeries(symbol: "{symbol}", timeframe: "{timeframe}") {{
        symbol
        name
        timeframe
        totalReturnPercent
        dataPoints {{
          timestamp
          value
          change
          changePercent
        }}
        startValue
        endValue
        totalReturn
        volatility
      }}
    }}
    """
    
    try:
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': query},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and data['data']['benchmarkSeries']:
                benchmark = data['data']['benchmarkSeries']
                return {
                    'success': True,
                    'symbol': benchmark.get('symbol'),
                    'name': benchmark.get('name'),
                    'return': benchmark.get('totalReturnPercent'),
                    'dataPoints': len(benchmark.get('dataPoints', [])),
                    'startValue': benchmark.get('startValue'),
                    'endValue': benchmark.get('endValue')
                }
            else:
                return {'success': False, 'error': 'No data in response'}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_all_benchmarks():
    """Test all benchmark symbols and timeframes"""
    print("🧪 Testing All Benchmark Symbols...")
    print("=" * 60)
    
    results = {}
    
    for symbol in SYMBOLS:
        print(f"\n📊 Testing {symbol}:")
        symbol_results = {}
        
        for timeframe in TIMEFRAMES:
            result = test_benchmark_symbol(symbol, timeframe)
            symbol_results[timeframe] = result
            
            if result['success']:
                print(f"   ✅ {timeframe}: {result['return']:.2f}% ({result['dataPoints']} points)")
            else:
                print(f"   ❌ {timeframe}: {result['error']}")
        
        results[symbol] = symbol_results
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY:")
    
    total_tests = len(SYMBOLS) * len(TIMEFRAMES)
    successful_tests = sum(
        1 for symbol_results in results.values()
        for result in symbol_results.values()
        if result['success']
    )
    
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("\n🎉 All benchmark data is working perfectly!")
        return True
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests failed")
        return False

if __name__ == "__main__":
    test_all_benchmarks()
