"""
Paper Trading Service - Simulated trading without real money
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .paper_trading_models import (
    PaperTradingAccount, PaperTradingPosition, PaperTradingOrder, PaperTradingTrade
)
from .enhanced_stock_service import EnhancedStockService
import logging

logger = logging.getLogger(__name__)


class PaperTradingService:
    """Service for managing paper trading accounts and simulated trades"""
    
    def __init__(self):
        self.stock_service = EnhancedStockService()
    
    def get_or_create_account(self, user, initial_balance: Decimal = Decimal('100000.00')):
        """Get or create a paper trading account for a user"""
        try:
            account, created = PaperTradingAccount.objects.get_or_create(
                user=user,
                defaults={
                    'initial_balance': initial_balance,
                    'current_balance': initial_balance,
                    'total_value': initial_balance,
                }
            )
            return account
        except Exception as e:
            # If database table doesn't exist, return a mock account
            logger.warning(f"⚠️ [Paper Trading] Database error (table may not exist): {e}")
            logger.warning(f"⚠️ [Paper Trading] Returning mock account for user {user.id}")
            
            class MockAccount:
                id = 1
                user = user
                initial_balance = initial_balance
                current_balance = initial_balance
                total_value = initial_balance
                realized_pnl = Decimal('0.00')
                unrealized_pnl = Decimal('0.00')
                total_pnl = Decimal('0.00')
                total_pnl_percent = Decimal('0.00')
                total_trades = 0
                winning_trades = 0
                losing_trades = 0
                win_rate = Decimal('0.00')
            
            return MockAccount()
    
    def get_account(self, user):
        """Get paper trading account for a user"""
        try:
            return PaperTradingAccount.objects.get(user=user)
        except PaperTradingAccount.DoesNotExist:
            return self.get_or_create_account(user)
        except Exception as e:
            # If database table doesn't exist, return a mock account
            logger.warning(f"⚠️ [Paper Trading] Database error getting account: {e}")
            return self.get_or_create_account(user)
    
    def get_positions(self, user):
        """Get all open positions for a user's paper account"""
        try:
            account = self.get_account(user)
            positions = PaperTradingPosition.objects.filter(account=account, shares__gt=0).select_related('stock')
            
            # Update P&L with current prices
            for position in positions:
                try:
                    current_price = self.stock_service.get_current_price(position.stock.symbol)
                    if current_price:
                        position.update_pnl(Decimal(str(current_price)))
                except Exception as e:
                    logger.warning(f"Could not update price for {position.stock.symbol}: {e}")
            
            return positions
        except Exception as e:
            # If database table doesn't exist, return empty list
            logger.warning(f"⚠️ [Paper Trading] Database error getting positions: {e}")
            return []
    
    def get_orders(self, user, status=None, limit=50):
        """Get orders for a user's paper account"""
        try:
            account = self.get_account(user)
            orders = PaperTradingOrder.objects.filter(account=account).select_related('stock')
            
            if status:
                orders = orders.filter(status=status)
            
            return orders[:limit]
        except Exception as e:
            # If database table doesn't exist, return empty list
            logger.warning(f"⚠️ [Paper Trading] Database error getting orders: {e}")
            return []
    
    def get_trade_history(self, user, limit=100):
        """Get trade history for a user's paper account"""
        try:
            account = self.get_account(user)
            return PaperTradingTrade.objects.filter(account=account).select_related('stock').order_by('-created_at')[:limit]
        except Exception as e:
            # If database table doesn't exist, return empty list
            logger.warning(f"⚠️ [Paper Trading] Database error getting trade history: {e}")
            return []
    
    def place_order(
        self,
        user,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = 'MARKET',
        limit_price: Decimal = None,
        stop_price: Decimal = None
    ):
        """Place a paper trading order"""
        if side not in ['BUY', 'SELL']:
            raise ValidationError("Side must be 'BUY' or 'SELL'")
        
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        
        from .models import Stock
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
        except Stock.DoesNotExist:
            raise ValidationError(f"Stock {symbol} not found")
        
        account = self.get_account(user)
        
        # Get current price
        try:
            current_price = self.stock_service.get_current_price(symbol)
            if not current_price:
                raise ValidationError(f"Could not get current price for {symbol}")
            current_price = Decimal(str(current_price))
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise ValidationError(f"Could not get current price for {symbol}")
        
        # Determine execution price
        if order_type == 'MARKET':
            execution_price = current_price
        elif order_type == 'LIMIT':
            if not limit_price:
                raise ValidationError("Limit price required for limit orders")
            if side == 'BUY' and limit_price < current_price:
                execution_price = limit_price  # Limit buy below market
            elif side == 'SELL' and limit_price > current_price:
                execution_price = limit_price  # Limit sell above market
            else:
                execution_price = current_price  # Execute at market if limit is better
        else:
            execution_price = current_price  # Default to market
        
        # Calculate total cost
        total_cost = execution_price * Decimal(quantity)
        commission = Decimal('0.00')  # Paper trading has no commission
        
        # Check if user has enough balance (for BUY) or shares (for SELL)
        if side == 'BUY':
            if account.current_balance < total_cost + commission:
                raise ValidationError(f"Insufficient balance. Need ${total_cost + commission:,.2f}, have ${account.current_balance:,.2f}")
        else:  # SELL
            try:
                position = PaperTradingPosition.objects.get(account=account, stock=stock)
                if position.shares < quantity:
                    raise ValidationError(f"Insufficient shares. Need {quantity}, have {position.shares}")
            except PaperTradingPosition.DoesNotExist:
                raise ValidationError(f"No position found for {symbol}")
        
        # Create order
        with transaction.atomic():
            order = PaperTradingOrder.objects.create(
                account=account,
                stock=stock,
                side=side,
                order_type=order_type,
                quantity=quantity,
                limit_price=limit_price,
                stop_price=stop_price,
                filled_price=execution_price,
                filled_quantity=quantity,
                total_cost=total_cost,
                commission=commission,
                status='FILLED',
                filled_at=timezone.now(),
            )
            
            # Execute the trade
            self._execute_trade(account, order, stock, side, quantity, execution_price, total_cost, commission)
            
            # Update account statistics
            account.update_statistics()
        
        return order
    
    def _execute_trade(
        self,
        account: PaperTradingAccount,
        order: PaperTradingOrder,
        stock,  # Stock model - using string reference to avoid circular import
        side: str,
        quantity: int,
        price: Decimal,
        total_cost: Decimal,
        commission: Decimal
    ):
        """Execute a paper trade"""
        with transaction.atomic():
            # Get or create position
            position, created = PaperTradingPosition.objects.get_or_create(
                account=account,
                stock=stock,
                defaults={
                    'shares': 0,
                    'average_price': Decimal('0.00'),
                    'cost_basis': Decimal('0.00'),
                }
            )
            
            if side == 'BUY':
                # Update position for buy
                if position.shares == 0:
                    position.shares = quantity
                    position.average_price = price
                    position.cost_basis = total_cost
                else:
                    # Calculate new average price
                    old_cost = position.cost_basis
                    new_cost = total_cost
                    total_shares = position.shares + quantity
                    position.shares = total_shares
                    position.average_price = (old_cost + new_cost) / Decimal(total_shares)
                    position.cost_basis = old_cost + new_cost
                
                # Update account balance
                account.current_balance -= (total_cost + commission)
                
            else:  # SELL
                # Calculate realized P&L
                cost_basis_per_share = position.average_price
                realized_pnl = (price - cost_basis_per_share) * Decimal(quantity)
                realized_pnl_percent = (realized_pnl / (cost_basis_per_share * Decimal(quantity))) * Decimal('100.00') if cost_basis_per_share > 0 else Decimal('0.00')
                
                # Update position
                position.shares -= quantity
                if position.shares == 0:
                    position.cost_basis = Decimal('0.00')
                    position.average_price = Decimal('0.00')
                else:
                    position.cost_basis -= (cost_basis_per_share * Decimal(quantity))
                
                # Update account balance
                account.current_balance += (total_cost - commission)
                
                # Update realized P&L
                account.realized_pnl += realized_pnl
                
                # Update trade statistics
                if realized_pnl > 0:
                    account.winning_trades += 1
                else:
                    account.losing_trades += 1
                account.total_trades += 1
                
                # Create trade record
                PaperTradingTrade.objects.create(
                    account=account,
                    stock=stock,
                    side=side,
                    quantity=quantity,
                    price=price,
                    total_value=total_cost,
                    commission=commission,
                    realized_pnl=realized_pnl,
                    realized_pnl_percent=realized_pnl_percent,
                    sell_order=order,
                )
            
            # Update position P&L
            try:
                current_price = self.stock_service.get_current_price(stock.symbol)
                if current_price:
                    position.update_pnl(Decimal(str(current_price)))
            except Exception as e:
                logger.warning(f"Could not update position P&L for {stock.symbol}: {e}")
            
            position.save()
            
            # Update account total value
            self._update_account_value(account)
    
    def _update_account_value(self, account: PaperTradingAccount):
        """Update account total value and unrealized P&L"""
        try:
            positions = PaperTradingPosition.objects.filter(account=account, shares__gt=0)
            
            total_market_value = Decimal('0.00')
            total_unrealized_pnl = Decimal('0.00')
            
            for position in positions:
                try:
                    current_price = self.stock_service.get_current_price(position.stock.symbol)
                    if current_price:
                        position.update_pnl(Decimal(str(current_price)))
                        total_market_value += position.market_value
                        total_unrealized_pnl += position.unrealized_pnl
                except Exception as e:
                    logger.warning(f"Could not update value for {position.stock.symbol}: {e}")
            
            account.unrealized_pnl = total_unrealized_pnl
            account.total_value = account.current_balance + total_market_value
            account.save()
        except Exception as e:
            # If database table doesn't exist, skip update
            logger.warning(f"⚠️ [Paper Trading] Could not update account value (table may not exist): {e}")
            # For mock accounts, just set default values
            if hasattr(account, 'current_balance'):
                account.total_value = account.current_balance
                account.unrealized_pnl = Decimal('0.00')
    
    def cancel_order(self, user, order_id: int):
        """Cancel a pending order"""
        account = self.get_account(user)
        try:
            order = PaperTradingOrder.objects.get(id=order_id, account=account, status='PENDING')
            order.status = 'CANCELLED'
            order.save()
            return order
        except PaperTradingOrder.DoesNotExist:
            raise ValidationError("Order not found or cannot be cancelled")
    
    def get_account_summary(self, user):
        """Get comprehensive account summary"""
        try:
            account = self.get_account(user)
            
            # Try to update account value, but don't fail if it errors
            try:
                self._update_account_value(account)
                account.update_statistics()
            except Exception as e:
                logger.warning(f"⚠️ [Paper Trading] Could not update account value: {e}")
            
            positions = self.get_positions(user)
            orders = self.get_orders(user, limit=10)
            recent_trades = self.get_trade_history(user, limit=10)
            
            # Handle mock account attributes
            total_trades = getattr(account, 'total_trades', 0) if hasattr(account, 'total_trades') else 0
            winning_trades = getattr(account, 'winning_trades', 0) if hasattr(account, 'winning_trades') else 0
            losing_trades = getattr(account, 'losing_trades', 0) if hasattr(account, 'losing_trades') else 0
            win_rate = getattr(account, 'win_rate', Decimal('0.00')) if hasattr(account, 'win_rate') else Decimal('0.00')
            total_pnl = getattr(account, 'total_pnl', Decimal('0.00')) if hasattr(account, 'total_pnl') else Decimal('0.00')
            total_pnl_percent = getattr(account, 'total_pnl_percent', Decimal('0.00')) if hasattr(account, 'total_pnl_percent') else Decimal('0.00')
            realized_pnl = getattr(account, 'realized_pnl', Decimal('0.00')) if hasattr(account, 'realized_pnl') else Decimal('0.00')
            unrealized_pnl = getattr(account, 'unrealized_pnl', Decimal('0.00')) if hasattr(account, 'unrealized_pnl') else Decimal('0.00')
            
            # Only return account if it's a real Django model instance, not a mock
            account_to_return = account if hasattr(account, '_meta') else None
            
            return {
                'account': account_to_return,
                'positions': positions,
                'open_orders': [o for o in orders if hasattr(o, 'status') and o.status == 'PENDING'],
                'recent_trades': recent_trades,
                'statistics': {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': float(win_rate),
                    'total_pnl': float(total_pnl),
                    'total_pnl_percent': float(total_pnl_percent),
                    'realized_pnl': float(realized_pnl),
                    'unrealized_pnl': float(unrealized_pnl),
                }
            }
        except Exception as e:
            # If database table doesn't exist, return None for account (frontend will use default)
            logger.warning(f"⚠️ [Paper Trading] Database error getting account summary: {e}")
            logger.warning(f"⚠️ [Paper Trading] Returning summary with null account for user {user.id}")
            
            return {
                'account': None,  # Return None - frontend will use defaultAccount
                'positions': [],
                'open_orders': [],
                'recent_trades': [],
                'statistics': {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_pnl_percent': 0.0,
                    'realized_pnl': 0.0,
                    'unrealized_pnl': 0.0,
                }
            }

