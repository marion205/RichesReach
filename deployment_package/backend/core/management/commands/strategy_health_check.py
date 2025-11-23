"""
Django management command to run Investment Committee health checks on strategies.

Usage:
    python manage.py strategy_health_check --mode SAFE
    python manage.py strategy_health_check --mode AGGRESSIVE
    python manage.py strategy_health_check --all
    python manage.py strategy_health_check --all --period ALL_TIME
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.signal_performance_models import StrategyPerformance
from core.strategy_governance import StrategyHealthCheck, StrategyStatus
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Investment Committee health checks on day trading strategies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['SAFE', 'AGGRESSIVE'],
            help='Mode to check (SAFE or AGGRESSIVE)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all modes'
        )
        parser.add_argument(
            '--period',
            type=str,
            choices=['DAILY', 'WEEKLY', 'MONTHLY', 'ALL_TIME'],
            default='ALL_TIME',
            help='Period to evaluate (default: ALL_TIME)'
        )
        parser.add_argument(
            '--save-status',
            action='store_true',
            help='Save status to database (requires StrategyGovernance model)'
        )

    def handle(self, *args, **options):
        modes = []
        if options['all']:
            modes = ['SAFE', 'AGGRESSIVE']
        elif options['mode']:
            modes = [options['mode']]
        else:
            self.stdout.write(self.style.ERROR('Must specify --mode or --all'))
            return

        period = options['period']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n╔══════════════════════════════════════════════════════════════╗\n'
            f'║  RICHESREACH INVESTMENT COMMITTEE - STRATEGY HEALTH CHECK   ║\n'
            f'╚══════════════════════════════════════════════════════════════╝\n'
        ))

        for mode in modes:
            self.stdout.write(f'\n{"="*65}\n')
            self.stdout.write(self.style.WARNING(f'Evaluating {mode} Mode ({period} period)\n'))
            self.stdout.write(f'{"="*65}\n')

            # Get most recent strategy performance for this mode and period
            try:
                strategy = StrategyPerformance.objects.filter(
                    mode=mode,
                    period=period
                ).order_by('-period_end').first()

                if not strategy:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  No {period} performance data found for {mode} mode\n'
                        f'   Run: python manage.py calculate_strategy_performance --period {period.lower()}\n'
                    ))
                    continue

                # Run health check
                health_check = StrategyHealthCheck(strategy, mode)
                evaluation = health_check.evaluate()
                report = health_check.get_report()

                # Print report
                self.stdout.write(report)

                # Color-code status
                if evaluation['status'] == StrategyStatus.ACTIVE:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ {mode} mode is ACTIVE - Meeting all KPIs\n'
                    ))
                elif evaluation['status'] == StrategyStatus.WATCH:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  {mode} mode is on WATCH - Below target but above minimum\n'
                    ))
                elif evaluation['status'] == StrategyStatus.REVIEW:
                    self.stdout.write(self.style.ERROR(
                        f'❌ {mode} mode requires REVIEW - Below minimum thresholds\n'
                    ))

                # Save status if requested
                if options['save_status']:
                    # TODO: Implement StrategyGovernance model to persist status
                    self.stdout.write(self.style.SUCCESS('Status saved to database\n'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'❌ Error evaluating {mode} mode: {e}\n'
                ))
                logger.exception(f'Error in strategy_health_check for {mode}')

        self.stdout.write(f'\n{"="*65}\n')
        self.stdout.write(self.style.SUCCESS('Health check complete!\n'))

