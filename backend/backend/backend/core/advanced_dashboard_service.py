import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth.models import User
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service
from .custom_benchmark_service import custom_benchmark_service

logger = logging.getLogger(__name__)

class AdvancedDashboardService:
    """Service for comprehensive performance metrics visualization and dashboard data"""
    
    def __init__(self):
        self.analytics_service = advanced_analytics_service
        self.market_service = real_market_data_service
        self.benchmark_service = custom_benchmark_service
    
    def get_comprehensive_dashboard_data(self, user: User, portfolio_id: str = None, timeframe: str = '1Y') -> Dict[str, Any]:
        """Get comprehensive dashboard data for advanced visualization"""
        try:
            dashboard_data = {
                'overview': self._get_overview_metrics(user, portfolio_id, timeframe),
                'performance': self._get_performance_metrics(user, portfolio_id, timeframe),
                'risk_metrics': self._get_risk_metrics(user, portfolio_id, timeframe),
                'attribution': self._get_attribution_analysis(user, portfolio_id, timeframe),
                'benchmark_comparison': self._get_benchmark_comparison(user, portfolio_id, timeframe),
                'sector_analysis': self._get_sector_analysis(user, portfolio_id, timeframe),
                'correlation_matrix': self._get_correlation_matrix(user, portfolio_id, timeframe),
                'risk_attribution': self._get_risk_attribution(user, portfolio_id, timeframe),
                'drawdown_analysis': self._get_drawdown_analysis(user, portfolio_id, timeframe),
                'volatility_analysis': self._get_volatility_analysis(user, portfolio_id, timeframe),
                'momentum_indicators': self._get_momentum_indicators(user, portfolio_id, timeframe),
                'market_regime': self._get_market_regime_analysis(user, portfolio_id, timeframe),
                'alerts': self._get_active_alerts(user, portfolio_id),
                'recommendations': self._get_recommendations(user, portfolio_id, timeframe),
                'timestamp': datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive dashboard data: {e}")
            return self._get_default_dashboard_data()
    
    def _get_overview_metrics(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get high-level overview metrics"""
        try:
            # This would integrate with your portfolio service
            # For now, return mock data with realistic values
            return {
                'total_value': 125000.0,
                'total_return': 8750.0,
                'total_return_percent': 7.5,
                'day_change': 125.0,
                'day_change_percent': 0.1,
                'ytd_return': 12.3,
                'inception_return': 45.6,
                'sharpe_ratio': 1.25,
                'max_drawdown': -8.2,
                'volatility': 14.8,
                'beta': 1.05,
                'alpha': 2.1,
                'information_ratio': 0.85,
                'calmar_ratio': 0.91,
                'sortino_ratio': 1.68,
                'treynor_ratio': 7.14,
                'jensen_alpha': 1.8,
                'm2_measure': 1.2,
                'm2_alpha': 0.9
            }
        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            return {}
    
    def _get_performance_metrics(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            return {
                'returns': {
                    'daily': self._get_daily_returns(user, portfolio_id, timeframe),
                    'monthly': self._get_monthly_returns(user, portfolio_id, timeframe),
                    'quarterly': self._get_quarterly_returns(user, portfolio_id, timeframe),
                    'yearly': self._get_yearly_returns(user, portfolio_id, timeframe)
                },
                'cumulative_returns': self._get_cumulative_returns(user, portfolio_id, timeframe),
                'rolling_metrics': {
                    'rolling_sharpe': self._get_rolling_sharpe(user, portfolio_id, timeframe),
                    'rolling_volatility': self._get_rolling_volatility(user, portfolio_id, timeframe),
                    'rolling_beta': self._get_rolling_beta(user, portfolio_id, timeframe)
                },
                'performance_attribution': {
                    'asset_allocation': self._get_asset_allocation_contribution(user, portfolio_id, timeframe),
                    'security_selection': self._get_security_selection_contribution(user, portfolio_id, timeframe),
                    'interaction': self._get_interaction_contribution(user, portfolio_id, timeframe)
                }
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def _get_risk_metrics(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get comprehensive risk metrics"""
        try:
            return {
                'value_at_risk': {
                    'var_95_1d': -2.1,
                    'var_99_1d': -3.2,
                    'var_95_1w': -4.8,
                    'var_99_1w': -7.1,
                    'var_95_1m': -9.5,
                    'var_99_1m': -14.2
                },
                'conditional_var': {
                    'cvar_95_1d': -2.8,
                    'cvar_99_1d': -4.1,
                    'cvar_95_1w': -6.2,
                    'cvar_99_1w': -9.3,
                    'cvar_95_1m': -12.1,
                    'cvar_99_1m': -18.7
                },
                'tail_risk': {
                    'skewness': -0.15,
                    'kurtosis': 3.8,
                    'excess_kurtosis': 0.8,
                    'tail_ratio': 0.85
                },
                'downside_risk': {
                    'downside_deviation': 8.2,
                    'downside_capture': 95.5,
                    'upside_capture': 108.3,
                    'downside_beta': 0.98,
                    'upside_beta': 1.12
                },
                'liquidity_risk': {
                    'bid_ask_spread': 0.12,
                    'market_impact': 0.08,
                    'liquidity_score': 7.5,
                    'turnover_ratio': 0.35
                },
                'concentration_risk': {
                    'herfindahl_index': 0.15,
                    'top_10_weight': 0.45,
                    'sector_concentration': 0.28,
                    'geographic_concentration': 0.12
                }
            }
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}
    
    def _get_attribution_analysis(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get performance attribution analysis"""
        try:
            return {
                'brinson_attribution': {
                    'asset_allocation': 0.8,
                    'security_selection': 1.2,
                    'interaction': 0.1,
                    'total_active_return': 2.1
                },
                'factor_attribution': {
                    'market_factor': 0.9,
                    'size_factor': 0.3,
                    'value_factor': -0.2,
                    'momentum_factor': 0.4,
                    'quality_factor': 0.6,
                    'low_volatility_factor': 0.1,
                    'residual': 0.0
                },
                'sector_attribution': {
                    'technology': 0.8,
                    'healthcare': 0.4,
                    'financials': -0.1,
                    'consumer_discretionary': 0.3,
                    'industrials': 0.2,
                    'energy': -0.2,
                    'materials': 0.1,
                    'utilities': 0.0,
                    'real_estate': 0.1,
                    'consumer_staples': 0.0,
                    'communication_services': 0.1
                },
                'geographic_attribution': {
                    'north_america': 1.2,
                    'europe': 0.3,
                    'asia_pacific': 0.4,
                    'emerging_markets': 0.2
                }
            }
        except Exception as e:
            logger.error(f"Error getting attribution analysis: {e}")
            return {}
    
    def _get_benchmark_comparison(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get benchmark comparison data"""
        try:
            return {
                'primary_benchmark': {
                    'name': 'S&P 500',
                    'symbol': 'SPY',
                    'return': 6.8,
                    'volatility': 16.2,
                    'sharpe_ratio': 0.95,
                    'max_drawdown': -12.1,
                    'correlation': 0.89,
                    'beta': 1.05,
                    'alpha': 2.1,
                    'tracking_error': 3.2,
                    'information_ratio': 0.66
                },
                'alternative_benchmarks': [
                    {
                        'name': 'NASDAQ 100',
                        'symbol': 'QQQ',
                        'return': 8.2,
                        'volatility': 18.5,
                        'sharpe_ratio': 1.02,
                        'correlation': 0.85,
                        'beta': 1.12,
                        'alpha': 1.8
                    },
                    {
                        'name': 'Russell 2000',
                        'symbol': 'IWM',
                        'return': 4.1,
                        'volatility': 22.3,
                        'sharpe_ratio': 0.68,
                        'correlation': 0.72,
                        'beta': 0.95,
                        'alpha': 3.2
                    }
                ],
                'peer_comparison': {
                    'percentile_rank': 78,
                    'peer_group_return': 6.2,
                    'peer_group_volatility': 15.8,
                    'peer_group_sharpe': 0.88
                }
            }
        except Exception as e:
            logger.error(f"Error getting benchmark comparison: {e}")
            return {}
    
    def _get_sector_analysis(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get sector analysis data"""
        try:
            return {
                'sector_weights': {
                    'technology': 0.28,
                    'healthcare': 0.18,
                    'financials': 0.15,
                    'consumer_discretionary': 0.12,
                    'industrials': 0.10,
                    'energy': 0.05,
                    'materials': 0.04,
                    'utilities': 0.03,
                    'real_estate': 0.03,
                    'consumer_staples': 0.02
                },
                'sector_performance': {
                    'technology': 12.5,
                    'healthcare': 8.2,
                    'financials': 3.1,
                    'consumer_discretionary': 9.8,
                    'industrials': 5.4,
                    'energy': -2.1,
                    'materials': 4.2,
                    'utilities': 1.8,
                    'real_estate': 2.9,
                    'consumer_staples': 0.5
                },
                'sector_attribution': {
                    'technology': 0.8,
                    'healthcare': 0.4,
                    'financials': -0.1,
                    'consumer_discretionary': 0.3,
                    'industrials': 0.2,
                    'energy': -0.2,
                    'materials': 0.1,
                    'utilities': 0.0,
                    'real_estate': 0.1,
                    'consumer_staples': 0.0
                },
                'sector_risk': {
                    'technology': 18.5,
                    'healthcare': 14.2,
                    'financials': 16.8,
                    'consumer_discretionary': 17.1,
                    'industrials': 15.9,
                    'energy': 22.3,
                    'materials': 19.2,
                    'utilities': 12.1,
                    'real_estate': 13.8,
                    'consumer_staples': 11.5
                }
            }
        except Exception as e:
            logger.error(f"Error getting sector analysis: {e}")
            return {}
    
    def _get_correlation_matrix(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get correlation matrix data"""
        try:
            # This would be calculated from actual portfolio holdings
            # For now, return a realistic correlation matrix
            sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer Discretionary', 'Industrials']
            correlation_matrix = {}
            
            for i, sector1 in enumerate(sectors):
                correlation_matrix[sector1] = {}
                for j, sector2 in enumerate(sectors):
                    if i == j:
                        correlation_matrix[sector1][sector2] = 1.0
                    else:
                        # Generate realistic correlations
                        base_correlation = 0.3 + (0.4 * np.random.random())
                        correlation_matrix[sector1][sector2] = round(base_correlation, 3)
            
            return {
                'sector_correlations': correlation_matrix,
                'average_correlation': 0.45,
                'max_correlation': 0.78,
                'min_correlation': 0.12,
                'correlation_volatility': 0.15
            }
        except Exception as e:
            logger.error(f"Error getting correlation matrix: {e}")
            return {}
    
    def _get_risk_attribution(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get risk attribution analysis"""
        try:
            return {
                'risk_budget': {
                    'total_risk': 14.8,
                    'systematic_risk': 12.1,
                    'idiosyncratic_risk': 8.2,
                    'concentration_risk': 2.3,
                    'liquidity_risk': 1.1
                },
                'risk_contributors': {
                    'technology': 4.2,
                    'healthcare': 2.8,
                    'financials': 2.1,
                    'consumer_discretionary': 1.9,
                    'industrials': 1.6,
                    'energy': 0.8,
                    'materials': 0.7,
                    'utilities': 0.4,
                    'real_estate': 0.3,
                    'consumer_staples': 0.0
                },
                'risk_decomposition': {
                    'factor_risk': 8.5,
                    'specific_risk': 4.2,
                    'currency_risk': 1.1,
                    'liquidity_risk': 0.8,
                    'model_risk': 0.2
                }
            }
        except Exception as e:
            logger.error(f"Error getting risk attribution: {e}")
            return {}
    
    def _get_drawdown_analysis(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get drawdown analysis"""
        try:
            return {
                'current_drawdown': -2.1,
                'max_drawdown': -8.2,
                'max_drawdown_date': '2023-03-15',
                'recovery_date': '2023-05-22',
                'drawdown_duration': 68,  # days
                'drawdown_events': [
                    {
                        'start_date': '2023-03-15',
                        'end_date': '2023-05-22',
                        'max_drawdown': -8.2,
                        'duration': 68,
                        'recovery_time': 45
                    },
                    {
                        'start_date': '2022-09-20',
                        'end_date': '2022-11-15',
                        'max_drawdown': -6.8,
                        'duration': 56,
                        'recovery_time': 38
                    }
                ],
                'drawdown_statistics': {
                    'average_drawdown': -3.2,
                    'drawdown_frequency': 2.1,  # per year
                    'average_recovery_time': 42,  # days
                    'worst_month': -5.8,
                    'worst_quarter': -8.2
                }
            }
        except Exception as e:
            logger.error(f"Error getting drawdown analysis: {e}")
            return {}
    
    def _get_volatility_analysis(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get volatility analysis"""
        try:
            return {
                'current_volatility': 14.8,
                'realized_volatility': {
                    '1m': 12.5,
                    '3m': 14.2,
                    '6m': 15.1,
                    '1y': 14.8,
                    '2y': 16.3
                },
                'implied_volatility': 15.2,
                'volatility_forecast': {
                    '1m': 13.8,
                    '3m': 14.5,
                    '6m': 15.2
                },
                'volatility_regime': 'normal',
                'volatility_clustering': True,
                'volatility_percentiles': {
                    'current_percentile': 65,
                    'historical_high': 28.5,
                    'historical_low': 8.2,
                    'median': 14.1
                }
            }
        except Exception as e:
            logger.error(f"Error getting volatility analysis: {e}")
            return {}
    
    def _get_momentum_indicators(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get momentum indicators"""
        try:
            return {
                'price_momentum': {
                    '1m': 2.1,
                    '3m': 5.8,
                    '6m': 8.2,
                    '12m': 12.5
                },
                'relative_momentum': {
                    'vs_spy_1m': 0.8,
                    'vs_spy_3m': 1.2,
                    'vs_spy_6m': 2.1,
                    'vs_spy_12m': 3.8
                },
                'momentum_score': 7.2,  # 1-10 scale
                'momentum_regime': 'positive',
                'momentum_consistency': 0.78,
                'momentum_persistence': 0.65
            }
        except Exception as e:
            logger.error(f"Error getting momentum indicators: {e}")
            return {}
    
    def _get_market_regime_analysis(self, user: User, portfolio_id: str, timeframe: str) -> Dict[str, Any]:
        """Get market regime analysis"""
        try:
            return {
                'current_regime': 'bull_market',
                'regime_probability': 0.78,
                'regime_duration': 245,  # days
                'regime_characteristics': {
                    'volatility_regime': 'low',
                    'correlation_regime': 'normal',
                    'trend_regime': 'upward',
                    'liquidity_regime': 'high'
                },
                'regime_indicators': {
                    'vix_level': 18.5,
                    'term_structure': 'normal',
                    'credit_spreads': 'tight',
                    'earnings_growth': 'positive',
                    'economic_indicators': 'expansion'
                },
                'regime_impact': {
                    'portfolio_performance': 'favorable',
                    'risk_level': 'moderate',
                    'correlation_impact': 'neutral',
                    'volatility_impact': 'positive'
                }
            }
        except Exception as e:
            logger.error(f"Error getting market regime analysis: {e}")
            return {}
    
    def _get_active_alerts(self, user: User, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get active alerts and warnings"""
        try:
            return [
                {
                    'id': 'alert_001',
                    'type': 'risk_warning',
                    'level': 'medium',
                    'title': 'Volatility Increase',
                    'message': 'Portfolio volatility has increased by 15% over the past week',
                    'metric': 'volatility',
                    'current_value': 16.2,
                    'threshold': 15.0,
                    'timestamp': datetime.now().isoformat(),
                    'action_required': False
                },
                {
                    'id': 'alert_002',
                    'type': 'performance_alert',
                    'level': 'low',
                    'title': 'Underperformance vs Benchmark',
                    'message': 'Portfolio is underperforming benchmark by 0.8% this month',
                    'metric': 'relative_performance',
                    'current_value': -0.8,
                    'threshold': -1.0,
                    'timestamp': datetime.now().isoformat(),
                    'action_required': False
                }
            ]
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def _get_recommendations(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict[str, Any]]:
        """Get portfolio recommendations"""
        try:
            return [
                {
                    'id': 'rec_001',
                    'type': 'rebalancing',
                    'priority': 'medium',
                    'title': 'Consider Rebalancing Technology Sector',
                    'description': 'Technology sector weight is 3% above target allocation',
                    'current_weight': 0.28,
                    'target_weight': 0.25,
                    'recommended_action': 'Reduce technology exposure by 3%',
                    'expected_impact': 'Reduce concentration risk',
                    'confidence': 0.75
                },
                {
                    'id': 'rec_002',
                    'type': 'risk_management',
                    'priority': 'high',
                    'title': 'Add Defensive Holdings',
                    'description': 'Consider adding defensive sectors to reduce volatility',
                    'recommended_action': 'Increase utilities and consumer staples allocation',
                    'expected_impact': 'Reduce portfolio volatility by 1-2%',
                    'confidence': 0.85
                }
            ]
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    # Helper methods for time series data
    def _get_daily_returns(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get daily returns data"""
        # This would fetch actual daily returns from your data source
        return [{'date': '2024-01-01', 'return': 0.5}, {'date': '2024-01-02', 'return': -0.2}]
    
    def _get_monthly_returns(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get monthly returns data"""
        return [{'month': '2024-01', 'return': 2.1}, {'month': '2024-02', 'return': 1.8}]
    
    def _get_quarterly_returns(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get quarterly returns data"""
        return [{'quarter': '2024-Q1', 'return': 5.8}, {'quarter': '2024-Q2', 'return': 3.2}]
    
    def _get_yearly_returns(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get yearly returns data"""
        return [{'year': '2023', 'return': 12.5}, {'year': '2024', 'return': 8.2}]
    
    def _get_cumulative_returns(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get cumulative returns data"""
        return [{'date': '2024-01-01', 'cumulative_return': 0.0}, {'date': '2024-01-02', 'cumulative_return': 0.5}]
    
    def _get_rolling_sharpe(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get rolling Sharpe ratio data"""
        return [{'date': '2024-01-01', 'rolling_sharpe': 1.2}, {'date': '2024-01-02', 'rolling_sharpe': 1.25}]
    
    def _get_rolling_volatility(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get rolling volatility data"""
        return [{'date': '2024-01-01', 'rolling_volatility': 14.5}, {'date': '2024-01-02', 'rolling_volatility': 14.8}]
    
    def _get_rolling_beta(self, user: User, portfolio_id: str, timeframe: str) -> List[Dict]:
        """Get rolling beta data"""
        return [{'date': '2024-01-01', 'rolling_beta': 1.05}, {'date': '2024-01-02', 'rolling_beta': 1.08}]
    
    def _get_asset_allocation_contribution(self, user: User, portfolio_id: str, timeframe: str) -> float:
        """Get asset allocation contribution to performance"""
        return 0.8
    
    def _get_security_selection_contribution(self, user: User, portfolio_id: str, timeframe: str) -> float:
        """Get security selection contribution to performance"""
        return 1.2
    
    def _get_interaction_contribution(self, user: User, portfolio_id: str, timeframe: str) -> float:
        """Get interaction contribution to performance"""
        return 0.1
    
    def _get_default_dashboard_data(self) -> Dict[str, Any]:
        """Return default dashboard data when calculation fails"""
        return {
            'overview': {},
            'performance': {},
            'risk_metrics': {},
            'attribution': {},
            'benchmark_comparison': {},
            'sector_analysis': {},
            'correlation_matrix': {},
            'risk_attribution': {},
            'drawdown_analysis': {},
            'volatility_analysis': {},
            'momentum_indicators': {},
            'market_regime': {},
            'alerts': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }

# Global instance
advanced_dashboard_service = AdvancedDashboardService()
