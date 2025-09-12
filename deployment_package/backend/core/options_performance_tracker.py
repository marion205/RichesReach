"""
Live Performance Tracking System for AI Options
Track real-time performance and compare against benchmarks
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np
from .ai_options_engine import AIOptionsEngine
from .ai_options_api import OptionsRecommendation

logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    """Snapshot of performance at a specific time"""
    timestamp: datetime
    symbol: str
    strategy_name: str
    current_price: float
    recommendation_price: float
    unrealized_pnl: float
    realized_pnl: float
    confidence_score: float
    risk_score: float
    days_since_recommendation: int

@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    total_recommendations: int
    winning_recommendations: int
    losing_recommendations: int
    win_rate: float
    avg_return: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    avg_confidence: float
    avg_risk_score: float

class OptionsPerformanceTracker:
    """Live performance tracking for AI Options system"""
    
    def __init__(self):
        self.ai_engine = AIOptionsEngine()
        self.tracking_data = []
        self.performance_history = []
        self.benchmark_data = {}
        
    async def start_live_tracking(self, symbols: List[str], update_interval: int = 3600):
        """Start live performance tracking"""
        logger.info(f"🚀 Starting live performance tracking for {len(symbols)} symbols")
        logger.info(f"📊 Update interval: {update_interval} seconds")
        
        while True:
            try:
                # Generate new recommendations
                new_recommendations = await self.generate_tracking_recommendations(symbols)
                
                # Update performance for existing recommendations
                await self.update_performance_tracking()
                
                # Calculate current metrics
                current_metrics = await self.calculate_current_metrics()
                
                # Log performance
                logger.info(f"📈 Current Performance: {current_metrics.win_rate:.1%} win rate, {current_metrics.avg_return:.2%} avg return")
                
                # Save snapshot
                await self.save_performance_snapshot(current_metrics)
                
                # Wait for next update
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in live tracking: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def generate_tracking_recommendations(self, symbols: List[str]) -> List[OptionsRecommendation]:
        """Generate recommendations for tracking"""
        recommendations = []
        
        for symbol in symbols:
            try:
                # Generate AI recommendation
                recs = await self.ai_engine.generate_recommendations(
                    symbol=symbol,
                    user_risk_tolerance='medium',
                    portfolio_value=10000,
                    time_horizon=30
                )
                
                if recs:
                    # Add to tracking data
                    for rec in recs:
                        self.tracking_data.append({
                            'recommendation': rec,
                            'timestamp': datetime.now(),
                            'symbol': symbol,
                            'initial_price': rec.current_price,
                            'status': 'active'
                        })
                    
                    recommendations.extend(recs)
                    
            except Exception as e:
                logger.error(f"Error generating recommendations for {symbol}: {e}")
                continue
        
        return recommendations
    
    async def update_performance_tracking(self):
        """Update performance for all active recommendations"""
        current_time = datetime.now()
        
        for item in self.tracking_data:
            if item['status'] != 'active':
                continue
            
            try:
                # Get current price
                symbol = item['symbol']
                stock = yf.Ticker(symbol)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                
                # Calculate performance
                days_since = (current_time - item['timestamp']).days
                price_change = (current_price - item['initial_price']) / item['initial_price']
                
                # Create performance snapshot
                snapshot = PerformanceSnapshot(
                    timestamp=current_time,
                    symbol=symbol,
                    strategy_name=item['recommendation'].strategy_name,
                    current_price=current_price,
                    recommendation_price=item['initial_price'],
                    unrealized_pnl=price_change * 10000,  # Assuming $10k position
                    realized_pnl=0.0,  # No realized PnL yet
                    confidence_score=item['recommendation'].confidence_score,
                    risk_score=item['recommendation'].risk_score,
                    days_since_recommendation=days_since
                )
                
                # Add to performance history
                self.performance_history.append(snapshot)
                
                # Check if recommendation should be closed
                if days_since >= 30:  # Close after 30 days
                    item['status'] = 'closed'
                    item['final_price'] = current_price
                    item['final_return'] = price_change
                
            except Exception as e:
                logger.error(f"Error updating performance for {item['symbol']}: {e}")
                continue
    
    async def calculate_current_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics"""
        if not self.performance_history:
            return PerformanceMetrics(
                total_recommendations=0,
                winning_recommendations=0,
                losing_recommendations=0,
                win_rate=0.0,
                avg_return=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                avg_confidence=0.0,
                avg_risk_score=0.0
            )
        
        # Calculate basic metrics
        total_recommendations = len(self.performance_history)
        returns = [snapshot.unrealized_pnl / 10000 for snapshot in self.performance_history]
        
        winning_recommendations = sum(1 for r in returns if r > 0)
        losing_recommendations = sum(1 for r in returns if r < 0)
        win_rate = winning_recommendations / total_recommendations if total_recommendations > 0 else 0
        
        avg_return = np.mean(returns)
        total_return = np.sum(returns)
        
        # Calculate risk metrics
        max_drawdown = self.calculate_max_drawdown(returns)
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Calculate profit factor
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]
        profit_factor = sum(positive_returns) / abs(sum(negative_returns)) if negative_returns else float('inf')
        
        # Calculate average confidence and risk scores
        avg_confidence = np.mean([snapshot.confidence_score for snapshot in self.performance_history])
        avg_risk_score = np.mean([snapshot.risk_score for snapshot in self.performance_history])
        
        return PerformanceMetrics(
            total_recommendations=total_recommendations,
            winning_recommendations=winning_recommendations,
            losing_recommendations=losing_recommendations,
            win_rate=win_rate,
            avg_return=avg_return,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            avg_confidence=avg_confidence,
            avg_risk_score=avg_risk_score
        )
    
    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns:
            return 0.0
        
        cumulative = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)
    
    async def save_performance_snapshot(self, metrics: PerformanceMetrics):
        """Save performance snapshot to file"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(metrics),
            'active_recommendations': len([item for item in self.tracking_data if item['status'] == 'active'])
        }
        
        # Append to performance log
        with open('options_performance_log.json', 'a') as f:
            f.write(json.dumps(snapshot) + '\n')
    
    async def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        metrics = await self.calculate_current_metrics()
        
        report = f"""
