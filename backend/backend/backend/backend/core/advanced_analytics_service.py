import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from .real_market_data_service import real_market_data_service

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """Service for advanced portfolio analytics and performance metrics"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
    def calculate_comprehensive_metrics(self, portfolio_data: Dict[str, Any], benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            portfolio_returns = self._extract_returns(portfolio_data)
            benchmark_returns = self._extract_returns(benchmark_data)
            
            if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
                return self._get_default_metrics()
            
            # Align returns (same length)
            min_length = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns[-min_length:]
            benchmark_returns = benchmark_returns[-min_length:]
            
            metrics = {
                # Basic metrics
                'portfolioReturn': portfolio_data.get('totalReturnPercent', 0),
                'benchmarkReturn': benchmark_data.get('totalReturnPercent', 0),
                'excessReturn': portfolio_data.get('totalReturnPercent', 0) - benchmark_data.get('totalReturnPercent', 0),
                
                # Risk metrics
                'portfolioVolatility': portfolio_data.get('volatility', 0),
                'benchmarkVolatility': benchmark_data.get('volatility', 0),
                'trackingError': self.calculate_tracking_error(portfolio_returns, benchmark_returns),
                'maxDrawdown': portfolio_data.get('maxDrawdown', 0),
                'benchmarkMaxDrawdown': benchmark_data.get('maxDrawdown', 0),
                
                # Risk-adjusted metrics
                'sharpeRatio': portfolio_data.get('sharpeRatio', 0),
                'benchmarkSharpeRatio': benchmark_data.get('sharpeRatio', 0),
                'informationRatio': self.calculate_information_ratio(portfolio_returns, benchmark_returns),
                'sortinoRatio': self.calculate_sortino_ratio(portfolio_returns),
                'calmarRatio': self.calculate_calmar_ratio(portfolio_returns, portfolio_data.get('maxDrawdown', 0)),
                
                # Correlation and beta
                'beta': self.calculate_beta(portfolio_returns, benchmark_returns),
                'correlation': self.calculate_correlation(portfolio_returns, benchmark_returns),
                'rSquared': self.calculate_r_squared(portfolio_returns, benchmark_returns),
                
                # Advanced metrics
                'alpha': self.calculate_alpha(portfolio_returns, benchmark_returns),
                'treynorRatio': self.calculate_treynor_ratio(portfolio_returns, benchmark_returns),
                'jensenAlpha': self.calculate_jensen_alpha(portfolio_returns, benchmark_returns),
                'm2Measure': self.calculate_m2_measure(portfolio_returns, benchmark_returns),
                'm2Alpha': self.calculate_m2_alpha(portfolio_returns, benchmark_returns),
                
                # Downside risk metrics
                'downsideDeviation': self.calculate_downside_deviation(portfolio_returns),
                'upsideCapture': self.calculate_upside_capture(portfolio_returns, benchmark_returns),
                'downsideCapture': self.calculate_downside_capture(portfolio_returns, benchmark_returns),
                
                # Tail risk metrics
                'var95': self.calculate_var(portfolio_returns, 0.95),
                'var99': self.calculate_var(portfolio_returns, 0.99),
                'cvar95': self.calculate_cvar(portfolio_returns, 0.95),
                'cvar99': self.calculate_cvar(portfolio_returns, 0.99),
                
                # Skewness and kurtosis
                'skewness': self.calculate_skewness(portfolio_returns),
                'kurtosis': self.calculate_kurtosis(portfolio_returns),
                'excessKurtosis': self.calculate_excess_kurtosis(portfolio_returns),
                
                # Performance attribution
                'activeReturn': self.calculate_active_return(portfolio_returns, benchmark_returns),
                'activeRisk': self.calculate_active_risk(portfolio_returns, benchmark_returns),
                'activeShare': self.calculate_active_share(portfolio_returns, benchmark_returns),
                
                # Time period analysis
                'winRate': self.calculate_win_rate(portfolio_returns, benchmark_returns),
                'averageWin': self.calculate_average_win(portfolio_returns, benchmark_returns),
                'averageLoss': self.calculate_average_loss(portfolio_returns, benchmark_returns),
                'profitFactor': self.calculate_profit_factor(portfolio_returns, benchmark_returns),
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics: {e}")
            return self._get_default_metrics()
    
    def _extract_returns(self, data: Dict[str, Any]) -> List[float]:
        """Extract returns from data points"""
        data_points = data.get('dataPoints', [])
        if len(data_points) < 2:
            return []
        
        prices = [point['value'] for point in data_points]
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        return returns
    
    def calculate_beta(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate beta (systematic risk)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 1.0
        
        portfolio_returns = np.array(portfolio_returns)
        benchmark_returns = np.array(benchmark_returns)
        
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance == 0:
            return 1.0
        
        return covariance / benchmark_variance
    
    def calculate_correlation(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        return np.corrcoef(portfolio_returns, benchmark_returns)[0, 1]
    
    def calculate_r_squared(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate R-squared (coefficient of determination)"""
        correlation = self.calculate_correlation(portfolio_returns, benchmark_returns)
        return correlation ** 2
    
    def calculate_alpha(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate alpha (excess return)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        portfolio_annual_return = np.mean(portfolio_returns) * 252
        benchmark_annual_return = np.mean(benchmark_returns) * 252
        beta = self.calculate_beta(portfolio_returns, benchmark_returns)
        
        return portfolio_annual_return - (self.risk_free_rate + beta * (benchmark_annual_return - self.risk_free_rate))
    
    def calculate_tracking_error(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate tracking error (standard deviation of excess returns)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        excess_returns = np.array(portfolio_returns) - np.array(benchmark_returns)
        return np.std(excess_returns) * np.sqrt(252)  # Annualized
    
    def calculate_information_ratio(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate information ratio (excess return / tracking error)"""
        tracking_error = self.calculate_tracking_error(portfolio_returns, benchmark_returns)
        if tracking_error == 0:
            return 0.0
        
        excess_returns = np.array(portfolio_returns) - np.array(benchmark_returns)
        excess_return = np.mean(excess_returns) * 252  # Annualized
        
        return excess_return / tracking_error
    
    def calculate_sortino_ratio(self, portfolio_returns: List[float]) -> float:
        """Calculate Sortino ratio (return / downside deviation)"""
        if len(portfolio_returns) < 2:
            return 0.0
        
        downside_deviation = self.calculate_downside_deviation(portfolio_returns)
        if downside_deviation == 0:
            return 0.0
        
        excess_return = np.mean(portfolio_returns) * 252 - self.risk_free_rate
        return excess_return / downside_deviation
    
    def calculate_calmar_ratio(self, portfolio_returns: List[float], max_drawdown: float) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        if max_drawdown == 0:
            return 0.0
        
        annual_return = np.mean(portfolio_returns) * 252
        return annual_return / (max_drawdown / 100)  # Convert drawdown to decimal
    
    def calculate_treynor_ratio(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate Treynor ratio (excess return / beta)"""
        beta = self.calculate_beta(portfolio_returns, benchmark_returns)
        if beta == 0:
            return 0.0
        
        excess_return = np.mean(portfolio_returns) * 252 - self.risk_free_rate
        return excess_return / beta
    
    def calculate_jensen_alpha(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate Jensen's alpha"""
        return self.calculate_alpha(portfolio_returns, benchmark_returns)
    
    def calculate_m2_measure(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate M2 measure (risk-adjusted return)"""
        portfolio_return = np.mean(portfolio_returns) * 252
        portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
        benchmark_volatility = np.std(benchmark_returns) * np.sqrt(252)
        
        if benchmark_volatility == 0:
            return 0.0
        
        # Adjust portfolio to benchmark volatility
        adjusted_return = self.risk_free_rate + (portfolio_return - self.risk_free_rate) * (benchmark_volatility / portfolio_volatility)
        benchmark_return = np.mean(benchmark_returns) * 252
        
        return adjusted_return - benchmark_return
    
    def calculate_m2_alpha(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate M2 alpha"""
        return self.calculate_m2_measure(portfolio_returns, benchmark_returns)
    
    def calculate_downside_deviation(self, portfolio_returns: List[float]) -> float:
        """Calculate downside deviation (volatility of negative returns)"""
        if len(portfolio_returns) < 2:
            return 0.0
        
        negative_returns = [r for r in portfolio_returns if r < 0]
        if len(negative_returns) == 0:
            return 0.0
        
        return np.std(negative_returns) * np.sqrt(252)  # Annualized
    
    def calculate_upside_capture(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate upside capture ratio"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 100.0
        
        portfolio_upside = [r for r in portfolio_returns if r > 0]
        benchmark_upside = [r for r in benchmark_returns if r > 0]
        
        if len(portfolio_upside) == 0 or len(benchmark_upside) == 0:
            return 100.0
        
        portfolio_upside_avg = np.mean(portfolio_upside)
        benchmark_upside_avg = np.mean(benchmark_upside)
        
        if benchmark_upside_avg == 0:
            return 100.0
        
        return (portfolio_upside_avg / benchmark_upside_avg) * 100
    
    def calculate_downside_capture(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate downside capture ratio"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 100.0
        
        portfolio_downside = [r for r in portfolio_returns if r < 0]
        benchmark_downside = [r for r in benchmark_returns if r < 0]
        
        if len(portfolio_downside) == 0 or len(benchmark_downside) == 0:
            return 100.0
        
        portfolio_downside_avg = np.mean(portfolio_downside)
        benchmark_downside_avg = np.mean(benchmark_downside)
        
        if benchmark_downside_avg == 0:
            return 100.0
        
        return (portfolio_downside_avg / benchmark_downside_avg) * 100
    
    def calculate_var(self, portfolio_returns: List[float], confidence_level: float) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(portfolio_returns) < 2:
            return 0.0
        
        return np.percentile(portfolio_returns, (1 - confidence_level) * 100) * 100
    
    def calculate_cvar(self, portfolio_returns: List[float], confidence_level: float) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        if len(portfolio_returns) < 2:
            return 0.0
        
        var_threshold = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        tail_returns = [r for r in portfolio_returns if r <= var_threshold]
        
        if len(tail_returns) == 0:
            return 0.0
        
        return np.mean(tail_returns) * 100
    
    def calculate_skewness(self, portfolio_returns: List[float]) -> float:
        """Calculate skewness (third moment)"""
        if len(portfolio_returns) < 3:
            return 0.0
        
        return stats.skew(portfolio_returns)
    
    def calculate_kurtosis(self, portfolio_returns: List[float]) -> float:
        """Calculate kurtosis (fourth moment)"""
        if len(portfolio_returns) < 4:
            return 0.0
        
        return stats.kurtosis(portfolio_returns)
    
    def calculate_excess_kurtosis(self, portfolio_returns: List[float]) -> float:
        """Calculate excess kurtosis (kurtosis - 3)"""
        return self.calculate_kurtosis(portfolio_returns) - 3
    
    def calculate_active_return(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate active return (portfolio return - benchmark return)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        portfolio_return = np.mean(portfolio_returns) * 252
        benchmark_return = np.mean(benchmark_returns) * 252
        
        return portfolio_return - benchmark_return
    
    def calculate_active_risk(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate active risk (tracking error)"""
        return self.calculate_tracking_error(portfolio_returns, benchmark_returns)
    
    def calculate_active_share(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate active share (percentage of portfolio different from benchmark)"""
        # This is a simplified version - in practice, you'd need actual holdings data
        return self.calculate_tracking_error(portfolio_returns, benchmark_returns) / np.std(benchmark_returns) * 100
    
    def calculate_win_rate(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate win rate (percentage of periods where portfolio outperforms benchmark)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 50.0
        
        wins = sum(1 for p, b in zip(portfolio_returns, benchmark_returns) if p > b)
        return (wins / len(portfolio_returns)) * 100
    
    def calculate_average_win(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate average win (average outperformance when portfolio wins)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        wins = [p - b for p, b in zip(portfolio_returns, benchmark_returns) if p > b]
        return np.mean(wins) * 100 if wins else 0.0
    
    def calculate_average_loss(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate average loss (average underperformance when portfolio loses)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        losses = [p - b for p, b in zip(portfolio_returns, benchmark_returns) if p < b]
        return np.mean(losses) * 100 if losses else 0.0
    
    def calculate_profit_factor(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 1.0
        
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        gross_profit = sum(r for r in excess_returns if r > 0)
        gross_loss = abs(sum(r for r in excess_returns if r < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 1.0
        
        return gross_profit / gross_loss
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default metrics when calculation fails"""
        return {
            'portfolioReturn': 0,
            'benchmarkReturn': 0,
            'excessReturn': 0,
            'portfolioVolatility': 0,
            'benchmarkVolatility': 0,
            'trackingError': 0,
            'maxDrawdown': 0,
            'benchmarkMaxDrawdown': 0,
            'sharpeRatio': 0,
            'benchmarkSharpeRatio': 0,
            'informationRatio': 0,
            'sortinoRatio': 0,
            'calmarRatio': 0,
            'beta': 1.0,
            'correlation': 0,
            'rSquared': 0,
            'alpha': 0,
            'treynorRatio': 0,
            'jensenAlpha': 0,
            'm2Measure': 0,
            'm2Alpha': 0,
            'downsideDeviation': 0,
            'upsideCapture': 100,
            'downsideCapture': 100,
            'var95': 0,
            'var99': 0,
            'cvar95': 0,
            'cvar99': 0,
            'skewness': 0,
            'kurtosis': 0,
            'excessKurtosis': 0,
            'activeReturn': 0,
            'activeRisk': 0,
            'activeShare': 0,
            'winRate': 50,
            'averageWin': 0,
            'averageLoss': 0,
            'profitFactor': 1.0,
        }

# Global instance
advanced_analytics_service = AdvancedAnalyticsService()
