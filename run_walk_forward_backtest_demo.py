#!/usr/bin/env python3
"""
Walk-Forward Backtest Demo with Synthetic Data

Generates realistic synthetic historical price data to test the complete pipeline.
This allows testing without external data dependencies.
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine
from backend.core.chan_quant_signal_engine import ChanQuantSignalEngine
from backend.core.chan_portfolio_allocator import get_chan_portfolio_allocator


def generate_synthetic_prices(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    base_prices: Dict[str, float] = None,
    correlations: Dict[tuple, float] = None
) -> Dict:
    """Generate realistic synthetic historical price data"""
    print(f"\n📊 Generating synthetic data for {len(tickers)} tickers...")
    
    # Create date range (business days only)
    dates = pd.bdate_range(start=start_date, end=end_date)
    n_days = len(dates)
    
    # Default base prices
    if base_prices is None:
        base_prices = {ticker: 100.0 + np.random.uniform(-20, 20) for ticker in tickers}
    
    # Generate correlated returns
    np.random.seed(42)  # For reproducibility
    
    # Create correlation matrix
    n_tickers = len(tickers)
    if correlations is None:
        # Default: tech stocks correlated, others less so
        corr_matrix = np.eye(n_tickers)
        for i, ticker_i in enumerate(tickers):
            for j, ticker_j in enumerate(tickers):
                if i != j:
                    if 'AAPL' in ticker_i and 'MSFT' in ticker_j:
                        corr_matrix[i, j] = 0.7  # Tech correlation
                    elif 'JPM' in ticker_i and 'BAC' in ticker_j:
                        corr_matrix[i, j] = 0.6  # Financial correlation
                    else:
                        corr_matrix[i, j] = np.random.uniform(0.2, 0.5)
    else:
        corr_matrix = np.eye(n_tickers)
        for (t1, t2), corr in correlations.items():
            if t1 in tickers and t2 in tickers:
                i, j = tickers.index(t1), tickers.index(t2)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
    
    # Generate daily returns with correlation
    # Use Cholesky decomposition for correlated random variables
    L = np.linalg.cholesky(corr_matrix + 0.01 * np.eye(n_tickers))  # Add small epsilon for stability
    
    # Generate uncorrelated random returns
    uncorrelated_returns = np.random.normal(0, 0.02, (n_days, n_tickers))  # 2% daily vol
    
    # Apply correlation
    correlated_returns = uncorrelated_returns @ L.T
    
    # Add some trend and mean reversion
    for i, ticker in enumerate(tickers):
        # Add slight positive drift (market goes up over time)
        drift = np.random.normal(0.0003, 0.0001)  # ~7.5% annual return
        correlated_returns[:, i] += drift
        
        # Add some mean reversion
        for j in range(1, n_days):
            if correlated_returns[j-1, i] > 0.05:  # If big up day
                correlated_returns[j, i] -= 0.01  # Slight pullback
            elif correlated_returns[j-1, i] < -0.05:  # If big down day
                correlated_returns[j, i] += 0.01  # Slight bounce
    
    # Convert returns to prices
    prices_dict = {}
    volumes_dict = {}
    
    for i, ticker in enumerate(tickers):
        prices = [base_prices[ticker]]
        for ret in correlated_returns[:, i]:
            prices.append(prices[-1] * (1 + ret))
        
        prices_dict[ticker] = pd.Series(prices[1:], index=dates)
        
        # Generate volumes (higher on volatile days)
        base_volume = 1_000_000
        volumes = []
        for ret in correlated_returns[:, i]:
            vol_multiplier = 1.0 + abs(ret) * 5  # Higher volume on big moves
            volumes.append(int(base_volume * vol_multiplier * np.random.uniform(0.8, 1.2)))
        volumes_dict[ticker] = pd.Series(volumes, index=dates)
    
    # Generate SPY (market benchmark)
    spy_returns = np.random.normal(0.0003, 0.015, n_days)  # Slightly lower vol than individual stocks
    spy_prices = [100.0]
    for ret in spy_returns:
        spy_prices.append(spy_prices[-1] * (1 + ret))
    spy_series = pd.Series(spy_prices[1:], index=dates)
    
    prices_df = pd.DataFrame(prices_dict)
    volumes_df = pd.DataFrame(volumes_dict)
    
    print(f"✅ Generated {len(dates)} days of data")
    print(f"   Date range: {dates[0].date()} to {dates[-1].date()}")
    
    return {
        "prices": prices_df,
        "volumes": volumes_df,
        "spy": spy_series
    }


def run_demo_backtest():
    """Run walk-forward backtest with synthetic data"""
    print("\n" + "="*80)
    print("CHAN PORTFOLIO PIPELINE - WALK-FORWARD BACKTEST (DEMO)")
    print("="*80)
    print("\nUsing synthetic data to test the complete pipeline:")
    print("  1. FSS Engine → FSS scores")
    print("  2. Regime Robustness → Filter by robustness")
    print("  3. Chan Quant Signals → Kelly fractions")
    print("  4. Portfolio Allocator → Correlation-aware weights")
    print("  5. Walk-forward testing → No look-ahead bias")
    
    # Test on diverse basket
    test_tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
    
    print(f"\n📊 Testing on {len(test_tickers)} tickers:")
    print(f"   {', '.join(test_tickers)}")
    
    # 3-year backtest
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    print(f"\n📅 Backtest Period: {start_date.date()} to {end_date.date()}")
    
    # Generate synthetic data
    data = generate_synthetic_prices(test_tickers, start_date, end_date)
    
    # Initialize engines
    fss_engine = get_fss_engine()
    chan_engine = ChanQuantSignalEngine()
    allocator = get_chan_portfolio_allocator()
    
    # Get rebalance dates (monthly)
    rebal_dates = data["prices"].resample("M").last().index
    rebal_dates = rebal_dates[rebal_dates >= start_date]
    
    print(f"\n🔄 Running walk-forward backtest ({len(rebal_dates)} rebalance dates)...")
    
    # Track portfolio
    portfolio_weights = pd.DataFrame(0.0, index=data["prices"].index, columns=test_tickers)
    allocations_by_date = {}
    robustness_by_date = {}
    robustness_vs_returns_data = []
    
    training_window = 252  # 1 year
    min_robustness = 0.5
    
    # Walk-forward loop
    for i, rebal_date in enumerate(rebal_dates):
        if rebal_date not in data["prices"].index:
            continue
        
        # Training window
        train_end = rebal_date
        train_start_idx = data["prices"].index.get_loc(train_end) - training_window
        if train_start_idx < 0:
            continue
        
        train_start = data["prices"].index[train_start_idx]
        train_prices = data["prices"].loc[train_start:train_end]
        train_volumes = data["volumes"].loc[train_start:train_end]
        train_spy = data["spy"].loc[train_start:train_end]
        
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
            
            for ticker in test_tickers:
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
            top_positions = sorted_weights[:5]
            
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
                hold_range = data["prices"].loc[rebal_date:next_rebal].index
                if len(hold_range) > 1:
                    hold_range = hold_range[:-1]
            else:
                hold_range = data["prices"].loc[rebal_date:].index
            
            for ticker, weight in final_weights.items():
                if ticker in portfolio_weights.columns:
                    portfolio_weights.loc[hold_range, ticker] = weight
            
            # Track robustness vs returns
            for ticker in final_weights.keys():
                if ticker in data["prices"].columns and len(hold_range) > 1:
                    forward_return = (data["prices"].loc[hold_range[-1], ticker] / data["prices"].loc[hold_range[0], ticker]) - 1.0
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
    daily_returns = data["prices"][test_tickers].pct_change().fillna(0.0)
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
    spy_returns = data["spy"].pct_change().fillna(0.0)
    spy_equity = (1.0 + spy_returns).cumprod()
    benchmark_return = spy_equity.iloc[-1] ** (252 / len(spy_equity)) - 1.0 if len(spy_equity) > 0 else 0.0
    alpha = annual_return - benchmark_return
    tracking_error = (portfolio_returns_net - spy_returns.loc[portfolio_returns_net.index]).std() * np.sqrt(252)
    information_ratio = alpha / (tracking_error + 1e-12)
    
    # Robustness analysis
    robustness_df = pd.DataFrame(robustness_vs_returns_data)
    if not robustness_df.empty:
        robustness_correlation = robustness_df["robustness"].corr(robustness_df["forward_return"])
        high_rob = robustness_df[robustness_df["robustness"] >= 0.7]
        low_rob = robustness_df[robustness_df["robustness"] < 0.7]
        
        high_robustness_performance = {
            "mean_return": high_rob["forward_return"].mean() if len(high_rob) > 0 else 0.0,
            "win_rate": (high_rob["forward_return"] > 0).mean() if len(high_rob) > 0 else 0.0,
            "count": len(high_rob)
        }
        
        low_robustness_performance = {
            "mean_return": low_rob["forward_return"].mean() if len(low_rob) > 0 else 0.0,
            "win_rate": (low_rob["forward_return"] > 0).mean() if len(low_rob) > 0 else 0.0,
            "count": len(low_rob)
        }
    else:
        robustness_correlation = 0.0
        high_robustness_performance = {}
        low_robustness_performance = {}
    
    # Print results
    print("\n" + "="*80)
    print("WALK-FORWARD BACKTEST RESULTS")
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
        print(f"    Mean Return:       {high_robustness_performance['mean_return']:.2%}")
        print(f"    Win Rate:          {high_robustness_performance['win_rate']:.2%}")
        print(f"    Count:             {high_robustness_performance['count']}")
    
    if low_robustness_performance:
        print(f"\n  Low Robustness (<0.7):")
        print(f"    Mean Return:       {low_robustness_performance['mean_return']:.2%}")
        print(f"    Win Rate:          {low_robustness_performance['win_rate']:.2%}")
        print(f"    Count:             {low_robustness_performance['count']}")
    
    print(f"\n💼 Portfolio Metrics:")
    print(f"  Avg Positions:       {portfolio_weights.sum(axis=1).mean():.1f}")
    print(f"  Avg Turnover:        {turnover.mean():.2%}")
    print(f"  Rebalance Dates:     {len(rebal_dates)}")
    
    print("\n" + "="*80)
    print("✅ BACKTEST COMPLETE")
    print("="*80 + "\n")
    
    # Key insights
    print("📈 Key Insights:")
    if alpha > 0:
        print(f"   ✅ Positive alpha: {alpha:.2%} vs SPY")
    else:
        print(f"   ⚠️  Negative alpha: {alpha:.2%} vs SPY")
    
    if sharpe_ratio > 1.0:
        print(f"   ✅ Strong Sharpe ratio: {sharpe_ratio:.2f}")
    elif sharpe_ratio > 0.5:
        print(f"   ⚠️  Moderate Sharpe ratio: {sharpe_ratio:.2f}")
    else:
        print(f"   ❌ Low Sharpe: {sharpe_ratio:.2f}")
    
    if not robustness_df.empty:
        if robustness_correlation > 0.1:
            print(f"   ✅ Robustness correlates with returns: {robustness_correlation:.3f}")
        else:
            print(f"   ⚠️  Weak robustness-return correlation: {robustness_correlation:.3f}")
    
    if high_robustness_performance and low_robustness_performance:
        high_mean = high_robustness_performance.get("mean_return", 0.0)
        low_mean = low_robustness_performance.get("mean_return", 0.0)
        if high_mean > low_mean:
            print(f"   ✅ High robustness stocks outperform: {high_mean:.2%} vs {low_mean:.2%}")
        else:
            print(f"   ⚠️  High robustness stocks underperform: {high_mean:.2%} vs {low_mean:.2%}")
    
    print()
    
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe_ratio": sharpe_ratio,
        "alpha": alpha,
        "robustness_correlation": robustness_correlation,
        "equity_curve": equity_curve
    }


if __name__ == "__main__":
    result = run_demo_backtest()