# AI Options System Live Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Performance Metrics
- Total Recommendations: {metrics.total_recommendations}
- Win Rate: {metrics.win_rate:.1%}
- Average Return: {metrics.avg_return:.2%}
- Total Return: {metrics.total_return:.2%}
- Max Drawdown: {metrics.max_drawdown:.2%}
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Profit Factor: {metrics.profit_factor:.2f}

## AI System Metrics
- Average Confidence: {metrics.avg_confidence:.1f}%
- Average Risk Score: {metrics.avg_risk_score:.1f}

## Active Recommendations
- Currently Tracking: {len([item for item in self.tracking_data if item['status'] == 'active'])}
- Closed Recommendations: {len([item for item in self.tracking_data if item['status'] == 'closed'])}

## Performance Analysis
"""
        
        # Add performance analysis
        if metrics.win_rate > 0.6:
            report += "✅ Strong win rate - system performing well\n"
        elif metrics.win_rate > 0.5:
            report += "⚠️ Moderate win rate - monitor performance\n"
        else:
            report += "❌ Low win rate - review strategy selection\n"
        
        if metrics.sharpe_ratio > 1.0:
            report += "✅ Excellent risk-adjusted returns\n"
        elif metrics.sharpe_ratio > 0.5:
            report += "⚠️ Moderate risk-adjusted returns\n"
        else:
            report += "❌ Poor risk-adjusted returns - review risk management\n"
        
        if metrics.max_drawdown < 0.1:
            report += "✅ Low drawdown - good risk control\n"
        elif metrics.max_drawdown < 0.2:
            report += "⚠️ Moderate drawdown - monitor risk\n"
        else:
            report += "❌ High drawdown - review risk management\n"
        
        return report
    
    async def compare_with_benchmarks(self) -> Dict[str, Any]:
        """Compare performance with market benchmarks"""
        metrics = await self.calculate_current_metrics()
        
        # Get benchmark data
        benchmark_data = await self.get_benchmark_data()
        
        comparison = {
            'our_performance': {
                'return': metrics.avg_return,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown
            },
            'benchmarks': benchmark_data,
            'outperformance': {
                'vs_sp500': metrics.avg_return - benchmark_data.get('sp500_return', 0),
                'vs_nasdaq': metrics.avg_return - benchmark_data.get('nasdaq_return', 0),
                'vs_options_etf': metrics.avg_return - benchmark_data.get('options_etf_return', 0)
            }
        }
        
        return comparison
    
    async def get_benchmark_data(self) -> Dict[str, float]:
        """Get benchmark performance data"""
        try:
            # Get S&P 500 data
            sp500 = yf.Ticker("^GSPC")
            sp500_hist = sp500.history(period="1mo")
            sp500_return = (sp500_hist['Close'].iloc[-1] / sp500_hist['Close'].iloc[0]) - 1
            
            # Get NASDAQ data
            nasdaq = yf.Ticker("^IXIC")
            nasdaq_hist = nasdaq.history(period="1mo")
            nasdaq_return = (nasdaq_hist['Close'].iloc[-1] / nasdaq_hist['Close'].iloc[0]) - 1
            
            # Get options ETF data (SPY options)
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="1mo")
            spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0]) - 1
            
            return {
                'sp500_return': sp500_return,
                'nasdaq_return': nasdaq_return,
                'options_etf_return': spy_return
            }
            
        except Exception as e:
            logger.error(f"Error getting benchmark data: {e}")
            return {
                'sp500_return': 0.0,
                'nasdaq_return': 0.0,
                'options_etf_return': 0.0
            }

# Example usage
async def main():
    """Example usage of the performance tracker"""
    tracker = OptionsPerformanceTracker()
    
    # Start tracking
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    await tracker.start_live_tracking(symbols, update_interval=3600)  # Update every hour

if __name__ == "__main__":
    asyncio.run(main())
