#!/usr/bin/env python3
"""
Production Nightly Scan - REAL CHAN STRATEGIES

Uses actual ChanQuantSignalEngine to calculate:
- Bollinger Band Mean Reversion signals
- Relative Strength Momentum signals
- Composite FSS score from these real signals
- Real robustness calculation based on actual signal performance

This replaces all mock/placeholder data with authentic Chan strategy calculations.
"""

import sys
import os
import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine
from backend.core.chan_quant_signal_engine import ChanQuantSignalEngine
from backend.core.chan_portfolio_allocator import get_chan_portfolio_allocator

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available. Install with: pip install yfinance")
    sys.exit(1)


# --- CONFIGURATION ---
UNIVERSE = [
    'SPY', 'QQQ', 'IWM', 'TLT', 'GLD',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
    'BRK.B', 'JPM', 'V', 'XOM', 'JNJ', 'WMT', 'MA', 'PG', 'UNH', 'LLY', 'HD'
]

GATING_RULES = {
    'MIN_ROBUSTNESS': 0.70,
    'MIN_SSR': 0.50,
    'MIN_HISTORY': 252,
    'FORBIDDEN_REGIMES': ['Crash', 'Bear Volatile', 'Crisis', 'Deflation']
}

CAPITAL = 100000.0
LOG_FILE = "trading_log.jsonl"
ORDERS_FILE = "morning_orders.csv"
MAX_POSITIONS = 10


def log_decision(decision_dict: Dict[str, Any]):
    """Appends a structured log entry to the JSONL file."""
    decision_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(decision_dict) + "\n")


def detect_regime(prices: pd.Series, spy: Optional[pd.Series] = None) -> str:
    """Simple regime detection based on price trend and volatility."""
    if len(prices) < 200:
        return 'Neutral'
    
    sma200 = prices.rolling(200).mean().iloc[-1]
    current_price = prices.iloc[-1]
    returns = prices.pct_change().dropna()
    vol21 = returns.rolling(21).std().iloc[-1] * np.sqrt(252)
    
    above_sma = current_price > sma200
    low_vol = vol21 < 0.15
    high_vol = vol21 >= 0.25
    extreme_vol = vol21 >= 0.40
    
    if extreme_vol:
        return 'Crash'
    elif above_sma and low_vol:
        return 'Bull Quiet'
    elif above_sma and high_vol:
        return 'Bull Volatile'
    elif not above_sma and high_vol:
        return 'Bear Volatile'
    elif not above_sma and low_vol:
        return 'Bear Quiet'
    else:
        return 'Neutral'


def build_chan_fss_history(
    ticker: str,
    prices: pd.Series,
    volumes: pd.Series,
    spy_prices: pd.Series,
    chan_engine: ChanQuantSignalEngine,
    fss_engine
) -> pd.DataFrame:
    """
    Build historical FSS scores using REAL Chan strategies.
    
    For each day in history:
    1. Calculate mean reversion signal (Bollinger Bands)
    2. Calculate momentum signal (relative strength)
    3. Combine into composite FSS score
    4. Detect regime
    5. Calculate forward return
    
    Returns DataFrame with columns: ['regime', 'fss_score', 'forward_ret']
    """
    history_rows = []
    
    # Need at least 252 days for meaningful history
    if len(prices) < 300:  # Extra buffer for forward returns
        return pd.DataFrame()
    
    # Calculate forward returns (21-day ahead)
    forward_returns = prices.pct_change(21).shift(-21)
    
    # For each day (starting from day 200 to have enough history for regime detection)
    for i in range(200, len(prices) - 21):  # -21 to ensure forward return exists
        date = prices.index[i]
        price_window = prices.iloc[:i+1]  # Prices up to this date
        
        if len(price_window) < 20:
            continue
        
        # 1. Calculate Mean Reversion Signal (Bollinger Bands)
        try:
            mr_signal = chan_engine.calculate_mean_reversion_signal(
                symbol=ticker,
                prices=price_window,
                lookback_window=20,
                reversion_horizon=10
            )
            # Convert reversion probability to score (0-100)
            # High reversion prob when oversold = high buy score
            mr_score = mr_signal.reversion_probability * 100.0
        except Exception:
            mr_score = 50.0  # Neutral if calculation fails
        
        # 2. Calculate Momentum Signal (Relative Strength)
        try:
            # Get SPY prices up to this date
            spy_window = spy_prices.reindex(price_window.index).ffill()
            if len(spy_window) < 60:
                mom_score = 50.0
            else:
                mom_signal = chan_engine.calculate_momentum_signal(
                    symbol=ticker,
                    prices=price_window,
                    spy=spy_window,
                    lookback_days=60
                )
                # Convert timing confidence to score (0-100)
                mom_score = mom_signal.timing_confidence * 100.0
        except Exception:
            mom_score = 50.0
        
        # 3. Composite FSS Score (equal weight for now)
        fss_score = (mr_score + mom_score) / 2.0
        
        # 4. Detect Regime
        spy_window_for_regime = spy_prices.iloc[:i+1]
        regime = detect_regime(spy_window_for_regime)
        
        # 5. Forward Return
        forward_ret = forward_returns.iloc[i]
        
        if pd.notna(forward_ret) and pd.notna(fss_score):
            history_rows.append({
                'regime': regime,
                'fss_score': float(fss_score),
                'forward_ret': float(forward_ret)
            })
    
    if len(history_rows) < 20:
        return pd.DataFrame()
    
    return pd.DataFrame(history_rows)


