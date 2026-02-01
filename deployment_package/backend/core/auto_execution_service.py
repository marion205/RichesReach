"""
Auto-Execution Service
Automatically executes high-confidence trading signals via broker APIs.
Similar to Trade Ideas' Money Machine bots or IBKR's auto-trading.
"""
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AutoExecutionService:
    """
    Service for automatically executing trading signals.
    Supports paper trading and live trading modes.
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Initialize auto-execution service.
        
        Args:
            paper_trading: If True, use paper trading (default: True for safety)
        """
        self.paper_trading = paper_trading
        self.min_confidence = 0.8  # Minimum confidence to auto-execute
        self.max_position_size_pct = 0.10  # Max 10% of account per position
        self.daily_loss_limit_pct = -0.05  # Stop trading if down 5% for the day
        
    def should_auto_execute(
        self,
        signal: Dict[str, Any],
        user_id: int,
        account_equity: float
    ) -> Dict[str, Any]:
        """
        Determine if a signal should be auto-executed.
        
        Args:
            signal: Trading signal with confidence, symbol, side, etc.
            user_id: User ID
            account_equity: Account equity
        
        Returns:
            Dict with 'should_execute' (bool) and 'reason' (str)
        """
        # Check confidence threshold
        confidence = signal.get('confidence', 0.0) or signal.get('ml_probability', 0.0)
        if confidence < self.min_confidence:
            return {
                'should_execute': False,
                'reason': f'Confidence {confidence:.2%} below threshold {self.min_confidence:.2%}'
            }
        
        # Check daily loss limit
        daily_pnl = self._get_daily_pnl(user_id)
        if daily_pnl < self.daily_loss_limit_pct * account_equity:
            return {
                'should_execute': False,
                'reason': f'Daily loss limit reached: ${daily_pnl:.2f}'
            }
        
        # Check position size limits
        position_value = self._calculate_position_size(signal, account_equity)
        max_position_value = account_equity * self.max_position_size_pct
        
        if position_value > max_position_value:
            return {
                'should_execute': False,
                'reason': f'Position size ${position_value:.2f} exceeds limit ${max_position_value:.2f}'
            }
        
        # Check if user has auto-trading enabled
        if not self._is_auto_trading_enabled(user_id):
            return {
                'should_execute': False,
                'reason': 'Auto-trading not enabled for user'
            }
        
        return {
            'should_execute': True,
            'reason': 'All checks passed',
            'position_size': position_value,
            'confidence': confidence
        }
    
    def execute_signal(
        self,
        signal: Dict[str, Any],
        user_id: int,
        broker_account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a trading signal automatically.
        Also records signal for transparency dashboard.
        """
        """
        Execute a trading signal automatically.
        
        Args:
            signal: Trading signal
            user_id: User ID
            broker_account_id: Optional broker account ID
        
        Returns:
            Dict with execution result
        """
        try:
            # Get user's broker account
            if not broker_account_id:
                broker_account_id = self._get_user_broker_account(user_id)
            
            if not broker_account_id:
                return {
                    'success': False,
                    'error': 'No broker account found for user'
                }
            
            # Get account equity
            account_equity = self._get_account_equity(broker_account_id)
            
            # Check if should execute
            execution_check = self.should_auto_execute(signal, user_id, account_equity)
            
            if not execution_check['should_execute']:
                return {
                    'success': False,
                    'error': execution_check['reason']
                }
            
            # Calculate position size (using Kelly Criterion if available)
            position_size = execution_check.get('position_size')
            if not position_size:
                position_size = self._calculate_position_size(signal, account_equity)
            
            # Get order details
            symbol = signal.get('symbol', '').upper()
            side = signal.get('side', 'LONG').upper()
            entry_price = signal.get('entry_price') or signal.get('price')
            
            if not entry_price:
                return {
                    'success': False,
                    'error': 'No entry price in signal'
                }
            
            # Calculate shares (round down to whole shares)
            shares = int(position_size / float(entry_price))
            
            if shares < 1:
                return {
                    'success': False,
                    'error': f'Position size too small: ${position_size:.2f}'
                }
            
            # Place order via broker API
            order_result = self._place_order(
                broker_account_id=broker_account_id,
                symbol=symbol,
                side='buy' if side == 'LONG' else 'sell',
                shares=shares,
                order_type='limit',  # Use limit to control fill price
                limit_price=float(entry_price),
                paper_trading=self.paper_trading
            )
            
            if order_result.get('success'):
                # Log execution
                self._log_execution(user_id, signal, order_result, position_size)
                
                # Record signal for transparency dashboard
                try:
                    from .transparency_dashboard import get_transparency_dashboard
                    dashboard = get_transparency_dashboard()
                    dashboard.record_signal(
                        symbol=symbol,
                        action=side,  # LONG or SHORT
                        confidence=signal.get('confidence', 0.5),
                        entry_price=float(entry_price),
                        reasoning=signal.get('reasoning', f'Auto-executed {side} signal'),
                        user_id=user_id
                    )
                except Exception as e:
                    logger.warning(f"Could not record signal for transparency dashboard: {e}")
                
                return {
                    'success': True,
                    'order_id': order_result.get('order_id'),
                    'symbol': symbol,
                    'side': side,
                    'shares': shares,
                    'entry_price': float(entry_price),
                    'position_value': position_size,
                    'paper_trading': self.paper_trading
                }
            else:
                return {
                    'success': False,
                    'error': order_result.get('error', 'Order placement failed')
                }
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_position_size(
        self,
        signal: Dict[str, Any],
        account_equity: float
    ) -> float:
        """Calculate position size using Kelly Criterion or fixed percentage"""
        # Try to use Kelly Criterion if available
        kelly_fraction = signal.get('kelly_fraction') or signal.get('recommended_fraction')
        
        if kelly_fraction:
            # Use conservative Kelly (recommended fraction)
            position_pct = float(kelly_fraction) * 0.5  # Further reduce for safety
            return account_equity * position_pct
        else:
            # Default: 2% of account per position
            return account_equity * 0.02
    
    def _place_order(
        self,
        broker_account_id: str,
        symbol: str,
        side: str,
        shares: int,
        order_type: str,
        limit_price: float,
        paper_trading: bool
    ) -> Dict[str, Any]:
        """Place order via broker API (Alpaca)"""
        try:
            from .alpaca_trading_service import AlpacaTradingService
            from .broker_models import BrokerAccount
            
            # Get broker account
            broker_account = BrokerAccount.objects.get(id=broker_account_id)
            
            # Get access token
            access_token = broker_account.access_token
            if not access_token:
                return {
                    'success': False,
                    'error': 'No access token for broker account'
                }
            
            # Initialize trading service
            trading_service = AlpacaTradingService(
                access_token=access_token,
                paper=paper_trading
            )
            
            # Create order
            order = trading_service.create_order(
                symbol=symbol,
                qty=float(shares),
                side=side,
                order_type=order_type,
                time_in_force='day',
                limit_price=limit_price if order_type == 'limit' else None
            )
            
            if order and 'id' in order:
                return {
                    'success': True,
                    'order_id': order['id'],
                    'order': order
                }
            else:
                return {
                    'success': False,
                    'error': order.get('error', 'Order creation failed'),
                    'order': order
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_user_broker_account(self, user_id: int) -> Optional[str]:
        """Get user's primary broker account ID"""
        try:
            from .broker_models import BrokerAccount
            account = BrokerAccount.objects.filter(
                user_id=user_id,
                status='ACTIVE'
            ).first()
            return str(account.id) if account else None
        except Exception as e:
            logger.error(f"Error getting broker account: {e}")
            return None
    
    def _get_account_equity(self, broker_account_id: str) -> float:
        """Get account equity from broker"""
        try:
            from .alpaca_trading_service import AlpacaTradingService
            from .broker_models import BrokerAccount
            
            broker_account = BrokerAccount.objects.get(id=broker_account_id)
            trading_service = AlpacaTradingService(
                access_token=broker_account.access_token,
                paper=self.paper_trading
            )
            
            account = trading_service.get_account()
            if account and 'equity' in account:
                return float(account['equity'])
            else:
                return 10000.0  # Default fallback
                
        except Exception as e:
            logger.error(f"Error getting account equity: {e}")
            return 10000.0  # Default fallback
    
    def _get_daily_pnl(self, user_id: int) -> float:
        """Get today's P&L for user"""
        try:
            from .paper_trading_models import PaperTrade
            
            today = timezone.now().date()
            today_trades = PaperTrade.objects.filter(
                user_id=user_id,
                executed_at__date=today
            )
            
            total_pnl = sum(float(t.realized_pnl or 0) for t in today_trades)
            return total_pnl
            
        except Exception as e:
            logger.error(f"Error getting daily P&L: {e}")
            return 0.0
    
    def _is_auto_trading_enabled(self, user_id: int) -> bool:
        """Check if user has auto-trading enabled"""
        try:
            from .raha_models import RAHAAutoTradingSettings
            
            settings = RAHAAutoTradingSettings.objects.filter(
                user_id=user_id
            ).first()
            
            return settings.auto_trading_enabled if settings else False
            
        except Exception as e:
            logger.error(f"Error checking auto-trading settings: {e}")
            return False
    
    def _log_execution(
        self,
        user_id: int,
        signal: Dict[str, Any],
        order_result: Dict[str, Any],
        position_size: float
    ):
        """Log auto-execution for tracking"""
        try:
            from .signal_performance_models import DayTradingSignal
            
            # Create signal record if it doesn't exist
            signal_record, created = DayTradingSignal.objects.get_or_create(
                user_id=user_id,
                symbol=signal.get('symbol'),
                side=signal.get('side', 'LONG'),
                defaults={
                    'entry_price': Decimal(str(signal.get('entry_price', 0))),
                    'score': signal.get('score', 0.0),
                    'mode': signal.get('mode', 'SAFE'),
                    'features': signal,
                    'generated_at': timezone.now()
                }
            )
            
            # Store execution metadata
            execution_metadata = {
                'auto_executed': True,
                'order_id': order_result.get('order_id'),
                'position_size': position_size,
                'paper_trading': self.paper_trading,
                'executed_at': timezone.now().isoformat()
            }
            
            if hasattr(signal_record, 'execution_metadata'):
                signal_record.execution_metadata = execution_metadata
                signal_record.save()
            
            logger.info(f"✅ Auto-executed signal for {signal.get('symbol')}: {order_result.get('order_id')}")
            
        except Exception as e:
            logger.error(f"Error logging execution: {e}")


# Global instance (paper trading by default)
_auto_execution_service = None

def get_auto_execution_service(paper_trading: bool = True) -> AutoExecutionService:
    """Get global auto-execution service instance"""
    global _auto_execution_service
    if _auto_execution_service is None:
        _auto_execution_service = AutoExecutionService(paper_trading=paper_trading)
    return _auto_execution_service

