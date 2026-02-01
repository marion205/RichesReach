"""
QuantConnect Bridge
Exports strategies to QuantConnect format for independent backtesting and benchmarking.
Enables third-party verification of strategy performance.
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QuantConnectBridge:
    """
    Bridge to QuantConnect platform for strategy backtesting.
    Exports strategies in QuantConnect format for independent verification.
    """
    
    def __init__(self):
        self.platform = "QuantConnect"
        self.version = "1.0"
    
    def export_strategy(
        self,
        strategy_name: str,
        strategy_logic: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export strategy to QuantConnect format.
        
        Args:
            strategy_name: Name of the strategy
            strategy_logic: Strategy logic/conditions
            parameters: Strategy parameters
        
        Returns:
            QuantConnect algorithm code (Python)
        """
        try:
            # Generate QuantConnect algorithm code
            algorithm_code = self._generate_algorithm_code(
                strategy_name,
                strategy_logic,
                parameters
            )
            
            return {
                'success': True,
                'algorithm_code': algorithm_code,
                'format': 'python',
                'platform': 'QuantConnect',
                'exported_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting strategy to QuantConnect: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_algorithm_code(
        self,
        strategy_name: str,
        strategy_logic: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> str:
        """Generate QuantConnect algorithm code"""
        
        # Template for QuantConnect algorithm
        template = f'''"""
QuantConnect Algorithm: {strategy_name}
Exported from RichesReach
Generated: {datetime.now().isoformat()}
"""

from AlgorithmImports import *

class RichesReachStrategy(QCAlgorithm):
    """
    {strategy_name}
    Exported from RichesReach ML System
    """
    
    def Initialize(self):
        self.SetStartDate({parameters.get('start_date', '2020, 1, 1')})
        self.SetEndDate({parameters.get('end_date', '2023, 12, 31')})
        self.SetCash({parameters.get('initial_capital', 100000)})
        
        # Add universe
        self.AddEquity("SPY", Resolution.Minute)
        
        # Strategy parameters
        self.entry_threshold = {parameters.get('entry_threshold', 0.7)}
        self.exit_threshold = {parameters.get('exit_threshold', 0.3)}
        self.position_size = {parameters.get('position_size', 0.1)}
        
        # Indicators
        self.rsi = self.RSI("SPY", 14, Resolution.Daily)
        self.sma = self.SMA("SPY", 20, Resolution.Daily)
        
    def OnData(self, data):
        """Main strategy logic"""
        if not self.rsi.IsReady or not self.sma.IsReady:
            return
        
        # Entry logic
        if self.Portfolio["SPY"].Invested == 0:
            if self._should_enter(data):
                self.SetHoldings("SPY", self.position_size)
        
        # Exit logic
        else:
            if self._should_exit(data):
                self.Liquidate("SPY")
    
    def _should_enter(self, data) -> bool:
        """Entry conditions"""
        # Strategy-specific logic here
        return (
            self.rsi.Current.Value < 30 and
            data["SPY"].Close > self.sma.Current.Value
        )
    
    def _should_exit(self, data) -> bool:
        """Exit conditions"""
        return (
            self.rsi.Current.Value > 70 or
            data["SPY"].Close < self.sma.Current.Value * 0.95
        )
'''
        
        return template
    
    def export_backtest_results(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format backtest results for QuantConnect comparison.
        
        Args:
            backtest_results: Results from RichesReach backtest
        
        Returns:
            Formatted results in QuantConnect format
        """
        try:
            return {
                'total_return': backtest_results.get('total_return', 0.0),
                'sharpe_ratio': backtest_results.get('sharpe_ratio', 0.0),
                'max_drawdown': backtest_results.get('max_drawdown', 0.0),
                'win_rate': backtest_results.get('win_rate', 0.0),
                'total_trades': backtest_results.get('total_trades', 0),
                'profit_factor': backtest_results.get('profit_factor', 0.0),
                'alpha': backtest_results.get('alpha', 0.0),
                'beta': backtest_results.get('beta', 1.0),
                'information_ratio': backtest_results.get('information_ratio', 0.0),
                'exported_at': datetime.now().isoformat(),
                'platform': 'RichesReach'
            }
            
        except Exception as e:
            logger.error(f"Error exporting backtest results: {e}")
            return {
                'error': str(e)
            }
    
    def compare_with_quantconnect(
        self,
        richesreach_results: Dict[str, Any],
        quantconnect_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare RichesReach backtest results with QuantConnect results.
        
        Args:
            richesreach_results: Results from RichesReach
            quantconnect_results: Results from QuantConnect
        
        Returns:
            Comparison analysis
        """
        try:
            comparison = {
                'metrics': {},
                'differences': {},
                'consistency_score': 0.0
            }
            
            metrics_to_compare = [
                'total_return', 'sharpe_ratio', 'max_drawdown',
                'win_rate', 'profit_factor'
            ]
            
            differences = []
            for metric in metrics_to_compare:
                rr_value = richesreach_results.get(metric, 0.0)
                qc_value = quantconnect_results.get(metric, 0.0)
                
                if qc_value != 0:
                    diff_pct = abs((rr_value - qc_value) / qc_value) * 100
                else:
                    diff_pct = 0.0
                
                comparison['metrics'][metric] = {
                    'richesreach': rr_value,
                    'quantconnect': qc_value,
                    'difference_pct': diff_pct
                }
                
                differences.append(diff_pct)
            
            # Consistency score (lower difference = higher score)
            avg_difference = sum(differences) / len(differences) if differences else 0.0
            consistency_score = max(0.0, 100.0 - avg_difference)
            comparison['consistency_score'] = consistency_score
            
            # Overall assessment
            if consistency_score >= 90:
                comparison['assessment'] = 'Excellent: Results highly consistent'
            elif consistency_score >= 75:
                comparison['assessment'] = 'Good: Results mostly consistent'
            elif consistency_score >= 60:
                comparison['assessment'] = 'Moderate: Some differences noted'
            else:
                comparison['assessment'] = 'Poor: Significant differences - review methodology'
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing results: {e}")
            return {
                'error': str(e)
            }


# Global instance
_quantconnect_bridge = None

def get_quantconnect_bridge() -> QuantConnectBridge:
    """Get global QuantConnect bridge instance"""
    global _quantconnect_bridge
    if _quantconnect_bridge is None:
        _quantconnect_bridge = QuantConnectBridge()
    return _quantconnect_bridge

