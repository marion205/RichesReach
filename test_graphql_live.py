#!/usr/bin/env python3
"""
End-to-end test: GraphQL query with live Polygon data
"""
import os
import sys
import django


def main() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    os.environ['POLYGON_API_KEY'] = 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2'

    sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')

    django.setup()

    from django.test import Client
    import json

    # Create GraphQL client
    client = Client()

    # Test GraphQL query
    query = """
{
  optionsAnalysis(ticker: "AAPL", experienceLevel: "basic") {
    ticker
    regime
    regimeConfidence
    marketDataSnapshot {
      currentPrice
      ivRank
      realizedVolatility
      bidAskSpread
    }
    flightManuals {
      headline
      strategyType
      contractsToTrade
      riskDollars
      maxProfit
      maxLoss
      probabilityOfProfit
    }
  }
}
"""

    print("=" * 80)
    print("END-TO-END: GraphQL Query with Live Polygon Data")
    print("=" * 80)
    print("\n📝 Query:")
    print(query)

    print("\n⏳ Executing query...")
    response = client.post(
        '/graphql/',
        json={'query': query},
        content_type='application/json'
    )

    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Response received!")
        print("\n📊 Data:")
        print(json.dumps(data, indent=2))

        # Check for errors
        if data.get('errors'):
            print("\n❌ GraphQL Errors:")
            for error in data['errors']:
                print(f"  - {error}")
        else:
            result = data.get('data', {}).get('optionsAnalysis', {})
            if result:
                print(f"\n🎯 Key Results:")
                print(f"  Ticker: {result.get('ticker')}")
                print(f"  Regime: {result.get('regime')}")
                print(f"  Confidence: {result.get('regimeConfidence'):.1%}")
                flight_manuals = result.get('flightManuals', [])
                print(f"  Strategies: {len(flight_manuals)} options")
                if flight_manuals:
                    fm = flight_manuals[0]
                    print(f"\n    Top Strategy:")
                    print(f"      Headline: {fm.get('headline')}")
                    print(f"      Risk: ${fm.get('riskDollars')}")
                    print(f"      POP: {fm.get('probabilityOfProfit'):.1%}")
    else:
        print(f"❌ Error: {response.text}")


if __name__ == '__main__':
    main()
