"""
Nightly Backtest Service
Runs global backtests for all strategies nightly to filter weak performers.
Similar to Trade Ideas' Holly system that runs 70+ strategy backtests nightly.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)


class NightlyBacktestService:
    """
    Service for running nightly backtests across all strategies.
    Filters strategies by performance thresholds (Sharpe >1.5, drawdown <20%, etc.)
    """
    
    def __init__(self):
        self.performance_thresholds = {
            'min_sharpe': 1.5,
            'max_drawdown': -0.20,  # -20%
            'min_win_rate': 0.55,  # 55% after costs
            'min_profit_factor': 1.5,  # Gross profit / gross loss
            'min_trades': 30,  # Minimum trades for statistical significance
        }
    
    def run_nightly_backtests(self, days_back: int = 252) -> Dict[str, Any]:
        """
        Run backtests for all active strategies.
        
        Args:
            days_back: How many days of history to backtest
        
        Returns:
            Dictionary with results for each strategy
        """
        logger.info(f"🌙 Starting nightly backtests (last {days_back} days)")
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'strategies_tested': 0,
            'strategies_passed': 0,
            'strategies_failed': 0,
            'strategy_results': {},
            'summary': {}
        }
        
        # Test Day Trading strategies
        day_trading_results = self._backtest_day_trading_strategies(days_back)
        results['strategy_results']['day_trading'] = day_trading_results
        results['strategies_tested'] += day_trading_results.get('count', 0)
        results['strategies_passed'] += day_trading_results.get('passed', 0)
        results['strategies_failed'] += day_trading_results.get('failed', 0)
        
        # Test Swing Trading strategies
        swing_trading_results = self._backtest_swing_trading_strategies(days_back)
        results['strategy_results']['swing_trading'] = swing_trading_results
        results['strategies_tested'] += swing_trading_results.get('count', 0)
        results['strategies_passed'] += swing_trading_results.get('passed', 0)
        results['strategies_failed'] += swing_trading_results.get('failed', 0)
        
        # Test Pre-Market strategies
        pre_market_results = self._backtest_pre_market_strategies(days_back)
        results['strategy_results']['pre_market'] = pre_market_results
        results['strategies_tested'] += pre_market_results.get('count', 0)
        results['strategies_passed'] += pre_market_results.get('passed', 0)
        results['strategies_failed'] += pre_market_results.get('failed', 0)
        
        # Test RAHA strategies
        raha_results = self._backtest_raha_strategies(days_back)
        results['strategy_results']['raha'] = raha_results
        results['strategies_tested'] += raha_results.get('count', 0)
        results['strategies_passed'] += raha_results.get('passed', 0)
        results['strategies_failed'] += raha_results.get('failed', 0)
        
        # Generate summary
        results['summary'] = {
            'pass_rate': results['strategies_passed'] / results['strategies_tested'] if results['strategies_tested'] > 0 else 0.0,
            'recommendation': self._generate_recommendation(results)
        }
        
        # Cache results (24 hours)
        cache.set('nightly_backtest_results', results, timeout=86400)

        # Close the feedback loop: adapt based on results
        self._trigger_adaptations(results)

        logger.info(f"Nightly backtests complete: {results['strategies_passed']}/{results['strategies_tested']} passed")

        return results
    
    def _backtest_day_trading_strategies(self, days_back: int) -> Dict[str, Any]:
        """Backtest day trading strategies"""
        try:
            from .signal_performance_models import DayTradingSignal, SignalPerformance
            
            # Get signals from last N days
            cutoff_date = timezone.now() - timedelta(days=days_back)
            signals = DayTradingSignal.objects.filter(
                generated_at__gte=cutoff_date
            ).select_related()
            
            if signals.count() < self.performance_thresholds['min_trades']:
                return {
                    'count': 0,
                    'passed': 0,
                    'failed': 0,
                    'reason': 'insufficient_data'
                }
            
            # Get performance data
            performances = SignalPerformance.objects.filter(
                signal__in=signals,
                horizon='EOD'  # End of day performance
            )
            
            if performances.count() < self.performance_thresholds['min_trades']:
                return {
                    'count': 1,
                    'passed': 0,
                    'failed': 1,
                    'reason': 'insufficient_performance_data'
                }
            
            # Calculate metrics
            metrics = self._calculate_performance_metrics(performances)
            
            # Check if passes thresholds
            passed = self._check_performance_thresholds(metrics)
            
            return {
                'count': 1,
                'passed': 1 if passed else 0,
                'failed': 0 if passed else 1,
                'metrics': metrics,
                'passed_thresholds': passed
            }
            
        except Exception as e:
            logger.error(f"Error backtesting day trading strategies: {e}")
            return {
                'count': 0,
                'passed': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def _backtest_swing_trading_strategies(self, days_back: int) -> Dict[str, Any]:
        """Backtest swing trading strategies"""
        try:
            from .signal_performance_models import SwingTradingSignal, SignalPerformance
            
            cutoff_date = timezone.now() - timedelta(days=days_back)
            signals = SwingTradingSignal.objects.filter(
                generated_at__gte=cutoff_date
            ).select_related()
            
            if signals.count() < self.performance_thresholds['min_trades']:
                return {
                    'count': 0,
                    'passed': 0,
                    'failed': 0,
                    'reason': 'insufficient_data'
                }
            
            performances = SignalPerformance.objects.filter(
                swing_signal__in=signals,
                horizon__in=['1W', '2W', '1M']  # Weekly/monthly performance
            )
            
            if performances.count() < self.performance_thresholds['min_trades']:
                return {
                    'count': 1,
                    'passed': 0,
                    'failed': 1,
                    'reason': 'insufficient_performance_data'
                }
            
            metrics = self._calculate_performance_metrics(performances)
            passed = self._check_performance_thresholds(metrics)
            
            return {
                'count': 1,
                'passed': 1 if passed else 0,
                'failed': 0 if passed else 1,
                'metrics': metrics,
                'passed_thresholds': passed
            }
            
        except Exception as e:
            logger.error(f"Error backtesting swing trading strategies: {e}")
            return {
                'count': 0,
                'passed': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def _backtest_pre_market_strategies(self, days_back: int) -> Dict[str, Any]:
        """Backtest pre-market scan strategies"""
        # Similar to day trading but with pre-market specific logic
        # For now, return placeholder
        return {
            'count': 0,
            'passed': 0,
            'failed': 0,
            'reason': 'not_implemented'
        }
    
    def _backtest_raha_strategies(self, days_back: int) -> Dict[str, Any]:
        """Backtest RAHA strategies"""
        try:
            from .raha_models import Strategy, StrategyVersion, RAHABacktestRun
            from .raha_backtest_service import RAHABacktestService
            
            # Get active RAHA strategies
            strategies = Strategy.objects.filter(enabled=True)
            
            if strategies.count() == 0:
                return {
                    'count': 0,
                    'passed': 0,
                    'failed': 0,
                    'reason': 'no_active_strategies'
                }
            
            results = []
            passed_count = 0
            failed_count = 0
            
            for strategy in strategies:
                try:
                    # Get latest strategy version
                    version = StrategyVersion.objects.filter(
                        strategy=strategy
                    ).order_by('-created_at').first()
                    
                    if not version:
                        continue
                    
                    # Run backtest for this strategy
                    backtest_result = self._run_raha_backtest(version, days_back)
                    
                    if backtest_result['passed']:
                        passed_count += 1
                    else:
                        failed_count += 1
                    
                    results.append({
                        'strategy': strategy.name,
                        'version': version.version,
                        'metrics': backtest_result.get('metrics', {}),
                        'passed': backtest_result['passed']
                    })
                    
                except Exception as e:
                    logger.warning(f"Error backtesting RAHA strategy {strategy.name}: {e}")
                    failed_count += 1
            
            return {
                'count': len(results),
                'passed': passed_count,
                'failed': failed_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error backtesting RAHA strategies: {e}")
            return {
                'count': 0,
                'passed': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def _run_raha_backtest(self, strategy_version, days_back: int) -> Dict[str, Any]:
        """Run backtest for a single RAHA strategy"""
        try:
            # Use existing RAHA backtest service
            from .raha_backtest_service import RAHABacktestService
            from .raha_models import RAHABacktestRun
            
            # Create backtest run
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Use SPY as default symbol (most reliable data)
            backtest = RAHABacktestRun.objects.create(
                user=None,  # System backtest
                strategy_version=strategy_version,
                symbol='SPY',
                timeframe='5m',
                start_date=start_date,
                end_date=end_date,
                parameters={},
                status='PENDING'
            )
            
            # Run backtest
            backtest_service = RAHABacktestService()
            result = backtest_service.run_backtest(str(backtest.id))
            
            # Extract metrics
            metrics = result.metrics or {}
            
            # Check thresholds
            passed = self._check_performance_thresholds(metrics)
            
            return {
                'passed': passed,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.warning(f"Error running RAHA backtest: {e}")
            return {
                'passed': False,
                'metrics': {},
                'error': str(e)
            }
    
    def _calculate_performance_metrics(self, performances) -> Dict[str, float]:
        """Calculate performance metrics from SignalPerformance records"""
        if performances.count() == 0:
            return {}
        
        # Extract PnL values
        pnl_values = [float(p.pnl_percent) for p in performances if p.pnl_percent is not None]
        
        if len(pnl_values) == 0:
            return {}
        
        pnl_array = np.array(pnl_values)
        
        # Calculate metrics
        total_return = float(np.sum(pnl_array))
        win_rate = float(np.sum(pnl_array > 0) / len(pnl_array))
        
        # Winning and losing trades
        winning_trades = pnl_array[pnl_array > 0]
        losing_trades = pnl_array[pnl_array < 0]
        
        avg_win = float(np.mean(winning_trades)) if len(winning_trades) > 0 else 0.0
        avg_loss = float(np.mean(losing_trades)) if len(losing_trades) > 0 else 0.0
        
        # Profit factor
        gross_profit = float(np.sum(winning_trades)) if len(winning_trades) > 0 else 0.0
        gross_loss = abs(float(np.sum(losing_trades))) if len(losing_trades) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        
        # Sharpe ratio (simplified - assumes daily returns)
        if len(pnl_array) > 1:
            sharpe_ratio = float(np.mean(pnl_array) / np.std(pnl_array) * np.sqrt(252)) if np.std(pnl_array) > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown (simplified)
        cumulative = np.cumsum(pnl_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(pnl_array),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }
    
    def _check_performance_thresholds(self, metrics: Dict[str, float]) -> bool:
        """Check if metrics pass performance thresholds"""
        if not metrics:
            return False
        
        checks = [
            metrics.get('sharpe_ratio', 0) >= self.performance_thresholds['min_sharpe'],
            metrics.get('max_drawdown', 0) >= self.performance_thresholds['max_drawdown'],  # max_drawdown is negative
            metrics.get('win_rate', 0) >= self.performance_thresholds['min_win_rate'],
            metrics.get('profit_factor', 0) >= self.performance_thresholds['min_profit_factor'],
            metrics.get('total_trades', 0) >= self.performance_thresholds['min_trades']
        ]
        
        return all(checks)
    
    def _trigger_adaptations(self, results: Dict[str, Any]):
        """
        Close the feedback loop: adapt the system based on backtest results.
        1. Feed rewards to bandit (Thompson Sampling)
        2. Update strategy health records
        3. Trigger parameter optimization for failing strategies
        4. Auto-disable consistently failing strategies
        5. Re-enable long-disabled strategies with optimized params
        """
        try:
            from .bandit_service import BanditService
            from .signal_performance_models import StrategyHealthRecord

            bandit = BanditService()

            for category, category_results in results.get('strategy_results', {}).items():
                if not isinstance(category_results, dict):
                    continue

                for strat_result in category_results.get('results', []):
                    strategy_name = strat_result.get('strategy', strat_result.get('name', ''))
                    if not strategy_name:
                        continue

                    passed = strat_result.get('passed', False)
                    strategy_slug = strategy_name.lower().replace(' ', '_').replace('-', '_')

                    # 1. Update bandit
                    reward = 1.0 if passed else 0.0
                    bandit.update_reward(strategy_slug, reward)

                    # 2. Update health record
                    health, _ = StrategyHealthRecord.objects.get_or_create(
                        strategy_name=strategy_name,
                    )
                    health.last_backtest_date = timezone.now().date()
                    health.last_backtest_passed = passed

                    if passed:
                        health.consecutive_passes += 1
                        health.consecutive_failures = 0
                    else:
                        health.consecutive_failures += 1
                        health.consecutive_passes = 0

                    health.save()

                    # 3. Trigger parameter optimization for failing strategies
                    if not passed:
                        try:
                            from .celery_tasks import run_parameter_optimization_task
                            run_parameter_optimization_task.delay(strategy_name)
                            logger.info(f"Triggered parameter optimization for failing strategy: {strategy_name}")
                        except Exception as e:
                            logger.debug(f"Could not trigger optimization for {strategy_name}: {e}")

                    # 4. Auto-disable if 3+ consecutive failures
                    if health.consecutive_failures >= 3 and not health.auto_disabled:
                        health.auto_disabled = True
                        health.auto_disabled_at = timezone.now()
                        health.save()
                        logger.warning(f"Auto-disabled strategy {strategy_name} after {health.consecutive_failures} consecutive failures")

                    # 5. Re-enable if disabled 30+ days and optimization has run
                    if health.auto_disabled and health.auto_disabled_at:
                        days_disabled = (timezone.now() - health.auto_disabled_at).days
                        if days_disabled >= 30 and health.last_optimization_at:
                            health.auto_disabled = False
                            health.auto_disabled_at = None
                            health.consecutive_failures = 0
                            health.save()
                            logger.info(f"Re-enabled strategy {strategy_name} after {days_disabled} days (optimized params available)")

            # Recompute bandit allocation weights
            bandit.get_allocation_weights()

        except Exception as e:
            logger.error(f"Error in adaptation trigger: {e}", exc_info=True)

    def _generate_recommendation(self, results: Dict[str, Any]) -> str:
        """Generate recommendation based on backtest results"""
        pass_rate = results['summary'].get('pass_rate', 0.0)

        if pass_rate >= 0.7:
            return "Excellent: Most strategies passing thresholds. System is performing well."
        elif pass_rate >= 0.5:
            return "Moderate: Some strategies need improvement. Review failing strategies."
        else:
            return "Poor: Many strategies failing thresholds. Triggering parameter optimization."


# Celery task for nightly backtests
try:
    from celery import shared_task
    
    @shared_task
    def run_nightly_backtests_task():
        """Celery task to run nightly backtests"""
        service = NightlyBacktestService()
        results = service.run_nightly_backtests()
        logger.info(f"Nightly backtests completed: {results['strategies_passed']}/{results['strategies_tested']} passed")
        return results
except ImportError:
    logger.warning("Celery not available - nightly backtest task not registered")

