#!/usr/bin/env python3
"""
Test backtest service with real market data
Uses existing API keys to fetch real historical data
"""
import os
import sys
import django
from datetime import date, timedelta
import asyncio

# Setup Django
backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.raha_models import StrategyVersion, RAHABacktestRun
from core.raha_backtest_service import RAHABacktestService
from core.market_data_api_service import MarketDataAPIService
from django.contrib.auth import get_user_model

User = get_user_model()

async def test_market_data_fetch():
    """Test fetching real market data"""
    print("=" * 60)
    print("Testing Market Data Fetching")
    print("=" * 60)
    
    service = MarketDataAPIService()
    print(f"\n📊 Loaded {len(service.api_keys)} API keys:")
    for provider in service.api_keys.keys():
        print(f"   ✅ {provider.value}")
    
    if not service.api_keys:
        print("\n⚠️  No API keys found. Please set environment variables:")
        print("   - POLYGON_API_KEY")
        print("   - ALPHA_VANTAGE_API_KEY")
        print("   - FINNHUB_API_KEY")
        return False
    
    # Test fetching historical data for a popular symbol
    symbol = 'AAPL'
    print(f"\n🔄 Testing historical data fetch for {symbol}...")
    
    async with service:
        # Try to get historical data
        data = await service.get_historical_data(symbol, period='1mo')
        
        if data is not None and len(data) > 0:
            print(f"✅ Successfully fetched {len(data)} data points")
            print(f"   Columns: {list(data.columns)}")
            print(f"   Date range: {data.index[0]} to {data.index[-1]}")
            return True
        else:
            print("❌ No data returned")
            return False


def test_backtest_with_real_data():
    """Test backtest service with real market data"""
    print("\n" + "=" * 60)
    print("Testing Backtest Service with Real Data")
    print("=" * 60)
    
    # Get test user
    try:
        user = User.objects.get(email='test@richesreach.com')
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@richesreach.com',
            password='testpass123',
            name='Test User'
        )
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Get a strategy version
    from core.raha_models import Strategy
    strategy_version = StrategyVersion.objects.filter(strategy__enabled=True).first()
    if not strategy_version:
        print("❌ No enabled strategy versions found.")
        return False
    
    print(f"\n📊 Using strategy: {strategy_version.strategy.name}")
    
    # Use a shorter date range for faster testing (7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    print(f"\n📅 Backtest period: {start_date} to {end_date}")
    print(f"   Symbol: SPY (S&P 500 ETF - more reliable data)")
    print(f"   Timeframe: 5m")
    
    backtest = RAHABacktestRun.objects.create(
        user=user,
        strategy_version=strategy_version,
        symbol='SPY',  # Use SPY as it's more likely to have data
        timeframe='5m',
        start_date=start_date,
        end_date=end_date,
        parameters={},
        status='PENDING'
    )
    
    print(f"\n🔄 Running backtest (ID: {backtest.id})...")
    print("   This may take a few minutes...")
    
    # Run the backtest
    backtest_service = RAHABacktestService()
    try:
        result = backtest_service.run_backtest(str(backtest.id))
        result.refresh_from_db()
        
        print(f"\n✅ Backtest completed with status: {result.status}")
        
        if result.status == 'COMPLETED':
            metrics = result.metrics or {}
            print(f"\n📈 Backtest Results:")
            print(f"   Total Trades: {metrics.get('total_trades', 0)}")
            print(f"   Win Rate: {metrics.get('win_rate', 0):.2f}%")
            print(f"   Winning Trades: {metrics.get('winning_trades', 0)}")
            print(f"   Losing Trades: {metrics.get('losing_trades', 0)}")
            print(f"   Total P&L: {metrics.get('total_pnl_percent', 0):.2f}%")
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
            print(f"   Sortino Ratio: {metrics.get('sortino_ratio', 'N/A')}")
            print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.4f}")
            print(f"   Expectancy: {metrics.get('expectancy', 0):.2f}")
            print(f"   Avg Win: ${metrics.get('avg_win', 0):.2f}")
            print(f"   Avg Loss: ${metrics.get('avg_loss', 0):.2f}")
            
            equity_curve = result.equity_curve or []
            print(f"\n📊 Equity Curve Points: {len(equity_curve)}")
            if equity_curve:
                print(f"   Start Equity: ${equity_curve[0].get('equity', 0):.2f}")
                print(f"   End Equity: ${equity_curve[-1].get('equity', 0):.2f}")
            
            trade_log = result.trade_log or []
            print(f"\n📝 Trade Log Entries: {len(trade_log)}")
            if trade_log and len(trade_log) > 0:
                print(f"   Sample Trade: Entry=${trade_log[0].get('entry_price', 0):.2f}, Exit=${trade_log[0].get('exit_price', 0):.2f}, P&L=${trade_log[0].get('pnl', 0):.2f}")
            
            return True
        else:
            error_msg = result.metrics.get('error', 'Unknown error') if result.metrics else 'Unknown error'
            print(f"\n❌ Backtest failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🧪 RAHA Backtest Service - Real Data Test\n")
    
    # Test 1: Market Data Fetching
    data_success = asyncio.run(test_market_data_fetch())
    
    # Test 2: Backtest with Real Data
    if data_success:
        backtest_success = test_backtest_with_real_data()
    else:
        print("\n⚠️  Skipping backtest test - market data fetch failed")
        backtest_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Market Data Fetch: {'✅ PASS' if data_success else '❌ FAIL'}")
    print(f"Backtest Service: {'✅ PASS' if backtest_success else '❌ FAIL'}")
    print("=" * 60 + "\n")

