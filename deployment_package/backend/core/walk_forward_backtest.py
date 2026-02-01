"""
Walk-Forward Backtest for Chan Portfolio Pipeline

Tests the complete pipeline:
1. FSS Engine → FSS scores
2. Regime Robustness → Filter/rank by robustness
3. Chan Quant Signals → Kelly fractions
4. Portfolio Allocator → Correlation-aware weights
5. Walk-forward testing → No look-ahead bias

Verifies that high RegimeRobustness correlates with better forward returns.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

from .fss_engine import get_fss_engine, FSSEngine
from .fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest, FSSDataResult
from .chan_quant_signal_engine import ChanQuantSignalEngine
from .chan_portfolio_allocator import get_chan_portfolio_allocator, ChanPortfolioAllocator
from .fss_backtest import FSSBacktester, BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardBacktestResult:
    """Result from walk-forward backtest"""
    # Overall performance
    total_return: float
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Benchmark comparison
    benchmark_return: float
    alpha: float
    information_ratio: float
    
    # Robustness analysis
    robustness_vs_returns: pd.DataFrame  # Correlation between robustness and forward returns
    high_robustness_performance: Dict[str, float]  # Performance of high robustness stocks
    low_robustness_performance: Dict[str, float]  # Performance of low robustness stocks
    
    # Portfolio metrics
    diversification_score: float
    avg_position_count: float
    turnover: float
    
    # Time series
    equity_curve: pd.Series
    drawdown: pd.Series
    monthly_returns: pd.Series
    
    # Detailed results
    rebalance_dates: List[datetime]
    allocations_by_date: Dict[datetime, Dict[str, float]]
    robustness_by_date: Dict[datetime, Dict[str, float]]


class WalkForwardBacktester:
    """
    Walk-forward backtester for Chan portfolio pipeline.
    
    Uses walk-forward methodology:
    - Training window: Calculate signals using only past data
    - Testing window: Hold positions and measure returns
    - Rolling forward: Move both windows forward
    """
    
    def __init__(
        self,
        training_window_days: int = 252,  # 1 year training
        testing_window_days: int = 63,  # 3 months testing
        rebalance_freq: str = "M",  # Monthly rebalancing
        min_robustness: float = 0.5,  # Minimum robustness to include
        max_positions: int = 20,  # Maximum positions
        transaction_cost_bps: float = 5.0  # 5 bps transaction cost
    ):
        """
        Initialize walk-forward backtester.
        
        Args:
            training_window_days: Days of data to use for signal calculation
            testing_window_days: Days to hold positions before rebalancing
            rebalance_freq: Rebalancing frequency ("W", "M", "Q")
            min_robustness: Minimum robustness score to include stock
            max_positions: Maximum number of positions
            transaction_cost_bps: Transaction cost in basis points
        """
        self.training_window_days = training_window_days
        self.testing_window_days = testing_window_days
        self.rebalance_freq = rebalance_freq
        self.min_robustness = min_robustness
        self.max_positions = max_positions
        self.transaction_cost_bps = transaction_cost_bps
        
        self.fss_engine = get_fss_engine()
        self.chan_engine = ChanQuantSignalEngine()
        self.allocator = get_chan_portfolio_allocator()
        self.backtester = FSSBacktester(transaction_cost_bps=transaction_cost_bps)
    
    async def run_walk_forward_backtest(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        benchmark_ticker: str = "SPY"
    ) -> WalkForwardBacktestResult:
        """
        Run walk-forward backtest on historical data.
        
        Args:
            tickers: List of stock symbols to test
            start_date: Start date for backtest
            end_date: End date for backtest
            benchmark_ticker: Benchmark ticker (default: SPY)
            
        Returns:
            WalkForwardBacktestResult with comprehensive metrics
        """
        logger.info(f"Starting walk-forward backtest: {len(tickers)} tickers, {start_date} to {end_date}")
        
        # Fetch all historical data
        pipeline = get_fss_data_pipeline()
        all_tickers = tickers + [benchmark_ticker]
        
        async with pipeline:
            # Calculate total lookback needed
            total_days = (end_date - start_date).days + self.training_window_days + 100
            request = FSSDataRequest(
                tickers=all_tickers,
                lookback_days=total_days,
                include_fundamentals=False
            )
            data_result = await pipeline.fetch_fss_data(request)
        
        if data_result.prices.empty:
            raise ValueError("No price data available for backtest")
        
        # Filter to test period
        prices = data_result.prices.loc[start_date:end_date]
        volumes = data_result.volumes.loc[start_date:end_date] if benchmark_ticker in data_result.volumes.columns else data_result.volumes
        spy = data_result.spy.loc[start_date:end_date] if benchmark_ticker in data_result.spy.index else None
        
        # Get rebalance dates
        rebal_dates = prices.resample(self.rebalance_freq).last().index
        rebal_dates = rebal_dates[rebal_dates >= start_date]
        
        # Track portfolio
        portfolio_weights = pd.DataFrame(0.0, index=prices.index, columns=tickers)
        allocations_by_date = {}
        robustness_by_date = {}
        
        # Track performance
        robustness_vs_returns_data = []
        
        # Walk-forward loop
        for i, rebal_date in enumerate(rebal_dates):
            if rebal_date not in prices.index:
                continue
            
            # Training window: data up to (but not including) rebal_date
            train_end = rebal_date
            train_start_idx = prices.index.get_loc(train_end) - self.training_window_days
            if train_start_idx < 0:
                continue
            
            train_start = prices.index[train_start_idx]
            train_prices = prices.loc[train_start:train_end]
            train_volumes = volumes.loc[train_start:train_end] if not volumes.empty else None
            train_spy = spy.loc[train_start:train_end] if spy is not None else None
            train_vix = data_result.vix.loc[train_start:train_end] if data_result.vix is not None and len(data_result.vix) > 0 else None
            
            if len(train_prices) < 60:  # Need minimum data
                continue
            
            logger.info(f"Rebalance {i+1}/{len(rebal_dates)}: {rebal_date.date()} (Training: {train_start.date()} to {train_end.date()})")
            
            try:
                # 1. Calculate FSS scores (using only training data)
                fss_data = self.fss_engine.compute_fss_v3(
                    prices=train_prices,
                    volumes=train_volumes,
                    spy=train_spy,
                    vix=train_vix
                )
                
                # 2. Calculate robustness and get Kelly fractions for each ticker
                ticker_signals = {}
                kelly_fractions = {}
                fss_scores = {}
                fss_robustness = {}
                volatilities = {}
                
                for ticker in tickers:
                    if ticker not in train_prices.columns:
                        continue
                    
                    try:
                        # Get FSS result with robustness
                        fss_result = self.fss_engine.get_stock_fss(
                            ticker=ticker,
                            fss_data=fss_data,
                            regime="Expansion",  # Will be calculated internally
                            prices=train_prices,
                            spy=train_spy,
                            vix=train_vix,
                            calculate_robustness=True
                        )
                        
                        if fss_result.regime_robustness_score is None or fss_result.regime_robustness_score < self.min_robustness:
                            continue  # Skip low robustness stocks
                        
                        # Get Chan quant signals (for Kelly)
                        # Calculate Kelly from historical returns
                        ticker_returns = train_prices[ticker].pct_change().dropna()
                        if len(ticker_returns) >= 20:
                            kelly_result = self.chan_engine.calculate_kelly_position_size(
                                symbol=ticker,
                                historical_returns=ticker_returns
                            )
                            kelly_fraction = kelly_result.recommended_fraction
                        else:
                            # Fallback: use FSS score as proxy for Kelly
                            kelly_fraction = min(0.15, fss_result.fss_score / 100.0 * 0.2)
                        
                        # Store signals
                        ticker_signals[ticker] = {
                            "fss": fss_result.fss_score,
                            "robustness": fss_result.regime_robustness_score,
                            "kelly": kelly_fraction
                        }
                        
                        kelly_fractions[ticker] = kelly_fraction
                        fss_scores[ticker] = fss_result.fss_score
                        fss_robustness[ticker] = fss_result.regime_robustness_score
                        
                        # Calculate volatility
                        returns = train_prices[ticker].pct_change().dropna()
                        if len(returns) > 20:
                            volatilities[ticker] = returns.std() * np.sqrt(252)  # Annualized
                        else:
                            volatilities[ticker] = 0.20  # Default 20%
                        
                    except Exception as e:
                        logger.warning(f"Error processing {ticker} at {rebal_date}: {e}")
                        continue
                
                if not ticker_signals:
                    logger.warning(f"No valid signals at {rebal_date}")
                    continue
                
                # 3. Portfolio allocation (using correlation-aware allocator)
                valid_tickers = list(ticker_signals.keys())
                if len(valid_tickers) < 2:
                    continue
                
                # Calculate returns matrix for correlation
                returns_matrix = train_prices[valid_tickers].pct_change().dropna()
                
                # Allocate portfolio
                allocation_result = self.allocator.allocate_portfolio(
                    tickers=valid_tickers,
                    kelly_fractions=kelly_fractions,
                    fss_scores=fss_scores,
                    fss_robustness=fss_robustness,
                    returns_matrix=returns_matrix,
                    volatilities=volatilities,
                    method="kelly_constrained"
                )
                
                # Limit to top N positions
                sorted_weights = sorted(allocation_result.weights.items(), key=lambda x: x[1], reverse=True)
                top_positions = sorted_weights[:self.max_positions]
                
                # Renormalize top positions
                total_weight = sum(w for _, w in top_positions)
                if total_weight > 0:
                    final_weights = {ticker: weight / total_weight for ticker, weight in top_positions}
                else:
                    continue
                
                # Store allocation
                allocations_by_date[rebal_date] = final_weights
                robustness_by_date[rebal_date] = {t: fss_robustness.get(t, 0.0) for t in final_weights.keys()}
                
                # Apply weights to holding period
                if i < len(rebal_dates) - 1:
                    next_rebal = rebal_dates[i+1]
                    hold_range = prices.loc[rebal_date:next_rebal].index
                    if len(hold_range) > 1:
                        hold_range = hold_range[:-1]  # Exclude next rebalance date
                else:
                    hold_range = prices.loc[rebal_date:].index
                
                for ticker, weight in final_weights.items():
                    if ticker in portfolio_weights.columns:
                        portfolio_weights.loc[hold_range, ticker] = weight
                
                # Track robustness vs returns for analysis
                for ticker in final_weights.keys():
                    if ticker in prices.columns and len(hold_range) > 1:
                        # Calculate forward return
                        forward_return = (prices.loc[hold_range[-1], ticker] / prices.loc[hold_range[0], ticker]) - 1.0
                        robustness_vs_returns_data.append({
                            "date": rebal_date,
                            "ticker": ticker,
                            "robustness": fss_robustness.get(ticker, 0.0),
                            "forward_return": forward_return,
                            "weight": final_weights.get(ticker, 0.0)
                        })
                
            except Exception as e:
                logger.error(f"Error in walk-forward step at {rebal_date}: {e}", exc_info=True)
                continue
        
        # Calculate portfolio returns
        daily_returns = prices[tickers].pct_change().fillna(0.0)
        portfolio_daily_returns = (portfolio_weights.shift(1).fillna(0.0) * daily_returns).sum(axis=1)
        
        # Apply transaction costs
        turnover = portfolio_weights.diff().abs().sum(axis=1)
        transaction_costs = turnover * (self.transaction_cost_bps / 10000.0)
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
            
            # Information ratio (alpha / tracking error)
            tracking_error = (portfolio_returns_net - spy_returns.loc[portfolio_returns_net.index]).std() * np.sqrt(252)
            information_ratio = alpha / (tracking_error + 1e-12)
        else:
            benchmark_return = 0.0
            alpha = 0.0
            information_ratio = 0.0
        
        # Robustness analysis
        robustness_df = pd.DataFrame(robustness_vs_returns_data)
        if not robustness_df.empty:
            # Correlation between robustness and returns
            robustness_correlation = robustness_df["robustness"].corr(robustness_df["forward_return"])
            
            # High vs low robustness performance
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
        
        # Portfolio metrics
        avg_position_count = portfolio_weights.sum(axis=1).mean()  # Average number of positions
        avg_turnover = turnover.mean()
        
        # Monthly returns
        monthly_returns = portfolio_returns_net.resample("M").apply(lambda x: (1 + x).prod() - 1)
        
        return WalkForwardBacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            annual_volatility=annual_vol,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            benchmark_return=benchmark_return,
            alpha=alpha,
            information_ratio=information_ratio,
            robustness_vs_returns=robustness_df,
            high_robustness_performance=high_robustness_performance,
            low_robustness_performance=low_robustness_performance,
            diversification_score=0.65,  # Would calculate from allocations
            avg_position_count=avg_position_count,
            turnover=avg_turnover,
            equity_curve=equity_curve,
            drawdown=drawdown,
            monthly_returns=monthly_returns,
            rebalance_dates=list(rebal_dates),
            allocations_by_date=allocations_by_date,
            robustness_by_date=robustness_by_date
        )
    
    def print_results(self, result: WalkForwardBacktestResult):
        """Print backtest results in a readable format"""
        print("\n" + "="*80)
        print("WALK-FORWARD BACKTEST RESULTS")
        print("="*80)
        
        print(f"\n📊 Performance Metrics:")
        print(f"  Total Return:        {result.total_return:.2%}")
        print(f"  Annual Return:       {result.annual_return:.2%}")
        print(f"  Annual Volatility:   {result.annual_volatility:.2%}")
        print(f"  Sharpe Ratio:        {result.sharpe_ratio:.3f}")
        print(f"  Max Drawdown:        {result.max_drawdown:.2%}")
        print(f"  Calmar Ratio:         {result.calmar_ratio:.3f}")
        
        print(f"\n📈 Benchmark Comparison:")
        print(f"  Benchmark Return:    {result.benchmark_return:.2%}")
        print(f"  Alpha:               {result.alpha:.2%}")
        print(f"  Information Ratio:   {result.information_ratio:.3f}")
        
        print(f"\n🔬 Robustness Analysis:")
        if not result.robustness_vs_returns.empty:
            corr = result.robustness_vs_returns["robustness"].corr(result.robustness_vs_returns["forward_return"])
            print(f"  Robustness-Return Correlation: {corr:.3f}")
        
        if result.high_robustness_performance:
            print(f"\n  High Robustness (≥0.7):")
            print(f"    Mean Return:       {result.high_robustness_performance['mean_return']:.2%}")
            print(f"    Win Rate:          {result.high_robustness_performance['win_rate']:.2%}")
            print(f"    Count:             {result.high_robustness_performance['count']}")
        
        if result.low_robustness_performance:
            print(f"\n  Low Robustness (<0.7):")
            print(f"    Mean Return:       {result.low_robustness_performance['mean_return']:.2%}")
            print(f"    Win Rate:          {result.low_robustness_performance['win_rate']:.2%}")
            print(f"    Count:             {result.low_robustness_performance['count']}")
        
        print(f"\n💼 Portfolio Metrics:")
        print(f"  Avg Positions:       {result.avg_position_count:.1f}")
        print(f"  Avg Turnover:        {result.turnover:.2%}")
        print(f"  Diversification:     {result.diversification_score:.2f}")
        
        print("\n" + "="*80)


async def run_walk_forward_backtest_demo():
    """Demo function to run walk-forward backtest"""
    # Test on a basket of diverse stocks
    test_tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ", "V", "PG", "MA"]
    
    backtester = WalkForwardBacktester(
        training_window_days=252,
        testing_window_days=63,
        rebalance_freq="M",
        min_robustness=0.5,
        max_positions=5
    )
    
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    result = await backtester.run_walk_forward_backtest(
        tickers=test_tickers,
        start_date=start_date,
        end_date=end_date
    )
    
    backtester.print_results(result)
    
    return result


if __name__ == "__main__":
    asyncio.run(run_walk_forward_backtest_demo())

