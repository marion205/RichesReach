#!/usr/bin/env python3
"""
Production Nightly Scan - REAL CHAN STRATEGIES

Final polished version using authentic Chan quantitative strategies:
- Bollinger Band Mean Reversion (20-day MA ± 2 STD)
- Relative Strength Momentum (vs SPY)
- Real robustness calculations based on actual signal performance

This is the production-ready version that replaces all mock/placeholder data.
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


def detect_regime(prices: pd.Series) -> str:
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


def calculate_robustness_from_history(history_df: pd.DataFrame, fss_engine) -> float:
    """Calculate robustness using internal method (handles single-regime case)."""
    if history_df.empty or len(history_df) < 20:
        return 0.5
    
    unique_regimes = history_df['regime'].nunique()
    
    if unique_regimes < 2:
        # Single regime case: Calculate time-based robustness
        if len(history_df) >= 60:
            ic = fss_engine._safe_corr(
                pd.Series(history_df['fss_score'].values),
                pd.Series(history_df['forward_ret'].values),
                method='spearman'
            )
            if ic > 0:
                robustness = min(0.7 + (ic * 1.5), 1.0)
            else:
                robustness = 0.3
        else:
            robustness = 0.5
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
    
    # Fetch SPY once for all tickers (efficiency)
    print(f"\n📊 Fetching SPY data...")
    spy_df = yf.download('SPY', period="2y", progress=False, auto_adjust=True)
    if spy_df.empty:
        print("❌ Failed to fetch SPY data")
        return
    
    if isinstance(spy_df.columns, pd.MultiIndex):
        try:
            spy_df = spy_df.xs('SPY', axis=1, level=1)
        except:
            spy_df.columns = spy_df.columns.droplevel(1)
    
    spy_prices = spy_df['Close']
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
            df = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if df.empty or len(df) < GATING_RULES['MIN_HISTORY']:
                print("SKIP (Insufficient data)")
                log_decision({
                    "symbol": ticker,
                    "decision": "SKIP",
                    "reason": "Insufficient historical data",
                    "metrics": {}
                })
                continue
            
            # Handle MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    df = df.xs(ticker, axis=1, level=1)
                except:
                    df.columns = df.columns.droplevel(1)
            
            # Standardize columns
            df = df.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
            
            # --- REAL CHAN STRATEGY CALCULATION (Vectorized) ---
            
            # A. MEAN REVERSION (Bollinger Bands %B)
            window = 20
            df['ma20'] = df['close'].rolling(window).mean()
            df['std20'] = df['close'].rolling(window).std()
            df['upper'] = df['ma20'] + 2 * df['std20']
            df['lower'] = df['ma20'] - 2 * df['std20']
            df['pct_b'] = (df['close'] - df['lower']) / (df['upper'] - df['lower']).replace(0, np.nan)
            # Score: High when oversold (low %B)
            df['mr_score'] = (1.0 - df['pct_b'].clip(0, 1)) * 100.0
            
            # B. MOMENTUM (Relative Strength vs SPY)
            aligned_spy = spy_prices.reindex(df.index).ffill()
            df['rel_strength'] = df['close'] / aligned_spy
            df['rs_mom'] = df['rel_strength'].pct_change(60)
            # Map momentum to 0-100 score
            df['mom_score'] = 50 + (df['rs_mom'] * 500).clip(-50, 50)
            
            # C. COMPOSITE FSS SCORE
            df['fss_score'] = (df['mr_score'] + df['mom_score']) / 2.0
            
            # D. REGIME DETECTION
            df['vol21'] = df['close'].pct_change().rolling(21).std() * np.sqrt(252)
            df['sma200'] = df['close'].rolling(200).mean()
            
            conditions = [
                (df['close'] > df['sma200']) & (df['vol21'] < 0.15),
                (df['close'] > df['sma200']) & (df['vol21'] >= 0.15),
                (df['close'] < df['sma200']) & (df['vol21'] >= 0.25),
                (df['close'] < df['sma200']) & (df['vol21'] < 0.25),
            ]
            choices = ['Bull Quiet', 'Bull Volatile', 'Bear Volatile', 'Bear Quiet']
            df['regime'] = np.select(conditions, choices, default='Neutral')
            
            # E. FORWARD RETURNS (for Robustness)
            df['forward_ret'] = df['close'].shift(-21).pct_change(21)
            
            # Build history DataFrame for robustness calculation
            history_df = df[['regime', 'fss_score', 'forward_ret']].dropna()
            
            if len(history_df) < 60:
                print("SKIP (Insufficient history)")
                log_decision({
                    "symbol": ticker,
                    "decision": "SKIP",
                    "reason": "Insufficient history for robustness",
                    "metrics": {}
                })
                continue
            
            # Calculate robustness from REAL history
            robustness = calculate_robustness_from_history(history_df, fss_engine)
            
            # Calculate SSR from history
            ssr = fss_engine._calculate_signal_stability_rating_from_history(
                history_df[['fss_score', 'forward_ret']]
            )
            
            # Current values
            current_fss = df['fss_score'].iloc[-1]
            current_regime = df['regime'].iloc[-1]
            current_price = float(df['close'].iloc[-1])
            current_prices[ticker] = current_price
            
            # Calculate Kelly fraction
            ticker_returns = df['close'].pct_change().dropna()
            if len(ticker_returns) >= 20:
                try:
                    kelly_result = chan_engine.calculate_kelly_position_size(
                        symbol=ticker,
                        historical_returns=ticker_returns
                    )
                    kelly_fraction = kelly_result.recommended_fraction
                except:
                    # Fallback: Map FSS to Kelly probability
                    p = 0.50 + (current_fss - 50) * 0.002
                    kelly_fraction = max(0, 2 * p - 1.0) * 0.25  # Conservative Kelly
            else:
                kelly_fraction = 0.0
            
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
            
            # Signal strength check (must be bullish)
            if current_fss < 55:
                reasons.append(f"Weak Signal ({current_fss:.1f} < 55)")
                passed = False
            
            if passed:
                print(f"✅ PASS (Rob: {robustness:.3f}, SSR: {ssr:.3f}, FSS: {current_fss:.1f})")
                
                valid_signals[ticker] = kelly_fraction
                robustness_scores[ticker] = robustness
                ssr_scores[ticker] = ssr
                fss_scores_dict[ticker] = current_fss
                market_data[ticker] = ticker_returns
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
        
        # Handle both dict and object results
        if isinstance(allocation_result, dict):
            weights = allocation_result.get('weights', {})
        else:
            weights = getattr(allocation_result, 'weights', {})
        
        # Limit to top N positions
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
        
        # Safety check: normalize if weight > 1.0 (shouldn't happen, but defensive)
        if weight > 1.0:
            weight = weight / 100.0
        
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
            "Weight_Pct": round(weight * 100, 2),  # Display as 16.93%
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
        
        print("\n📋 Summary:")
        for o in orders:
            print(f"   {o['Symbol']}: {o['Action']} {o['Quantity']} shs @ ${o['Limit_Price']} ({o['Weight_Pct']}%) [Rob: {o['Robustness']}]")
        
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
