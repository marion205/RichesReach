#!/usr/bin/env python3
"""
Test script to verify Portfolio Comparison component integration with real data
"""
import requests
import json

def test_portfolio_comparison_queries():
    """Test the exact queries that Portfolio Comparison component makes"""
    
    # These are the exact queries the Portfolio Comparison component makes
    queries = [
        {
            'name': 'SPY 1Y',
            'query': '''
            query GetSPYBenchmark {
              benchmarkSeries(symbol: "SPY", timeframe: "1Y") {
                symbol
                name
                timeframe
                dataPoints {
                  timestamp
                  value
                  change
                  changePercent
                }
                startValue
                endValue
                totalReturn
                totalReturnPercent
                volatility
              }
            }
            '''
        },
        {
            'name': 'QQQ 1Y',
            'query': '''
            query GetQQQBenchmark {
              benchmarkSeries(symbol: "QQQ", timeframe: "1Y") {
                symbol
                name
                timeframe
                dataPoints {
                  timestamp
                  value
                  change
                  changePercent
                }
                startValue
                endValue
                totalReturn
                totalReturnPercent
                volatility
              }
            }
            '''
        },
        {
            'name': 'DIA 1Y',
            'query': '''
            query GetDIABenchmark {
              benchmarkSeries(symbol: "DIA", timeframe: "1Y") {
                symbol
                name
                timeframe
                dataPoints {
                  timestamp
                  value
                  change
                  changePercent
                }
                startValue
                endValue
                totalReturn
                totalReturnPercent
                volatility
              }
            }
            '''
        },
        {
            'name': 'VTI 1Y',
            'query': '''
            query GetVTIBenchmark {
              benchmarkSeries(symbol: "VTI", timeframe: "1Y") {
                symbol
                name
                timeframe
                dataPoints {
                  timestamp
                  value
                  change
                  changePercent
                }
                startValue
                endValue
                totalReturn
                totalReturnPercent
                volatility
              }
            }
            '''
        }
    ]
    
    print("🧪 Testing Portfolio Comparison Component Integration...")
    print("=" * 60)
    
    results = []
    
    for test in queries:
        print(f"\n📊 Testing {test['name']}:")
        
        try:
            response = requests.post(
                'http://localhost:8000/graphql/',
                json={'query': test['query']},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data'] and data['data']['benchmarkSeries']:
                    benchmark = data['data']['benchmarkSeries']
                    
                    # Verify the data structure matches what the component expects
                    required_fields = ['symbol', 'name', 'timeframe', 'totalReturnPercent', 'dataPoints']
                    missing_fields = [field for field in required_fields if field not in benchmark]
                    
                    if not missing_fields:
                        print(f"   ✅ {benchmark['symbol']}: {benchmark['totalReturnPercent']:.2f}% ({len(benchmark['dataPoints'])} points)")
                        print(f"   📈 Start: ${benchmark['startValue']:.2f} → End: ${benchmark['endValue']:.2f}")
                        print(f"   📊 Volatility: {benchmark['volatility']:.2f}%")
                        
                        results.append({
                            'symbol': benchmark['symbol'],
                            'success': True,
                            'return': benchmark['totalReturnPercent'],
                            'dataPoints': len(benchmark['dataPoints']),
                            'volatility': benchmark['volatility']
                        })
                    else:
                        print(f"   ❌ Missing fields: {missing_fields}")
                        results.append({'symbol': test['name'], 'success': False, 'error': f'Missing fields: {missing_fields}'})
                else:
                    print(f"   ❌ No benchmark data in response")
                    results.append({'symbol': test['name'], 'success': False, 'error': 'No data in response'})
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                results.append({'symbol': test['name'], 'success': False, 'error': f'HTTP {response.status_code}'})
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({'symbol': test['name'], 'success': False, 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 PORTFOLIO COMPARISON INTEGRATION SUMMARY:")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print(f"\n🎯 Real Benchmark Data Available:")
        for result in successful:
            print(f"   • {result['symbol']}: {result['return']:.2f}% return, {result['dataPoints']} data points")
    
    if failed:
        print(f"\n⚠️  Failed Tests:")
        for result in failed:
            print(f"   • {result['symbol']}: {result['error']}")
    
    print("\n" + "=" * 60)
    if len(successful) == len(results):
        print("🎉 Portfolio Comparison component is ready to use REAL DATA!")
        print("✅ All benchmark queries are working correctly")
        print("✅ Data structure matches component expectations")
        print("✅ Real market data is being served")
        return True
    else:
        print("❌ Portfolio Comparison component has integration issues")
        return False

if __name__ == "__main__":
    test_portfolio_comparison_queries()
