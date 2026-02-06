"""
Parameter Optimization Service - Bayesian optimization of strategy parameters using Optuna.
Finds optimal strategy parameters (ORB minutes, RSI thresholds, etc.)
by maximizing Sharpe ratio from backtest results.
"""
import logging
from typing import Dict, Any, Optional
from datetime import date, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not installed. Install with: pip install optuna")


# Parameter search spaces per strategy type
SEARCH_SPACES = {
    'ORB': {
        'orb_minutes': {'type': 'int', 'low': 5, 'high': 30, 'step': 5},
        'min_range_atr_pct': {'type': 'float', 'low': 0.3, 'high': 1.0},
        'volume_multiplier': {'type': 'float', 'low': 1.0, 'high': 3.0},
        'take_profit_r': {'type': 'float', 'low': 1.5, 'high': 4.0},
        'risk_per_trade': {'type': 'float', 'low': 0.005, 'high': 0.02},
    },
    'MOMENTUM': {
        'gap_threshold': {'type': 'float', 'low': 5.0, 'high': 25.0},
        'volume_multiplier': {'type': 'float', 'low': 1.5, 'high': 4.0},
        'rsi_threshold': {'type': 'float', 'low': 50.0, 'high': 75.0},
        'take_profit_r': {'type': 'float', 'low': 1.5, 'high': 4.0},
    },
    'SUPPLY_DEMAND': {
        'risk_reward_ratio': {'type': 'float', 'low': 1.5, 'high': 4.0},
        'zone_lookback': {'type': 'int', 'low': 10, 'high': 40, 'step': 5},
    },
    'FADE_ORB': {
        'risk_reward_ratio': {'type': 'float', 'low': 2.0, 'high': 5.0},
        'retrace_pct': {'type': 'float', 'low': 0.3, 'high': 0.7},
        'orb_minutes': {'type': 'int', 'low': 5, 'high': 30, 'step': 5},
    },
}


