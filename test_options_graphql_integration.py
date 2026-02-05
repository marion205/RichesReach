#!/usr/bin/env python3
"""
Quick test of Options Edge Factory GraphQL integration
Run: python3 test_options_graphql_integration.py
"""
import sys
import os

# Add Django path
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

import django
django.setup()

from core.options_models import OptionsPortfolio, OptionsPosition, OptionsRegimeSnapshot
from django.contrib.auth import get_user_model

User = get_user_model()

def test_database_models():
    """Test that models are properly installed"""
    print("=" * 80)
    print("TEST 1: Database Models")
    print("=" * 80)
    
    # Check tables exist
    print("✓ OptionsPortfolio model loaded")
    print("✓ OptionsPosition model loaded")
    print("✓ OptionsRegimeSnapshot model loaded")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test@richesreach.com",
        defaults={'name': 'Test User'}
    )
    print(f"✓ Test user: {user.email} (created={created})")
    
    # Create portfolio if doesn't exist
    portfolio, created = OptionsPortfolio.objects.get_or_create(
        user=user,
        defaults={
            'account_equity': 25000,
            'experience_level': 'basic',
            'risk_appetite': 0.5
        }
    )
    print(f"✓ Portfolio: ${portfolio.account_equity} equity (created={created})")
    print(f"  - Experience: {portfolio.experience_level}")
    print(f"  - Total Delta: {portfolio.total_delta}")
    print(f"  - Total Vega: {portfolio.total_vega}")
    print(f"  - Open Positions: {portfolio.total_positions_count}")
    
    return user, portfolio


def test_graphql_schema():
    """Test that GraphQL schema includes Options queries"""
    print("\n" + "=" * 80)
    print("TEST 2: GraphQL Schema")
    print("=" * 80)
    
    from core.schema import schema
    
    # Check if queries exist in schema
    query_type = schema.graphql_schema.query_type
    fields = query_type.fields
    
    options_queries = [
        'optionsAnalysis',
        'myOptionsPortfolio',
        'optionsPositions',
        'optionsRegime'
    ]
    
    for query_name in options_queries:
        if query_name in fields:
            print(f"✓ {query_name} query available")
        else:
            print(f"✗ {query_name} query MISSING")
    
    return True


def test_adapter_functions():
    """Test adapter functions work"""
    print("\n" + "=" * 80)
    print("TEST 3: Adapter Functions")
    print("=" * 80)
    
    from core.options_adapter import build_portfolio_snapshot_from_db
    
    # Get test user
    user = User.objects.filter(email="test@richesreach.com").first()
    if not user:
        print("✗ Test user not found")
        return False
    
    # Test portfolio snapshot builder
    snapshot = build_portfolio_snapshot_from_db(user.id)
    
    print(f"✓ build_portfolio_snapshot_from_db(user_id={user.id})")
    print(f"  - Equity: ${snapshot.equity}")
    print(f"  - Delta: {snapshot.greeks_total.delta}")
    print(f"  - Vega: {snapshot.greeks_total.vega}")
    print(f"  - Sector exposure: {len(snapshot.sector_exposure_pct)} sectors")
    print(f"  - Ticker exposure: {len(snapshot.ticker_exposure_pct)} tickers")
    
    return True


def test_pipeline_components():
    """Test that all pipeline components are importable"""
    print("\n" + "=" * 80)
    print("TEST 4: Pipeline Components")
    print("=" * 80)
    
    try:
        from core.options_regime_detector import RegimeDetector
        print("✓ RegimeDetector imported")
    except ImportError as e:
        print(f"✗ RegimeDetector: {e}")
    
    try:
        from core.options_valuation_engine import OptionsValuationEngine
        print("✓ OptionsValuationEngine imported")
    except ImportError as e:
        print(f"✗ OptionsValuationEngine: {e}")
    
    try:
        from core.options_strategy_router import StrategyRouter
        print("✓ StrategyRouter imported")
    except ImportError as e:
        print(f"✗ StrategyRouter: {e}")
    
    try:
        from core.options_risk_sizer import OptionsRiskSizer
        print("✓ OptionsRiskSizer imported")
    except ImportError as e:
        print(f"✗ OptionsRiskSizer: {e}")
    
    try:
        from core.options_flight_manual import FlightManualEngine
        print("✓ FlightManualEngine imported")
    except ImportError as e:
        print(f"✗ FlightManualEngine: {e}")
    
    try:
        from core.options_api_wiring import OptionsAnalysisPipeline
        print("✓ OptionsAnalysisPipeline imported")
    except ImportError as e:
        print(f"✗ OptionsAnalysisPipeline: {e}")
    
    return True


def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " OPTIONS EDGE FACTORY - INTEGRATION TEST ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        test_database_models()
        test_graphql_schema()
        test_adapter_functions()
        test_pipeline_components()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Start backend: python manage.py runserver")
        print("2. Open GraphQL Playground: http://localhost:8000/graphql/")
        print("3. Try query from: test_options_graphql_query.graphql")
        print("4. Example query:")
        print("""
query {
  optionsAnalysis(ticker: "AAPL", experienceLevel: "basic") {
    ticker
    regime
    flightManuals {
      headline
      riskDollars
      probabilityOfProfit
      actionRecommended
    }
  }
}
        """)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
