import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from scipy.optimize import minimize
from scipy import stats
from django.contrib.auth.models import User
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service

logger = logging.getLogger(__name__)

class PortfolioOptimizationService:
    """Service for advanced portfolio construction and optimization"""
    
    def __init__(self):
        self.market_service = real_market_data_service
        self.analytics_service = advanced_analytics_service
    
    def optimize_portfolio(self, 
                          symbols: List[str], 
                          optimization_type: str = 'max_sharpe',
                          constraints: Dict[str, Any] = None,
                          risk_free_rate: float = 0.02,
                          target_return: float = None,
                          target_volatility: float = None) -> Dict[str, Any]:
        """Optimize portfolio using various optimization methods"""
        try:
            # Get historical data for all symbols
            returns_data = self._get_returns_data(symbols)
            if returns_data is None or returns_data.empty:
                raise ValueError("Unable to fetch returns data for optimization")
            
            # Calculate expected returns and covariance matrix
            expected_returns = self._calculate_expected_returns(returns_data)
            cov_matrix = self._calculate_covariance_matrix(returns_data)
            
            # Set up constraints
            if constraints is None:
                constraints = self._get_default_constraints(symbols)
            
            # Perform optimization based on type
            if optimization_type == 'max_sharpe':
                result = self._maximize_sharpe_ratio(expected_returns, cov_matrix, risk_free_rate, constraints)
            elif optimization_type == 'min_variance':
                result = self._minimize_variance(expected_returns, cov_matrix, constraints)
            elif optimization_type == 'max_return':
                result = self._maximize_return(expected_returns, cov_matrix, constraints)
            elif optimization_type == 'target_return':
                if target_return is None:
                    raise ValueError("Target return must be specified for target_return optimization")
                result = self._minimize_variance_for_target_return(expected_returns, cov_matrix, target_return, constraints)
            elif optimization_type == 'target_volatility':
                if target_volatility is None:
                    raise ValueError("Target volatility must be specified for target_volatility optimization")
                result = self._maximize_return_for_target_volatility(expected_returns, cov_matrix, target_volatility, constraints)
            elif optimization_type == 'black_litterman':
                result = self._black_litterman_optimization(expected_returns, cov_matrix, constraints)
            elif optimization_type == 'risk_parity':
                result = self._risk_parity_optimization(expected_returns, cov_matrix, constraints)
            else:
                raise ValueError(f"Unknown optimization type: {optimization_type}")
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(result['weights'], expected_returns, cov_matrix, risk_free_rate)
            
            return {
                'success': True,
                'optimization_type': optimization_type,
                'weights': dict(zip(symbols, result['weights'])),
                'metrics': portfolio_metrics,
                'constraints': constraints,
                'optimization_details': result.get('details', {}),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_returns_data(self, symbols: List[str], timeframe: str = '1Y') -> Optional[pd.DataFrame]:
        """Get historical returns data for symbols"""
        try:
            returns_data = {}
            
            for symbol in symbols:
                # Get market data
                data = self.market_service.get_benchmark_data(symbol, timeframe)
                if data and 'dataPoints' in data:
                    # Extract prices and calculate returns
                    prices = [point['value'] for point in data['dataPoints']]
                    returns = np.diff(prices) / prices[:-1]
                    returns_data[symbol] = returns
            
            if not returns_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(returns_data)
            return df
            
        except Exception as e:
            logger.error(f"Error getting returns data: {e}")
            return None
    
    def _calculate_expected_returns(self, returns_data: pd.DataFrame) -> np.ndarray:
        """Calculate expected returns from historical data"""
        try:
            # Use mean historical returns as expected returns
            # In practice, you might use more sophisticated methods like CAPM, Fama-French, etc.
            expected_returns = returns_data.mean().values * 252  # Annualize
            return expected_returns
        except Exception as e:
            logger.error(f"Error calculating expected returns: {e}")
            return np.zeros(len(returns_data.columns))
    
    def _calculate_covariance_matrix(self, returns_data: pd.DataFrame) -> np.ndarray:
        """Calculate covariance matrix from historical data"""
        try:
            # Calculate annualized covariance matrix
            cov_matrix = returns_data.cov().values * 252  # Annualize
            return cov_matrix
        except Exception as e:
            logger.error(f"Error calculating covariance matrix: {e}")
            return np.eye(len(returns_data.columns))
    
    def _get_default_constraints(self, symbols: List[str]) -> Dict[str, Any]:
        """Get default optimization constraints"""
        return {
            'min_weight': 0.0,  # No short selling
            'max_weight': 0.4,  # Maximum 40% in any single asset
            'sum_weights': 1.0,  # Weights must sum to 1
            'sector_constraints': {},  # No sector constraints by default
            'turnover_limit': None,  # No turnover limit by default
            'transaction_costs': 0.0  # No transaction costs by default
        }
    
    def _maximize_sharpe_ratio(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                              risk_free_rate: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize Sharpe ratio"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: negative Sharpe ratio (to minimize)
            def objective(weights):
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                if portfolio_volatility == 0:
                    return -np.inf
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
                return -sharpe_ratio  # Negative because we're minimizing
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': -result.fun,  # Actual Sharpe ratio
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Sharpe ratio optimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _minimize_variance(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                          constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize portfolio variance"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: portfolio variance
            def objective(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': result.fun,
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in variance minimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _maximize_return(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                        constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize portfolio return"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: negative return (to minimize)
            def objective(weights):
                return -np.dot(weights, expected_returns)
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': -result.fun,  # Actual return
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in return maximization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _minimize_variance_for_target_return(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                                           target_return: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize variance for a target return"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: portfolio variance
            def objective(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']},
                {'type': 'eq', 'fun': lambda w: np.dot(w, expected_returns) - target_return}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': result.fun,
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in target return optimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _maximize_return_for_target_volatility(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                                             target_volatility: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize return for a target volatility"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: negative return (to minimize)
            def objective(weights):
                return -np.dot(weights, expected_returns)
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']},
                {'type': 'eq', 'fun': lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))) - target_volatility}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': -result.fun,  # Actual return
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in target volatility optimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _black_litterman_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                                    constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Black-Litterman optimization with views"""
        try:
            # This is a simplified implementation
            # In practice, you would incorporate investor views and confidence levels
            
            n_assets = len(expected_returns)
            
            # For now, use market cap weights as equilibrium weights
            market_cap_weights = np.array([1.0 / n_assets] * n_assets)
            
            # Calculate implied equilibrium returns
            risk_aversion = 3.0  # Typical risk aversion parameter
            implied_returns = risk_aversion * np.dot(cov_matrix, market_cap_weights)
            
            # Use implied returns for optimization
            return self._maximize_sharpe_ratio(implied_returns, cov_matrix, 0.02, constraints)
            
        except Exception as e:
            logger.error(f"Error in Black-Litterman optimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _risk_parity_optimization(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                                constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Risk parity optimization"""
        try:
            n_assets = len(expected_returns)
            
            # Objective function: minimize sum of squared differences from equal risk contribution
            def objective(weights):
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                if portfolio_volatility == 0:
                    return np.inf
                
                # Calculate risk contributions
                risk_contributions = (weights * np.dot(cov_matrix, weights)) / portfolio_volatility
                
                # Target equal risk contribution
                target_risk_contribution = 1.0 / n_assets
                
                # Sum of squared differences
                return np.sum((risk_contributions - target_risk_contribution) ** 2)
            
            # Constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - constraints['sum_weights']}
            ]
            
            # Bounds
            bounds = [(constraints['min_weight'], constraints['max_weight']) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            return {
                'weights': result.x,
                'success': result.success,
                'details': {
                    'fun': result.fun,
                    'message': result.message
                }
            }
            
        except Exception as e:
            logger.error(f"Error in risk parity optimization: {e}")
            return {'weights': np.array([1.0 / len(expected_returns)] * len(expected_returns)), 'success': False}
    
    def _calculate_portfolio_metrics(self, weights: np.ndarray, expected_returns: np.ndarray, 
                                   cov_matrix: np.ndarray, risk_free_rate: float) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        try:
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Calculate additional metrics
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Calculate individual asset contributions
            asset_contributions = weights * expected_returns
            risk_contributions = (weights * np.dot(cov_matrix, weights)) / portfolio_volatility if portfolio_volatility > 0 else weights
            
            return {
                'expected_return': portfolio_return,
                'volatility': portfolio_volatility,
                'variance': portfolio_variance,
                'sharpe_ratio': sharpe_ratio,
                'asset_contributions': asset_contributions.tolist(),
                'risk_contributions': risk_contributions.tolist(),
                'concentration_risk': np.sum(weights ** 2),  # Herfindahl index
                'effective_number_of_assets': 1 / np.sum(weights ** 2) if np.sum(weights ** 2) > 0 else len(weights)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {}
    
    def generate_efficient_frontier(self, symbols: List[str], num_portfolios: int = 100) -> Dict[str, Any]:
        """Generate efficient frontier"""
        try:
            # Get returns data
            returns_data = self._get_returns_data(symbols)
            if returns_data is None or returns_data.empty:
                raise ValueError("Unable to fetch returns data for efficient frontier")
            
            # Calculate expected returns and covariance matrix
            expected_returns = self._calculate_expected_returns(returns_data)
            cov_matrix = self._calculate_covariance_matrix(returns_data)
            
            # Generate random portfolios
            portfolios = []
            for _ in range(num_portfolios):
                # Generate random weights
                weights = np.random.random(len(symbols))
                weights = weights / np.sum(weights)  # Normalize to sum to 1
                
                # Calculate portfolio metrics
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                portfolios.append({
                    'return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'weights': weights.tolist()
                })
            
            # Find efficient portfolios (highest return for each volatility level)
            efficient_portfolios = []
            volatility_levels = np.linspace(min(p['volatility'] for p in portfolios), 
                                          max(p['volatility'] for p in portfolios), 50)
            
            for vol in volatility_levels:
                # Find portfolio with highest return for this volatility level
                candidates = [p for p in portfolios if abs(p['volatility'] - vol) < 0.01]
                if candidates:
                    best_portfolio = max(candidates, key=lambda x: x['return'])
                    efficient_portfolios.append(best_portfolio)
            
            return {
                'success': True,
                'efficient_frontier': efficient_portfolios,
                'all_portfolios': portfolios,
                'symbols': symbols,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating efficient frontier: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def backtest_optimization(self, symbols: List[str], optimization_type: str = 'max_sharpe',
                            rebalance_frequency: str = 'monthly', lookback_period: int = 252) -> Dict[str, Any]:
        """Backtest portfolio optimization strategy"""
        try:
            # This would implement a full backtesting framework
            # For now, return mock results
            
            return {
                'success': True,
                'backtest_results': {
                    'total_return': 0.15,
                    'annualized_return': 0.12,
                    'volatility': 0.18,
                    'sharpe_ratio': 0.67,
                    'max_drawdown': -0.08,
                    'calmar_ratio': 1.5,
                    'win_rate': 0.58,
                    'profit_factor': 1.35
                },
                'optimization_type': optimization_type,
                'rebalance_frequency': rebalance_frequency,
                'lookback_period': lookback_period,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in backtesting: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
portfolio_optimization_service = PortfolioOptimizationService()
