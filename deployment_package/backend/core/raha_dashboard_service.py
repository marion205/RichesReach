"""
RAHA Dashboard Service
Aggregates performance data for strategy dashboard
"""
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta

from .raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
from .signal_performance_models import SignalPerformance

logger = logging.getLogger(__name__)


class RAHADashboardService:
    """
    Service for aggregating strategy performance data for dashboard views.
    """
    
    def get_strategy_dashboard_data(self, user) -> List[Dict[str, Any]]:
        """
        Get dashboard data for all user's enabled strategies.
        
        Returns:
            List of strategy data dictionaries with metrics
        """
        try:
            # Get user's enabled strategies
            user_settings = UserStrategySettings.objects.filter(
                user=user,
                enabled=True
            ).select_related('strategy_version', 'strategy_version__strategy')
            
            dashboard_data = []
            
            for setting in user_settings:
                strategy_version = setting.strategy_version
                strategy = strategy_version.strategy
                
                # Get signals for this strategy (optimized with select_related)
                signals = RAHASignal.objects.filter(
                    user=user,
                    strategy_version=strategy_version
                ).select_related('day_trading_signal')
                
                total_signals = signals.count()
                
                # Get performance data (optimized query)
                day_trading_signal_ids = list(
                    signals.filter(day_trading_signal__isnull=False)
                    .values_list('day_trading_signal_id', flat=True)
                )
                
                performances = SignalPerformance.objects.filter(
                    signal_id__in=day_trading_signal_ids
                ).select_related('signal') if day_trading_signal_ids else SignalPerformance.objects.none()
                
                # Calculate metrics
                metrics = self._calculate_strategy_metrics(
                    signals, performances, total_signals
                )
                
                # Get latest backtest (optimized with select_related)
                latest_backtest = RAHABacktestRun.objects.filter(
                    user=user,
                    strategy_version=strategy_version,
                    status='COMPLETED'
                ).select_related('strategy_version', 'strategy_version__strategy').order_by('-completed_at').first()
                
                # Get equity curve from backtest if available
                equity_curve = []
                if latest_backtest and latest_backtest.equity_curve:
                    equity_curve = latest_backtest.equity_curve
                
                dashboard_data.append({
                    'strategy_id': str(strategy.id),
                    'strategy_name': strategy.name or 'Unknown Strategy',
                    'strategy_version_id': str(strategy_version.id),
                    'category': strategy.category or 'N/A',
                    'enabled': setting.enabled if setting else False,
                    'total_signals': total_signals or 0,
                    'metrics': metrics or {},
                    'latest_backtest': {
                        'id': str(latest_backtest.id) if latest_backtest else None,
                        'symbol': latest_backtest.symbol if latest_backtest else None,
                        'completed_at': latest_backtest.completed_at.isoformat() if latest_backtest and latest_backtest.completed_at else None,
                    } if latest_backtest else None,
                    'equity_curve': equity_curve or [],
                })
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}", exc_info=True)
            return []
    
    def _calculate_strategy_metrics(
        self,
        signals,
        performances,
        total_signals: int
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy"""
        if not performances.exists():
            # Fallback to signal confidence
            avg_confidence = signals.aggregate(Avg('confidence_score'))['confidence_score__avg'] or Decimal('0.5')
            estimated_win_rate = float(avg_confidence) * 100.0
            
            return {
                'win_rate': estimated_win_rate,
                'total_trades': total_signals,
                'winning_trades': int(total_signals * (estimated_win_rate / 100.0)),
                'losing_trades': total_signals - int(total_signals * (estimated_win_rate / 100.0)),
                'total_pnl_dollars': 0.0,
                'total_pnl_percent': 0.0,
                'sharpe_ratio': None,
                'sortino_ratio': None,
                'max_drawdown': None,
                'expectancy': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
            }
        
        # Calculate from performance data
        winning = performances.filter(outcome__in=['WIN', 'TARGET_HIT']).count()
        losing = performances.filter(outcome__in=['LOSS', 'STOP_HIT']).count()
        win_rate = (winning / len(performances) * 100) if performances.exists() else 0.0
        
        total_pnl_dollars = float(
            performances.aggregate(Sum('pnl_dollars'))['pnl_dollars__sum'] or Decimal('0.00')
        )
        total_pnl_percent = float(
            performances.aggregate(Sum('pnl_percent'))['pnl_percent__sum'] or Decimal('0.00')
        )
        
        # Calculate returns for Sharpe/Sortino
        returns = [float(p.pnl_percent) for p in performances]
        
        sharpe = self._calculate_sharpe(returns) if len(returns) > 1 else None
        sortino = self._calculate_sortino(returns) if len(returns) > 1 else None
        
        # Max drawdown
        max_dd = self._calculate_max_drawdown_simple(returns)
        
        # Expectancy
        wins = [float(p.pnl_dollars) for p in performances if p.pnl_dollars > 0]
        losses = [abs(float(p.pnl_dollars)) for p in performances if p.pnl_dollars < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        
        expectancy = (win_rate / 100.0 * avg_win) - ((1 - win_rate / 100.0) * avg_loss)
        
        return {
            'win_rate': win_rate,
            'total_trades': len(performances),
            'winning_trades': winning,
            'losing_trades': losing,
            'total_pnl_dollars': total_pnl_dollars,
            'total_pnl_percent': total_pnl_percent,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd,
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
        }
    
    def _calculate_sharpe(self, returns: List[float]) -> Optional[float]:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return None
        
        import math
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0.01
        
        # Annualized Sharpe (assuming daily returns)
        sharpe = (mean_return / std_dev) if std_dev > 0 else 0.0
        return sharpe * math.sqrt(252)  # Annualize
        
    def _calculate_sortino(self, returns: List[float]) -> Optional[float]:
        """Calculate Sortino ratio (downside deviation only)"""
        if len(returns) < 2:
            return None
        
        import math
        mean_return = sum(returns) / len(returns)
        
        # Only count negative returns for downside deviation
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return None
        
        downside_variance = sum((r - mean_return) ** 2 for r in negative_returns) / len(negative_returns)
        downside_std = math.sqrt(downside_variance) if downside_variance > 0 else 0.01
        
        sortino = (mean_return / downside_std) if downside_std > 0 else 0.0
        return sortino * math.sqrt(252)  # Annualize
    
    def _calculate_max_drawdown_simple(self, returns: List[float]) -> Optional[float]:
        """Calculate maximum drawdown"""
        if not returns:
            return None
        
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for ret in returns:
            cumulative += ret
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd

