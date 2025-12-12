#!/usr/bin/env python3
"""
Test script for RAHA Backtest Service
Tests the backtest execution and metrics calculation
"""
import os
import sys
import django
from datetime import date, timedelta

# Setup Django
backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.raha_models import StrategyVersion, RAHABacktestRun, RAHASignal
from core.raha_backtest_service import RAHABacktestService
from core.raha_queries import RAHAQueries
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_backtest_service():
    """Test the backtest service"""
    print("=" * 60)
    print("Testing RAHA Backtest Service")
    print("=" * 60)
    
    # Get or create a test user
    try:
        user = User.objects.get(email='test@richesreach.com')
        print(f"✅ Using existing test user: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@richesreach.com',
            password='testpass123',
            name='Test User'
        )
        print(f"✅ Created test user: {user.email}")
    
    # Get a strategy version
    try:
        from core.raha_models import Strategy
        strategy_version = StrategyVersion.objects.filter(strategy__enabled=True).first()
        if not strategy_version:
            print("❌ No enabled strategy versions found. Please seed strategies first.")
            print("   Run: python manage.py seed_raha_strategies")
            return False
        
        print(f"\n📊 Using strategy: {strategy_version.strategy.name}")
        print(f"   Version: {strategy_version.version}")
        print(f"   Logic: {strategy_version.logic_ref}")
        
        # Create a backtest run
        end_date = date.today()
        start_date = end_date - timedelta(days=30)  # 30 days backtest
        
        print(f"\n📅 Backtest period: {start_date} to {end_date}")
        print(f"   Symbol: AAPL")
        print(f"   Timeframe: 5m")
        
        backtest = RAHABacktestRun.objects.create(
            user=user,
            strategy_version=strategy_version,
            symbol='AAPL',
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
        result = backtest_service.run_backtest(str(backtest.id))
        
        # Check results
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
            if trade_log:
                print(f"   First Trade: {trade_log[0]}")
                print(f"   Last Trade: {trade_log[-1]}")
            
            return True
        else:
            print(f"\n❌ Backtest failed")
            print(f"   Metrics: {result.metrics}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_calculation():
    """Test the metrics calculation"""
    print("\n" + "=" * 60)
    print("Testing RAHA Metrics Calculation")
    print("=" * 60)
    
    # Get test user
    try:
        user = User.objects.get(email='test@richesreach.com')
    except User.DoesNotExist:
        print("❌ Test user not found. Run backtest test first.")
        return False
    
    # Get a strategy version
    try:
        from core.raha_models import Strategy
        strategy_version = StrategyVersion.objects.filter(strategy__enabled=True).first()
        if not strategy_version:
            print("❌ No enabled strategy versions found.")
            return False
        
        print(f"\n📊 Testing metrics for: {strategy_version.strategy.name}")
        
        # Create a mock query context
        class MockInfo:
            class MockContext:
                def __init__(self, user):
                    self.user = user
            def __init__(self, user):
                self.context = self.MockContext(user)
        
        info = MockInfo(user)
        queries = RAHAQueries()
        
        # Test metrics query
        print("\n🔄 Querying metrics...")
        metrics = queries.resolve_raha_metrics(
            info,
            str(strategy_version.id),
            period="ALL_TIME"
        )
        
        if metrics:
            print(f"\n✅ Metrics Retrieved:")
            print(f"   Total Signals: {metrics.total_signals}")
            print(f"   Winning Signals: {metrics.winning_signals}")
            print(f"   Losing Signals: {metrics.losing_signals}")
            print(f"   Win Rate: {metrics.win_rate:.2f}%")
            print(f"   Total P&L Dollars: ${metrics.total_pnl_dollars:.2f}")
            print(f"   Total P&L Percent: {metrics.total_pnl_percent:.2f}%")
            print(f"   Avg P&L per Signal: {metrics.avg_pnl_per_signal:.2f}%")
            print(f"   Sharpe Ratio: {metrics.sharpe_ratio or 'N/A'}")
            print(f"   Sortino Ratio: {metrics.sortino_ratio or 'N/A'}")
            print(f"   Max Drawdown: {metrics.max_drawdown or 'N/A'}")
            print(f"   Expectancy: {metrics.expectancy:.2f}")
            print(f"   Avg Win: ${metrics.avg_win:.2f}")
            print(f"   Avg Loss: ${metrics.avg_loss:.2f}")
            print(f"   Avg R-Multiple: {metrics.avg_r_multiple:.2f}")
            print(f"   Best R-Multiple: {metrics.best_r_multiple:.2f}")
            print(f"   Worst R-Multiple: {metrics.worst_r_multiple:.2f}")
            return True
        else:
            print("\n❌ No metrics returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🧪 RAHA Backtest Service & Metrics Test Suite\n")
    
    # Test 1: Backtest Service
    backtest_success = test_backtest_service()
    
    # Test 2: Metrics Calculation
    metrics_success = test_metrics_calculation()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Backtest Service: {'✅ PASS' if backtest_success else '❌ FAIL'}")
    print(f"Metrics Calculation: {'✅ PASS' if metrics_success else '❌ FAIL'}")
    print("=" * 60 + "\n")

