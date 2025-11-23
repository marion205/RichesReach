"""
Django management command to compare performance of CORE vs DYNAMIC_MOVERS universes.

Usage:
    python manage.py compare_universe_performance
    python manage.py compare_universe_performance --horizon 30m
    python manage.py compare_universe_performance --mode SAFE
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, Avg, Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import math

from core.signal_performance_models import DayTradingSignal, SignalPerformance, StrategyPerformance


class Command(BaseCommand):
    help = 'Compare performance metrics between CORE and DYNAMIC_MOVERS universes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--horizon',
            type=str,
            default='30m',
            choices=['30m', '2h', 'EOD', '1d', '2d'],
            help='Time horizon for performance evaluation (default: 30m)'
        )
        parser.add_argument(
            '--mode',
            type=str,
            default=None,
            choices=['SAFE', 'AGGRESSIVE'],
            help='Filter by trading mode (default: all modes)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back (default: 30)'
        )

    def handle(self, *args, **options):
        horizon = options['horizon']
        mode_filter = options['mode']
        days_back = options['days']
        
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS(f'📊 UNIVERSE PERFORMANCE COMPARISON'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f'\nHorizon: {horizon} | Days Back: {days_back}')
        if mode_filter:
            self.stdout.write(f'Mode Filter: {mode_filter}')
        self.stdout.write('')
        
        # Build base queryset
        signals_qs = DayTradingSignal.objects.filter(generated_at__gte=cutoff_date)
        if mode_filter:
            signals_qs = signals_qs.filter(mode=mode_filter)
        
        # Get signals by universe source
        core_signals = signals_qs.filter(universe_source='CORE')
        dynamic_signals = signals_qs.filter(universe_source='DYNAMIC_MOVERS')
        
        self.stdout.write(f'📈 CORE Universe Signals: {core_signals.count()}')
        self.stdout.write(f'📈 DYNAMIC_MOVERS Universe Signals: {dynamic_signals.count()}')
        self.stdout.write('')
        
        # Compare metrics for each universe
        core_metrics = self._calculate_metrics(core_signals, horizon)
        dynamic_metrics = self._calculate_metrics(dynamic_signals, horizon)
        
        # Display comparison table
        self.stdout.write(self.style.SUCCESS('─'*80))
        self.stdout.write(self.style.SUCCESS(f'{"Metric":<30} {"CORE":<25} {"DYNAMIC_MOVERS":<25}'))
        self.stdout.write(self.style.SUCCESS('─'*80))
        
        metrics_to_compare = [
            ('Total Signals', 'total_signals', 'int'),
            ('Signals with Performance Data', 'signals_with_perf', 'int'),
            ('Win Rate', 'win_rate', 'percent'),
            ('Average PnL per Signal', 'avg_pnl', 'currency'),
            ('Total PnL', 'total_pnl', 'currency'),
            ('Average R:R', 'avg_rr', 'decimal'),
            ('Sharpe Ratio', 'sharpe', 'decimal'),
            ('Max Drawdown', 'max_dd', 'currency'),
            ('Best Trade', 'best_trade', 'currency'),
            ('Worst Trade', 'worst_trade', 'currency'),
        ]
        
        for metric_name, metric_key, format_type in metrics_to_compare:
            core_val = core_metrics.get(metric_key, 0)
            dynamic_val = dynamic_metrics.get(metric_key, 0)
            
            if format_type == 'percent':
                core_str = f"{core_val:.2f}%" if core_val else "N/A"
                dynamic_str = f"{dynamic_val:.2f}%" if dynamic_val else "N/A"
            elif format_type == 'currency':
                core_str = f"${core_val:.2f}" if core_val else "N/A"
                dynamic_str = f"${dynamic_val:.2f}" if dynamic_val else "N/A"
            elif format_type == 'decimal':
                core_str = f"{core_val:.3f}" if core_val else "N/A"
                dynamic_str = f"{dynamic_val:.3f}" if dynamic_val else "N/A"
            else:  # int
                core_str = str(int(core_val)) if core_val else "0"
                dynamic_str = str(int(dynamic_val)) if dynamic_val else "0"
            
            # Highlight winner
            if format_type in ['percent', 'decimal', 'currency'] and core_val and dynamic_val:
                if metric_key in ['win_rate', 'avg_pnl', 'total_pnl', 'avg_rr', 'sharpe', 'best_trade']:
                    # Higher is better
                    winner = 'CORE' if core_val > dynamic_val else 'DYNAMIC_MOVERS'
                    if core_val > dynamic_val:
                        core_str = self.style.SUCCESS(core_str + ' ⭐')
                    else:
                        dynamic_str = self.style.SUCCESS(dynamic_str + ' ⭐')
                elif metric_key in ['max_dd', 'worst_trade']:
                    # Lower is better (less negative)
                    if core_val > dynamic_val:
                        core_str = self.style.SUCCESS(core_str + ' ⭐')
                    else:
                        dynamic_str = self.style.SUCCESS(dynamic_str + ' ⭐')
            
            self.stdout.write(f'{metric_name:<30} {core_str:<25} {dynamic_str:<25}')
        
        self.stdout.write(self.style.SUCCESS('─'*80))
        self.stdout.write('')
        
        # Summary recommendation
        if core_metrics.get('total_signals', 0) > 10 and dynamic_metrics.get('total_signals', 0) > 10:
            self._print_recommendation(core_metrics, dynamic_metrics)
        
        self.stdout.write('')

    def _calculate_metrics(self, signals_qs, horizon):
        """Calculate performance metrics for a set of signals"""
        total_signals = signals_qs.count()
        
        if total_signals == 0:
            return {
                'total_signals': 0,
                'signals_with_perf': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'avg_rr': 0,
                'sharpe': 0,
                'max_dd': 0,
                'best_trade': 0,
                'worst_trade': 0,
            }
        
        # Get performance data for these signals at the specified horizon
        perf_qs = SignalPerformance.objects.filter(
            signal__in=signals_qs,
            horizon=horizon
        )
        
        signals_with_perf = perf_qs.values('signal').distinct().count()
        
        if signals_with_perf == 0:
            return {
                'total_signals': total_signals,
                'signals_with_perf': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'avg_rr': 0,
                'sharpe': 0,
                'max_dd': 0,
                'best_trade': 0,
                'worst_trade': 0,
            }
        
        # Calculate PnL metrics (use pnl_dollars for dollar-based comparison)
        pnl_values = list(perf_qs.values_list('pnl_dollars', flat=True))
        pnl_values = [float(p) for p in pnl_values if p is not None]
        
        if not pnl_values:
            return {
                'total_signals': total_signals,
                'signals_with_perf': signals_with_perf,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'avg_rr': 0,
                'sharpe': 0,
                'max_dd': 0,
                'best_trade': 0,
                'worst_trade': 0,
            }
        
        wins = sum(1 for pnl in pnl_values if pnl > 0)
        losses = sum(1 for pnl in pnl_values if pnl < 0)
        win_rate = (wins / len(pnl_values)) * 100 if pnl_values else 0
        
        avg_pnl = sum(pnl_values) / len(pnl_values)
        total_pnl = sum(pnl_values)
        best_trade = max(pnl_values)
        worst_trade = min(pnl_values)
        
        # Calculate max drawdown (simplified - cumulative PnL)
        cumulative_pnl = []
        running_total = 0
        for pnl in pnl_values:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        if cumulative_pnl:
            peak = cumulative_pnl[0]
            max_dd = 0
            for val in cumulative_pnl:
                if val > peak:
                    peak = val
                dd = peak - val
                if dd > max_dd:
                    max_dd = dd
        else:
            max_dd = 0
        
        # Calculate Sharpe ratio (simplified)
        if len(pnl_values) > 1:
            mean_pnl = avg_pnl
            std_pnl = math.sqrt(sum((x - mean_pnl) ** 2 for x in pnl_values) / len(pnl_values))
            sharpe = (mean_pnl / std_pnl) if std_pnl > 0 else 0
        else:
            sharpe = 0
        
        # Calculate average R:R (Risk:Reward)
        # R:R = average win / average loss (absolute values)
        wins_list = [pnl for pnl in pnl_values if pnl > 0]
        losses_list = [abs(pnl) for pnl in pnl_values if pnl < 0]
        
        avg_win = sum(wins_list) / len(wins_list) if wins_list else 0
        avg_loss = sum(losses_list) / len(losses_list) if losses_list else 0
        
        avg_rr = (avg_win / avg_loss) if avg_loss > 0 else 0
        
        return {
            'total_signals': total_signals,
            'signals_with_perf': signals_with_perf,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'avg_rr': avg_rr,
            'sharpe': sharpe,
            'max_dd': max_dd,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
        }

    def _print_recommendation(self, core_metrics, dynamic_metrics):
        """Print a recommendation based on the metrics"""
        self.stdout.write(self.style.SUCCESS('📊 RECOMMENDATION:'))
        self.stdout.write('─'*80)
        
        core_score = 0
        dynamic_score = 0
        
        # Score based on key metrics (higher is better)
        if core_metrics.get('win_rate', 0) > dynamic_metrics.get('win_rate', 0):
            core_score += 1
        elif dynamic_metrics.get('win_rate', 0) > core_metrics.get('win_rate', 0):
            dynamic_score += 1
        
        if core_metrics.get('avg_pnl', 0) > dynamic_metrics.get('avg_pnl', 0):
            core_score += 1
        elif dynamic_metrics.get('avg_pnl', 0) > core_metrics.get('avg_pnl', 0):
            dynamic_score += 1
        
        if core_metrics.get('sharpe', 0) > dynamic_metrics.get('sharpe', 0):
            core_score += 1
        elif dynamic_metrics.get('sharpe', 0) > core_metrics.get('sharpe', 0):
            dynamic_score += 1
        
        if core_metrics.get('avg_rr', 0) > dynamic_metrics.get('avg_rr', 0):
            core_score += 1
        elif dynamic_metrics.get('avg_rr', 0) > core_metrics.get('avg_rr', 0):
            dynamic_score += 1
        
        if core_score > dynamic_score:
            self.stdout.write(self.style.SUCCESS(
                f'✅ CORE universe is performing better ({core_score} vs {dynamic_score} key metrics)'
            ))
            self.stdout.write('   Consider using CORE for more stable, proven setups.')
        elif dynamic_score > core_score:
            self.stdout.write(self.style.SUCCESS(
                f'✅ DYNAMIC_MOVERS universe is performing better ({dynamic_score} vs {core_score} key metrics)'
            ))
            self.stdout.write('   Dynamic discovery is finding better opportunities!')
        else:
            self.stdout.write('⚖️  Both universes performing similarly.')
            self.stdout.write('   Consider using both or alternating based on market conditions.')
        
        self.stdout.write('─'*80)

