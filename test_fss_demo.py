#!/usr/bin/env python3
"""
FSS v3.0 Demo Test
Tests FSS calculation with demo data to show how it works.
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def main() -> None:
    # Add backend to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

    from core.fss_engine import get_fss_engine
    from core.fss_engine import get_safety_filter

    print("\n" + "="*80)
    print("FSS v3.0 Demo Test")
    print("="*80)
    print("Creating demo market data to test FSS calculation...\n")

    # Create demo data
    n_days = 252
    dates = pd.bdate_range(end=datetime.now(), periods=n_days)
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]

    # Generate realistic price data
    np.random.seed(42)
    prices_dict = {}
    volumes_dict = {}

    for ticker in tickers:
        # Different return profiles for each stock
        if ticker == "NVDA":
            daily_ret = np.random.normal(0.0015, 0.035, n_days)  # High growth, high vol
        elif ticker == "TSLA":
            daily_ret = np.random.normal(0.0008, 0.040, n_days)  # Very high vol
        elif ticker == "AAPL":
            daily_ret = np.random.normal(0.0005, 0.020, n_days)  # Stable
        elif ticker == "MSFT":
            daily_ret = np.random.normal(0.0006, 0.022, n_days)  # Stable
        else:  # GOOGL
            daily_ret = np.random.normal(0.0007, 0.025, n_days)  # Moderate

        # Generate prices
        prices = 150 * np.exp(np.cumsum(daily_ret))
        prices_dict[ticker] = pd.Series(prices, index=dates)

        # Generate volumes
        base_volume = 50_000_000 if ticker in ["AAPL", "MSFT"] else 30_000_000
        volumes = np.random.lognormal(np.log(base_volume), 0.3, n_days)
        volumes_dict[ticker] = pd.Series(volumes, index=dates)

    prices_df = pd.DataFrame(prices_dict)
    volumes_df = pd.DataFrame(volumes_dict)

    # Create SPY benchmark
    spy_ret = np.random.normal(0.0004, 0.015, n_days)
    spy = pd.Series(400 * np.exp(np.cumsum(spy_ret)), index=dates)

    # Create VIX (optional)
    vix = pd.Series(np.random.uniform(15, 25, n_days), index=dates)

    print(f"✅ Created demo data:")
    print(f"   - {len(dates)} trading days")
    print(f"   - {len(tickers)} stocks: {', '.join(tickers)}")
    print(f"   - SPY benchmark")
    print(f"   - VIX data\n")

    # Calculate FSS
    print("📊 Calculating FSS v3.0 scores...\n")

    fss_engine = get_fss_engine()
    safety_filter = get_safety_filter()

    # Compute FSS
    fss_data = fss_engine.compute_fss_v3(
        prices=prices_df,
        volumes=volumes_df,
        spy=spy,
        vix=vix,
        fundamentals_daily=None  # No fundamentals for demo
    )

    # Detect regime
    regime_result = fss_engine.detect_market_regime(spy, vix)

    # Get latest scores
    latest_date = fss_data.index[-1]
    fss_scores = fss_data["FSS"].loc[latest_date]

    print("="*80)
    print("FSS v3.0 Results (Demo Data)")
    print("="*80)
    print(f"Market Regime: {regime_result.regime}")
    print(f"Date: {latest_date.strftime('%Y-%m-%d')}\n")

    # Display results
    results = []
    for ticker in tickers:
        fss = float(fss_scores[ticker]) if ticker in fss_scores.index else 0.0

        # Get component scores
        T = float(fss_data["T"].loc[latest_date, ticker]) if ticker in fss_data["T"].columns else 50.0
        F = float(fss_data["F"].loc[latest_date, ticker]) if ticker in fss_data["F"].columns else 50.0
        C = float(fss_data["C"].loc[latest_date, ticker]) if ticker in fss_data["C"].columns else 50.0
        R = float(fss_data["R"].loc[latest_date, ticker]) if ticker in fss_data["R"].columns else 50.0

        # Check safety
        safety_passed, safety_reason = safety_filter.check_safety(ticker, volumes_df)

        # Confidence
        confidence = fss_engine.calculate_confidence(T, F, C, R)

        results.append({
            'ticker': ticker,
            'fss': fss,
            'T': T,
            'F': F,
            'C': C,
            'R': R,
            'confidence': confidence,
            'safety': safety_passed
        })

        # Status
        if fss >= 75:
            status = "🟢 HIGH CONVICTION"
        elif fss >= 60:
            status = "🟡 WATCHLIST"
        else:
            status = "🔴 AVOID"

        print(f"{ticker}: {fss:.1f}/100 {status}")
        print(f"  ├─ Trend:        {T:.1f}/100")
        print(f"  ├─ Fundamentals: {F:.1f}/100 (demo: using default)")
        print(f"  ├─ Capital Flow: {C:.1f}/100")
        print(f"  ├─ Risk:         {R:.1f}/100")
        print(f"  ├─ Confidence:   {confidence.upper()}")
        print(f"  └─ Safety:       {'✅ Passed' if safety_passed else '❌ Failed'}")
        print()

    # Summary
    print("="*80)
    print("Summary")
    print("="*80)

    results_sorted = sorted(results, key=lambda x: x['fss'], reverse=True)
    avg_fss = sum(r['fss'] for r in results) / len(results)
    high_conviction = [r['ticker'] for r in results if r['fss'] >= 75]
    watchlist = [r['ticker'] for r in results if 60 <= r['fss'] < 75]

    print(f"Average FSS Score: {avg_fss:.1f}/100")
    print(f"High Conviction (≥75): {', '.join(high_conviction) if high_conviction else 'None'}")
    print(f"Watchlist (60-74): {', '.join(watchlist) if watchlist else 'None'}")
    print(f"\nTop Stock: {results_sorted[0]['ticker']} ({results_sorted[0]['fss']:.1f}/100)")

    print("\n" + "="*80)
    print("✅ Demo Test Complete!")
    print("="*80)
    print("\nNote: This uses demo data. Real scores will vary based on:")
    print("  - Actual market conditions")
    print("  - Real fundamental data (EPS, revenue, etc.)")
    print("  - Current market regime")
    print("  - Safety filter results\n")


if __name__ == '__main__':
    main()

