#!/usr/bin/env python3
"""
Direct Alpha Vantage API Test
Test live market data directly with your API key
"""

import os
import asyncio
import aiohttp
import json
import time

async def test_alpha_vantage_direct():
    """Test Alpha Vantage API directly"""
    print("🔍 Direct Alpha Vantage API Test...")
    print("=" * 50)
    
    api_key = 'K0A7XYLDNXHNQ1WI'
    base_url = "https://www.alphavantage.co/query"
    
    # Test different endpoints
    tests = [
        {
            'name': 'VIX (Volatility Index)',
            'function': 'GLOBAL_QUOTE',
            'symbol': '^VIX',
            'description': 'Market fear gauge'
        },
        {
            'name': '10-Year Treasury Yield',
            'function': 'GLOBAL_QUOTE', 
            'symbol': '^TNX',
            'description': 'Bond market indicator'
        },
        {
            'name': 'S&P 500 ETF',
            'function': 'GLOBAL_QUOTE',
            'symbol': 'SPY',
            'description': 'Major market index'
        },
        {
            'name': 'Technology Sector ETF',
            'function': 'GLOBAL_QUOTE',
            'symbol': 'XLK',
            'description': 'Tech sector performance'
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests):
        print(f"\n🧪 Test {i+1}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        try:
            # Make API call
            params = {
                'function': test['function'],
                'symbol': test['symbol'],
                'apikey': api_key
            }
            
            # Create SSL context for macOS
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(base_url, params=params, ssl=ssl_context) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'Global Quote' in data and data['Global Quote']:
                            quote = data['Global Quote']
                            price = quote.get('05. price', 'N/A')
                            change = quote.get('09. change', 'N/A')
                            change_percent = quote.get('10. change percent', 'N/A')
                            
                            print(f"   ✅ SUCCESS!")
                            print(f"      Price: {price}")
                            print(f"      Change: {change}")
                            print(f"      Change %: {change_percent}")
                            
                            results.append({
                                'test': test['name'],
                                'status': 'SUCCESS',
                                'data': quote
                            })
                        else:
                            print(f"   ⚠️  No data returned")
                            print(f"      Response: {data}")
                            results.append({
                                'test': test['name'],
                                'status': 'NO_DATA',
                                'data': data
                            })
                    else:
                        print(f"   ❌ API call failed: {response.status}")
                        print(f"      Response: {await response.text()}")
                        results.append({
                            'test': test['name'],
                            'status': 'FAILED',
                            'error': f"HTTP {response.status}"
                        })
            
            # Rate limiting: Alpha Vantage free tier is 5 calls/minute
            if i < len(tests) - 1:  # Don't sleep after last test
                print(f"   ⏳ Waiting 15 seconds for rate limit...")
                await asyncio.sleep(15)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'test': test['name'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Summary
    print(f"\n" + "=" * 50)
    print("📊 Direct Alpha Vantage Test Summary")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    for result in results:
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "⚠️" if result['status'] == 'NO_DATA' else "❌"
        print(f"{status_emoji} {result['test']}: {result['status']}")
    
    print(f"\n🎯 Overall: {success_count}/{total_count} tests successful")
    
    if success_count > 0:
        print(f"\n🚀 SUCCESS! Alpha Vantage API is working!")
        print(f"   You have live market data access!")
        print(f"   Rate limit: 5 calls/minute (free tier)")
        
        # Show sample live data
        print(f"\n📊 Sample Live Data:")
        for result in results:
            if result['status'] == 'SUCCESS' and 'data' in result:
                data = result['data']
                print(f"   {result['test']}: ${data.get('05. price', 'N/A')}")
    else:
        print(f"\n⚠️  Alpha Vantage test failed. Check:")
        print(f"   1. API key validity")
        print(f"   2. Rate limits (5 calls/minute)")
        print(f"   3. Network connectivity")
    
    return success_count > 0

async def main():
    """Main test function"""
    print("🚀 Direct Alpha Vantage API Test")
    print("=" * 50)
    print("Testing live market data with your API key...")
    print("Note: Free tier allows 5 calls/minute")
    
    success = await test_alpha_vantage_direct()
    
    if success:
        print(f"\n🎉 Live market data test successful!")
        print(f"📋 Next Steps:")
        print(f"1. 🔑 Get Finnhub API key: https://finnhub.io/register")
        print(f"2. 📰 Get News API key: https://newsapi.org/register")
        print(f"3. 🚀 Update .env file with all keys")
        print(f"4. 🧪 Test complete system: python3 test_api_connections.py")
    else:
        print(f"\n❌ Live market data test failed.")
        print(f"   Check API key and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
