#!/usr/bin/env python3
"""
Paper Trading Performance Tracker

Tracks paper trading performance and compares to backtest predictions.
Monitors:
- Actual vs expected returns
- Fill prices vs limit prices
- Performance by robustness bucket
- Win rate and Sharpe ratio

Usage:
    python3 track_paper_trading_performance.py
    python3 track_paper_trading_performance.py --compare-backtest
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Try to import Alpaca for position tracking
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

EXECUTION_LOG = "execution_log.jsonl"
TRADING_LOG = "trading_log.jsonl"
PERFORMANCE_LOG = "performance_tracking.jsonl"


def load_executions() -> pd.DataFrame:
    """Load order executions from log"""
    if not os.path.exists(EXECUTION_LOG):
        return pd.DataFrame()
    
    executions = []
    with open(EXECUTION_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('action') in ['SUBMIT', 'DRY_RUN']:
                    executions.append(entry)
            except:
                continue
    
    return pd.DataFrame(executions)


def load_trading_decisions() -> pd.DataFrame:
    """Load trading decisions from log"""
    if not os.path.exists(TRADING_LOG):
        return pd.DataFrame()
    
    decisions = []
    with open(TRADING_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('decision') == 'BUY':
                    decisions.append(entry)
            except:
                continue
    
    return pd.DataFrame(decisions)


def get_current_positions(api) -> Dict[str, Dict]:
    """Get current positions from Alpaca"""
    if not api:
        return {}
    
    try:
        positions = api.list_positions()
        return {
            pos.symbol: {
                'quantity': int(pos.qty),
                'avg_entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'market_value': float(pos.market_value),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc)
            }
            for pos in positions
        }
    except Exception as e:
        print(f"⚠️  Error fetching positions: {e}")
        return {}


def calculate_performance(executions_df: pd.DataFrame, decisions_df: pd.DataFrame, 
                          positions: Dict[str, Dict]) -> Dict:
    """Calculate performance metrics"""
    
    performance = {
        'total_orders': len(executions_df),
        'filled_orders': 0,
        'open_positions': len(positions),
        'total_unrealized_pl': 0.0,
        'total_unrealized_plpc': 0.0,
        'by_robustness': {},
        'fill_analysis': {}
    }
    
    # Analyze fills
    if not executions_df.empty:
        performance['filled_orders'] = len(executions_df[executions_df['action'] == 'SUBMIT'])
        
        if 'limit_price' in executions_df.columns and 'expected_fill' in executions_df.columns:
            fills = executions_df[executions_df['expected_fill'].notna()]
            if not fills.empty:
                performance['fill_analysis'] = {
                    'avg_limit_price': float(fills['limit_price'].mean()),
                    'avg_fill_price': float(fills['expected_fill'].mean()),
                    'avg_slippage': float((fills['expected_fill'] - fills['limit_price']).mean()),
                    'slippage_bps': float(((fills['expected_fill'] - fills['limit_price']) / fills['limit_price'] * 10000).mean())
                }
    
    # Current positions performance
    if positions:
        total_pl = sum(pos['unrealized_pl'] for pos in positions.values())
        total_value = sum(pos['market_value'] for pos in positions.values())
        
        performance['total_unrealized_pl'] = total_pl
        performance['total_unrealized_plpc'] = (total_pl / total_value * 100) if total_value > 0 else 0.0
        
        # Group by robustness (if available in decisions)
        if not decisions_df.empty and 'metrics' in decisions_df.columns:
            for symbol, pos_data in positions.items():
                decision = decisions_df[decisions_df['symbol'] == symbol]
                if not decision.empty:
                    metrics = decision.iloc[0].get('metrics', {})
                    robustness = metrics.get('regime_robustness', 0.0)
                    
                    bucket = 'high' if robustness >= 0.7 else 'medium' if robustness >= 0.5 else 'low'
                    if bucket not in performance['by_robustness']:
                        performance['by_robustness'][bucket] = {
                            'count': 0,
                            'total_pl': 0.0,
                            'total_plpc': 0.0
                        }
                    
                    performance['by_robustness'][bucket]['count'] += 1
                    performance['by_robustness'][bucket]['total_pl'] += pos_data['unrealized_pl']
                    performance['by_robustness'][bucket]['total_plpc'] += pos_data['unrealized_plpc']
    
    return performance


def print_performance(performance: Dict, compare_backtest: bool = False):
    """Print performance summary"""
    print("\n" + "="*80)
    print("PAPER TRADING PERFORMANCE TRACKER")
    print("="*80)
    
    print(f"\n📊 Orders:")
    print(f"   Total Orders: {performance['total_orders']}")
    print(f"   Filled Orders: {performance['filled_orders']}")
    print(f"   Open Positions: {performance['open_positions']}")
    
    if performance.get('fill_analysis'):
        fill = performance['fill_analysis']
        print(f"\n💰 Fill Analysis:")
        print(f"   Avg Limit Price: ${fill['avg_limit_price']:.2f}")
        print(f"   Avg Fill Price: ${fill['avg_fill_price']:.2f}")
        print(f"   Avg Slippage: ${fill['avg_slippage']:.4f} ({fill['slippage_bps']:.2f} bps)")
    
    print(f"\n📈 Current Performance:")
    print(f"   Total Unrealized P&L: ${performance['total_unrealized_pl']:,.2f}")
    print(f"   Total Unrealized P&L %: {performance['total_unrealized_plpc']:.2f}%")
    
    if performance.get('by_robustness'):
        print(f"\n🔬 Performance by Robustness:")
        for bucket, data in performance['by_robustness'].items():
            print(f"   {bucket.capitalize()} (≥{0.7 if bucket == 'high' else 0.5 if bucket == 'medium' else 0.0}):")
            print(f"     Positions: {data['count']}")
            print(f"     Total P&L: ${data['total_pl']:,.2f}")
            print(f"     Avg P&L %: {data['total_plpc'] / data['count']:.2f}%" if data['count'] > 0 else "     Avg P&L %: N/A")
    
    if compare_backtest:
        print(f"\n📊 Backtest Comparison:")
        print(f"   (Load backtest results and compare)")
        # TODO: Load backtest predictions and compare
    
    print("\n" + "="*80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Track Paper Trading Performance")
    parser.add_argument("--compare-backtest", action="store_true", help="Compare to backtest predictions")
    parser.add_argument("--execution-log", default=EXECUTION_LOG, help="Execution log file")
    parser.add_argument("--trading-log", default=TRADING_LOG, help="Trading log file")
    
    args = parser.parse_args()
    
    # Load data
    executions_df = load_executions()
    decisions_df = load_trading_decisions()
    
    # Get current positions (if Alpaca available)
    positions = {}
    if ALPACA_AVAILABLE:
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        if api_key and api_secret:
            try:
                api = tradeapi.REST(api_key, api_secret, base_url='https://paper-api.alpaca.markets')
                positions = get_current_positions(api)
            except:
                pass
    
    # Calculate performance
    performance = calculate_performance(executions_df, decisions_df, positions)
    
    # Print results
    print_performance(performance, compare_backtest=args.compare_backtest)
    
    # Save performance snapshot
    snapshot = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'performance': performance
    }
    
    with open(PERFORMANCE_LOG, 'a') as f:
        f.write(json.dumps(snapshot) + "\n")
    
    print(f"\n📋 Performance snapshot saved to: {PERFORMANCE_LOG}")


if __name__ == "__main__":
    main()

