"""
Execution Advisor - Phase 3: Execution Intelligence
Provides smart order suggestions to improve execution quality and reduce slippage.
"""
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExecutionAdvisor:
    """
    Generates smart order suggestions for day trading and swing trading signals.
    Helps users execute trades with better fill prices and reduced slippage.
    """
    
    def suggest_order(self, signal: Dict[str, Any], signal_type: str = 'day_trading') -> Dict[str, Any]:
        """
        Generate smart order suggestions for a signal.
        
        Args:
            signal: Signal dict with symbol, side, entry_price, stop, targets, etc.
            signal_type: 'day_trading' or 'swing_trading'
        
        Returns:
            Dict with order_type, price_band, time_in_force, entry_strategy, bracket_legs
        """
        try:
            symbol = signal.get('symbol', '')
            side = signal.get('side', 'LONG')
            risk_dict = signal.get('risk', {})
            entry_price = float(signal.get('entry_price', risk_dict.get('stop', 0) + 1))
            stop_price = float(risk_dict.get('stop', 0))
            targets = risk_dict.get('targets', [])
            
            # Get microstructure data if available
            features = signal.get('features', {})
            microstructure = {
                'execution_quality_score': features.get('executionQualityScore'),
                'spread_bps': features.get('spreadBps', 5.0),
                'order_imbalance': features.get('orderImbalance', 0),
                'bid_depth': features.get('bidDepth', 0),
                'ask_depth': features.get('askDepth', 0),
                'depth_imbalance': features.get('depthImbalance', 0),
            }
            spread_bps = microstructure['spread_bps']
            
            # Determine order type based on signal type and market conditions
            if signal_type == 'day_trading':
                order_type, price_band, time_in_force, entry_strategy, microstructure_summary = self._suggest_day_trading_order(
                    entry_price, side, microstructure
                )
            else:  # swing_trading
                order_type, price_band, time_in_force, entry_strategy, microstructure_summary = self._suggest_swing_trading_order(
                    entry_price, side, microstructure
                )
            
            # Generate bracket legs (stop + targets)
            bracket_legs = self._generate_bracket_legs(entry_price, stop_price, targets, side)
            
            return {
                'order_type': order_type,
                'price_band': price_band,
                'time_in_force': time_in_force,
                'entry_strategy': entry_strategy,
                'bracket_legs': bracket_legs,
                'suggested_size': signal.get('risk', {}).get('sizeShares', 100),
                'rationale': self._generate_rationale(order_type, price_band, entry_strategy, spread_bps),
                'microstructure_summary': microstructure_summary  # New: microstructure hint
            }
        except Exception as e:
            logger.error(f"Error generating order suggestion: {e}", exc_info=True)
            # Return safe defaults
            return self._get_default_suggestion(signal)
    
    def _suggest_day_trading_order(
        self,
        entry_price: float,
        side: str,
        microstructure: Dict[str, Any]
    ) -> tuple:
        """
        Suggest order for day trading (intraday, fast execution needed).
        
        Returns:
            (order_type, price_band, time_in_force, entry_strategy, microstructure_summary)
        """
        spread_bps = microstructure.get('spread_bps', 5.0)
        execution_quality = microstructure.get('execution_quality_score')
        order_imbalance = microstructure.get('order_imbalance', 0)
        bid_depth = microstructure.get('bid_depth', 0)
        ask_depth = microstructure.get('ask_depth', 0)
        depth_imbalance = microstructure.get('depth_imbalance', 0)
        
        # Calculate total depth and liquidity assessment
        total_depth = bid_depth + ask_depth
        liquidity = 'High' if total_depth > 100000 else ('Medium' if total_depth > 50000 else 'Low')
        
        # Determine book bias
        if depth_imbalance > 0.2:
            book_bias = 'Bid-heavy'
        elif depth_imbalance < -0.2:
            book_bias = 'Ask-heavy'
        else:
            book_bias = 'Balanced'
        
        # Generate microstructure summary
        microstructure_summary = f"Spread {spread_bps:.2f}% · Book: {book_bias} · Liquidity: {liquidity}"
        
        # If spread is wide (> 20 bps) or execution quality is low, use limit order
        if spread_bps > 20 or (execution_quality and execution_quality < 5.0):
            # Use limit order with tight band around mid-price
            if side == 'LONG':
                price_band = [entry_price * 0.9995, entry_price * 1.0005]  # ±0.05%
            else:  # SHORT
                price_band = [entry_price * 0.9995, entry_price * 1.0005]
            order_type = 'LIMIT'
            time_in_force = 'DAY'
            entry_strategy = 'Place limit order at mid-price to avoid slippage'
            # Adjust size if depth is thin
            if total_depth < 50000:
                entry_strategy += ' (reduced size recommended due to thin depth)'
        elif spread_bps < 10 and (not execution_quality or execution_quality >= 7.0):
            # Tight spread, good execution quality - can use market order or tight limit
            if side == 'LONG':
                price_band = [entry_price * 0.9998, entry_price * 1.0002]  # Very tight
            else:
                price_band = [entry_price * 0.9998, entry_price * 1.0002]
            order_type = 'LIMIT'  # Still prefer limit for safety
            time_in_force = 'IOC'  # Immediate or cancel for fast fills
            entry_strategy = 'Tight spread detected - use limit order with IOC for fast execution'
            # If book is bid-heavy and we're going long, that's favorable
            if side == 'LONG' and depth_imbalance > 0.1:
                entry_strategy += ' (bid-heavy book supports long entry)'
        else:
            # Medium spread - use limit with wider band
            if side == 'LONG':
                price_band = [entry_price * 0.999, entry_price * 1.001]  # ±0.1%
            else:
                price_band = [entry_price * 0.999, entry_price * 1.001]
            order_type = 'LIMIT'
            time_in_force = 'DAY'
            entry_strategy = 'Use limit order to control entry price'
        
        return order_type, price_band, time_in_force, entry_strategy, microstructure_summary
    
    def _suggest_swing_trading_order(
        self,
        entry_price: float,
        side: str,
        microstructure: Dict[str, Any]
    ) -> tuple:
        """
        Suggest order for swing trading (multi-day hold, can wait for better entry).
        
        Returns:
            (order_type, price_band, time_in_force, entry_strategy, microstructure_summary)
        """
        spread_bps = microstructure.get('spread_bps', 5.0)
        bid_depth = microstructure.get('bid_depth', 0)
        ask_depth = microstructure.get('ask_depth', 0)
        depth_imbalance = microstructure.get('depth_imbalance', 0)
        
        total_depth = bid_depth + ask_depth
        liquidity = 'High' if total_depth > 100000 else ('Medium' if total_depth > 50000 else 'Low')
        
        if depth_imbalance > 0.2:
            book_bias = 'Bid-heavy'
        elif depth_imbalance < -0.2:
            book_bias = 'Ask-heavy'
        else:
            book_bias = 'Balanced'
        
        microstructure_summary = f"Spread {spread_bps:.2f}% · Book: {book_bias} · Liquidity: {liquidity}"
        
        # For swing trades, we can be more patient
        # Suggest waiting for pullback or using wider limit band
        
        # Check if we should wait for pullback (if price is extended)
        # This is simplified - in production would check VWAP distance, momentum, etc.
        
        if spread_bps > 30:
            # Wide spread - definitely use limit
            if side == 'LONG':
                price_band = [entry_price * 0.995, entry_price * 1.005]  # ±0.5%
            else:
                price_band = [entry_price * 0.995, entry_price * 1.005]
            order_type = 'LIMIT'
            time_in_force = 'DAY'
            entry_strategy = 'Wide spread - use limit order, consider waiting for better entry'
        else:
            # Normal spread - can use limit with moderate band
            if side == 'LONG':
                price_band = [entry_price * 0.998, entry_price * 1.002]  # ±0.2%
            else:
                price_band = [entry_price * 0.998, entry_price * 1.002]
            order_type = 'LIMIT'
            time_in_force = 'DAY'
            entry_strategy = 'Use limit order, consider entering on pullback to VWAP'
        
        return order_type, price_band, time_in_force, entry_strategy, microstructure_summary
    
    def _generate_bracket_legs(
        self,
        entry_price: float,
        stop_price: float,
        targets: List[float],
        side: str
    ) -> Dict[str, Any]:
        """
        Generate bracket order legs (stop loss + profit targets).
        
        Returns:
            Dict with stop, target1, target2, and suggested order structure
        """
        bracket = {
            'stop': round(stop_price, 2),
            'target1': round(targets[0], 2) if len(targets) > 0 else None,
            'target2': round(targets[1], 2) if len(targets) > 1 else None,
        }
        
        # Suggest bracket order structure
        if side == 'LONG':
            bracket['order_structure'] = {
                'parent': 'LIMIT',
                'stop_loss': 'STOP',
                'take_profit': 'LIMIT'
            }
        else:  # SHORT
            bracket['order_structure'] = {
                'parent': 'LIMIT',
                'stop_loss': 'STOP',
                'take_profit': 'LIMIT'
            }
        
        return bracket
    
    def _generate_rationale(
        self,
        order_type: str,
        price_band: List[float],
        entry_strategy: str,
        spread_bps: float
    ) -> str:
        """Generate human-readable rationale for the order suggestion."""
        rationale_parts = [
            f"Suggested {order_type} order",
            f"Price band: ${price_band[0]:.2f} - ${price_band[1]:.2f}",
            entry_strategy
        ]
        
        if spread_bps > 20:
            rationale_parts.append(f"Wide spread ({spread_bps:.1f} bps) - limit order recommended to avoid slippage")
        elif spread_bps < 10:
            rationale_parts.append(f"Tight spread ({spread_bps:.1f} bps) - good execution conditions")
        
        return ". ".join(rationale_parts) + "."
    
    def _get_default_suggestion(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Return safe default suggestion if analysis fails."""
        risk_dict = signal.get('risk', {})
        entry_price = float(signal.get('entry_price', risk_dict.get('stop', 0) + 1))
        stop_price = float(risk_dict.get('stop', 0))
        targets = risk_dict.get('targets', [])
        side = signal.get('side', 'LONG')
        
        return {
            'order_type': 'LIMIT',
            'price_band': [entry_price * 0.999, entry_price * 1.001],
            'time_in_force': 'DAY',
            'entry_strategy': 'Use limit order at entry price',
            'bracket_legs': {
                'stop': round(stop_price, 2),
                'target1': round(targets[0], 2) if len(targets) > 0 else None,
                'target2': round(targets[1], 2) if len(targets) > 1 else None,
            },
            'suggested_size': signal.get('risk', {}).get('sizeShares', 100),
            'rationale': 'Default suggestion: Use limit order to control entry price'
        }
    
    def suggest_entry_timing(self, signal: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """
        Suggest when to enter the trade (now vs wait for pullback).
        
        Returns:
            Dict with recommendation, wait_reason, pullback_target
        """
        entry_price = float(signal.get('entry_price', current_price))
        side = signal.get('side', 'LONG')
        
        # Calculate distance from entry
        if side == 'LONG':
            distance_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            distance_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Decision logic
        if abs(distance_pct) < 0.1:  # Within 0.1% of entry
            recommendation = 'ENTER_NOW'
            wait_reason = None
            pullback_target = None
        elif distance_pct > 0.5:  # Price moved away (LONG: price up, SHORT: price down)
            recommendation = 'WAIT_FOR_PULLBACK'
            wait_reason = f"Price moved {abs(distance_pct):.2f}% away from entry. Wait for pullback."
            if side == 'LONG':
                pullback_target = entry_price * 0.998  # 0.2% below entry
            else:
                pullback_target = entry_price * 1.002  # 0.2% above entry
        else:  # Price moved toward entry (good)
            recommendation = 'ENTER_NOW'
            wait_reason = None
            pullback_target = None
        
        return {
            'recommendation': recommendation,
            'wait_reason': wait_reason,
            'pullback_target': pullback_target,
            'current_distance_pct': round(distance_pct, 2)
        }

