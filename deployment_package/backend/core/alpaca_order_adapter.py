"""
Alpaca Order Adapter - Phase 3.2
Enhanced broker integration that uses ExecutionAdvisor to pre-fill orders with smart suggestions.
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.utils import timezone

from .execution_advisor import ExecutionAdvisor
from .alpaca_broker_service import AlpacaBrokerService

logger = logging.getLogger(__name__)


class AlpacaOrderAdapter:
    """
    Enhanced Alpaca order adapter that integrates with ExecutionAdvisor.
    Pre-fills orders with smart execution suggestions.
    """
    
    def __init__(self):
        self.execution_advisor = ExecutionAdvisor()
        self.alpaca_service = AlpacaBrokerService()
    
    def create_order_from_signal(
        self,
        signal: Dict[str, Any],
        signal_type: str = 'day_trading',
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate Alpaca order JSON from a trading signal with execution suggestions.
        
        Args:
            signal: Signal dict with symbol, side, entry_price, risk, features, etc.
            signal_type: 'day_trading' or 'swing_trading'
            user_id: Optional user ID for user-specific preferences
        
        Returns:
            Dict with:
            - alpaca_order: Pre-filled Alpaca order JSON
            - execution_suggestion: The suggestion used
            - bracket_legs: Stop loss and profit targets
            - ready_to_submit: Whether order is ready to submit
        """
        try:
            # Get execution suggestion
            suggestion = self.execution_advisor.suggest_order(signal, signal_type)
            
            if not suggestion:
                logger.warning(f"Could not generate execution suggestion for {signal.get('symbol')}")
                # Fallback to basic order
                return self._create_basic_order(signal)
            
            symbol = signal.get('symbol', '').upper()
            side = signal.get('side', 'LONG')
            size_shares = suggestion.get('suggested_size', signal.get('risk', {}).get('sizeShares', 100))
            price_band = suggestion.get('price_band', [])
            order_type = suggestion.get('order_type', 'LIMIT')
            time_in_force = suggestion.get('time_in_force', 'DAY')
            bracket_legs = suggestion.get('bracket_legs', {})
            
            # Determine limit price (use midpoint of price band, or entry price)
            if price_band and len(price_band) == 2:
                limit_price = (price_band[0] + price_band[1]) / 2
            else:
                limit_price = float(signal.get('entry_price', signal.get('risk', {}).get('stop', 0) + 1))
            
            # Build Alpaca order
            alpaca_order = {
                'symbol': symbol,
                'qty': str(int(size_shares)),
                'side': 'buy' if side == 'LONG' else 'sell',
                'type': order_type.lower(),
                'time_in_force': time_in_force.lower(),
            }
            
            # Add limit price if LIMIT order
            if order_type == 'LIMIT':
                alpaca_order['limit_price'] = str(round(limit_price, 2))
            
            # Add bracket legs if available (Alpaca supports bracket orders)
            if bracket_legs.get('stop') and bracket_legs.get('target1'):
                # Alpaca bracket order structure
                # Note: Alpaca requires separate orders for bracket, but we can suggest them
                alpaca_order['stop_loss'] = {
                    'stop_price': str(round(bracket_legs['stop'], 2)),
                }
                alpaca_order['take_profit'] = {
                    'limit_price': str(round(bracket_legs['target1'], 2)),
                }
            
            return {
                'alpaca_order': alpaca_order,
                'execution_suggestion': suggestion,
                'bracket_legs': bracket_legs,
                'ready_to_submit': True,
                'suggested_price_band': price_band,
                'rationale': suggestion.get('rationale', ''),
            }
        except Exception as e:
            logger.error(f"Error creating order from signal: {e}", exc_info=True)
            return self._create_basic_order(signal)
    
    def _create_basic_order(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic order without execution suggestions (fallback)."""
        symbol = signal.get('symbol', '').upper()
        side = signal.get('side', 'LONG')
        size_shares = signal.get('risk', {}).get('sizeShares', 100)
        entry_price = float(signal.get('entry_price', signal.get('risk', {}).get('stop', 0) + 1))
        
        return {
            'alpaca_order': {
                'symbol': symbol,
                'qty': str(int(size_shares)),
                'side': 'buy' if side == 'LONG' else 'sell',
                'type': 'limit',
                'time_in_force': 'day',
                'limit_price': str(round(entry_price, 2)),
            },
            'execution_suggestion': None,
            'bracket_legs': {
                'stop': signal.get('risk', {}).get('stop'),
                'target1': signal.get('risk', {}).get('targets', [])[0] if signal.get('risk', {}).get('targets') else None,
                'target2': signal.get('risk', {}).get('targets', [])[1] if len(signal.get('risk', {}).get('targets', [])) > 1 else None,
            },
            'ready_to_submit': True,
            'suggested_price_band': [entry_price * 0.999, entry_price * 1.001],
            'rationale': 'Basic order - execution suggestions unavailable',
        }
    
    def submit_order(
        self,
        alpaca_account_id: str,
        order_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Submit order to Alpaca API.
        
        Args:
            alpaca_account_id: Alpaca account ID
            order_data: Order data (from create_order_from_signal or manual)
            user_id: Optional user ID
        
        Returns:
            Dict with order_id, status, etc.
        """
        try:
            # Extract alpaca_order from order_data if it's wrapped
            alpaca_order = order_data.get('alpaca_order', order_data)
            
            # Submit to Alpaca
            result = self.alpaca_service.create_order(alpaca_account_id, alpaca_order)
            
            if result and 'error' in result:
                return {
                    'success': False,
                    'error': result.get('error'),
                    'order_id': None,
                }
            
            return {
                'success': True,
                'order_id': result.get('id') if result else None,
                'status': result.get('status') if result else 'NEW',
                'alpaca_response': result,
            }
        except Exception as e:
            logger.error(f"Error submitting order to Alpaca: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'order_id': None,
            }
    
    def create_bracket_order_from_signal(
        self,
        signal: Dict[str, Any],
        signal_type: str = 'day_trading'
    ) -> Dict[str, Any]:
        """
        Create a bracket order (parent + stop loss + take profit) from a signal.
        
        Note: Alpaca requires separate orders for bracket legs, but we can suggest them.
        
        Returns:
            Dict with parent_order, stop_order, take_profit_order suggestions
        """
        try:
            order_data = self.create_order_from_signal(signal, signal_type)
            bracket_legs = order_data.get('bracket_legs', {})
            alpaca_order = order_data.get('alpaca_order', {})
            
            symbol = signal.get('symbol', '').upper()
            side = signal.get('side', 'LONG')
            size_shares = alpaca_order.get('qty', '100')
            
            # Parent order (entry)
            parent_order = alpaca_order.copy()
            
            # Stop loss order
            stop_order = None
            if bracket_legs.get('stop'):
                stop_order = {
                    'symbol': symbol,
                    'qty': size_shares,
                    'side': 'sell' if side == 'LONG' else 'buy',
                    'type': 'stop',
                    'time_in_force': 'day',
                    'stop_price': str(round(bracket_legs['stop'], 2)),
                }
            
            # Take profit order
            take_profit_order = None
            if bracket_legs.get('target1'):
                take_profit_order = {
                    'symbol': symbol,
                    'qty': size_shares,
                    'side': 'sell' if side == 'LONG' else 'buy',
                    'type': 'limit',
                    'time_in_force': 'day',
                    'limit_price': str(round(bracket_legs['target1'], 2)),
                }
            
            return {
                'parent_order': parent_order,
                'stop_order': stop_order,
                'take_profit_order': take_profit_order,
                'execution_suggestion': order_data.get('execution_suggestion'),
                'rationale': order_data.get('rationale'),
            }
        except Exception as e:
            logger.error(f"Error creating bracket order: {e}", exc_info=True)
            return {
                'parent_order': None,
                'stop_order': None,
                'take_profit_order': None,
                'error': str(e),
            }

