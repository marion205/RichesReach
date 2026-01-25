# core/fss_backtest.py
"""
FSS Backtesting Engine
Cross-sectional strategy backtesting for FSS-based stock ranking.

Tests strategies that:
1. Rank stocks by FSS score
2. Buy top N stocks
3. Hold and rebalance periodically
4. Track performance vs benchmark
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Result from FSS backtest"""
    equity_curve: pd.Series
    returns: pd.Series
    drawdown: pd.Series
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    turnover: pd.Series
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None


class FSSBacktester:
    """
    Backtesting engine for FSS-based strategies.
    
    Supports:
    - Monthly/weekly rebalancing
    - Top N selection
    - Transaction costs
    - Benchmark comparison
    """
    
    def __init__(self, transaction_cost_bps: float = 5.0):
        """
        Initialize backtester.
        
        Args:
            transaction_cost_bps: Transaction cost in basis points (default: 5 bps = 0.05%)
        """
        self.transaction_cost_bps = transaction_cost_bps
    
    def forward_return(
        self,
        prices: pd.DataFrame,
        horizon: int = 126
    ) -> pd.DataFrame:
        """
        Calculate forward return over horizon.
        
        Args:
            prices: Price DataFrame
            horizon: Number of trading days (e.g., 126 for 6 months)
            
        Returns:
            Forward return DataFrame
        """
        return prices.shift(-horizon) / prices - 1.0
    
    def backtest_rank_strategy(
        self,
        prices: pd.DataFrame,
        fss: pd.DataFrame,
        spy: Optional[pd.Series] = None,
        rebalance_freq: str = "M",
        top_n: int = 20,
        hold_days: Optional[int] = None,
        long_only: bool = True,
        min_liquidity: float = 1_000_000
    ) -> BacktestResult:
        """
        Backtest a top-N ranking strategy.
        
        Args:
            prices: Price DataFrame (date x tickers)
            fss: FSS scores DataFrame (date x tickers) - use fss_data["FSS"] from compute_fss_v2
            spy: Optional SPY benchmark
            rebalance_freq: "W" for weekly, "M" for monthly
            top_n: Number of stocks to hold
            hold_days: Optional fixed holding period (if None, use rebalance schedule)
            long_only: Long-only strategy (default: True)
            min_liquidity: Minimum average volume filter
            
        Returns:
            BacktestResult with performance metrics
        """
        # Get rebalance dates
        rebal_dates = prices.resample(rebalance_freq).last().index.intersection(prices.index)
        
        # Daily returns
        daily_ret = prices.pct_change().fillna(0.0)
        
        # Weights matrix (date x tickers)
        W = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
        
        # Track trades
        trades = []
        
        for i, d in enumerate(rebal_dates):
            if d not in fss.index:
                continue
            
            # Get latest FSS scores
            scores = fss.loc[d].dropna()
            
            if scores.empty:
                continue
            
            # Select top N
            winners = scores.sort_values(ascending=False).head(top_n).index
            
            # Equal weight
            w = pd.Series(0.0, index=prices.columns)
            w.loc[winners] = 1.0 / len(winners)
            
            # Determine holding window
            if hold_days is not None:
                start_idx = prices.index.get_loc(d)
                end_idx = min(start_idx + hold_days, len(prices.index) - 1)
                hold_range = prices.index[start_idx:end_idx+1]
            else:
                # Hold until next rebalance
                if i < len(rebal_dates) - 1:
                    next_d = rebal_dates[i+1]
                    hold_range = prices.loc[d:next_d].index
                    hold_range = hold_range[:-1] if len(hold_range) > 1 else hold_range
                else:
                    hold_range = prices.loc[d:].index
            
            W.loc[hold_range] = w.values
            
            # Track trade
            trades.append({
                "date": d,
                "tickers": list(winners),
                "weights": w[winners].to_dict()
            })
        
        # Portfolio daily return
        port_ret = (W.shift(1).fillna(0.0) * daily_ret).sum(axis=1)
        
        # Transaction costs
        W_rebal = W.loc[rebal_dates].copy()
        turnover = W_rebal.diff().abs().sum(axis=1).fillna(W_rebal.abs().sum(axis=1))
        cost = turnover * (self.transaction_cost_bps / 10000.0)
        cost_daily = pd.Series(0.0, index=prices.index)
        cost_daily.loc[rebal_dates] = cost.values
        
        # Net returns
        port_ret_net = port_ret - cost_daily
        
        # Equity curve
        equity = (1.0 + port_ret_net).cumprod()
        
        # Drawdown
        cummax = equity.cummax()
        drawdown = (equity / cummax) - 1.0
        
        # Performance metrics
        ann_return = equity.iloc[-1] ** (252 / max(1, len(equity))) - 1
        ann_vol = port_ret_net.std() * np.sqrt(252)
        sharpe = ann_return / (ann_vol + 1e-12)
        max_dd = drawdown.min()
        
        # Win rate (positive return periods)
        positive_periods = (port_ret_net > 0).sum()
        win_rate = positive_periods / len(port_ret_net) if len(port_ret_net) > 0 else 0.0
        
        # Benchmark comparison
        benchmark_return = None
        alpha = None
        if spy is not None:
            spy_ret = spy.pct_change().fillna(0.0)
            spy_equity = (1.0 + spy_ret).cumprod()
            benchmark_return = spy_equity.iloc[-1] ** (252 / max(1, len(spy_equity))) - 1
            alpha = ann_return - benchmark_return
        
        return BacktestResult(
            equity_curve=equity,
            returns=port_ret_net,
            drawdown=drawdown,
            annual_return=ann_return,
            annual_volatility=ann_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            total_trades=len(trades),
            turnover=turnover,
            benchmark_return=benchmark_return,
            alpha=alpha
        )
    
    def calculate_ic(
        self,
        fss: pd.DataFrame,
        forward_returns: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate Information Coefficient (IC).
        
        IC = correlation between FSS scores and forward returns.
        Higher IC = better predictive power.
        
        Args:
            fss: FSS scores (date x tickers)
            forward_returns: Forward returns (date x tickers)
            
        Returns:
            IC time series
        """
        ic_series = []
        
        common_dates = fss.index.intersection(forward_returns.index)
        
        for date in common_dates:
            fss_scores = fss.loc[date].dropna()
            fwd_ret = forward_returns.loc[date].dropna()
            
            common_tickers = fss_scores.index.intersection(fwd_ret.index)
            
            if len(common_tickers) < 10:  # Need minimum stocks
                continue
            
            fss_vals = fss_scores.loc[common_tickers]
            ret_vals = fwd_ret.loc[common_tickers]
            
            ic = fss_vals.corr(ret_vals)
            
            if not pd.isna(ic):
                ic_series.append({"date": date, "ic": ic})
        
        if not ic_series:
            return pd.Series(dtype=float)
        
        ic_df = pd.DataFrame(ic_series).set_index("date")
        return ic_df["ic"]
    
    def analyze_decile_performance(
        self,
        fss: pd.DataFrame,
        forward_returns: pd.DataFrame,
        n_deciles: int = 10
    ) -> pd.DataFrame:
        """
        Analyze performance by FSS decile.
        
        Args:
            fss: FSS scores (date x tickers)
            forward_returns: Forward returns (date x tickers)
            n_deciles: Number of deciles (default: 10)
            
        Returns:
            DataFrame with decile performance stats
        """
        results = []
        
        common_dates = fss.index.intersection(forward_returns.index)
        
        for date in common_dates:
            fss_scores = fss.loc[date].dropna()
            fwd_ret = forward_returns.loc[date].dropna()
            
            common_tickers = fss_scores.index.intersection(fwd_ret.index)
            
            if len(common_tickers) < n_deciles:
                continue
            
            # Rank by FSS
            fss_vals = fss_scores.loc[common_tickers]
            ret_vals = fwd_ret.loc[common_tickers]
            
            # Create deciles
            fss_vals_ranked = pd.qcut(fss_vals, q=n_deciles, labels=False, duplicates='drop')
            
            for decile in range(n_deciles):
                decile_mask = fss_vals_ranked == decile
                decile_returns = ret_vals[decile_mask]
                
                if len(decile_returns) > 0:
                    results.append({
                        "date": date,
                        "decile": decile,
                        "mean_return": decile_returns.mean(),
                        "median_return": decile_returns.median(),
                        "count": len(decile_returns)
                    })
        
        if not results:
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        
        # Aggregate by decile
        decile_stats = results_df.groupby("decile").agg({
            "mean_return": "mean",
            "median_return": "median",
            "count": "sum"
        })
        
        return decile_stats


# Singleton instance
_fss_backtester = FSSBacktester()


def get_fss_backtester() -> FSSBacktester:
    """Get singleton FSS backtester instance"""
    return _fss_backtester