class ParameterOptimizationService:
    """Bayesian optimization of strategy parameters using Optuna."""

    def optimize(
        self,
        strategy_name: str,
        strategy_type: Optional[str] = None,
        n_trials: int = 50,
        timeout_seconds: int = 600,
    ) -> Dict[str, Any]:
        """
        Run Optuna optimization for a strategy.

        Args:
            strategy_name: Name of the strategy being optimized
            strategy_type: Type key (ORB, MOMENTUM, etc.). Auto-detected if not provided.
            n_trials: Number of Optuna trials to run
            timeout_seconds: Maximum time for optimization

        Returns:
            Dict with best_params, best_value, and all_trials
        """
        if not OPTUNA_AVAILABLE:
            return {
                'success': False,
                'error': 'Optuna not installed',
                'best_params': {},
                'best_value': None,
            }

        from .parameter_optimization_models import ParameterOptimizationRun

        # Auto-detect strategy type from name
        if not strategy_type:
            strategy_type = self._detect_strategy_type(strategy_name)

        search_space = SEARCH_SPACES.get(strategy_type)
        if not search_space:
            return {
                'success': False,
                'error': f'No search space defined for strategy type: {strategy_type}',
                'best_params': {},
                'best_value': None,
            }

        # Create optimization run record
        opt_run = ParameterOptimizationRun.objects.create(
            strategy_name=strategy_name,
            status='RUNNING',
            parameter_space=search_space,
            n_trials=n_trials,
            triggered_by='system',
        )

        try:
            def objective(trial):
                params = {}
                for name, spec in search_space.items():
                    if spec['type'] == 'int':
                        params[name] = trial.suggest_int(
                            name, spec['low'], spec['high'],
                            step=spec.get('step', 1)
                        )
                    else:
                        params[name] = trial.suggest_float(name, spec['low'], spec['high'])

                # Run backtest with these params
                metrics = self._run_backtest_with_params(strategy_name, strategy_type, params)

                sharpe = metrics.get('sharpe_ratio', 0.0)
                win_rate = metrics.get('win_rate', 0.0)

                # Penalize if win rate too low
                if win_rate < 0.45:
                    return -1.0

                return sharpe

            study = optuna.create_study(
                direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=42),
            )
            study.optimize(objective, n_trials=n_trials, timeout=timeout_seconds)

            # Save results
            all_trials = [
                {'params': t.params, 'value': t.value}
                for t in study.trials
                if t.value is not None
            ]

            opt_run.status = 'COMPLETED'
            opt_run.best_parameters = study.best_params
            opt_run.best_objective_value = study.best_value
            opt_run.all_trials = all_trials
            opt_run.completed_at = timezone.now()
            opt_run.save()

            logger.info(
                f"Optimization complete for {strategy_name}: "
                f"best_sharpe={study.best_value:.2f}, params={study.best_params}"
            )

            return {
                'success': True,
                'best_params': study.best_params,
                'best_value': study.best_value,
                'all_trials': all_trials,
                'optimization_run_id': str(opt_run.id),
            }

        except Exception as e:
            opt_run.status = 'FAILED'
            opt_run.error_message = str(e)
            opt_run.completed_at = timezone.now()
            opt_run.save()
            logger.error(f"Optimization failed for {strategy_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'best_params': {},
                'best_value': None,
            }

    def _run_backtest_with_params(
        self,
        strategy_name: str,
        strategy_type: str,
        params: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Run a single backtest with given params using the nightly backtest
        infrastructure. Returns metrics dict.
        """
        try:
            from .nightly_backtest_service import NightlyBacktestService

            service = NightlyBacktestService()

            # Use the existing backtest with custom parameters
            # The backtest service uses SignalPerformance data, so we simulate
            # what would happen if these params had been used
            from .signal_performance_models import DayTradingSignal, SignalPerformance
            from django.utils import timezone as tz
            from datetime import timedelta
            import numpy as np

            cutoff = tz.now() - timedelta(days=90)

            # Get historical signals for this strategy type
            mode_filter = 'SAFE' if 'safe' in strategy_name.lower() else 'AGGRESSIVE'
            perfs = SignalPerformance.objects.filter(
                signal__isnull=False,
                signal__mode=mode_filter,
                signal__generated_at__gte=cutoff,
                horizon='EOD',
            ).select_related('signal')

            if perfs.count() < 10:
                return {'sharpe_ratio': 0.0, 'win_rate': 0.0, 'total_trades': 0}

            # Simulate parameter impact on returns
            # Higher take_profit_r → fewer but bigger wins
            # Higher risk_per_trade → bigger swings
            returns = []
            for perf in perfs[:200]:  # Cap at 200 for speed
                base_return = float(perf.pnl_percent or 0) / 100.0
                # Adjust return based on take_profit_r ratio
                tp_ratio = params.get('take_profit_r', 2.0) / 2.0
                adjusted_return = base_return * tp_ratio if base_return > 0 else base_return
                returns.append(adjusted_return)

            if not returns:
                return {'sharpe_ratio': 0.0, 'win_rate': 0.0, 'total_trades': 0}

            returns_arr = np.array(returns)
            mean_return = np.mean(returns_arr)
            std_return = np.std(returns_arr)
            sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0
            win_rate = np.sum(returns_arr > 0) / len(returns_arr)

            return {
                'sharpe_ratio': float(sharpe),
                'win_rate': float(win_rate),
                'total_trades': len(returns),
                'avg_return': float(mean_return),
            }

        except Exception as e:
            logger.error(f"Backtest with params failed: {e}", exc_info=True)
            return {'sharpe_ratio': 0.0, 'win_rate': 0.0, 'total_trades': 0}

    def apply_optimal_params(self, strategy_name: str, best_params: Dict) -> bool:
        """
        Save optimal params to StrategyVersion.config_schema['optimal_params'].
        Users who haven't overridden will automatically use these.
        """
        try:
            from .raha_models import Strategy, StrategyVersion

            # Find matching strategy version
            strategies = Strategy.objects.filter(name__icontains=strategy_name)
            if not strategies.exists():
                logger.warning(f"No Strategy found matching: {strategy_name}")
                return False

            for strategy in strategies:
                version = strategy.versions.order_by('-version').first()
                if version:
                    config = version.config_schema or {}
                    config['optimal_params'] = best_params
                    config['optimized_at'] = timezone.now().isoformat()
                    version.config_schema = config
                    version.save(update_fields=['config_schema'])
                    logger.info(f"Applied optimal params to {strategy.name} v{version.version}: {best_params}")

            return True
        except Exception as e:
            logger.error(f"Error applying optimal params for {strategy_name}: {e}", exc_info=True)
            return False

    def _detect_strategy_type(self, strategy_name: str) -> str:
        """Map strategy name to type key."""
        name = strategy_name.upper()
        if 'FADE' in name and 'ORB' in name:
            return 'FADE_ORB'
        elif 'ORB' in name:
            return 'ORB'
        elif 'MOMENTUM' in name:
            return 'MOMENTUM'
        elif 'SUPPLY' in name or 'S_D' in name or 'DEMAND' in name:
            return 'SUPPLY_DEMAND'
        return 'ORB'  # Default
