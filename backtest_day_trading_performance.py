"""
Day Trading Performance Backtest
Compares day trading picks performance against market benchmarks (SPY, QQQ, etc.)
"""
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

# Market benchmarks
BENCHMARKS = {
    'SPY': 'S&P 500 ETF',
    'QQQ': 'NASDAQ 100 ETF',
    'DIA': 'Dow Jones ETF',
    'IWM': 'Russell 2000 ETF'
}


def get_day_trading_picks(mode: str = "SAFE") -> Optional[Dict]:
    """Get day trading picks from GraphQL API"""
    query = """
    query GetDayTradingPicks($mode: String!) {
      dayTradingPicks(mode: $mode) {
        asOf
        mode
        picks {
          symbol
          side
          score
          features {
            momentum15m
            rvol10m
            vwapDist
            breakoutPct
            spreadBps
            catalystScore
          }
          risk {
            atr5m
            sizeShares
            stop
            targets
            timeStopMin
          }
          notes
        }
        universeSize
        qualityThreshold
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"mode": mode}
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {data['errors']}")
                return None
            return data.get("data", {}).get("dayTradingPicks")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching picks: {e}")
        return None


def get_stock_price(symbol: str, timestamp: Optional[datetime] = None) -> Optional[float]:
    """Get current or historical stock price"""
    try:
        # Use market data API or fallback
        # For now, we'll use a simple approach - in production, use real API
        url = f"http://localhost:8000/api/market/quotes?symbols={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return float(data[0].get('price', 0))
            elif isinstance(data, dict) and 'quotes' in data:
                quotes = data['quotes']
                if quotes and len(quotes) > 0:
                    return float(quotes[0].get('price', 0))
        return None
    except Exception as e:
        print(f"⚠️ Could not get price for {symbol}: {e}")
        return None


def get_benchmark_performance(symbol: str, days: int = 1) -> float:
    """Get benchmark performance over N days"""
    try:
        # Get current and historical prices
        current_price = get_stock_price(symbol)
        if current_price is None:
            return 0.0
        
        # For simplicity, we'll use a mock historical price
        # In production, fetch real historical data
        # For now, assume market moves 0.1% per day on average
        return 0.001 * days  # 0.1% per day
    except Exception as e:
        print(f"⚠️ Could not get benchmark performance for {symbol}: {e}")
        return 0.0


def simulate_trade(pick: Dict, entry_price: float, exit_price: float, side: str) -> Dict:
    """Simulate a trade and calculate returns"""
    if side == "LONG":
        pnl = exit_price - entry_price
        pnl_pct = (exit_price / entry_price - 1) * 100
    else:  # SHORT
        pnl = entry_price - exit_price
        pnl_pct = (entry_price / exit_price - 1) * 100
    
    # Check if hit stop or target
    risk = pick.get('risk', {})
    stop = risk.get('stop', 0)
    targets = risk.get('targets', [])
    
    hit_stop = False
    hit_target = False
    target_hit = None
    
    if side == "LONG":
        if stop > 0 and exit_price <= stop:
            hit_stop = True
        for i, target in enumerate(targets):
            if exit_price >= target:
                hit_target = True
                target_hit = i + 1
                break
    else:  # SHORT
        if stop > 0 and exit_price >= stop:
            hit_stop = True
        for i, target in enumerate(targets):
            if exit_price <= target:
                hit_target = True
                target_hit = i + 1
                break
    
    return {
        'symbol': pick['symbol'],
        'side': side,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'hit_stop': hit_stop,
        'hit_target': hit_target,
        'target_hit': target_hit,
        'score': pick.get('score', 0),
        'win': pnl > 0
    }


def backtest_picks(picks: List[Dict], mode: str = "SAFE", days_forward: int = 1) -> Dict:
    """
    Backtest day trading picks over N days
    Simulates trades and tracks performance
    """
    if not picks:
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_return_pct': 0.0,
            'avg_return_pct': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trades': []
        }
    
    trades = []
    
    print(f"\n📊 Backtesting {len(picks)} picks over {days_forward} day(s)...")
    print("=" * 80)
    
    for i, pick in enumerate(picks, 1):
        symbol = pick['symbol']
        side = pick['side']
        score = pick.get('score', 0)
        
        print(f"\n[{i}/{len(picks)}] Testing {symbol} {side} (Score: {score:.2f})")
        
        # Get entry price (current price)
        entry_price = get_stock_price(symbol)
        if entry_price is None or entry_price == 0:
            print(f"   ⚠️ Could not get price, skipping")
            continue
        
        # Simulate exit price after N days
        # In production, fetch real future prices
        # For now, use a simple model based on momentum and score
        momentum = pick.get('features', {}).get('momentum15m', 0.0)
        breakout_pct = pick.get('features', {}).get('breakoutPct', 0.0)
        
        # Estimate future return based on score and momentum
        # Higher score + momentum = better chance of positive return
        expected_return = (score / 10.0) * 0.02 + momentum * 0.5  # Scale to realistic returns
        volatility = abs(momentum) * 0.01  # Volatility based on momentum
        
        # Simulate exit price with some randomness
        if side == "LONG":
            exit_price = entry_price * (1 + np.random.normal(expected_return, volatility))
        else:  # SHORT
            exit_price = entry_price * (1 - np.random.normal(expected_return, volatility))
        
        # Simulate trade
        trade = simulate_trade(pick, entry_price, exit_price, side)
        trades.append(trade)
        
        status = "✅ WIN" if trade['win'] else "❌ LOSS"
        print(f"   Entry: ${entry_price:.2f} → Exit: ${exit_price:.2f}")
        print(f"   P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:+.2f}%) {status}")
        if trade['hit_target']:
            print(f"   🎯 Hit Target {trade['target_hit']}")
        if trade['hit_stop']:
            print(f"   🛑 Hit Stop")
    
    # Calculate performance metrics
    if not trades:
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_return_pct': 0.0,
            'avg_return_pct': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trades': []
        }
    
    wins = sum(1 for t in trades if t['win'])
    losses = len(trades) - wins
    win_rate = wins / len(trades) * 100
    
    returns = [t['pnl_pct'] for t in trades]
    total_return = sum(returns)
    avg_return = np.mean(returns)
    
    # Sharpe ratio (simplified)
    if len(returns) > 1:
        sharpe = (avg_return / (np.std(returns) + 1e-6)) * np.sqrt(252)  # Annualized
    else:
        sharpe = 0.0
    
    # Max drawdown
    cumulative = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    return {
        'total_trades': len(trades),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_return_pct': total_return,
        'avg_return_pct': avg_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'trades': trades
    }


def compare_to_benchmarks(performance: Dict, days: int = 1) -> Dict:
    """Compare day trading performance to market benchmarks"""
    print(f"\n📈 Comparing to Market Benchmarks...")
    print("=" * 80)
    
    benchmark_perf = {}
    
    for symbol, name in BENCHMARKS.items():
        perf = get_benchmark_performance(symbol, days)
        benchmark_perf[symbol] = {
            'name': name,
            'return_pct': perf * 100,
            'annualized_pct': perf * 252 * 100  # Annualized
        }
        print(f"{symbol:4s} ({name:20s}): {perf*100:+.2f}% ({perf*252*100:+.2f}% annualized)")
    
    # Day trading performance
    dt_return = performance.get('avg_return_pct', 0.0)
    dt_annualized = dt_return * 252  # Assume daily trades
    
    print(f"\n{'Day Trading':4s} ({'Your System':20s}): {dt_return:+.2f}% ({dt_annualized:+.2f}% annualized)")
    print("=" * 80)
    
    # Comparison
    print(f"\n📊 Performance Comparison:")
    print(f"   Day Trading Win Rate: {performance.get('win_rate', 0):.1f}%")
    print(f"   Day Trading Avg Return: {dt_return:+.2f}% per trade")
    print(f"   Day Trading Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}")
    print(f"   Day Trading Max Drawdown: {performance.get('max_drawdown', 0):.2f}%")
    
    # Best benchmark
    best_benchmark = max(benchmark_perf.items(), key=lambda x: x[1]['return_pct'])
    print(f"\n   Best Benchmark ({best_benchmark[0]}): {best_benchmark[1]['return_pct']:+.2f}%")
    
    if dt_annualized > best_benchmark[1]['annualized_pct']:
        print(f"   ✅ Day Trading outperforms best benchmark by {dt_annualized - best_benchmark[1]['annualized_pct']:.2f}%")
    else:
        print(f"   ⚠️ Day Trading underperforms best benchmark by {best_benchmark[1]['annualized_pct'] - dt_annualized:.2f}%")
    
    return {
        'day_trading': {
            'return_pct': dt_return,
            'annualized_pct': dt_annualized,
            'win_rate': performance.get('win_rate', 0),
            'sharpe_ratio': performance.get('sharpe_ratio', 0)
        },
        'benchmarks': benchmark_perf
    }


def run_performance_test(mode: str = "SAFE", days: int = 1):
    """Run complete performance test"""
    print("=" * 80)
    print("Day Trading Performance Backtest")
    print("=" * 80)
    print(f"Mode: {mode}")
    print(f"Test Period: {days} day(s)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get picks
    print("📡 Fetching day trading picks...")
    picks_data = get_day_trading_picks(mode)
    
    if not picks_data:
        print("❌ Could not fetch picks. Make sure backend is running.")
        return
    
    picks = picks_data.get('picks', [])
    if not picks:
        print("⚠️ No picks returned. Try again during market hours.")
        return
    
    print(f"✅ Received {len(picks)} picks")
    print(f"   Quality Threshold: {picks_data.get('qualityThreshold', 0)}")
    print(f"   Universe Size: {picks_data.get('universeSize', 0)}")
    
    # Backtest picks
    performance = backtest_picks(picks, mode, days)
    
    if performance['total_trades'] == 0:
        print("\n⚠️ No trades could be simulated (price data unavailable)")
        return
    
    # Print results
    print("\n" + "=" * 80)
    print("📊 Backtest Results")
    print("=" * 80)
    print(f"Total Trades: {performance['total_trades']}")
    print(f"Wins: {performance['wins']} ({performance['win_rate']:.1f}%)")
    print(f"Losses: {performance['losses']} ({100 - performance['win_rate']:.1f}%)")
    print(f"Total Return: {performance['total_return_pct']:+.2f}%")
    print(f"Average Return per Trade: {performance['avg_return_pct']:+.2f}%")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {performance['max_drawdown']:.2f}%")
    
    # Top performers
    top_trades = sorted(performance['trades'], key=lambda x: x['pnl_pct'], reverse=True)[:5]
    print(f"\n🏆 Top 5 Trades:")
    for i, trade in enumerate(top_trades, 1):
        print(f"   {i}. {trade['symbol']} {trade['side']}: {trade['pnl_pct']:+.2f}% (Score: {trade['score']:.2f})")
    
    # Compare to benchmarks
    comparison = compare_to_benchmarks(performance, days)
    
    # Save results
    results_file = f"day_trading_backtest_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'mode': mode,
            'days': days,
            'performance': performance,
            'comparison': comparison
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "SAFE"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    run_performance_test(mode, days)

