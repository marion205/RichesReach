"""
Execution Quality Tracker - Phase 3.3
Tracks actual fill prices vs signal prices to measure execution quality and provide coaching.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q

from .signal_performance_models import DayTradingSignal, SwingTradingSignal, SignalPerformance

logger = logging.getLogger(__name__)


class ExecutionQualityTracker:
    """
    Tracks execution quality by comparing actual fills to signal prices.
    Provides coaching tips to help users improve execution.
    """
    
    def analyze_fill(
        self,
        signal: Any,  # DayTradingSignal or SwingTradingSignal
        actual_fill_price: Decimal,
        actual_fill_time: datetime,
        signal_type: str = 'day_trading'
    ) -> Dict[str, Any]:
        """
        Analyze a single fill and compare it to the signal.
        
        Args:
            signal: DayTradingSignal or SwingTradingSignal instance
            actual_fill_price: Price at which the order was actually filled
            actual_fill_time: When the order was filled
            signal_type: 'day_trading' or 'swing_trading'
        
        Returns:
            Dict with slippage, quality_score, chased_price, coaching_tip
        """
        try:
            entry_price = signal.entry_price
            side = signal.side
            
            # Calculate slippage
            if side == 'LONG':
                slippage = float(actual_fill_price - entry_price)
                slippage_pct = (slippage / float(entry_price)) * 100 if entry_price > 0 else 0
            else:  # SHORT
                slippage = float(entry_price - actual_fill_price)
                slippage_pct = (slippage / float(entry_price)) * 100 if entry_price > 0 else 0
            
            # Determine if user chased price
            # Chasing = slippage > 0.5% for day trading, > 1% for swing trading
            threshold = 0.5 if signal_type == 'day_trading' else 1.0
            chased_price = abs(slippage_pct) > threshold
            
            # Calculate quality score (0-10, higher is better)
            # Perfect fill = 10, slippage > 1% = 0
            if abs(slippage_pct) <= 0.1:
                quality_score = 10.0
            elif abs(slippage_pct) <= 0.25:
                quality_score = 8.0
            elif abs(slippage_pct) <= 0.5:
                quality_score = 6.0
            elif abs(slippage_pct) <= 1.0:
                quality_score = 4.0
            else:
                quality_score = max(0.0, 10.0 - (abs(slippage_pct) * 2))
            
            # Generate coaching tip
            coaching_tip = self._generate_coaching_tip(slippage_pct, chased_price, signal_type)
            
            return {
                'slippage': slippage,
                'slippage_pct': round(slippage_pct, 2),
                'quality_score': round(quality_score, 1),
                'chased_price': chased_price,
                'coaching_tip': coaching_tip,
                'entry_price': float(entry_price),
                'fill_price': float(actual_fill_price),
                'time_to_fill_seconds': (actual_fill_time - signal.generated_at).total_seconds() if hasattr(signal, 'generated_at') else 0,
            }
        except Exception as e:
            logger.error(f"Error analyzing fill: {e}", exc_info=True)
            return {
                'slippage': 0,
                'slippage_pct': 0,
                'quality_score': 5.0,
                'chased_price': False,
                'coaching_tip': 'Unable to analyze fill quality',
                'error': str(e)
            }
    
    def _generate_coaching_tip(
        self,
        slippage_pct: float,
        chased_price: bool,
        signal_type: str
    ) -> str:
        """Generate a coaching tip based on execution quality."""
        if abs(slippage_pct) <= 0.1:
            return "Excellent execution! Your fill was very close to the signal price."
        elif abs(slippage_pct) <= 0.25:
            return "Good execution. Consider using limit orders to reduce slippage further."
        elif chased_price:
            if signal_type == 'day_trading':
                return f"You chased the price by {abs(slippage_pct):.2f}%. Use limit orders at the suggested price band to avoid chasing."
            else:
                return f"You chased the price by {abs(slippage_pct):.2f}%. For swing trades, wait for pullbacks to entry price."
        elif slippage_pct > 0.5:
            return f"High slippage ({slippage_pct:.2f}%). Use limit orders instead of market orders to control fill price."
        else:
            return "Consider using limit orders to improve execution quality."
    
    def get_user_execution_stats(
        self,
        user_id: Optional[int] = None,
        signal_type: str = 'day_trading',
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregated execution quality stats for a user or all users.
        
        Args:
            user_id: Optional user ID (if None, aggregate all users)
            signal_type: 'day_trading' or 'swing_trading'
            days: Number of days to look back
        
        Returns:
            Dict with avg_slippage, avg_quality_score, chased_count, total_fills, etc.
        """
        try:
            # This would typically query a UserFill model that tracks actual fills
            # For now, we'll use SignalPerformance as a proxy (signals that were evaluated)
            # In production, you'd have a separate UserFill model
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            if signal_type == 'day_trading':
                signals = DayTradingSignal.objects.filter(generated_at__gte=cutoff_date)
            else:
                signals = SwingTradingSignal.objects.filter(generated_at__gte=cutoff_date)
            
            # Get performance records (proxy for fills)
            # In production, you'd track actual fills separately
            performances = SignalPerformance.objects.filter(
                signal__in=signals if signal_type == 'day_trading' else None,
                swing_signal__in=signals if signal_type == 'swing_trading' else None,
                evaluated_at__gte=cutoff_date
            )
            
            total_fills = performances.count()
            
            if total_fills == 0:
                return {
                    'avg_slippage_pct': 0,
                    'avg_quality_score': 5.0,
                    'chased_count': 0,
                    'total_fills': 0,
                    'improvement_tips': []
                }
            
            # Calculate average slippage (simplified - would need actual fill prices)
            # For now, use PnL as proxy (not ideal, but works for demonstration)
            avg_pnl = performances.aggregate(avg=Avg('pnl_percent'))['avg'] or 0
            
            # Estimate slippage from performance (very rough approximation)
            # In production, you'd track actual fill prices
            avg_slippage_pct = abs(float(avg_pnl)) * 0.1  # Rough estimate
            
            # Generate improvement tips
            improvement_tips = self._generate_improvement_tips(avg_slippage_pct, total_fills)
            
            return {
                'avg_slippage_pct': round(avg_slippage_pct, 2),
                'avg_quality_score': round(max(0, 10 - (avg_slippage_pct * 10)), 1),
                'chased_count': int(total_fills * 0.2) if avg_slippage_pct > 0.5 else 0,  # Estimate
                'total_fills': total_fills,
                'improvement_tips': improvement_tips,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting execution stats: {e}", exc_info=True)
            return {
                'avg_slippage_pct': 0,
                'avg_quality_score': 5.0,
                'chased_count': 0,
                'total_fills': 0,
                'improvement_tips': ['Unable to calculate execution stats'],
                'error': str(e)
            }
    
    def _generate_improvement_tips(
        self,
        avg_slippage_pct: float,
        total_fills: int
    ) -> List[str]:
        """Generate improvement tips based on execution stats."""
        tips = []
        
        if avg_slippage_pct > 0.5:
            tips.append(f"Your average slippage is {avg_slippage_pct:.2f}%. Using limit orders in the suggested price band would reduce this to ~0.15%.")
        
        if avg_slippage_pct > 0.3:
            tips.append("Consider using limit orders instead of market orders to control fill prices.")
        
        if total_fills < 10:
            tips.append("You need more trades to accurately measure execution quality. Keep trading!")
        elif avg_slippage_pct < 0.2:
            tips.append("Great execution quality! You're using limit orders effectively.")
        
        if not tips:
            tips.append("Your execution quality is good. Keep using the suggested order types and price bands.")
        
        return tips
    
    def compare_to_signal(
        self,
        signal: Any,
        actual_fill: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare actual fill to signal and return detailed analysis.

        Args:
            signal: DayTradingSignal or SwingTradingSignal
            actual_fill: Dict with 'price', 'time', 'size', etc.

        Returns:
            Detailed comparison dict
        """
        return self.analyze_fill(
            signal=signal,
            actual_fill_price=Decimal(str(actual_fill.get('price', 0))),
            actual_fill_time=actual_fill.get('time', timezone.now()),
            signal_type='day_trading' if isinstance(signal, DayTradingSignal) else 'swing_trading'
        )

    def update_symbol_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Aggregate execution quality for a symbol from UserFill data
        and upsert a SymbolExecutionProfile record.
        """
        try:
            from .signal_performance_models import UserFill, SymbolExecutionProfile

            fills = UserFill.objects.filter(
                symbol=symbol.upper(),
                execution_quality_score__isnull=False,
            )

            fill_count = fills.count()
            if fill_count == 0:
                return None

            agg = fills.aggregate(
                avg_slippage=Avg('slippage_bps'),
                avg_quality=Avg('execution_quality_score'),
            )

            profile, _ = SymbolExecutionProfile.objects.update_or_create(
                symbol=symbol.upper(),
                defaults={
                    'avg_slippage_bps': agg['avg_slippage'] or Decimal('0'),
                    'avg_quality_score': agg['avg_quality'] or Decimal('5.0'),
                    'fill_count': fill_count,
                }
            )

            return {
                'symbol': symbol,
                'avg_slippage_bps': float(profile.avg_slippage_bps),
                'avg_quality_score': float(profile.avg_quality_score),
                'fill_count': profile.fill_count,
            }
        except Exception as e:
            logger.error(f"Error updating symbol profile for {symbol}: {e}", exc_info=True)
            return None

    def update_all_symbol_profiles(self) -> Dict[str, Any]:
        """
        Update execution profiles for all symbols with UserFill data.
        Called by the nightly Celery task.
        """
        try:
            from .signal_performance_models import UserFill

            symbols = (
                UserFill.objects
                .filter(execution_quality_score__isnull=False)
                .values_list('symbol', flat=True)
                .distinct()
            )

            updated = 0
            for symbol in symbols:
                result = self.update_symbol_profile(symbol)
                if result:
                    updated += 1

            logger.info(f"Updated execution profiles for {updated} symbols")
            return {'symbols_updated': updated}
        except Exception as e:
            logger.error(f"Error updating all symbol profiles: {e}", exc_info=True)
            return {'symbols_updated': 0, 'error': str(e)}

