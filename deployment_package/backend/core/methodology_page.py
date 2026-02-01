"""
Methodology Page Content
Documents how RichesReach calculates signals, P&L, and performance metrics.
This is the "proof" artifact that makes our methodology indisputable.
"""
from typing import Dict, Any
from datetime import datetime


def get_methodology_content() -> Dict[str, Any]:
    """
    Get methodology documentation for transparency page.
    This explains how we calculate everything so skeptics can verify.
    """
    return {
        'last_updated': datetime.now().isoformat(),
        'version': '1.0',
        'sections': {
            'overview': {
                'title': 'Methodology Overview',
                'content': """
RichesReach uses a hybrid LSTM + XGBoost machine learning system to generate 
trading signals. All performance metrics are calculated net of costs (commissions, 
slippage, spreads) to reflect realistic profitability.
                """.strip()
            },
            'signal_generation': {
                'title': 'Signal Generation',
                'content': """
**Model Architecture:**
- LSTM Feature Extractor: Processes 60 bars of 1-minute OHLCV data
- XGBoost Classifier: Combines LSTM features with alternative data (options flow, 
  earnings, insider activity, social sentiment)
- Output: BUY/SELL/ABSTAIN decision with confidence score (0-1)

**Signal Criteria:**
- Only signals with confidence ≥ 0.78 are executed
- Regime-aware filtering (signals adapt to market conditions)
- Abstention policy: Model can choose not to trade if conditions aren't favorable

**Signal ID:**
- Each signal has an immutable ID: `RR-{timestamp}-{symbol}-{hash}`
- Signal IDs never change, even if model is updated
- Allows tracking signal revisions and model updates
                """.strip()
            },
            'pnl_calculation': {
                'title': 'P&L Calculation (Net of Costs)',
                'content': """
**Entry Price:**
- For market orders: Actual fill price (includes slippage)
- For limit orders: Limit price if filled, otherwise not counted
- Slippage model: 0.05% (5 basis points) for liquid stocks, 0.1% for less liquid

**Exit Price:**
- Actual exit fill price (includes slippage)
- Exit can be: target hit, stop loss, manual close, or time-based

**Costs Included:**
- Commission: $0.00 (commission-free broker) or actual commission
- Spread: Bid-ask spread at time of execution
- Slippage: 0.05% for liquid stocks, 0.1% for less liquid
- Total friction: Spread + Slippage + Commission

**Net P&L Formula:**
```
Net P&L = (Exit Price - Entry Price) × Shares - Total Friction
Net P&L % = Net P&L / (Entry Price × Shares)
```

**Why Net-of-Costs Matters:**
Many platforms show gross returns, which don't reflect real-world profitability. 
RichesReach shows net returns so you see actual performance after all costs.
                """.strip()
            },
            'time_zones': {
                'title': 'Time Zone Handling',
                'content': """
**All timestamps are in UTC:**
- Entry/exit timestamps: UTC
- Signal generation time: UTC
- Dashboard displays: Converted to user's local timezone

**Market Hours:**
- Signals generated during market hours (9:30 AM - 4:00 PM ET)
- Pre-market and after-hours signals are marked separately
- Paper trading uses market hours only

**Revision Policy:**
- Signal IDs are immutable (never change)
- If model is updated, new signals use new model version
- Historical signals retain their original predictions
- Model version is tracked in signal metadata
                """.strip()
            },
            'performance_metrics': {
                'title': 'Performance Metrics',
                'content': """
**Win Rate:**
- Calculated as: (Winning Trades) / (Total Closed Trades)
- Win = Net P&L > 0 after all costs
- Only closed trades are counted (open positions excluded)

**Profit Factor:**
- Calculated as: (Total Wins) / (Total Losses)
- Profit Factor > 1.0 = Profitable
- Profit Factor > 2.0 = Strong performance

**Sharpe Ratio:**
- Annualized Sharpe: (Mean Return / Std Dev) × √252
- Risk-free rate: 0% (for simplicity)
- Higher Sharpe = Better risk-adjusted returns

**Max Drawdown:**
- Largest peak-to-trough decline
- Calculated from cumulative P&L curve
- Shows worst-case scenario

**All metrics are calculated net of costs.**
                """.strip()
            },
            'live_vs_paper': {
                'title': 'Live vs Paper Trading',
                'content': """
**Paper Trading:**
- All signals start in paper trading mode
- Uses real market data but simulated execution
- Slippage and costs are modeled (not actual)
- Marked with "PAPER" badge

**Live Trading:**
- Only after paper trading validation period
- Uses actual broker execution
- Real slippage and costs
- Marked with "LIVE" badge

**Separation:**
- Live and paper results are NEVER mixed
- Dashboard can filter by trading mode
- Performance metrics calculated separately
- This ensures credibility and prevents confusion
                """.strip()
            },
            'data_sources': {
                'title': 'Data Sources',
                'content': """
**Price Data:**
- Primary: Alpaca API (real-time and historical)
- Fallback: Polygon, yfinance
- Frequency: 1-minute bars for day trading, daily for swing trading

**Alternative Data:**
- Options Flow: Real-time unusual options activity
- Earnings: Earnings surprises and revisions
- Insider Activity: SEC Form 4 filings
- Social Sentiment: StockTwits, Reddit, X/Twitter aggregation

**Data Quality:**
- All data is validated before use
- Missing data is handled gracefully (fallback or skip)
- Data freshness is monitored (stale data alerts)
                """.strip()
            },
            'verification': {
                'title': 'Independent Verification',
                'content': """
**CSV Export:**
- Download last 50-100 signals as CSV
- Includes all fields: symbol, entry/exit, P&L, confidence, reasoning
- Allows independent verification and analysis

**Signal IDs:**
- Each signal has immutable ID
- Can be shared and verified independently
- Links to individual signal pages

**QuantConnect Validation:**
- Strategies can be exported to QuantConnect
- Independent backtests can be run
- Results are publicly verifiable

**We encourage independent verification.**
                """.strip()
            }
        }
    }


def get_methodology_summary() -> str:
    """Get short summary for quick reference"""
    return """
RichesReach uses hybrid LSTM+XGBoost ML to generate trading signals. 
All P&L is calculated net of costs (commissions, slippage, spreads). 
Signals have immutable IDs and can be independently verified via CSV export.
Live and paper trading results are strictly separated.
    """.strip()

