"""
Celery Tasks for Async Execution
Background tasks for RAHA backtesting and other long-running operations
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Celery
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed. Install with: pip install celery")
    # Create mock decorator for development
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@shared_task(bind=True, max_retries=3)
def run_backtest_async(self, backtest_id: int):
    """
    Run a backtest asynchronously using Celery
    
    Args:
        backtest_id: ID of the backtest run to execute
    """
    try:
        from .raha_backtest_service import RAHABacktestService
        from .raha_models import RAHABacktestRun
        
        logger.info(f"Starting async backtest execution for ID: {backtest_id}")
        
        # Get the backtest run
        backtest = RAHABacktestRun.objects.get(id=backtest_id)
        backtest.status = 'RUNNING'
        backtest.save()
        
        # Execute the backtest
        service = RAHABacktestService()
        service.run_backtest(backtest_id)
        
        logger.info(f"Completed async backtest execution for ID: {backtest_id}")
        return {'status': 'success', 'backtest_id': backtest_id}
        
    except Exception as e:
        logger.error(f"Error in async backtest {backtest_id}: {e}", exc_info=True)
        
        # Update backtest status on failure
        try:
            backtest = RAHABacktestRun.objects.get(id=backtest_id)
            backtest.status = 'FAILED'
            backtest.save()
        except:
            pass
        
        # Retry if possible
        if CELERY_AVAILABLE and self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
        return {'status': 'failed', 'backtest_id': backtest_id, 'error': str(e)}


@shared_task
def process_webhook_async(webhook_id: int):
    """
    Process a banking webhook asynchronously

    Args:
        webhook_id: ID of the webhook event to process
    """
    try:
        from .banking_models import BankWebhookEvent
        from .banking_service import refresh_account_data, sync_transactions

        logger.info(f"Processing webhook ID: {webhook_id}")

        webhook = BankWebhookEvent.objects.get(id=webhook_id)
        event_type = webhook.event_type
        provider_account_id = webhook.provider_account_id

        # Process based on event type
        if event_type == 'ACCOUNT_UPDATE':
            # Refresh account data
            refresh_account_data(provider_account_id)
        elif event_type == 'TRANSACTION_UPDATE':
            # Sync new transactions
            sync_transactions(provider_account_id)
        elif event_type == 'ACCOUNT_DISCONNECTED':
            # Mark account as disconnected
            logger.warning(f"Account {provider_account_id} disconnected")

        # Mark webhook as processed
        webhook.processed = True
        webhook.processed_at = datetime.now()
        webhook.save()

        logger.info(f"Successfully processed webhook ID: {webhook_id}")
        return {'status': 'success', 'webhook_id': webhook_id}

    except Exception as e:
        logger.error(f"Error processing webhook {webhook_id}: {e}", exc_info=True)
        return {'status': 'failed', 'webhook_id': webhook_id, 'error': str(e)}


# ============================================================
# Self-Learning Feedback Loop Tasks
# ============================================================

@shared_task
def update_symbol_execution_profiles_task():
    """
    Daily task: Aggregate execution quality per symbol from UserFill data.
    Updates SymbolExecutionProfile records used by the ML scorer to
    penalize signals for symbols with historically poor execution.
    """
    try:
        from .execution_quality_tracker import ExecutionQualityTracker
        tracker = ExecutionQualityTracker()
        result = tracker.update_all_symbol_profiles()
        logger.info(f"Symbol execution profiles updated: {result}")
        return result
    except Exception as e:
        logger.error(f"Error updating symbol execution profiles: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def trigger_ml_retrain_task():
    """
    Triggered when enough new UserFill records accumulate.
    Forces a day trading ML model retrain.
    """
    try:
        from .day_trading_ml_learner import get_day_trading_ml_learner
        learner = get_day_trading_ml_learner()
        result = learner.train_model(force_retrain=True)
        logger.info(f"ML retrain triggered: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in ML retrain task: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def decay_bandit_priors_task():
    """
    Weekly task: Decay old evidence in bandit posteriors.
    Moves alpha/beta toward uniform prior so the system adapts
    to regime changes rather than being locked into old patterns.
    """
    try:
        from .bandit_service import BanditService
        bandit = BanditService()
        bandit.decay_priors(decay_factor=0.99)
        weights = bandit.get_allocation_weights()
        logger.info(f"Bandit priors decayed, new weights: {weights}")
        return {'weights': weights}
    except Exception as e:
        logger.error(f"Error decaying bandit priors: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def run_parameter_optimization_task(strategy_name: str, n_trials: int = 50):
    """
    On-demand task: Run Optuna Bayesian optimization for a strategy.
    Triggered when a strategy fails nightly backtest performance gates.
    """
    try:
        from .parameter_optimization_service import ParameterOptimizationService

        service = ParameterOptimizationService()
        result = service.optimize(strategy_name=strategy_name, n_trials=n_trials)

        if result.get('success') and result.get('best_params'):
            # Apply optimal params to strategy version
            service.apply_optimal_params(strategy_name, result['best_params'])

            # Update health record
            from .signal_performance_models import StrategyHealthRecord
            from django.utils import timezone
            try:
                health = StrategyHealthRecord.objects.get(strategy_name=strategy_name)
                health.last_optimization_at = timezone.now()
                health.save(update_fields=['last_optimization_at'])
            except StrategyHealthRecord.DoesNotExist:
                pass

        logger.info(f"Parameter optimization for {strategy_name}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in parameter optimization for {strategy_name}: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def optimize_regime_thresholds_task():
    """
    Monthly task: Learn optimal regime detection thresholds using Optuna.
    Finds thresholds that maximize correlation between regime classifications
    and subsequent strategy performance.
    """
    try:
        from .regime_learning_service import RegimeLearningService

        service = RegimeLearningService()
        result = service.optimize_thresholds(n_trials=100)

        if result.get('success') and result.get('best_thresholds'):
            service.apply_thresholds(result['best_thresholds'])

        logger.info(f"Regime threshold optimization: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in regime threshold optimization: {e}", exc_info=True)
        return {'error': str(e)}


# ============================================================
# Revolutionary Improvement Tasks
# ============================================================

@shared_task
def train_shadow_models_task():
    """
    Nightly task: Train candidate ML models with diverse algorithms.
    Each shadow model runs in parallel with the incumbent for 72 hours.
    If a shadow outperforms, it gets promoted to production.
    """
    try:
        from .shadow_model_service import ShadowModelService
        service = ShadowModelService()
        results = service.train_shadow_models()
        service.cleanup_old_shadows()
        logger.info(f"Shadow models trained: {len(results)} candidates")
        return {'models_trained': len(results), 'results': results}
    except Exception as e:
        logger.error(f"Error training shadow models: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def evaluate_shadow_models_task():
    """
    Periodic task (every 6h): Evaluate shadow models that have completed
    their 72-hour validation window. Promote any that beat the incumbent.
    """
    try:
        from .shadow_model_service import ShadowModelService
        service = ShadowModelService()
        results = service.evaluate_shadow_models()
        promoted = [r for r in results if r.get('promoted')]
        logger.info(f"Shadow evaluation: {len(results)} evaluated, {len(promoted)} promoted")
        return {'evaluated': len(results), 'promoted': len(promoted), 'results': results}
    except Exception as e:
        logger.error(f"Error evaluating shadow models: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def train_execution_policy_task():
    """
    Weekly task: Train RL execution policy from accumulated UserFill experiences.
    Learns optimal order type (market/limit/wait) for each market condition.
    """
    try:
        from .execution_rl_service import ExecutionRLService
        service = ExecutionRLService()
        result = service.train_policy()
        logger.info(f"Execution RL policy trained: {result}")
        return result
    except Exception as e:
        logger.error(f"Error training execution policy: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def train_hmm_regime_task():
    """
    Monthly task: Train HMM regime detector on historical market data.
    Runs before regime threshold optimization to provide fresh HMM model.
    """
    try:
        from .hmm_regime_detector import HMMRegimeDetector
        from .options_regime_detector import RegimeDetector
        import pandas as pd

        detector = HMMRegimeDetector()

        # Try to load historical data for SPY
        try:
            from .options_regime_integration import RegimeDetectionService
            service = RegimeDetectionService()
            df = service.get_market_data_for_symbol('SPY')
            if df is not None and len(df) >= 252:
                rule_detector = RegimeDetector()
                df = rule_detector.calculate_indicators(df)
                result = detector.train(df)
                logger.info(f"HMM regime model trained: {result}")
                return result
        except Exception:
            pass

        logger.info("HMM training skipped: insufficient market data")
        return {'success': False, 'error': 'Insufficient market data for HMM training'}
    except Exception as e:
        logger.error(f"Error training HMM regime model: {e}", exc_info=True)
        return {'error': str(e)}


# ============================================================
# DeFi Yield Data Tasks
# ============================================================

@shared_task(bind=True, max_retries=3)
def fetch_defi_yields(self):
    """
    Periodic task (every 5 minutes): Fetch live yield data from DefiLlama,
    persist to database, and cache in Redis for fast GraphQL queries.
    """
    try:
        from .defi_data_service import (
            fetch_defi_llama_pools,
            sync_pools_to_database,
            cache_top_yields,
        )

        logger.info("Starting DeFi yield data fetch from DefiLlama...")

        # 1. Fetch from DefiLlama API
        pools = fetch_defi_llama_pools()
        if not pools:
            logger.warning("No pools returned from DefiLlama, skipping sync")
            return {'status': 'no_data', 'pools_fetched': 0}

        # 2. Sync to database
        snapshot_count = sync_pools_to_database(pools)

        # 3. Update Redis cache
        cache_top_yields()

        logger.info(
            f"DeFi yield sync complete: {len(pools)} pools fetched, "
            f"{snapshot_count} snapshots created"
        )
        return {
            'status': 'success',
            'pools_fetched': len(pools),
            'snapshots_created': snapshot_count,
        }

    except Exception as e:
        logger.error(f"Error fetching DeFi yields: {e}", exc_info=True)
        if CELERY_AVAILABLE and self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        return {'status': 'failed', 'error': str(e)}


@shared_task
def cleanup_defi_snapshots():
    """
    Weekly task: Remove old yield snapshots to keep database manageable.
    Retains 90 days of historical data for analytics.
    """
    try:
        from .defi_data_service import cleanup_old_snapshots
        deleted = cleanup_old_snapshots(days_to_keep=90)
        logger.info(f"DeFi snapshot cleanup: {deleted} old records removed")
        return {'status': 'success', 'deleted': deleted}
    except Exception as e:
        logger.error(f"Error cleaning up DeFi snapshots: {e}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}


@shared_task
def monitor_defi_health_factors():
    """
    Periodic task (every 5 minutes): Monitor all active DeFi positions
    and send alerts for health factor warnings, APY changes, and harvest opportunities.
    """
    try:
        from .defi_alert_service import check_all_positions
        result = check_all_positions()
        logger.info(f"DeFi health monitor: {result}")
        return {'status': 'success', **result}
    except Exception as e:
        logger.error(f"Error in DeFi health monitor: {e}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}


@shared_task
def evaluate_strategy_rotations():
    """
    Periodic task (every 30 minutes): Evaluate all active DeFi positions
    for rotation opportunities and auto-compound triggers.

    Uses 7-day rolling average APY to avoid false signals from temporary spikes.
    Checks: APY improvement > 20%, risk delta < 20%, TVL > $100k, position age > 24h.
    """
    try:
        from .defi_strategy_engine import StrategyEvaluation
        engine = StrategyEvaluation()
        result = engine.auto_compound_check()
        logger.info(f"Strategy rotation evaluation complete: {result}")
        return {'status': 'success', **result}
    except Exception as e:
        logger.error(f"Error in strategy rotation evaluation: {e}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}