def calculate_robustness_from_history(history_df: pd.DataFrame, fss_engine) -> float:
    """Calculate robustness using internal method (handles single-regime case better)."""
    if history_df.empty or len(history_df) < 20:
        return 0.5
    
    # Check if we have at least 2 regimes
    unique_regimes = history_df['regime'].nunique()
    
    if unique_regimes < 2:
        # Single regime case: Calculate time-based robustness instead
        # If signal has been consistently predictive in this regime, that's still valuable
        if len(history_df) >= 60:
            # Calculate IC (correlation) between FSS and forward returns
            ic = fss_engine._safe_corr(
                pd.Series(history_df['fss_score'].values),
                pd.Series(history_df['forward_ret'].values),
                method='spearman'
            )
            # Map IC to robustness (0-1)
            # IC > 0.1 = good, IC > 0.2 = excellent
            if ic > 0:
                robustness = min(0.7 + (ic * 1.5), 1.0)  # Cap at 1.0
            else:
                robustness = 0.3  # Negative IC = not robust
        else:
            robustness = 0.5  # Insufficient data
    else:
        # Multiple regimes: Use standard calculation
        robustness = fss_engine._calculate_regime_robustness_from_history(history_df)
    
    return float(np.clip(robustness, 0.0, 1.0))


def run_nightly_scan():
    """Run the complete nightly scan with REAL Chan strategies."""
    print("\n" + "="*80)
    print("PRODUCTION NIGHTLY SCAN - REAL CHAN STRATEGIES")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Capital: ${CAPITAL:,.0f}")
    print(f"🔍 Scanning {len(UNIVERSE)} tickers")
    print(f"\n⚙️  Gating Rules:")
    print(f"   Min Robustness: {GATING_RULES['MIN_ROBUSTNESS']}")
    print(f"   Min SSR: {GATING_RULES['MIN_SSR']}")
    print(f"   Min History: {GATING_RULES['MIN_HISTORY']} days")
    print(f"   Forbidden Regimes: {', '.join(GATING_RULES['FORBIDDEN_REGIMES'])}")
    
    # Initialize engines
    fss_engine = get_fss_engine()
    chan_engine = ChanQuantSignalEngine()
    allocator = get_chan_portfolio_allocator()
    
    # Fetch SPY for regime detection and relative strength
    print(f"\n📊 Fetching SPY data...")
    spy_data = yf.download('SPY', period="2y", progress=False, auto_adjust=True)
    if spy_data.empty:
        print("❌ Failed to fetch SPY data")
        return
    
    # Handle MultiIndex
    if isinstance(spy_data.columns, pd.MultiIndex):
        try:
            spy_data = spy_data.xs('SPY', axis=1, level=1)
        except:
            spy_data.columns = spy_data.columns.droplevel(1)
    
    spy_prices = spy_data['Close']
    market_regime = detect_regime(spy_prices)
    print(f"   Market Regime: {market_regime}")
    
    if market_regime in GATING_RULES['FORBIDDEN_REGIMES']:
        print(f"\n🛑 MARKET REGIME FORBIDDEN: {market_regime}")
        log_decision({
            "scan_status": "ABORTED",
            "reason": f"Forbidden market regime: {market_regime}"
        })
        return
    
    # Track valid signals
    valid_signals = {}
    robustness_scores = {}
    ssr_scores = {}
    fss_scores_dict = {}
    market_data = {}
    current_prices = {}
    volatilities = {}
    
    print(f"\n🔍 Scanning Universe with REAL Chan Strategies...")
    
    # 1. SCANNING PHASE
    for ticker in UNIVERSE:
        print(f"   Scanning {ticker}...", end=" ", flush=True)
        
        try:
            # Fetch data (2 years for regime diversity)
            stock_data = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if stock_data.empty or len(stock_data) < GATING_RULES['MIN_HISTORY']:
                print("SKIP (Insufficient data)")
                log_decision({
                    "symbol": ticker,
                    "decision": "SKIP",
                    "reason": "Insufficient historical data",
                    "metrics": {}
                })
                continue
            
            # Handle MultiIndex
            if isinstance(stock_data.columns, pd.MultiIndex):
                try:
                    stock_data = stock_data.xs(ticker, axis=1, level=1)
                except:
                    stock_data.columns = stock_data.columns.droplevel(1)
            
            prices = stock_data['Close']
            volumes = stock_data['Volume']
            current_price = float(prices.iloc[-1])
            
            # Build REAL Chan FSS history
            history_df = build_chan_fss_history(
                ticker=ticker,
                prices=prices,
                volumes=volumes,
                spy_prices=spy_prices,
                chan_engine=chan_engine,
                fss_engine=fss_engine
            )
            
            if history_df.empty:
                print("SKIP (Could not build history)")
                log_decision({
                    "symbol": ticker,
                    "decision": "SKIP",
                    "reason": "Could not build Chan FSS history",
                    "metrics": {}
                })
                continue
            
            # Calculate robustness from REAL history
            robustness = calculate_robustness_from_history(history_df, fss_engine)
            
            # Calculate SSR from history
            ssr = fss_engine._calculate_signal_stability_rating_from_history(
                history_df[['fss_score', 'forward_ret']]
            )
            
            # Current FSS score (latest from history)
            current_fss = history_df['fss_score'].iloc[-1]
            current_regime = history_df['regime'].iloc[-1]
            
            # Calculate Kelly fraction
            ticker_returns = prices.pct_change().dropna()
            if len(ticker_returns) >= 20:
                try:
                    kelly_result = chan_engine.calculate_kelly_position_size(
                        symbol=ticker,
                        historical_returns=ticker_returns
                    )
                    kelly_fraction = kelly_result.recommended_fraction
                except:
                    kelly_fraction = min(0.15, current_fss / 100.0 * 0.2)
            else:
                kelly_fraction = min(0.15, current_fss / 100.0 * 0.2)
            
            # Calculate volatility
            if len(ticker_returns) > 20:
                volatility = ticker_returns.std() * np.sqrt(252)
            else:
                volatility = 0.20
            
            # --- GATING LOGIC ---
            reasons = []
            passed = True
            
            if robustness < GATING_RULES['MIN_ROBUSTNESS']:
                reasons.append(f"Low Robustness ({robustness:.3f} < {GATING_RULES['MIN_ROBUSTNESS']})")
                passed = False
            
            if ssr < GATING_RULES['MIN_SSR']:
                reasons.append(f"Low SSR ({ssr:.3f} < {GATING_RULES['MIN_SSR']})")
                passed = False
            
            if current_regime in GATING_RULES['FORBIDDEN_REGIMES']:
                reasons.append(f"Forbidden Regime ({current_regime})")
                passed = False
            
            if kelly_fraction <= 0:
                reasons.append(f"Negative/Zero Kelly ({kelly_fraction:.4f})")
                passed = False
            
            if passed:
                print(f"✅ PASS (Rob: {robustness:.3f}, SSR: {ssr:.3f}, FSS: {current_fss:.1f})")
                
                valid_signals[ticker] = kelly_fraction
                robustness_scores[ticker] = robustness
                ssr_scores[ticker] = ssr
                fss_scores_dict[ticker] = current_fss
                market_data[ticker] = ticker_returns
                current_prices[ticker] = current_price
                volatilities[ticker] = volatility
                
                log_decision({
                    "symbol": ticker,
                    "decision": "PASS",
                    "reason": "Passed all gating rules",
                    "metrics": {
                        "fss_score": float(current_fss),
                        "regime_robustness": float(robustness),
                        "ssr": float(ssr),
                        "kelly_fraction": float(kelly_fraction),
                        "regime": current_regime,
                        "volatility": float(volatility)
                    }
                })
            else:
                print(f"❌ FAIL: {', '.join(reasons)}")
                log_decision({
                    "symbol": ticker,
                    "decision": "SKIP",
                    "reason": "; ".join(reasons),
                    "metrics": {
                        "fss_score": float(current_fss),
                        "regime_robustness": float(robustness),
                        "ssr": float(ssr),
                        "kelly_fraction": float(kelly_fraction),
                        "regime": current_regime
                    }
                })
        
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            log_decision({
                "symbol": ticker,
                "decision": "ERROR",
                "reason": f"Exception: {str(e)}",
                "error_trace": traceback.format_exc(),
                "metrics": {}
            })
            continue
    
    print(f"\n✅ Scan complete: {len(valid_signals)} tickers passed gating")
    
    if not valid_signals:
        print("\n❌ No valid signals found. No orders generated.")
        log_decision({
            "scan_status": "COMPLETE",
            "orders_generated": 0,
            "reason": "No tickers passed gating rules"
        })
        return
    
    # 2. ALLOCATION PHASE
    print(f"\n💼 Running Chan Portfolio Allocator...")
    
    try:
        returns_matrix = pd.DataFrame(market_data).dropna()
        
        if len(returns_matrix) < 60:
            print("❌ Insufficient data for portfolio allocation")
            return
        
        allocation_result = allocator.allocate_portfolio(
            tickers=list(valid_signals.keys()),
            kelly_fractions=valid_signals,
            fss_scores=fss_scores_dict,
            fss_robustness=robustness_scores,
            returns_matrix=returns_matrix,
            volatilities=volatilities,
            method="kelly_constrained"
        )
        
        weights = allocation_result.weights
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        top_positions = sorted_weights[:MAX_POSITIONS]
        
        total_weight = sum(w for _, w in top_positions)
        if total_weight > 0:
            final_weights = {ticker: weight / total_weight for ticker, weight in top_positions}
        else:
            print("❌ Portfolio allocation failed (zero weights)")
            return
        
        print(f"✅ Allocated {len(final_weights)} positions")
        
    except Exception as e:
        print(f"❌ Allocation error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. ORDER GENERATION
    print(f"\n📝 Generating Orders...")
    orders = []
    
    for ticker, weight in sorted(final_weights.items(), key=lambda x: x[1], reverse=True):
        if weight < 0.01:
            continue
        
        current_price = current_prices.get(ticker, 0.0)
        if current_price == 0:
            continue
        
        dollar_amount = CAPITAL * weight
        shares = int(dollar_amount / current_price)
        
        if shares == 0:
            continue
        
        limit_price = round(current_price * 1.005, 2)
        
        order = {
            "Symbol": ticker,
            "Action": "BUY",
            "Quantity": shares,
            "Limit_Price": limit_price,
            "Weight_Pct": round(weight * 100, 2),  # Store as percentage (16.93) for CSV readability
            "Robustness": round(robustness_scores[ticker], 3),
            "SSR": round(ssr_scores[ticker], 3),
            "FSS_Score": round(fss_scores_dict[ticker], 1),
            "Kelly_Fraction": round(valid_signals[ticker], 4),
            "Current_Price": round(current_price, 2),
            "Strategy": "Chan_MeanRev_Momentum"
        }
        
        orders.append(order)
        
        log_decision({
            "symbol": ticker,
            "decision": "BUY",
            "reason": "Allocated by portfolio allocator",
            "metrics": {
                "fss_score": float(fss_scores_dict[ticker]),
                "regime_robustness": float(robustness_scores[ticker]),
                "ssr": float(ssr_scores[ticker]),
                "kelly_fraction": float(valid_signals[ticker]),
                "allocated_weight": float(weight)
            },
            "order_details": {
                "action": "BUY",
                "quantity": shares,
                "limit_price": limit_price,
                "dollar_amount": round(dollar_amount, 2)
            }
        })
    
    # Write orders CSV
    if orders:
        with open(ORDERS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=orders[0].keys())
            writer.writeheader()
            writer.writerows(orders)
        
        print(f"✅ Generated {len(orders)} orders in {ORDERS_FILE}")
        
        print("\n" + "="*80)
        print("ORDERS SUMMARY")
        print("="*80)
        print(f"\n{'Symbol':<8} {'Shares':<8} {'Weight':<10} {'Robust':<8} {'SSR':<8} {'FSS':<8}")
        print("-" * 80)
        
        for order in orders:
            # Weight_Pct is already a percentage (16.93), so divide by 100 for format specifier
            weight_decimal = float(order['Weight_Pct']) / 100.0
            print(f"{order['Symbol']:<8} {order['Quantity']:>7} {weight_decimal:>9.2%} "
                  f"{order['Robustness']:>7} {order['SSR']:>7} {order['FSS_Score']:>7}")
        
        log_decision({
            "scan_status": "COMPLETE",
            "orders_generated": len(orders),
            "orders_file": ORDERS_FILE,
            "market_regime": market_regime
        })
    else:
        print("❌ No orders generated")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    Path(LOG_FILE).touch(exist_ok=True)
    run_nightly_scan()

