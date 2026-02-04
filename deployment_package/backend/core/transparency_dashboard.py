"""
Transparency Dashboard Service
Public-facing dashboard showing last 50 signals with actual results.
Builds institutional-grade trust through transparency.
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
# Import SignalRecord from models (moved there for Django migrations)
try:
    from .models import SignalRecord
except ImportError:
    # Fallback if models not available
    SignalRecord = None

logger = logging.getLogger(__name__)


class TransparencyDashboard:
    """
    Service for generating transparency dashboard data.
    Shows last 50 signals with entry/exit and actual results.
    """
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache
    
    def record_signal(
        self,
        symbol: str,
        action: str,
        confidence: float,
        entry_price: float,
        reasoning: str = '',
        user_id: Optional[int] = None,
        trading_mode: str = 'PAPER',
        signal_id: Optional[str] = None
    ) -> SignalRecord:
        """
        Record a new signal for transparency tracking.
        
        Args:
            symbol: Stock symbol
            action: BUY, SELL, or ABSTAIN
            confidence: Confidence score (0-1)
            entry_price: Entry price (if executed)
            reasoning: Model reasoning
            user_id: Optional user ID
        
        Returns:
            SignalRecord instance
        """
        signal = SignalRecord.objects.create(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=entry_price if action != 'ABSTAIN' else None,
            entry_timestamp=timezone.now(),
            reasoning=reasoning,
            status='OPEN' if action != 'ABSTAIN' else 'ABSTAINED',
            user_id=user_id
        )
        
        logger.info(f"Recorded signal: {symbol} {action} @ {entry_price} (confidence: {confidence:.2%})")
        return signal
    
    def update_signal_exit(
        self,
        signal_id: int,
        exit_price: float,
        pnl: float,
        pnl_percent: float
    ) -> SignalRecord:
        """
        Update signal with exit price and P&L.
        
        Args:
            signal_id: Signal record ID
            exit_price: Exit price
            pnl: Net P&L (after costs)
            pnl_percent: P&L as percentage
        
        Returns:
            Updated SignalRecord
        """
        signal = SignalRecord.objects.get(id=signal_id)
        signal.exit_price = exit_price
        signal.exit_timestamp = timezone.now()
        signal.pnl = pnl
        signal.pnl_percent = pnl_percent
        signal.status = 'CLOSED'
        signal.save()
        
        logger.info(f"Updated signal {signal_id}: exit @ {exit_price}, P&L: {pnl:.2f} ({pnl_percent:.2%})")
        return signal
    
    def get_dashboard_data(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get transparency dashboard data (last N signals).
        
        Args:
            limit: Number of signals to return (default: 50)
        
        Returns:
            Dict with signals, statistics, and performance metrics
        """
        cache_key = f"transparency_dashboard_{limit}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        # Get last N signals
        signals = SignalRecord.objects.filter(
            status__in=['OPEN', 'CLOSED']
        ).order_by('-entry_timestamp')[:limit]
        
        # Calculate statistics
        closed_signals = [s for s in signals if s.status == 'CLOSED']
        
        if closed_signals:
            wins = [s for s in closed_signals if s.pnl and s.pnl > 0]
            losses = [s for s in closed_signals if s.pnl and s.pnl <= 0]
            
            win_rate = len(wins) / len(closed_signals) if closed_signals else 0.0
            avg_win = np.mean([s.pnl for s in wins]) if wins else 0.0
            avg_loss = np.mean([s.pnl for s in losses]) if losses else 0.0
            total_pnl = sum([s.pnl for s in closed_signals if s.pnl])
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        else:
            win_rate = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            total_pnl = 0.0
            profit_factor = 0.0
        
        # Format signals for display
        signal_list = []
        for signal in signals:
            signal_list.append({
                'id': signal.id,
                'symbol': signal.symbol,
                'action': signal.action,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'entry_timestamp': signal.entry_timestamp.isoformat(),
                'exit_price': signal.exit_price,
                'exit_timestamp': signal.exit_timestamp.isoformat() if signal.exit_timestamp else None,
                'pnl': signal.pnl,
                'pnl_percent': signal.pnl_percent,
                'status': signal.status,
                'reasoning': signal.reasoning,
                'trading_mode': signal.trading_mode or 'PAPER',
                'signal_id': signal.signal_id or ''
            })
        
        dashboard_data = {
            'signals': signal_list,
            'statistics': {
                'total_signals': len(signals),
                'closed_signals': len(closed_signals),
                'open_signals': len([s for s in signals if s.status == 'OPEN']),
                'abstained_signals': len([s for s in signals if s.status == 'ABSTAINED']),
                'win_rate': win_rate,
                'total_wins': len(wins) if closed_signals else 0,
                'total_losses': len(losses) if closed_signals else 0,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'total_pnl': total_pnl,
                'profit_factor': profit_factor,
                'last_updated': datetime.now().isoformat()
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, self.cache_ttl)
        
        return dashboard_data
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance summary for last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Performance summary dict
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        signals = SignalRecord.objects.filter(
            entry_timestamp__gte=cutoff_date,
            status='CLOSED'
        )
        
        if not signals.exists():
            return {
                'period_days': days,
                'total_signals': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
            }
        
        pnl_list = [s.pnl for s in signals if s.pnl is not None]
        wins = [p for p in pnl_list if p > 0]
        losses = [p for p in pnl_list if p <= 0]
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = abs(np.mean(losses)) if losses else 0.0
        profit_factor = (avg_win / avg_loss) if avg_loss != 0 else (float('inf') if avg_win > 0 else 0.0)
        if profit_factor == float('inf'):
            profit_factor = 999.0  # Cap for serialization

        return {
            'period_days': days,
            'total_signals': signals.count(),
            'win_rate': (len(wins) / len(pnl_list) * 100.0) if pnl_list else 0.0,
            'total_pnl': sum(pnl_list),
            'avg_pnl': np.mean(pnl_list) if pnl_list else 0.0,
            'sharpe_ratio': self._calculate_sharpe(pnl_list) if len(pnl_list) > 1 else 0.0,
            'max_drawdown': self._calculate_max_drawdown(pnl_list) if pnl_list else 0.0,
            'profit_factor': profit_factor,
        }
    
    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from returns"""
        import numpy as np
        if not returns or len(returns) < 2:
            return 0.0
        returns_array = np.array(returns)
        if returns_array.std() == 0:
            return 0.0
        return (returns_array.mean() / returns_array.std()) * np.sqrt(252)  # Annualized
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        import numpy as np
        if not returns:
            return 0.0
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0


# Global instance
_transparency_dashboard = None

def get_transparency_dashboard() -> TransparencyDashboard:
    """Get global transparency dashboard instance"""
    global _transparency_dashboard
    if _transparency_dashboard is None:
        _transparency_dashboard = TransparencyDashboard()
    return _transparency_dashboard

