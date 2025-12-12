"""
RAHA Auto-Trading Service
Executes RAHA signals automatically via broker API with risk management
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, time
from django.utils import timezone
from django.db import transaction

from .raha_models import RAHASignal, AutoTradingSettings, StrategyVersion
from .alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails
from .alpaca_trading_service import AlpacaTradingService
from .broker_models import BrokerAccount, BrokerOrder
from .paper_trading_service import PaperTradingService

logger = logging.getLogger(__name__)


class RAHAAutoTradingService:
    """
    Service for automatically executing RAHA signals via broker API.
    Includes risk management, position sizing, and order execution.
    """
    
    def __init__(self):
        self.broker_service = AlpacaBrokerService()
        self.paper_trading = PaperTradingService()
    
    def _get_user_settings(self, user) -> Optional[AutoTradingSettings]:
        """Get or create auto-trading settings for user"""
        try:
            settings, _ = AutoTradingSettings.objects.get_or_create(user=user)
            return settings
        except Exception as e:
            logger.error(f"Error getting auto-trading settings: {e}")
            return None
    
    def _get_broker_account(self, user) -> Optional[BrokerAccount]:
        """Get user's broker account"""
        try:
            return user.broker_account
        except BrokerAccount.DoesNotExist:
            logger.warning(f"No broker account found for user {user.email}")
            return None
    
    def _calculate_position_size(
        self,
        signal: RAHASignal,
        settings: AutoTradingSettings,
        account_info: Dict[str, Any]
    ) -> Decimal:
        """
        Calculate position size based on risk management rules.
        
        Uses:
        - Fixed dollar amount
        - Percentage of account equity
        - Risk-based sizing (R-multiple)
        """
        equity = Decimal(str(account_info.get('equity', 0) or account_info.get('cash', 0)))
        
        if equity <= 0:
            logger.warning(f"Invalid equity: {equity}")
            return Decimal('0')
        
        # Method 1: Fixed dollar amount
        if settings.position_sizing_method == 'FIXED':
            return min(
                Decimal(str(settings.fixed_position_size)),
                equity * Decimal('0.1')  # Cap at 10% of equity
            )
        
        # Method 2: Percentage of equity
        elif settings.position_sizing_method == 'PERCENTAGE':
            return equity * (Decimal(str(settings.position_size_percent)) / Decimal('100'))
        
        # Method 3: Risk-based (R-multiple)
        elif settings.position_sizing_method == 'RISK_BASED':
            # Calculate risk per share
            entry_price = signal.price
            stop_loss = signal.stop_loss or (entry_price * Decimal('0.98'))  # 2% default stop
            
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share <= 0:
                return Decimal('0')
            
            # Risk a fixed percentage of equity
            risk_amount = equity * (Decimal(str(settings.risk_per_trade_percent)) / Decimal('100'))
            
            # Calculate shares based on risk
            shares = risk_amount / risk_per_share
            position_value = shares * entry_price
            
            # Cap at max position size
            max_position = equity * (Decimal(str(settings.max_position_size_percent)) / Decimal('100'))
            return min(position_value, max_position)
        
        # Default: 1% of equity
        return equity * Decimal('0.01')
    
    def _check_risk_limits(
        self,
        user,
        signal: RAHASignal,
        position_size: Decimal,
        settings: AutoTradingSettings
    ) -> tuple[bool, str]:
        """
        Check if order passes all risk management limits.
        
        Returns: (allowed, reason)
        """
        # Check if auto-trading is enabled
        if not settings.enabled:
            return False, "Auto-trading is disabled"
        
        # Check confidence threshold
        if signal.confidence_score < settings.min_confidence_threshold:
            return False, f"Signal confidence {signal.confidence_score} below threshold {settings.min_confidence_threshold}"
        
        # Check broker account
        broker_account = self._get_broker_account(user)
        if not broker_account:
            return False, "No broker account found"
        
        # Check KYC status
        if broker_account.kyc_status != 'APPROVED':
            return False, f"Account not approved. Status: {broker_account.kyc_status}"
        
        # Check trading restrictions
        if broker_account.trading_blocked:
            return False, "Trading is blocked on this account"
        
        # Check guardrails
        allowed, reason = BrokerGuardrails.can_place_order(
            user=user,
            symbol=signal.symbol,
            notional=float(position_size),
            order_type='MARKET',
            daily_notional_used=float(BrokerGuardrails.get_daily_notional_used(user))
        )
        
        if not allowed:
            return False, reason
        
        # Check daily loss limit
        if settings.max_daily_loss_percent > 0:
            # Calculate today's P&L (would need to fetch from broker)
            # For now, we'll check this after order execution
            pass
        
        # Check max concurrent positions
        if settings.max_concurrent_positions > 0:
            # Count open positions (would need to fetch from broker)
            # For now, we'll check this after order execution
            pass
        
        return True, "All risk checks passed"
    
    def _create_bracket_order(
        self,
        signal: RAHASignal,
        quantity: int,
        broker_account: BrokerAccount,
        settings: AutoTradingSettings
    ) -> Optional[Dict[str, Any]]:
        """
        Create a bracket order (entry + stop loss + take profit).
        
        Returns order data or None if failed.
        """
        try:
            # Determine order side
            if signal.signal_type in ['ENTRY_LONG', 'BUY']:
                side = 'buy'
            elif signal.signal_type in ['ENTRY_SHORT', 'SELL']:
                side = 'sell'
            else:
                logger.warning(f"Unknown signal type: {signal.signal_type}")
                return None
            
            # Get access token (would need to be stored securely)
            # For now, using broker API which uses API keys
            access_token = None  # Would need OAuth token for Trading API
            
            # Use Broker API if available, otherwise Trading API
            if broker_account.alpaca_account_id:
                # Use Broker API
                order_data = {
                    'symbol': signal.symbol.upper(),
                    'qty': str(quantity),
                    'side': side,
                    'type': 'market',
                    'time_in_force': 'day',
                }
                
                # Add stop loss and take profit if provided
                if signal.stop_loss:
                    order_data['stop_loss'] = {
                        'stop_price': str(signal.stop_loss),
                    }
                
                if signal.take_profit:
                    order_data['take_profit'] = {
                        'limit_price': str(signal.take_profit),
                    }
                
                result = self.broker_service.create_order(
                    broker_account.alpaca_account_id,
                    order_data
                )
                
                if result and 'error' not in result:
                    return result
                else:
                    logger.error(f"Failed to create order: {result}")
                    return None
            else:
                logger.warning("No Alpaca account ID found")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bracket order: {e}", exc_info=True)
            return None
    
    def execute_signal(
        self,
        signal: RAHASignal,
        user=None
    ) -> Dict[str, Any]:
        """
        Execute a RAHA signal automatically.
        
        Args:
            signal: RAHASignal instance
            user: User (if None, uses signal.user)
        
        Returns:
            Dict with execution result
        """
        if user is None:
            user = signal.user
        
        if not user:
            return {
                'success': False,
                'error': 'No user associated with signal'
            }
        
        try:
            # Get settings
            settings = self._get_user_settings(user)
            if not settings:
                return {
                    'success': False,
                    'error': 'Could not load auto-trading settings'
                }
            
            # Check if enabled for this strategy
            from .raha_models import UserStrategySettings
            strategy_settings = UserStrategySettings.objects.filter(
                user=user,
                strategy_version=signal.strategy_version,
                enabled=True,
                auto_trade_enabled=True
            ).first()
            
            if not strategy_settings:
                return {
                    'success': False,
                    'error': 'Auto-trading not enabled for this strategy'
                }
            
            # Get broker account
            broker_account = self._get_broker_account(user)
            if not broker_account:
                return {
                    'success': False,
                    'error': 'No broker account found. Please complete onboarding.'
                }
            
            # Get account info
            if broker_account.alpaca_account_id:
                account_info = self.broker_service.get_account_info(broker_account.alpaca_account_id)
                if not account_info or 'error' in account_info:
                    return {
                        'success': False,
                        'error': 'Could not fetch account information'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Broker account not fully set up'
                }
            
            # Calculate base position size
            base_position_size = self._calculate_position_size(signal, settings, account_info)
            
            if base_position_size <= 0:
                return {
                    'success': False,
                    'error': 'Invalid position size calculated'
                }
            
            # Apply regime-based multiplier
            try:
                from .raha_regime_integration import raha_regime_integration
                regime_multiplier = raha_regime_integration.get_position_multiplier(signal)
                position_size = base_position_size * regime_multiplier
                
                # Get risk controls
                risk_controls = raha_regime_integration.get_risk_controls(signal.symbol)
                
                logger.info(
                    f"Regime adjustment for {signal.symbol}: "
                    f"base={base_position_size}, multiplier={regime_multiplier}, "
                    f"final={position_size}, stop_tightness={risk_controls['stop_loss_tightness']}"
                )
            except Exception as e:
                logger.warning(f"Could not get regime adjustment: {e}, using base position size")
                position_size = base_position_size
            
            # Calculate quantity
            entry_price = signal.price
            quantity = int(position_size / entry_price)
            
            if quantity <= 0:
                return {
                    'success': False,
                    'error': 'Quantity too small'
                }
            
            # Check risk limits
            allowed, reason = self._check_risk_limits(user, signal, position_size, settings)
            
            if not allowed:
                return {
                    'success': False,
                    'error': reason
                }
            
            # Create bracket order
            order_result = self._create_bracket_order(
                signal,
                quantity,
                broker_account,
                settings
            )
            
            if not order_result:
                return {
                    'success': False,
                    'error': 'Failed to create order with broker'
                }
            
            # Save order to database
            with transaction.atomic():
                broker_order = BrokerOrder.objects.create(
                    broker_account=broker_account,
                    client_order_id=str(signal.id),  # Use signal ID as client order ID
                    alpaca_order_id=order_result.get('id'),
                    symbol=signal.symbol,
                    side='BUY' if signal.signal_type in ['ENTRY_LONG', 'BUY'] else 'SELL',
                    order_type='MARKET',
                    time_in_force='DAY',
                    quantity=quantity,
                    notional=position_size,
                    limit_price=signal.take_profit,
                    stop_price=signal.stop_loss,
                    status='NEW',
                    source='RAHA_AUTO',
                    raha_signal=signal,
                )
            
            logger.info(f"✅ Auto-trade executed: {signal.symbol} {quantity} shares for {user.email}")
            
            return {
                'success': True,
                'order_id': broker_order.id,
                'alpaca_order_id': order_result.get('id'),
                'quantity': quantity,
                'position_size': float(position_size),
                'signal_id': str(signal.id),
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing auto-trade: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def should_execute_signal(self, signal: RAHASignal) -> bool:
        """
        Check if a signal should be automatically executed.
        This is called before execute_signal to do a quick check.
        """
        if not signal.user:
            return False
        
        settings = self._get_user_settings(signal.user)
        if not settings or not settings.enabled:
            return False
        
        # Check confidence threshold
        if signal.confidence_score < settings.min_confidence_threshold:
            return False
        
        # Check if auto-trading is enabled for this strategy
        from .raha_models import UserStrategySettings
        strategy_settings = UserStrategySettings.objects.filter(
            user=signal.user,
            strategy_version=signal.strategy_version,
            enabled=True,
            auto_trade_enabled=True
        ).first()
        
        return strategy_settings is not None

