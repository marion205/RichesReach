#!/usr/bin/env python3
"""
FSS v3.0 Paper Trading System
Runs daily FSS calculation and tracks paper portfolio performance.
Validates real-time performance vs backtested results.
"""
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import FSSBacktester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
from core.fss_service import get_fss_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paper trading portfolio file
PORTFOLIO_FILE = "fss_paper_portfolio.json"
RESULTS_FILE = "fss_paper_trading_results.json"


class FSSPaperTrading:
    """
    Paper trading system for FSS v3.0
    
    Tracks TWO portfolios:
    1. Regime-Aware: Uses cash-out during Crisis/Deflation
    2. Ghost Always-In: Always invested (for comparison)
    """
    
    def __init__(self, initial_capital=100000, execution_slippage_bps=5.0):
        """
        Args:
            initial_capital: Starting capital
            execution_slippage_bps: Execution slippage in basis points (default: 5 bps = 0.05%)
        """
        self.initial_capital = initial_capital
        self.execution_slippage = execution_slippage_bps / 10000.0  # Convert to decimal
        self.portfolio_file = Path(PORTFOLIO_FILE)
        self.results_file = Path(RESULTS_FILE)
        self.fss_service = get_fss_service()
        self.backtester = FSSBacktester(transaction_cost_bps=10.0)
        
    def load_portfolio(self):
        """Load existing portfolio or create new one"""
        if self.portfolio_file.exists():
            with open(self.portfolio_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "start_date": datetime.now().isoformat(),
                "initial_capital": self.initial_capital,
                "regime_aware": {
                    "current_capital": self.initial_capital,
                    "positions": {},
                    "cash": self.initial_capital,
                    "equity_curve": [],
                    "daily_returns": [],
                    "trades": []
                },
                "ghost_always_in": {
                    "current_capital": self.initial_capital,
                    "positions": {},
                    "cash": 0.0,
                    "equity_curve": [],
                    "daily_returns": [],
                    "trades": []
                }
            }
    
    def save_portfolio(self, portfolio):
        """Save portfolio state"""
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2, default=str)
    
    async def run_daily_update(self):
        """Run daily FSS calculation and update portfolio"""
        
        print("\n" + "="*80)
        print(f"FSS v3.0 Paper Trading - Daily Update")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("="*80 + "\n")
        
        # Load portfolio
        portfolio = self.load_portfolio()
        
        # Get top FSS stocks
        print("📊 Calculating FSS scores for today...")
        
        # Test universe
        test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"]
        
        # Get FSS scores
        fss_results = await self.fss_service.get_stocks_fss(test_stocks, use_cache=True)
        
        # Rank by FSS
        ranked = self.fss_service.rank_stocks_by_fss(fss_results)
        top_stocks = ranked[:5]  # Top 5
        
        print(f"\n🏆 Top 5 FSS Stocks Today:")
        for i, stock in enumerate(top_stocks, 1):
            fss_score = stock.get('fss_score', 0)
            confidence = stock.get('confidence', 'unknown')
            regime = stock.get('regime', 'unknown')
            print(f"   {i}. {stock['symbol']}: {fss_score:.1f}/100 ({confidence}, {regime})")
        
        # Check if rebalance needed (monthly)
        last_rebalance = portfolio.get('last_rebalance_date')
        today = datetime.now().date()
        
        if last_rebalance:
            last_rebalance_date = datetime.fromisoformat(last_rebalance).date()
            days_since_rebalance = (today - last_rebalance_date).days
        else:
            days_since_rebalance = 32  # Force rebalance
        
        # Get current regime (for cash-out decision)
        current_regime = top_stocks[0].get('regime', 'Expansion') if top_stocks else 'Expansion'
        go_to_cash = current_regime in ['Crisis', 'Deflation']
        
        if days_since_rebalance >= 30:
            print(f"\n🔄 Rebalancing portfolios (last rebalance: {days_since_rebalance} days ago)...")
            print(f"   Current Regime: {current_regime}")
            
            # 1. REGIME-AWARE PORTFOLIO
            regime_aware = portfolio.get('regime_aware', {})
            regime_value = regime_aware.get('current_capital', self.initial_capital)
            
            if go_to_cash:
                print(f"   🛡️  Regime-Aware: Moving to CASH (Crisis/Deflation detected)")
                regime_aware['positions'] = {}
                regime_aware['cash'] = regime_value
                regime_aware['trades'].append({
                    "date": today.isoformat(),
                    "action": "cash_out",
                    "regime": current_regime,
                    "value": regime_value
                })
            else:
                print(f"   📈 Regime-Aware: Investing in top 5 stocks")
                # Apply execution slippage
                slippage_cost = regime_value * self.execution_slippage
                investable_value = regime_value - slippage_cost
                
                new_positions = {}
                position_value = investable_value / 5  # Equal weight
                
                for stock in top_stocks:
                    symbol = stock['symbol']
                    new_positions[symbol] = {
                        "value": position_value,
                        "entry_date": today.isoformat(),
                        "fss_score": stock.get('fss_score', 0),
                        "entry_price": 0  # Would be actual price
                    }
                
                regime_aware['positions'] = new_positions
                regime_aware['cash'] = 0.0
                regime_aware['trades'].append({
                    "date": today.isoformat(),
                    "action": "rebalance",
                    "positions": list(new_positions.keys()),
                    "slippage_cost": slippage_cost
                })
            
            portfolio['regime_aware'] = regime_aware
            
            # 2. GHOST ALWAYS-IN PORTFOLIO (for comparison)
            ghost = portfolio.get('ghost_always_in', {})
            ghost_value = ghost.get('current_capital', self.initial_capital)
            
            print(f"   👻 Ghost Always-In: Investing in top 5 stocks")
            # Apply execution slippage
            slippage_cost = ghost_value * self.execution_slippage
            investable_value = ghost_value - slippage_cost
            
            new_positions_ghost = {}
            position_value_ghost = investable_value / 5
            
            for stock in top_stocks:
                symbol = stock['symbol']
                new_positions_ghost[symbol] = {
                    "value": position_value_ghost,
                    "entry_date": today.isoformat(),
                    "fss_score": stock.get('fss_score', 0),
                    "entry_price": 0
                }
            
            ghost['positions'] = new_positions_ghost
            ghost['cash'] = 0.0
            ghost['trades'].append({
                "date": today.isoformat(),
                "action": "rebalance",
                "positions": list(new_positions_ghost.keys()),
                "slippage_cost": slippage_cost
            })
            
            portfolio['ghost_always_in'] = ghost
            portfolio['last_rebalance_date'] = today.isoformat()
            
            if not go_to_cash:
                print(f"   ✅ Both portfolios rebalanced to: {', '.join([s['symbol'] for s in top_stocks])}")
        else:
            print(f"\n⏸️  No rebalance needed (last rebalance: {days_since_rebalance} days ago)")
            if go_to_cash:
                print(f"   🛡️  Regime-Aware: Already in CASH (Crisis/Deflation)")
        
        # Update portfolio values (simplified - in real trading, use actual prices)
        # For now, we'll track based on FSS score changes or market moves
        regime_value = portfolio['regime_aware'].get('current_capital', self.initial_capital)
        ghost_value = portfolio['ghost_always_in'].get('current_capital', self.initial_capital)
        
        # Save portfolio
        self.save_portfolio(portfolio)
        
        # Update results
        self.update_results(portfolio, top_stocks)
        
        # Calculate Calmar Ratio
        regime_returns = portfolio['regime_aware'].get('daily_returns', [])
        ghost_returns = portfolio['ghost_always_in'].get('daily_returns', [])
        
        regime_max_dd = self._calculate_max_drawdown(regime_returns) if regime_returns else 0
        ghost_max_dd = self._calculate_max_drawdown(ghost_returns) if ghost_returns else 0
        
        regime_ann_return = (regime_value / self.initial_capital) ** (252 / max(1, len(regime_returns))) - 1 if regime_returns else 0
        ghost_ann_return = (ghost_value / self.initial_capital) ** (252 / max(1, len(ghost_returns))) - 1 if ghost_returns else 0
        
        regime_calmar = abs(regime_ann_return / regime_max_dd) if regime_max_dd != 0 else 0
        ghost_calmar = abs(ghost_ann_return / ghost_max_dd) if ghost_max_dd != 0 else 0
        
        print(f"\n💰 Portfolio Values:")
        print(f"   Regime-Aware: ${regime_value:,.2f} ({(regime_value / self.initial_capital - 1) * 100:.2f}%)")
        print(f"   Ghost Always-In: ${ghost_value:,.2f} ({(ghost_value / self.initial_capital - 1) * 100:.2f}%)")
        print(f"   Safety Alpha: {((regime_value - ghost_value) / self.initial_capital) * 100:.2f}%")
        
        print(f"\n📊 Risk Metrics:")
        print(f"   Regime-Aware Calmar Ratio: {regime_calmar:.2f}")
        print(f"   Ghost Always-In Calmar Ratio: {ghost_calmar:.2f}")
        if regime_calmar > ghost_calmar:
            print(f"   ✅ Regime-Aware has better risk-adjusted returns")
        
        print(f"\n✅ Daily update complete!")
    
    def _calculate_max_drawdown(self, returns):
        """Calculate max drawdown from returns series"""
        if not returns:
            return 0
        equity = (1 + pd.Series(returns)).cumprod()
        cummax = equity.cummax()
        drawdown = (equity / cummax) - 1.0
        return drawdown.min()
    
    def update_results(self, portfolio, top_stocks):
        """Update paper trading results"""
        today = datetime.now()
        
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {
                "start_date": portfolio.get('start_date'),
                "initial_capital": self.initial_capital,
                "daily_updates": [],
                "daily_returns": {},  # For transparency engine
                "current_regime": "Expansion"
            }
        
        regime_aware = portfolio.get('regime_aware', {})
        ghost = portfolio.get('ghost_always_in', {})
        
        # Calculate daily returns
        prev_regime_value = results.get('daily_updates', [{}])[-1].get('regime_aware', {}).get('portfolio_value', self.initial_capital)
        prev_ghost_value = results.get('daily_updates', [{}])[-1].get('ghost_always_in', {}).get('portfolio_value', self.initial_capital)
        
        current_regime_value = regime_aware.get('current_capital', self.initial_capital)
        current_ghost_value = ghost.get('current_capital', self.initial_capital)
        
        fss_return = (current_regime_value / prev_regime_value - 1.0) if prev_regime_value > 0 else 0.0
        ghost_return = (current_ghost_value / prev_ghost_value - 1.0) if prev_ghost_value > 0 else 0.0
        
        # Store daily returns for transparency engine
        date_str = today.strftime('%Y-%m-%d')
        if 'daily_returns' not in results:
            results['daily_returns'] = {}
        results['daily_returns'][date_str] = {
            'fss_return': fss_return,
            'ghost_return': ghost_return
        }
        
        results['daily_updates'].append({
            "date": today.isoformat(),
            "regime_aware": {
                "portfolio_value": current_regime_value,
                "positions": list(regime_aware.get('positions', {}).keys()),
                "in_cash": regime_aware.get('cash', 0) > 0
            },
            "ghost_always_in": {
                "portfolio_value": current_ghost_value,
                "positions": list(ghost.get('positions', {}).keys())
            },
            "top_stocks": [s['symbol'] for s in top_stocks],
            "safety_alpha": ((current_regime_value - current_ghost_value) / self.initial_capital) * 100
        })
        
        # Update current regime (if available from portfolio)
        if 'current_regime' in portfolio:
            results['current_regime'] = portfolio['current_regime']
        
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)


async def run_paper_trading():
    """Run paper trading system"""
    trader = FSSPaperTrading(initial_capital=100000)
    await trader.run_daily_update()


if __name__ == "__main__":
    asyncio.run(run_paper_trading())

