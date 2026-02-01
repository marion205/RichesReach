#!/usr/bin/env python3
"""
Nightly Chan Portfolio Scan

Scans the market using the complete Chan portfolio pipeline:
1. FSS Engine → FSS scores
2. Regime Robustness → Filter by robustness (min 0.5)
3. Chan Quant Signals → Kelly fractions
4. Portfolio Allocator → Correlation-aware weights
5. Generate Orders CSV → Ready for paper trading

Usage:
    python3 run_nightly_chan_scan.py
    python3 run_nightly_chan_scan.py --universe SP500
    python3 run_nightly_chan_scan.py --output orders.csv
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import csv

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine
from backend.core.chan_quant_signal_engine import ChanQuantSignalEngine
from backend.core.chan_portfolio_allocator import get_chan_portfolio_allocator
from backend.core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest

# Try to import yfinance for data fetching
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available. Install with: pip install yfinance")


# Default universe (can be expanded)
SP500_SAMPLE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "V", "JNJ", "WMT", "PG", "JPM", "MA", "UNH", "HD", "DIS", "BAC",
    "XOM", "VZ", "ADBE", "CMCSA", "NFLX", "COST", "NKE", "MRK", "PFE"
]

DOW30 = [
    "AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "MCD", "AMGN", "V", "HON",
    "TRV", "AXP", "IBM", "JPM", "JNJ", "WMT", "PG", "CVX", "MRK", "BA",
    "DIS", "DOW", "CSCO", "VZ", "INTC", "NKE", "WBA", "MMM", "KO", "CRM"
]


def fetch_current_prices(tickers: List[str]) -> Dict[str, float]:
    """Fetch current prices for tickers"""
    if not YFINANCE_AVAILABLE:
        print("⚠️  yfinance not available, using mock prices")
        return {ticker: 100.0 + np.random.uniform(-20, 20) for ticker in tickers}
    
    prices = {}
    print(f"\n📊 Fetching current prices for {len(tickers)} tickers...")
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price:
                prices[ticker] = float(current_price)
                print(f"   {ticker}: ${current_price:.2f}")
            else:
                print(f"   {ticker}: ❌ (no price data)")
        except Exception as e:
            print(f"   {ticker}: ❌ ({e})")
    
    return prices


def fetch_historical_data(tickers: List[str], lookback_days: int = 252) -> Dict:
    """Fetch historical data for analysis"""
    if not YFINANCE_AVAILABLE:
        print("⚠️  yfinance not available, cannot fetch historical data")
        return None
    
    print(f"\n📈 Fetching {lookback_days} days of historical data...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days + 30)
    
    prices_dict = {}
    volumes_dict = {}
    spy_data = None
    
    # Fetch stock data
    for ticker in tickers:
        try:
            print(f"   Fetching {ticker}...", end=" ", flush=True)
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date, auto_adjust=True)
            
            if not hist.empty:
                prices_dict[ticker] = hist['Close']
                volumes_dict[ticker] = hist['Volume']
                print("✅")
            else:
                print("❌")
        except Exception as e:
            print(f"❌ ({e})")
    
    # Fetch SPY
    try:
        print(f"   Fetching SPY...", end=" ", flush=True)
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(start=start_date, end=end_date, auto_adjust=True)
        if not spy_hist.empty:
            spy_data = spy_hist['Close']
            print("✅")
        else:
            print("❌")
    except Exception as e:
        print(f"❌ ({e})")
    
    if not prices_dict:
        return None
    
    prices_df = pd.DataFrame(prices_dict)
    volumes_df = pd.DataFrame(volumes_dict)
    
    return {
        "prices": prices_df.sort_index(),
        "volumes": volumes_df.sort_index().fillna(0),
        "spy": spy_data.sort_index() if spy_data is not None else None
    }


def run_nightly_scan(
    universe: List[str] = None,
    min_robustness: float = 0.5,
    max_positions: int = 10,
    output_file: str = "chan_orders.csv"
):
    """Run nightly scan and generate orders CSV"""
    print("\n" + "="*80)
    print("NIGHTLY CHAN PORTFOLIO SCAN")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if universe is None:
        universe = SP500_SAMPLE
    
    print(f"\n📊 Universe: {len(universe)} tickers")
    print(f"   Min Robustness: {min_robustness}")
    print(f"   Max Positions: {max_positions}")
    
    # Fetch historical data
    historical_data = fetch_historical_data(universe, lookback_days=252)
    
    if historical_data is None:
        print("\n❌ Failed to fetch historical data. Cannot generate signals.")
        return None
    
    prices = historical_data["prices"]
    volumes = historical_data["volumes"]
    spy = historical_data["spy"]
    
    print(f"\n✅ Loaded {len(prices)} days of data")
    print(f"   Tickers with data: {len(prices.columns)}")
    
    # Initialize engines
    print("\n🔧 Initializing engines...")
    fss_engine = get_fss_engine()
    chan_engine = ChanQuantSignalEngine()
    allocator = get_chan_portfolio_allocator()
    
    # Calculate FSS scores
    print("\n📈 Calculating FSS scores...")
    try:
        fss_data = fss_engine.compute_fss_v3(
            prices=prices,
            volumes=volumes,
            spy=spy,
            vix=None
        )
        print("✅ FSS calculation complete")
    except Exception as e:
        print(f"❌ FSS calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Get signals for each ticker
    print("\n🔍 Analyzing signals...")
    ticker_signals = {}
    kelly_fractions = {}
    fss_scores = {}
    fss_robustness = {}
    volatilities = {}
    
    for ticker in universe:
        if ticker not in prices.columns:
            continue
        
        try:
            # Get FSS result with robustness
            fss_result = fss_engine.get_stock_fss(
                ticker=ticker,
                fss_data=fss_data,
                regime="Expansion",
                prices=prices,
                spy=spy,
                vix=None,
                calculate_robustness=True
            )
            
            if fss_result.regime_robustness_score is None or fss_result.regime_robustness_score < min_robustness:
                continue
            
            # Get Kelly fraction
            ticker_returns = prices[ticker].pct_change().dropna()
            if len(ticker_returns) >= 20:
                kelly_result = chan_engine.calculate_kelly_position_size(
                    symbol=ticker,
                    historical_returns=ticker_returns
                )
                kelly_fraction = kelly_result.recommended_fraction
            else:
                kelly_fraction = min(0.15, fss_result.fss_score / 100.0 * 0.2)
            
            kelly_fractions[ticker] = kelly_fraction
            fss_scores[ticker] = fss_result.fss_score
            fss_robustness[ticker] = fss_result.regime_robustness_score
            
            # Calculate volatility
            if len(ticker_returns) > 20:
                volatilities[ticker] = ticker_returns.std() * np.sqrt(252)
            else:
                volatilities[ticker] = 0.20
            
            ticker_signals[ticker] = {
                "fss": fss_result.fss_score,
                "robustness": fss_result.regime_robustness_score,
                "kelly": kelly_fraction
            }
            
        except Exception as e:
            print(f"   ⚠️  {ticker}: {e}")
            continue
    
    print(f"\n✅ Analyzed {len(ticker_signals)} tickers with robustness ≥ {min_robustness}")
    
    if not ticker_signals:
        print("\n❌ No tickers passed robustness filter. No orders generated.")
        return None
    
    # Portfolio allocation
    print("\n💼 Running portfolio allocation...")
    valid_tickers = list(ticker_signals.keys())
    
    if len(valid_tickers) < 2:
        print("⚠️  Need at least 2 tickers for portfolio allocation")
        # Use equal weights
        weights = {ticker: 1.0 / len(valid_tickers) for ticker in valid_tickers}
    else:
        returns_matrix = prices[valid_tickers].pct_change().dropna()
        
        allocation_result = allocator.allocate_portfolio(
            tickers=valid_tickers,
            kelly_fractions=kelly_fractions,
            fss_scores=fss_scores,
            fss_robustness=fss_robustness,
            returns_matrix=returns_matrix,
            volatilities=volatilities,
            method="kelly_constrained"
        )
        
        # Limit to top positions
        sorted_weights = sorted(allocation_result.weights.items(), key=lambda x: x[1], reverse=True)
        top_positions = sorted_weights[:max_positions]
        
        total_weight = sum(w for _, w in top_positions)
        if total_weight > 0:
            weights = {ticker: weight / total_weight for ticker, weight in top_positions}
        else:
            print("❌ Portfolio allocation failed")
            return None
    
    print(f"✅ Allocated {len(weights)} positions")
    
    # Fetch current prices
    current_prices = fetch_current_prices(list(weights.keys()))
    
    # Generate orders CSV
    print(f"\n📝 Generating orders CSV: {output_file}")
    
    orders = []
    for ticker, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        current_price = current_prices.get(ticker, 0.0)
        if current_price == 0:
            continue
        
        orders.append({
            "symbol": ticker,
            "action": "BUY",
            "quantity": f"{weight:.4f}",  # Fractional shares (weight of portfolio)
            "price": f"{current_price:.2f}",
            "order_type": "MARKET",
            "fss_score": f"{fss_scores.get(ticker, 0):.2f}",
            "robustness": f"{fss_robustness.get(ticker, 0):.3f}",
            "kelly_fraction": f"{kelly_fractions.get(ticker, 0):.4f}",
            "weight": f"{weight:.4f}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Write CSV
    with open(output_file, 'w', newline='') as f:
        if orders:
            writer = csv.DictWriter(f, fieldnames=orders[0].keys())
            writer.writeheader()
            writer.writerows(orders)
    
    print(f"✅ Generated {len(orders)} orders")
    
    # Print summary
    print("\n" + "="*80)
    print("ORDERS SUMMARY")
    print("="*80)
    print(f"\n{'Symbol':<8} {'Weight':<10} {'FSS':<8} {'Robust':<8} {'Kelly':<10} {'Price':<10}")
    print("-" * 80)
    
    total_weight = 0.0
    for order in orders:
        symbol = order["symbol"]
        weight = float(order["weight"])
        total_weight += weight
        print(f"{symbol:<8} {weight:>9.2%} {order['fss_score']:>7} {order['robustness']:>7} {order['kelly_fraction']:>9} ${order['price']:>9}")
    
    print("-" * 80)
    print(f"{'TOTAL':<8} {total_weight:>9.2%}")
    print(f"\n📄 Orders saved to: {output_file}")
    print("="*80 + "\n")
    
    return {
        "orders": orders,
        "weights": weights,
        "signals": ticker_signals,
        "output_file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Nightly Chan Portfolio Scan")
    parser.add_argument(
        "--universe",
        choices=["SP500", "DOW30", "custom"],
        default="SP500",
        help="Universe to scan (default: SP500)"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Custom ticker list (use with --universe custom)"
    )
    parser.add_argument(
        "--min-robustness",
        type=float,
        default=0.5,
        help="Minimum robustness score (default: 0.5)"
    )
    parser.add_argument(
        "--max-positions",
        type=int,
        default=10,
        help="Maximum positions (default: 10)"
    )
    parser.add_argument(
        "--output",
        default="chan_orders.csv",
        help="Output CSV file (default: chan_orders.csv)"
    )
    
    args = parser.parse_args()
    
    # Select universe
    if args.universe == "SP500":
        universe = SP500_SAMPLE
    elif args.universe == "DOW30":
        universe = DOW30
    elif args.universe == "custom" and args.tickers:
        universe = args.tickers
    else:
        universe = SP500_SAMPLE
    
    result = run_nightly_scan(
        universe=universe,
        min_robustness=args.min_robustness,
        max_positions=args.max_positions,
        output_file=args.output
    )
    
    if result:
        print("✅ Nightly scan complete!")
    else:
        print("❌ Nightly scan failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

