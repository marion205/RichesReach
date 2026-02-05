#!/usr/bin/env python3
import os
import requests
from datetime import datetime, timedelta

api_key = os.getenv('POLYGON_API_KEY')
if not api_key:
    print("❌ POLYGON_API_KEY not set")
    exit(1)

print(f"✅ API Key loaded: {api_key[:20]}...")

# Test 1: OHLCV History
ticker = "AAPL"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=60)

url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
params = {'apiKey': api_key, 'sort': 'asc', 'limit': 50000}

print(f"\n[1] Fetching {ticker} OHLCV ({start_date} to {end_date})...")
try:
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"✅ Got {len(results)} bars")
        if results:
            latest = results[-1]
            print(f"   Latest: {latest.get('t')} - Close: ${latest.get('c')}")
    else:
        print(f"❌ Status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Current Quote
print(f"\n[2] Fetching {ticker} current quote...")
url = f"https://api.polygon.io/v1/last/quotes/{ticker}"
try:
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'OK':
            quote = data.get('last', {})
            bid = quote.get('bid')
            ask = quote.get('ask')
            mid = (bid + ask) / 2 if bid and ask else None
            print(f"✅ Bid: ${bid}, Ask: ${ask}, Mid: ${mid}")
        else:
            print(f"❌ API Error: {data.get('message')}")
    else:
        print(f"❌ Status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Option Chain
print(f"\n[3] Fetching {ticker} option chain...")
url = f"https://api.polygon.io/v3/reference/options/contracts"
params_opts = {'underlying_ticker': ticker, 'apiKey': api_key, 'limit': 100}
try:
    response = requests.get(url, params=params_opts, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'OK':
            contracts = data.get('results', [])
            print(f"✅ Got {len(contracts)} contracts")
            if contracts:
                first = contracts[0]
                print(f"   Sample: {first.get('ticker')} - Strike: {first.get('strike_price')}")
        else:
            print(f"❌ API Error: {data.get('message')}")
    else:
        print(f"❌ Status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Live Polygon API test complete!")
