"""
Nightly Research Runner - Phase 4: R&D Firepower
Runs automated research cycle to evaluate strategy variants and retire underperformers.

Usage:
    python manage.py run_research_cycle
    python manage.py run_research_cycle --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from datetime import timedelta
from decimal import Decimal
import logging
import math

from core.signal_performance_models import (
    DayTradingSignal, SwingTradingSignal, SignalPerformance, StrategyPerformance
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run nightly research cycle to evaluate strategy variants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be evaluated without saving'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('\n🔬 Starting Research Cycle...'))
        
        # 1. Evaluate current strategy versions
        self.stdout.write('\n📊 Evaluating current strategies...')
        self.evaluate_current_strategies(dry_run)
        
        # 2. Generate and evaluate candidate variants
        self.stdout.write('\n🧪 Testing strategy variants...')
        self.evaluate_candidate_variants(dry_run)
        
        # 3. Compare and promote winners
        self.stdout.write('\n🏆 Comparing strategy performance...')
        self.compare_and_promote(dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Research cycle complete!'))
    
    def evaluate_current_strategies(self, dry_run=False):
        """Evaluate current strategy versions (SAFE, AGGRESSIVE, MOMENTUM, etc.)"""
        now = timezone.now()
        period_start = now - timedelta(days=30)
        
        # Day trading strategies
        for mode in ['SAFE', 'AGGRESSIVE']:
            signals = DayTradingSignal.objects.filter(
                mode=mode,
                generated_at__gte=period_start
            )
            
            performances = SignalPerformance.objects.filter(
                signal__mode=mode,
                signal__generated_at__gte=period_start,
                horizon='EOD'
            )
            
            if performances.count() > 0:
                stats = self._calculate_strategy_stats(performances)
                self.stdout.write(
                    f"  {mode}: {stats['win_rate']:.1f}% win rate, "
                    f"Sharpe {stats['sharpe']:.2f}, {stats['total_signals']} signals"
                )
    
    def evaluate_candidate_variants(self, dry_run=False):
        """
        Generate and evaluate candidate strategy variants.
        For v1, we'll test simple variants like:
        - Different RVOL thresholds
        - Different momentum windows
        - Microstructure-aware filtering
        """
        now = timezone.now()
        period_start = now - timedelta(days=30)
        
        # Example variant: "SAFE with tighter microstructure filter"
        # In production, this would be a separate strategy_id, but for now we'll simulate
        
        variants = [
            {
                'name': 'SAFE_v2_microstructure',
                'description': 'SAFE mode with enhanced microstructure filtering',
                'base_mode': 'SAFE',
            },
            {
                'name': 'AGGRESSIVE_v2_volume',
                'description': 'AGGRESSIVE mode with higher volume threshold',
                'base_mode': 'AGGRESSIVE',
            },
        ]
        
        for variant in variants:
            # In production, you'd have separate signals for each variant
            # For now, we'll use the base mode as proxy
            base_mode = variant['base_mode']
            signals = DayTradingSignal.objects.filter(
                mode=base_mode,
                generated_at__gte=period_start
            )
            
            # Filter by variant criteria (simplified - in production would be separate strategy)
            # For example, microstructure-aware would filter signals with executionQualityScore > 7
            if 'microstructure' in variant['name']:
                # Simulate: only signals with good microstructure
                # In production, this would be a separate strategy_id
                filtered_signals = signals.filter(
                    features__executionQualityScore__gt=7.0
                )
            else:
                filtered_signals = signals
            
            if filtered_signals.count() > 0:
                performances = SignalPerformance.objects.filter(
                    signal__in=filtered_signals,
                    horizon='EOD'
                )
                
                if performances.count() > 0:
                    stats = self._calculate_strategy_stats(performances)
                    self.stdout.write(
                        f"  {variant['name']}: {stats['win_rate']:.1f}% win rate, "
                        f"Sharpe {stats['sharpe']:.2f}, {stats['total_signals']} signals"
                    )
                    
                    if not dry_run:
                        # Create StrategyPerformance record for variant
                        self._create_strategy_performance(
                            variant['name'],
                            'MONTHLY',
                            period_start,
                            now,
                            stats
                        )
    
    def compare_and_promote(self, dry_run=False):
        """Compare strategy versions and log winners"""
        now = timezone.now()
        period_start = now - timedelta(days=30)
        
        # Get all strategy performances for the period
        strategies = StrategyPerformance.objects.filter(
            period='MONTHLY',
            period_start__gte=period_start
        ).order_by('-sharpe_ratio')
        
        if strategies.count() > 1:
            best = strategies.first()
            self.stdout.write(
                f"\n🏆 Best performing strategy: {best.mode} "
                f"(Sharpe: {best.sharpe_ratio:.2f}, Win Rate: {best.win_rate:.1f}%)"
            )
            
            # Log comparison
            logger.info(
                "ResearchCycleComparison",
                extra={
                    "best_strategy": best.mode,
                    "best_sharpe": float(best.sharpe_ratio) if best.sharpe_ratio else 0,
                    "best_win_rate": float(best.win_rate),
                    "total_strategies": strategies.count(),
                }
            )
    
    def _calculate_strategy_stats(self, performances):
        """Calculate stats from performance records"""
        total = performances.count()
        winning = performances.filter(outcome__in=['WIN', 'TARGET_HIT']).count()
        losing = performances.filter(outcome__in=['LOSS', 'STOP_HIT']).count()
        
        win_rate = (winning / total * 100) if total > 0 else 0
        
        returns = [float(p.pnl_percent) for p in performances]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 0.01
            sharpe = (mean_return / std_dev) if std_dev > 0 else 0
        else:
            sharpe = 0
        
        return {
            'total_signals': total,
            'win_rate': win_rate,
            'sharpe': sharpe,
            'winning': winning,
            'losing': losing,
        }
    
    def _create_strategy_performance(
        self,
        strategy_id: str,
        period: str,
        period_start,
        period_end,
        stats: dict
    ):
        """Create or update StrategyPerformance record"""
        StrategyPerformance.objects.update_or_create(
            mode=strategy_id,  # Using mode field for strategy_id
            period=period,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'total_signals': stats['total_signals'],
                'signals_evaluated': stats['total_signals'],
                'winning_signals': stats['winning'],
                'losing_signals': stats['losing'],
                'win_rate': Decimal(str(stats['win_rate'])),
                'sharpe_ratio': Decimal(str(stats['sharpe'])),
            }
        )

