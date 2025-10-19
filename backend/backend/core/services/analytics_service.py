"""
Analytics Service for Trading Performance and Reporting
Handles comprehensive trading analytics, performance metrics, and reporting
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Avg, Count, Q, F
from django.contrib.auth import get_user_model
from django.utils import timezone
import pandas as pd
import numpy as np

User = get_user_model()
logger = logging.getLogger(__name__)

class TradingAnalyticsService:
    """Service for comprehensive trading analytics and performance reporting"""
    
    def __init__(self):
        self.logger = logger
    
    def get_user_portfolio_analytics(self, user: User, period_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive portfolio analytics for a user"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Get user's Alpaca account
            from .models.alpaca_models import AlpacaAccount, AlpacaOrder, AlpacaPosition
            
            try:
                alpaca_account = AlpacaAccount.objects.get(user=user)
            except AlpacaAccount.DoesNotExist:
                return self._get_empty_analytics()
            
            # Get positions
            positions = AlpacaPosition.objects.filter(alpaca_account=alpaca_account)
            
            # Get orders for the period
            orders = AlpacaOrder.objects.filter(
                alpaca_account=alpaca_account,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(positions, orders, period_days)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(positions, orders, period_days)
            
            # Calculate trading metrics
            trading_metrics = self._calculate_trading_metrics(orders, period_days)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(positions, orders, period_days)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                },
                'portfolio': portfolio_metrics,
                'performance': performance_metrics,
                'trading': trading_metrics,
                'risk': risk_metrics,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio analytics for user {user.id}: {e}")
            return self._get_empty_analytics()
    
    def _calculate_portfolio_metrics(self, positions, orders, period_days: int) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        try:
            # Total portfolio value
            total_value = sum(float(pos.market_value or 0) for pos in positions)
            
            # Total cost basis
            total_cost = sum(float(pos.cost_basis or 0) for pos in positions)
            
            # Total unrealized P&L
            total_unrealized_pl = sum(float(pos.unrealized_pl or 0) for pos in positions)
            
            # Number of positions
            num_positions = positions.count()
            
            # Top positions by value
            top_positions = positions.order_by('-market_value')[:5]
            top_positions_data = [
                {
                    'symbol': pos.symbol,
                    'market_value': float(pos.market_value or 0),
                    'unrealized_pl': float(pos.unrealized_pl or 0),
                    'unrealized_pl_pc': float(pos.unrealized_pl_pc or 0),
                    'qty': float(pos.qty or 0)
                }
                for pos in top_positions
            ]
            
            # Asset allocation
            asset_allocation = self._calculate_asset_allocation(positions)
            
            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_unrealized_pl': total_unrealized_pl,
                'total_unrealized_pl_pc': (total_unrealized_pl / total_cost * 100) if total_cost > 0 else 0,
                'num_positions': num_positions,
                'top_positions': top_positions_data,
                'asset_allocation': asset_allocation
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio metrics: {e}")
            return {}
    
    def _calculate_performance_metrics(self, positions, orders, period_days: int) -> Dict[str, Any]:
        """Calculate performance metrics"""
        try:
            # Get filled orders for realized P&L calculation
            filled_orders = orders.filter(status='FILLED')
            
            # Calculate realized P&L
            realized_pl = 0.0
            total_trades = filled_orders.count()
            winning_trades = 0
            losing_trades = 0
            
            # Group orders by symbol to calculate P&L
            symbols = filled_orders.values_list('symbol', flat=True).distinct()
            
            for symbol in symbols:
                symbol_orders = filled_orders.filter(symbol=symbol)
                symbol_pl = self._calculate_symbol_realized_pl(symbol_orders)
                realized_pl += symbol_pl
                
                if symbol_pl > 0:
                    winning_trades += 1
                elif symbol_pl < 0:
                    losing_trades += 1
            
            # Calculate win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate average win/loss
            avg_win = self._calculate_average_win(filled_orders)
            avg_loss = self._calculate_average_loss(filled_orders)
            
            # Calculate profit factor
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # Calculate daily returns (simplified)
            daily_returns = self._calculate_daily_returns(positions, period_days)
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
            
            return {
                'realized_pl': realized_pl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'daily_returns': daily_returns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {e}")
            return {}
    
    def _calculate_trading_metrics(self, orders, period_days: int) -> Dict[str, Any]:
        """Calculate trading activity metrics"""
        try:
            total_orders = orders.count()
            filled_orders = orders.filter(status='FILLED')
            pending_orders = orders.filter(status__in=['NEW', 'PENDING'])
            cancelled_orders = orders.filter(status='CANCELED')
            
            # Order types distribution
            order_types = orders.values('type').annotate(count=Count('id'))
            order_type_distribution = {ot['type']: ot['count'] for ot in order_types}
            
            # Buy vs Sell distribution
            buy_orders = orders.filter(side='buy').count()
            sell_orders = orders.filter(side='sell').count()
            
            # Average order size
            avg_order_size = orders.aggregate(avg_size=Avg('qty'))['avg_size'] or 0
            
            # Most traded symbols
            top_symbols = orders.values('symbol').annotate(
                count=Count('id'),
                total_qty=Sum('qty')
            ).order_by('-count')[:5]
            
            # Trading frequency
            trading_days = orders.values('created_at__date').distinct().count()
            avg_trades_per_day = total_orders / period_days if period_days > 0 else 0
            
            return {
                'total_orders': total_orders,
                'filled_orders': filled_orders.count(),
                'pending_orders': pending_orders.count(),
                'cancelled_orders': cancelled_orders.count(),
                'fill_rate': (filled_orders.count() / total_orders * 100) if total_orders > 0 else 0,
                'order_type_distribution': order_type_distribution,
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'avg_order_size': float(avg_order_size),
                'top_symbols': list(top_symbols),
                'trading_days': trading_days,
                'avg_trades_per_day': avg_trades_per_day
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate trading metrics: {e}")
            return {}
    
    def _calculate_risk_metrics(self, positions, orders, period_days: int) -> Dict[str, Any]:
        """Calculate risk metrics"""
        try:
            # Portfolio volatility (simplified)
            daily_returns = self._calculate_daily_returns(positions, period_days)
            volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0
            
            # Maximum drawdown
            max_drawdown = self._calculate_max_drawdown(daily_returns)
            
            # Value at Risk (VaR) - 95% confidence
            var_95 = np.percentile(daily_returns, 5) if len(daily_returns) > 0 else 0
            
            # Position concentration
            total_value = sum(float(pos.market_value or 0) for pos in positions)
            position_concentration = []
            
            for pos in positions:
                if total_value > 0:
                    concentration = float(pos.market_value or 0) / total_value * 100
                    position_concentration.append({
                        'symbol': pos.symbol,
                        'concentration': concentration
                    })
            
            # Sort by concentration
            position_concentration.sort(key=lambda x: x['concentration'], reverse=True)
            
            # Calculate Herfindahl-Hirschman Index (HHI) for concentration
            hhi = sum(conc['concentration'] ** 2 for conc in position_concentration)
            
            return {
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'var_95': var_95,
                'position_concentration': position_concentration[:10],  # Top 10
                'hhi': hhi,
                'concentration_risk': 'High' if hhi > 2500 else 'Medium' if hhi > 1500 else 'Low'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
            return {}
    
    def _calculate_asset_allocation(self, positions) -> Dict[str, Any]:
        """Calculate asset allocation breakdown"""
        try:
            total_value = sum(float(pos.market_value or 0) for pos in positions)
            
            if total_value == 0:
                return {}
            
            # Group by sector (simplified - would need sector data)
            allocation = {}
            for pos in positions:
                # For now, just use symbol as category
                # In a real implementation, you'd map symbols to sectors
                category = pos.symbol[:3] if len(pos.symbol) >= 3 else 'Other'
                
                if category not in allocation:
                    allocation[category] = 0
                allocation[category] += float(pos.market_value or 0)
            
            # Convert to percentages
            allocation_pct = {}
            for category, value in allocation.items():
                allocation_pct[category] = {
                    'value': value,
                    'percentage': (value / total_value) * 100
                }
            
            return allocation_pct
            
        except Exception as e:
            self.logger.error(f"Failed to calculate asset allocation: {e}")
            return {}
    
    def _calculate_symbol_realized_pl(self, symbol_orders) -> float:
        """Calculate realized P&L for a specific symbol"""
        try:
            # This is a simplified calculation
            # In reality, you'd need to track cost basis and match buy/sell orders
            buy_orders = symbol_orders.filter(side='buy', status='FILLED')
            sell_orders = symbol_orders.filter(side='sell', status='FILLED')
            
            total_buy_value = sum(float(order.qty or 0) * float(order.filled_avg_price or 0) for order in buy_orders)
            total_sell_value = sum(float(order.qty or 0) * float(order.filled_avg_price or 0) for order in sell_orders)
            
            return total_sell_value - total_buy_value
            
        except Exception as e:
            self.logger.error(f"Failed to calculate symbol realized P&L: {e}")
            return 0.0
    
    def _calculate_average_win(self, orders) -> float:
        """Calculate average winning trade"""
        try:
            # Simplified calculation
            winning_trades = []
            # This would need more sophisticated logic to identify winning trades
            return 0.0  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Failed to calculate average win: {e}")
            return 0.0
    
    def _calculate_average_loss(self, orders) -> float:
        """Calculate average losing trade"""
        try:
            # Simplified calculation
            losing_trades = []
            # This would need more sophisticated logic to identify losing trades
            return 0.0  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Failed to calculate average loss: {e}")
            return 0.0
    
    def _calculate_daily_returns(self, positions, period_days: int) -> List[float]:
        """Calculate daily returns (simplified)"""
        try:
            # This is a placeholder - in reality, you'd need historical price data
            # For now, return some mock data
            return [0.01, -0.02, 0.015, -0.005, 0.02] * (period_days // 5)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate daily returns: {e}")
            return []
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(daily_returns) < 2:
                return 0.0
            
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            
            # Assume risk-free rate of 2% annually
            risk_free_rate = 0.02 / 252  # Daily risk-free rate
            
            if std_return == 0:
                return 0.0
            
            return (mean_return - risk_free_rate) / std_return * np.sqrt(252)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate Sharpe ratio: {e}")
            return 0.0
    
    def _calculate_max_drawdown(self, daily_returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(daily_returns) < 2:
                return 0.0
            
            cumulative_returns = np.cumprod(1 + np.array(daily_returns))
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            
            return float(np.min(drawdown))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate max drawdown: {e}")
            return 0.0
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'period': {
                'start_date': timezone.now().isoformat(),
                'end_date': timezone.now().isoformat(),
                'days': 30
            },
            'portfolio': {
                'total_value': 0,
                'total_cost': 0,
                'total_unrealized_pl': 0,
                'total_unrealized_pl_pc': 0,
                'num_positions': 0,
                'top_positions': [],
                'asset_allocation': {}
            },
            'performance': {
                'realized_pl': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'daily_returns': []
            },
            'trading': {
                'total_orders': 0,
                'filled_orders': 0,
                'pending_orders': 0,
                'cancelled_orders': 0,
                'fill_rate': 0,
                'order_type_distribution': {},
                'buy_orders': 0,
                'sell_orders': 0,
                'avg_order_size': 0,
                'top_symbols': [],
                'trading_days': 0,
                'avg_trades_per_day': 0
            },
            'risk': {
                'volatility': 0,
                'max_drawdown': 0,
                'var_95': 0,
                'position_concentration': [],
                'hhi': 0,
                'concentration_risk': 'Low'
            },
            'generated_at': timezone.now().isoformat()
        }
    
    def generate_performance_report(self, user: User, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            analytics = self.get_user_portfolio_analytics(user, period_days)
            
            # Add report-specific formatting
            report = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'report_period': analytics['period'],
                'summary': self._generate_summary(analytics),
                'detailed_analytics': analytics,
                'recommendations': self._generate_recommendations(analytics),
                'generated_at': timezone.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report for user {user.id}: {e}")
            return {}
    
    def _generate_summary(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of analytics"""
        try:
            portfolio = analytics.get('portfolio', {})
            performance = analytics.get('performance', {})
            trading = analytics.get('trading', {})
            risk = analytics.get('risk', {})
            
            return {
                'portfolio_value': portfolio.get('total_value', 0),
                'total_return': portfolio.get('total_unrealized_pl_pc', 0),
                'win_rate': performance.get('win_rate', 0),
                'total_trades': trading.get('total_trades', 0),
                'volatility': risk.get('volatility', 0),
                'risk_level': risk.get('concentration_risk', 'Low'),
                'key_insights': [
                    f"Portfolio value: ${portfolio.get('total_value', 0):,.2f}",
                    f"Total return: {portfolio.get('total_unrealized_pl_pc', 0):.2f}%",
                    f"Win rate: {performance.get('win_rate', 0):.1f}%",
                    f"Total trades: {trading.get('total_trades', 0)}",
                    f"Risk level: {risk.get('concentration_risk', 'Low')}"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return {}
    
    def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading recommendations based on analytics"""
        try:
            recommendations = []
            
            portfolio = analytics.get('portfolio', {})
            performance = analytics.get('performance', {})
            risk = analytics.get('risk', {})
            
            # Portfolio diversification recommendation
            if risk.get('hhi', 0) > 2500:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'high',
                    'title': 'Improve Portfolio Diversification',
                    'description': 'Your portfolio is highly concentrated. Consider diversifying across more positions.',
                    'action': 'Add positions in different sectors or asset classes'
                })
            
            # Win rate recommendation
            if performance.get('win_rate', 0) < 40:
                recommendations.append({
                    'type': 'strategy',
                    'priority': 'medium',
                    'title': 'Improve Trading Strategy',
                    'description': 'Your win rate is below 40%. Consider reviewing your entry and exit strategies.',
                    'action': 'Analyze losing trades and adjust your trading approach'
                })
            
            # Risk management recommendation
            if risk.get('volatility', 0) > 0.3:
                recommendations.append({
                    'type': 'risk_management',
                    'priority': 'high',
                    'title': 'Reduce Portfolio Volatility',
                    'description': 'Your portfolio volatility is high. Consider adding more stable positions.',
                    'action': 'Add defensive stocks or bonds to reduce volatility'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return []
