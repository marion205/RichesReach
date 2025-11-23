"""
Management command to calculate aggregated strategy performance stats.
Run this nightly to compute Sharpe, win rate, max DD, etc. for each mode.

Usage:
    python manage.py calculate_strategy_performance --period daily
    python manage.py calculate_strategy_performance --period weekly
    python manage.py calculate_strategy_performance --period monthly
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Avg, Sum, Count, Max, Min
from datetime import timedelta
from decimal import Decimal
import logging
import math

from core.signal_performance_models import (
    DayTradingSignal, SignalPerformance, StrategyPerformance
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate aggregated strategy performance statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'all_time'],
            default='daily',
            help='Time period to calculate stats for'
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['SAFE', 'AGGRESSIVE'],
            help='Specific mode to calculate (optional, defaults to both)'
        )

    def handle(self, *args, **options):
        period = options.get('period', 'daily')
        mode_filter = options.get('mode')
        
        modes = ['SAFE', 'AGGRESSIVE'] if not mode_filter else [mode_filter]
        
        for mode in modes:
            self.stdout.write(self.style.SUCCESS(f'\n📊 Calculating {period} performance for {mode} mode...'))
            self.calculate_performance(mode, period)
            self.stdout.write(self.style.SUCCESS(f'✅ Completed {mode} {period} performance'))
    
    def calculate_performance(self, mode, period):
        """Calculate performance stats for a mode and period"""
        now = timezone.now()
        
        # Determine time window
        if period == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = now
            period_name = 'DAILY'
        elif period == 'weekly':
            # Start of week (Monday)
            days_since_monday = now.weekday()
            period_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = now
            period_name = 'WEEKLY'
        elif period == 'monthly':
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = now
            period_name = 'MONTHLY'
        else:  # all_time
            period_start = timezone.now() - timedelta(days=365)  # Last year
            period_end = now
            period_name = 'ALL_TIME'
        
        # Get signals for this period
        signals = DayTradingSignal.objects.filter(
            mode=mode,
            generated_at__gte=period_start,
            generated_at__lte=period_end
        )
        
        # Get performance data (use EOD for daily/weekly, 1d for monthly/all_time)
        horizon = 'EOD' if period in ['daily', 'weekly'] else '1d'
        
        performances = SignalPerformance.objects.filter(
            signal__mode=mode,
            signal__generated_at__gte=period_start,
            signal__generated_at__lte=period_end,
            horizon=horizon
        )
        
        total_signals = signals.count()
        signals_evaluated = performances.count()
        
        if signals_evaluated == 0:
            self.stdout.write(self.style.WARNING(f'  No evaluated signals for {mode} {period}'))
            return
        
        # Win/Loss stats
        winning = performances.filter(outcome__in=['WIN', 'TARGET_HIT']).count()
        losing = performances.filter(outcome__in=['LOSS', 'STOP_HIT']).count()
        breakeven = performances.filter(outcome='BREAKEVEN').count()
        win_rate = (winning / signals_evaluated * 100) if signals_evaluated > 0 else 0
        
        # PnL stats
        total_pnl_dollars = performances.aggregate(Sum('pnl_dollars'))['pnl_dollars__sum'] or Decimal('0.00')
        total_pnl_percent = performances.aggregate(Sum('pnl_percent'))['pnl_percent__sum'] or Decimal('0.00')
        avg_pnl = total_pnl_percent / signals_evaluated if signals_evaluated > 0 else Decimal('0.00')
        
        # Risk metrics
        pnl_values = list(performances.values_list('pnl_percent', flat=True))
        
        # Calculate Sharpe ratio
        sharpe = self.calculate_sharpe(pnl_values)
        
        # Calculate max drawdown
        max_dd, max_dd_duration = self.calculate_max_drawdown(performances)
        
        # Calculate Sortino (downside deviation only)
        sortino = self.calculate_sortino(pnl_values)
        
        # Calmar ratio (return / max DD)
        calmar = abs(avg_pnl / max_dd) if max_dd != 0 else None
        
        # Tail risk
        worst_loss = performances.aggregate(Min('pnl_percent'))['pnl_percent__min'] or Decimal('0.00')
        best_win = performances.aggregate(Max('pnl_percent'))['pnl_percent__max'] or Decimal('0.00')
        
        # Build equity curve
        equity_curve = self.build_equity_curve(performances)
        
        # Save or update
        perf_obj, created = StrategyPerformance.objects.update_or_create(
            mode=mode,
            period=period_name,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'total_signals': total_signals,
                'signals_evaluated': signals_evaluated,
                'winning_signals': winning,
                'losing_signals': losing,
                'breakeven_signals': breakeven,
                'win_rate': Decimal(str(win_rate)),
                'total_pnl_dollars': total_pnl_dollars,
                'total_pnl_percent': total_pnl_percent,
                'avg_pnl_per_signal': avg_pnl,
                'sharpe_ratio': Decimal(str(sharpe)) if sharpe else None,
                'max_drawdown': Decimal(str(max_dd)) if max_dd else None,
                'max_drawdown_duration_days': max_dd_duration,
                'sortino_ratio': Decimal(str(sortino)) if sortino else None,
                'calmar_ratio': Decimal(str(calmar)) if calmar else None,
                'worst_single_loss': Decimal(str(worst_loss)),
                'best_single_win': Decimal(str(best_win)),
                'equity_curve': equity_curve,
                'calculated_at': now,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Created {mode} {period} performance'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  🔄 Updated {mode} {period} performance'))
        
        # Print summary
        self.stdout.write(f'  📊 Stats: {signals_evaluated} signals, {win_rate:.1f}% win rate')
        self.stdout.write(f'  💰 PnL: {total_pnl_percent:.2f}% total, {avg_pnl:.2f}% avg')
        if sharpe:
            self.stdout.write(f'  📈 Sharpe: {sharpe:.2f}')
        if max_dd:
            self.stdout.write(f'  📉 Max DD: {max_dd:.2f}%')
    
    def calculate_sharpe(self, returns):
        """Calculate Sharpe ratio (annualized)"""
        if not returns or len(returns) < 2:
            return None
        
        import statistics
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
        
        if std_return == 0:
            return None
        
        # Annualize (assuming ~252 trading days, but for intraday we scale differently)
        # For day trading, assume ~6.5 hours per day, so ~390 minutes
        # If we're evaluating 30m/2h signals, scale accordingly
        annualized_sharpe = (mean_return / std_return) * math.sqrt(252)  # Rough approximation
        return annualized_sharpe
    
    def calculate_sortino(self, returns):
        """Calculate Sortino ratio (downside deviation only)"""
        if not returns or len(returns) < 2:
            return None
        
        import statistics
        mean_return = statistics.mean(returns)
        
        # Only count negative returns for downside deviation
        downside_returns = [r for r in returns if r < 0]
        if len(downside_returns) < 2:
            return None
        
        downside_std = statistics.stdev(downside_returns)
        if downside_std == 0:
            return None
        
        sortino = (mean_return / downside_std) * math.sqrt(252)
        return sortino
    
    def calculate_max_drawdown(self, performances):
        """Calculate maximum drawdown and duration"""
        if not performances.exists():
            return None, None
        
        # Build cumulative equity curve
        sorted_perfs = performances.order_by('evaluated_at')
        equity = 100.0  # Start at 100
        equity_curve = [equity]
        dates = []
        
        for perf in sorted_perfs:
            equity *= (1 + float(perf.pnl_percent) / 100)
            equity_curve.append(equity)
            dates.append(perf.evaluated_at)
        
        # Calculate drawdowns
        max_equity = equity_curve[0]
        max_dd = 0
        max_dd_start = None
        max_dd_end = None
        
        for i, eq in enumerate(equity_curve):
            if eq > max_equity:
                max_equity = eq
            dd = ((eq - max_equity) / max_equity) * 100
            if dd < max_dd:
                max_dd = dd
                if max_dd_start is None:
                    max_dd_start = dates[i-1] if i > 0 else dates[0]
                max_dd_end = dates[i-1] if i < len(dates) else dates[-1]
        
        duration = (max_dd_end - max_dd_start).days if max_dd_start and max_dd_end else None
        
        return abs(max_dd), duration
    
    def build_equity_curve(self, performances):
        """Build equity curve data points"""
        sorted_perfs = performances.order_by('evaluated_at')
        equity = 100.0
        curve = [{'date': sorted_perfs[0].evaluated_at.isoformat(), 'equity': equity}]
        
        for perf in sorted_perfs:
            equity *= (1 + float(perf.pnl_percent) / 100)
            curve.append({
                'date': perf.evaluated_at.isoformat(),
                'equity': round(equity, 2)
            })
        
        return curve

