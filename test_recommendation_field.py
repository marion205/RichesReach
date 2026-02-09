#!/usr/bin/env python3
"""Test if recommendation field exists and works"""
import json
import urllib.request
import urllib.error


def main() -> None:
  url = "http://localhost:8001/graphql"

  query = '''
query {
  beginnerFriendlyStocks {
  symbol
  recommendation
  beginnerFriendlyScore
  marketCap
  peRatio
  }
}
'''

  data = json.dumps({"query": query}).encode('utf-8')
  req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

  try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())

    print("Response received!")
    if "errors" in result:
      print("❌ GraphQL Errors:")
      for error in result["errors"]:
        print(f"  - {error.get('message', error)}")
    else:
      stocks = result.get("data", {}).get("beginnerFriendlyStocks", [])
      print(f"\n✅ Got {len(stocks)} stocks\n")

      for stock in stocks[:3]:
        print(f"{stock['symbol']}:")
        print(f"  Score: {stock.get('beginnerFriendlyScore')}")
        print(f"  Recommendation: {stock.get('recommendation')}")
        print(f"  Market Cap: {stock.get('marketCap')}")
        print(f"  P/E: {stock.get('peRatio')}")
        print()

  except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
  except Exception as e:
    print(f"Error: {e}")


if __name__ == '__main__':
  main()
