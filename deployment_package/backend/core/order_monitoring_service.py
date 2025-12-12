"""
Order Monitoring Service
Calculates metrics and aggregates data for the Order Monitoring Dashboard
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncDate

from .broker_models import BrokerOrder, BrokerPosition, BrokerAccount
from .raha_models import RAHASignal

logger = logging.getLogger(__name__)


class OrderMonitoringService:
    """
    Service for aggregating order and trade data for the monitoring dashboard.
    """
    
    def get_order_dashboard_data(
        self, 
        user,
        orders_limit: int = 20,
        orders_offset: int = 0,
        filled_orders_limit: int = 20,
        filled_orders_offset: int = 0,
        raha_orders_limit: int = 20,
        raha_orders_offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get comprehensive order dashboard data for a user with pagination.
        
        Args:
            user: User to get dashboard data for
            orders_limit: Maximum number of orders to return
            orders_offset: Offset for orders pagination
            filled_orders_limit: Maximum number of filled orders to return
            filled_orders_offset: Offset for filled orders pagination
            raha_orders_limit: Maximum number of RAHA orders to return
            raha_orders_offset: Offset for RAHA orders pagination
        
        Returns:
            Dict with orders, positions, metrics, and risk status
        """
        try:
            broker_account = BrokerAccount.objects.get(user=user)
        except BrokerAccount.DoesNotExist:
            return {
                'error': 'No broker account found',
                'orders': [],
                'positions': [],
                'metrics': {},
                'risk_status': {}
            }
        
        # Get recent orders (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        orders_queryset = BrokerOrder.objects.filter(
            broker_account=broker_account,
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')
        
        # Get total count for pagination info
        total_orders_count = orders_queryset.count()
        
        # Apply pagination to orders
        orders = list(orders_queryset[orders_offset:orders_offset + orders_limit])
        
        # Get active orders (no pagination needed - typically small)
        active_orders = orders_queryset.filter(
            status__in=['NEW', 'PENDING_NEW', 'ACCEPTED', 'PARTIALLY_FILLED']
        )
        
        # Get filled orders (completed trades) with pagination
        filled_orders_queryset = orders_queryset.filter(status='FILLED')
        total_filled_count = filled_orders_queryset.count()
        filled_orders = list(filled_orders_queryset[filled_orders_offset:filled_orders_offset + filled_orders_limit])
        
        # Get positions (no pagination needed - typically small)
        positions = BrokerPosition.objects.filter(broker_account=broker_account)
        
        # Calculate metrics (use all filled orders for accurate metrics)
        all_filled_orders = list(orders_queryset.filter(status='FILLED'))
        metrics = self._calculate_metrics(all_filled_orders, list(positions), broker_account)
        
        # Calculate risk status
        risk_status = self._calculate_risk_status(user, broker_account, orders_queryset, positions)
        
        # Get RAHA auto-trade orders with pagination
        raha_orders_queryset = orders_queryset.filter(source='RAHA_AUTO', raha_signal__isnull=False)
        total_raha_count = raha_orders_queryset.count()
        raha_orders = list(raha_orders_queryset[raha_orders_offset:raha_orders_offset + raha_orders_limit])
        
        return {
            'orders': orders,
            'orders_has_more': (orders_offset + orders_limit) < total_orders_count,
            'active_orders': list(active_orders),
            'filled_orders': filled_orders,
            'filled_orders_has_more': (filled_orders_offset + filled_orders_limit) < total_filled_count,
            'positions': list(positions),
            'raha_orders': raha_orders,
            'raha_orders_has_more': (raha_orders_offset + raha_orders_limit) < total_raha_count,
            'metrics': metrics,
            'risk_status': risk_status,
        }
    
    def _calculate_metrics(
        self,
        filled_orders: List[BrokerOrder],
        positions: List[BrokerPosition],
        broker_account: BrokerAccount
    ) -> Dict[str, Any]:
        """Calculate trading performance metrics"""
        
        if not filled_orders:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_percent': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'profit_factor': 0.0,
            }
        
        # Calculate P&L for each filled order
        # Note: This is simplified - in production, you'd need to match buy/sell pairs
        # or calculate based on position entry/exit prices
        
        total_trades = len(filled_orders)
        
        # For now, estimate P&L based on filled price vs current positions
        # In production, you'd track actual realized P&L from order fills
        winning_trades = 0
        losing_trades = 0
        total_pnl = Decimal('0.00')
        wins = []
        losses = []
        
        for order in filled_orders:
            # Simplified P&L calculation
            # In production, match with position entry/exit
            if order.filled_avg_price and order.quantity:
                # Estimate P&L (this is simplified - real calculation needs position tracking)
                pnl = Decimal('0.00')  # Placeholder
                if pnl > 0:
                    winning_trades += 1
                    wins.append(float(pnl))
                elif pnl < 0:
                    losing_trades += 1
                    losses.append(float(pnl))
                total_pnl += pnl
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0
        
        # Profit factor = total wins / total losses (absolute)
        total_wins = sum(wins) if wins else 0.0
        total_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        # Calculate P&L percent based on account equity
        equity = broker_account.equity or broker_account.cash or Decimal('1.00')
        total_pnl_percent = (total_pnl / equity * 100) if equity > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': float(win_rate),
            'total_pnl': float(total_pnl),
            'total_pnl_percent': float(total_pnl_percent),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
        }
    
    def _calculate_risk_status(
        self,
        user,
        broker_account: BrokerAccount,
        orders: List[BrokerOrder],
        positions: List[BrokerPosition]
    ) -> Dict[str, Any]:
        """Calculate current risk status and limits"""
        
        from .alpaca_broker_service import BrokerGuardrails
        
        # Get daily notional used
        daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
        daily_notional_remaining = BrokerGuardrails.MAX_DAILY_NOTIONAL - daily_notional_used
        
        # Count active positions
        active_positions_count = len(positions)
        
        # Calculate total position value
        total_position_value = sum(
            float(pos.market_value) if pos.market_value else 0.0
            for pos in positions
        )
        
        # Calculate unrealized P&L
        total_unrealized_pnl = sum(
            float(pos.unrealized_pl) if pos.unrealized_pl else 0.0
            for pos in positions
        )
        
        # Get account equity
        equity = float(broker_account.equity or broker_account.cash or 0.0)
        
        # Calculate position size as % of equity
        position_size_percent = (total_position_value / equity * 100) if equity > 0 else 0.0
        
        # Check if approaching limits
        daily_limit_warning = daily_notional_used > (BrokerGuardrails.MAX_DAILY_NOTIONAL * 0.8)
        position_limit_warning = active_positions_count >= 4  # Warning at 4/5 max
        
        return {
            'daily_notional_used': float(daily_notional_used),
            'daily_notional_remaining': float(daily_notional_remaining),
            'daily_notional_limit': float(BrokerGuardrails.MAX_DAILY_NOTIONAL),
            'daily_limit_warning': daily_limit_warning,
            'active_positions_count': active_positions_count,
            'max_positions': 5,  # Default max
            'position_limit_warning': position_limit_warning,
            'total_position_value': total_position_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'position_size_percent': position_size_percent,
            'account_equity': equity,
            'trading_blocked': broker_account.trading_blocked,
            'pattern_day_trader': broker_account.pattern_day_trader,
            'day_trade_count': broker_account.day_trade_count,
        }

