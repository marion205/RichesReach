#!/usr/bin/env python3
"""
Get Day Trading Performance Stats - See Biggest Wins
"""
import requests
import json
from typing import Dict, Optional

GRAPHQL_URL = "http://localhost:8000/graphql/"

def get_day_trading_stats(mode: str = None, period: str = "ALL_TIME") -> Optional[Dict]:
    """Get day trading performance stats from GraphQL API"""
    query = """
    query GetDayTradingStats($mode: String, $period: String!) {
      dayTradingStats(mode: $mode, period: $period) {
        mode
        period
        asOf
        winRate
        sharpeRatio
        maxDrawdown
        avgPnlPerSignal
        totalSignals
        signalsEvaluated
        totalPnlPercent
        sortinoRatio
        calmarRatio
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"mode": mode, "period": period}
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None
            return data.get("data", {}).get("dayTradingStats", [])
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Get performance stats"""
    print("\n" + "="*100)
    print("DAY TRADING PERFORMANCE STATS")
    print("="*100)
    print()
    
    for period in ["DAILY", "WEEKLY", "ALL_TIME"]:
        print(f"\n{'#'*100}")
        print(f"# {period} PERFORMANCE")
        print(f"{'#'*100}\n")
        
        stats_list = get_day_trading_stats(period=period)
        
        if not stats_list:
            print(f"⚠️  No stats available for {period}")
            continue
        
        for stats in stats_list:
            mode = stats.get('mode', 'N/A')
            win_rate = stats.get('winRate', 0)
            sharpe = stats.get('sharpeRatio')
            max_dd = stats.get('maxDrawdown')
            avg_pnl = stats.get('avgPnlPerSignal', 0)
            total_signals = stats.get('totalSignals', 0)
            total_pnl = stats.get('totalPnlPercent', 0)
            sortino = stats.get('sortinoRatio')
            calmar = stats.get('calmarRatio')
            
            print(f"Mode: {mode}")
            print(f"  • Total Signals: {total_signals}")
            print(f"  • Win Rate: {win_rate:.1f}%")
            print(f"  • Total PnL: {total_pnl:.2f}%")
            print(f"  • Avg PnL per Signal: {avg_pnl:.2f}%")
            if sharpe:
                print(f"  • Sharpe Ratio: {sharpe:.2f}")
            if sortino:
                print(f"  • Sortino Ratio: {sortino:.2f}")
            if calmar:
                print(f"  • Calmar Ratio: {calmar:.2f}")
            if max_dd:
                print(f"  • Max Drawdown: {max_dd:.2f}%")
            print()
    
    print("="*100)
    print("NOTE: If no stats shown, the algorithm may be new or performance tracking")
    print("      hasn't been evaluated yet. Signals are logged but need time to evaluate.")
    print("="*100)
    print()


if __name__ == "__main__":
    main()

