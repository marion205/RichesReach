#!/usr/bin/env python3
"""
Real Data Walk-Forward Backtest

Runs walk-forward backtest using real historical prices from yfinance.
Replaces synthetic data with actual market data.

Usage:
    python3 run_real_data_backtest.py
    python3 run_real_data_backtest.py --tickers AAPL MSFT GOOGL
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine
from backend.core.chan_quant_signal_engine import ChanQuantSignalEngine
from backend.core.chan_portfolio_allocator import get_chan_portfolio_allocator

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available. Install with: pip install yfinance")
    sys.exit(1)


def fetch_real_data(tickers: List[str], start_date: datetime, end_date: datetime) -> Dict:
    """Fetch real historical data using yfinance"""
    print(f"\n📊 Fetching REAL data for {len(tickers)} tickers...")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    
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
                print(f"✅ ({len(hist)} days)")
            else:
                print("❌ (no data)")
        except Exception as e:
            print(f"❌ ({e})")
    
    # Fetch SPY
    try:
        print(f"   Fetching SPY...", end=" ", flush=True)
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(start=start_date, end=end_date, auto_adjust=True)
        if not spy_hist.empty:
            spy_data = spy_hist['Close']
            print(f"✅ ({len(spy_hist)} days)")
        else:
            print("❌")
    except Exception as e:
        print(f"❌ ({e})")
    
    if not prices_dict:
        return None
    
    prices_df = pd.DataFrame(prices_dict)
    volumes_df = pd.DataFrame(volumes_dict)
    
    # Remove timezone if present (yfinance returns timezone-aware)
    if prices_df.index.tz is not None:
        prices_df.index = prices_df.index.tz_localize(None)
    if volumes_df.index.tz is not None:
        volumes_df.index = volumes_df.index.tz_localize(None)
    if spy_data is not None and spy_data.index.tz is not None:
        spy_data.index = spy_data.index.tz_localize(None)
    
    # Align dates and forward-fill
    prices_df = prices_df.sort_index().fillna(method='ffill')
    volumes_df = volumes_df.sort_index().fillna(0)
    
    print(f"\n✅ Loaded {len(prices_df)} days of REAL data")
    print(f"   Tickers with data: {list(prices_df.columns)}")
    
    return {
        "prices": prices_df,
        "volumes": volumes_df,
        "spy": spy_data.sort_index() if spy_data is not None else None
    }


def run_real_data_backtest(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    min_robustness: float = 0.5,
    max_positions: int = 10
):
    """Run walk-forward backtest with real data"""
    print("\n" + "="*80)
    print("REAL DATA WALK-FORWARD BACKTEST")
    print("="*80)
    print(f"\n📅 Period: {start_date.date()} to {end_date.date()}")
    print(f"📊 Tickers: {', '.join(tickers)}")
    print(f"   Min Robustness: {min_robustness}")
    print(f"   Max Positions: {max_positions}")
    
    # Fetch real data
    data = fetch_real_data(tickers + ["SPY"], start_date, end_date)
    
    if data is None or data["prices"].empty:
        print("\n❌ Failed to fetch real data")
        return None
    
    prices = data["prices"]
    volumes = data["volumes"]
    spy = data["spy"]
    
    # Initialize engines
    fss_engine = get_fss_engine()
    chan_engine = ChanQuantSignalEngine()
    allocator = get_chan_portfolio_allocator()
    
    # Get rebalance dates (monthly)
    rebal_dates = prices.resample("M").last().index
    # Convert to timezone-naive if needed for comparison
    if rebal_dates.tz is not None:
        rebal_dates = rebal_dates.tz_localize(None)
    rebal_dates = rebal_dates[rebal_dates >= start_date]
    
    print(f"\n🔄 Running walk-forward backtest ({len(rebal_dates)} rebalance dates)...")
    
    # Track portfolio
    portfolio_weights = pd.DataFrame(0.0, index=prices.index, columns=tickers)
    allocations_by_date = {}
    robustness_by_date = {}
    robustness_vs_returns_data = []
    
    training_window = 252  # 1 year
    
    # Walk-forward loop
    for i, rebal_date in enumerate(rebal_dates):
        if rebal_date not in prices.index:
            continue
        
        # Training window
        train_end = rebal_date
        train_start_idx = prices.index.get_loc(train_end) - training_window
        if train_start_idx < 0:
            continue
        
        train_start = prices.index[train_start_idx]
        train_prices = prices.loc[train_start:train_end]
        train_volumes = volumes.loc[train_start:train_end] if not volumes.empty else None
        train_spy = spy.loc[train_start:train_end] if spy is not None else None
        
        if len(train_prices) < 60:
            continue
        
        if (i + 1) % 3 == 0:
            print(f"   Rebalance {i+1}/{len(rebal_dates)}: {rebal_date.date()}")
        
        try:
            # Calculate FSS for training window
            train_fss = fss_engine.compute_fss_v3(
                prices=train_prices,
                volumes=train_volumes,
                spy=train_spy,
                vix=None
            )
            
            # Get signals for each ticker
            kelly_fractions = {}
            fss_scores = {}
            fss_robustness = {}
            volatilities = {}
            
            for ticker in tickers:
                if ticker not in train_prices.columns:
                    continue
                
                try:
                    # Get FSS result with robustness
                    fss_result = fss_engine.get_stock_fss(
                        ticker=ticker,
                        fss_data=train_fss,
                        regime="Expansion",
                        prices=train_prices,
                        spy=train_spy,
                        vix=None,
                        calculate_robustness=True
                    )
                    
                    if fss_result.regime_robustness_score is None or fss_result.regime_robustness_score < min_robustness:
                        continue
                    
                    # Get Kelly fraction
                    ticker_returns = train_prices[ticker].pct_change().dropna()
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
                    
                except Exception as e:
                    continue
            
            if not kelly_fractions:
                continue
            
            # Portfolio allocation
            valid_tickers = list(kelly_fractions.keys())
            if len(valid_tickers) < 2:
                continue
            
            returns_matrix = train_prices[valid_tickers].pct_change().dropna()
            
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
                final_weights = {ticker: weight / total_weight for ticker, weight in top_positions}
            else:
                continue
            
            allocations_by_date[rebal_date] = final_weights
            robustness_by_date[rebal_date] = {t: fss_robustness.get(t, 0.0) for t in final_weights.keys()}
            
            # Apply weights to holding period
            if i < len(rebal_dates) - 1:
                next_rebal = rebal_dates[i+1]
                hold_range = prices.loc[rebal_date:next_rebal].index
                if len(hold_range) > 1:
                    hold_range = hold_range[:-1]
            else:
                hold_range = prices.loc[rebal_date:].index
            
            for ticker, weight in final_weights.items():
                if ticker in portfolio_weights.columns:
                    portfolio_weights.loc[hold_range, ticker] = weight
            
            # Track robustness vs returns
            for ticker in final_weights.keys():
                if ticker in prices.columns and len(hold_range) > 1:
                    forward_return = (prices.loc[hold_range[-1], ticker] / prices.loc[hold_range[0], ticker]) - 1.0
                    robustness_vs_returns_data.append({
                        "date": rebal_date,
                        "ticker": ticker,
                        "robustness": fss_robustness.get(ticker, 0.0),
                        "forward_return": forward_return,
                        "weight": final_weights.get(ticker, 0.0)
                    })
        
        except Exception as e:
            print(f"   ⚠️  Error at {rebal_date.date()}: {e}")
            continue
    
    # Calculate portfolio returns
    print("\n📊 Calculating portfolio performance...")
    daily_returns = prices[tickers].pct_change().fillna(0.0)
    portfolio_daily_returns = (portfolio_weights.shift(1).fillna(0.0) * daily_returns).sum(axis=1)
    
    # Transaction costs (5 bps)
    turnover = portfolio_weights.diff().abs().sum(axis=1)
    transaction_costs = turnover * 0.0005
    portfolio_returns_net = portfolio_daily_returns - transaction_costs
    
    # Equity curve
    equity_curve = (1.0 + portfolio_returns_net).cumprod()
    
    # Drawdown
    cummax = equity_curve.cummax()
    drawdown = (equity_curve / cummax) - 1.0
    
    # Performance metrics
    total_return = equity_curve.iloc[-1] - 1.0
    n_days = len(equity_curve)
    annual_return = equity_curve.iloc[-1] ** (252 / n_days) - 1.0 if n_days > 0 else 0.0
    annual_vol = portfolio_returns_net.std() * np.sqrt(252)
    sharpe_ratio = annual_return / (annual_vol + 1e-12)
    max_drawdown = drawdown.min()
    calmar_ratio = abs(annual_return / max_drawdown) if max_drawdown != 0 else 0.0
    
    # Benchmark comparison
    if spy is not None:
        spy_returns = spy.pct_change().fillna(0.0)
        spy_equity = (1.0 + spy_returns).cumprod()
        benchmark_return = spy_equity.iloc[-1] ** (252 / len(spy_equity)) - 1.0 if len(spy_equity) > 0 else 0.0
        alpha = annual_return - benchmark_return
        tracking_error = (portfolio_returns_net - spy_returns.loc[portfolio_returns_net.index]).std() * np.sqrt(252)
        information_ratio = alpha / (tracking_error + 1e-12)
    else:
        benchmark_return = 0.0
        alpha = 0.0
        information_ratio = 0.0
    
    # Robustness analysis
    robustness_df = pd.DataFrame(robustness_vs_returns_data)
    if not robustness_df.empty:
        robustness_correlation = robustness_df["robustness"].corr(robustness_df["forward_return"])
        high_rob = robustness_df[robustness_df["robustness"] >= 0.7]
        low_rob = robustness_df[robustness_df["robustness"] < 0.7]
        
        high_robustness_performance = {
            "mean_return": high_rob["forward_return"].mean() if len(high_rob) > 0 else 0.0,
            "median_return": high_rob["forward_return"].median() if len(high_rob) > 0 else 0.0,
            "win_rate": (high_rob["forward_return"] > 0).mean() if len(high_rob) > 0 else 0.0,
            "count": len(high_rob)
        }
        
        low_robustness_performance = {
            "mean_return": low_rob["forward_return"].mean() if len(low_rob) > 0 else 0.0,
            "median_return": low_rob["forward_return"].median() if len(low_rob) > 0 else 0.0,
            "win_rate": (low_rob["forward_return"] > 0).mean() if len(low_rob) > 0 else 0.0,
            "count": len(low_rob)
        }
    else:
        robustness_correlation = 0.0
        high_robustness_performance = {}
        low_robustness_performance = {}
    
    # Print results
    print("\n" + "="*80)
    print("REAL DATA BACKTEST RESULTS")
    print("="*80)
    
    print(f"\n📊 Performance Metrics:")
    print(f"  Total Return:        {total_return:.2%}")
    print(f"  Annual Return:       {annual_return:.2%}")
    print(f"  Annual Volatility:   {annual_vol:.2%}")
    print(f"  Sharpe Ratio:        {sharpe_ratio:.3f}")
    print(f"  Max Drawdown:        {max_drawdown:.2%}")
    print(f"  Calmar Ratio:         {calmar_ratio:.3f}")
    
    print(f"\n📈 Benchmark Comparison:")
    print(f"  Benchmark Return:    {benchmark_return:.2%}")
    print(f"  Alpha:               {alpha:.2%}")
    print(f"  Information Ratio:   {information_ratio:.3f}")
    
    print(f"\n🔬 Robustness Analysis:")
    if not robustness_df.empty:
        print(f"  Robustness-Return Correlation: {robustness_correlation:.3f}")
    
    if high_robustness_performance:
        print(f"\n  High Robustness (≥0.7):")
        print(f"    Count:             {high_robustness_performance['count']}")
        print(f"    Mean Return:       {high_robustness_performance['mean_return']:.2%}")
        print(f"    Median Return:     {high_robustness_performance['median_return']:.2%}")
        print(f"    Win Rate:          {high_robustness_performance['win_rate']:.2%}")
    
    if low_robustness_performance:
        print(f"\n  Low Robustness (<0.7):")
        print(f"    Count:             {low_robustness_performance['count']}")
        print(f"    Mean Return:       {low_robustness_performance['mean_return']:.2%}")
        print(f"    Median Return:     {low_robustness_performance['median_return']:.2%}")
        print(f"    Win Rate:          {low_robustness_performance['win_rate']:.2%}")
    
    print(f"\n💼 Portfolio Metrics:")
    print(f"  Avg Positions:       {portfolio_weights.sum(axis=1).mean():.1f}")
    print(f"  Avg Turnover:        {turnover.mean():.2%}")
    print(f"  Rebalance Dates:     {len(rebal_dates)}")
    
    print("\n" + "="*80)
    print("✅ REAL DATA BACKTEST COMPLETE")
    print("="*80 + "\n")
    
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe_ratio": sharpe_ratio,
        "alpha": alpha,
        "robustness_correlation": robustness_correlation,
        "high_robustness_performance": high_robustness_performance,
        "low_robustness_performance": low_robustness_performance,
        "robustness_df": robustness_df,
        "equity_curve": equity_curve
    }


def main():
    parser = argparse.ArgumentParser(description="Real Data Walk-Forward Backtest")
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"],
                        help="Tickers to test (default: AAPL MSFT GOOGL JPM JNJ)")
    parser.add_argument("--start-date", type=str, default="2022-01-01",
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2024-12-31",
                        help="End date (YYYY-MM-DD)")
    parser.add_argument("--min-robustness", type=float, default=0.5,
                        help="Minimum robustness (default: 0.5)")
    parser.add_argument("--max-positions", type=int, default=10,
                        help="Max positions (default: 10)")
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    result = run_real_data_backtest(
        tickers=args.tickers,
        start_date=start_date,
        end_date=end_date,
        min_robustness=args.min_robustness,
        max_positions=args.max_positions
    )
    
    if result:
        print("✅ Real data backtest complete!")
    else:
        print("❌ Real data backtest failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

