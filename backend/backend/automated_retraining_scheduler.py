"""
Automated Retraining Scheduler for Production Alpha System
Handles scheduled retraining, performance monitoring, and model deployment
"""

import schedule
import time
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
from dataclasses import asdict

# Import the production alpha system
try:
    from production_alpha_system import ProductionAlphaSystem, PerformanceMetrics
    PRODUCTION_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Production Alpha System not available: {e}")
    PRODUCTION_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)

class AutomatedRetrainingScheduler:
    """
    Automated retraining scheduler with performance monitoring and alerting
    """
    
    def __init__(self):
        self.production_system = None
        self.retraining_config = {
            'daily_retrain': True,
            'weekly_full_retrain': True,
            'monthly_deep_retrain': True,
            'performance_threshold_r2': 0.02,  # Minimum R² threshold
            'performance_threshold_rank_ic': 0.05,  # Minimum Rank-IC threshold
            'alert_on_degradation': True,
            'auto_deploy_on_improvement': True
        }
        
        self.retraining_history = []
        self.performance_alerts = []
        
        if PRODUCTION_SYSTEM_AVAILABLE:
            self.production_system = ProductionAlphaSystem()
            logger.info("Automated Retraining Scheduler initialized with Production Alpha System")
        else:
            logger.warning("Automated Retraining Scheduler initialized without Production Alpha System")
    
    def setup_schedules(self):
        """Set up automated retraining schedules"""
        
        # Daily incremental retraining (lightweight)
        if self.retraining_config['daily_retrain']:
            schedule.every().day.at("06:00").do(self.daily_incremental_retrain)
            logger.info("Daily incremental retraining scheduled for 06:00")
        
        # Weekly full retraining
        if self.retraining_config['weekly_full_retrain']:
            schedule.every().sunday.at("02:00").do(self.weekly_full_retrain)
            logger.info("Weekly full retraining scheduled for Sunday 02:00")
        
        # Monthly deep retraining with extended data
        if self.retraining_config['monthly_deep_retrain']:
            schedule.every().month.do(self.monthly_deep_retrain)
            logger.info("Monthly deep retraining scheduled")
        
        # Performance monitoring every 4 hours
        schedule.every(4).hours.do(self.performance_monitoring_check)
        logger.info("Performance monitoring scheduled every 4 hours")
        
        # Model health check every hour
        schedule.every().hour.do(self.model_health_check)
        logger.info("Model health check scheduled every hour")
    
    def daily_incremental_retrain(self):
        """Daily incremental retraining with recent data"""
        try:
            logger.info("Starting daily incremental retraining...")
            
            if not self.production_system:
                logger.error("Production system not available for retraining")
                return
            
            # Load existing models
            self.production_system.load_models()
            
            # Run incremental training (smaller dataset, faster)
            start_time = datetime.now()
            
            # Use smaller dataset for daily retraining
            from enhanced_r2_model import EnhancedR2Model
            base_model = EnhancedR2Model()
            df = base_model.fetch_panel_data()
            
            # Use only recent data for incremental training
            recent_df = df.tail(1000)  # Last 1000 records
            
            # Run training
            results = self.production_system.full_training_pipeline(recent_df)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log retraining results
            retraining_record = {
                'timestamp': start_time.isoformat(),
                'type': 'daily_incremental',
                'duration_seconds': duration,
                'results': results,
                'status': 'success'
            }
            
            self.retraining_history.append(retraining_record)
            
            # Check if we should deploy
            if self.retraining_config['auto_deploy_on_improvement']:
                self.check_and_deploy_if_improved(results)
            
            logger.info(f"Daily incremental retraining completed in {duration:.2f} seconds")
            logger.info(f"Overall R²: {results.get('overall_r2', 0):.4f}")
            
        except Exception as e:
            logger.error(f"Daily incremental retraining failed: {e}")
            self.retraining_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'daily_incremental',
                'status': 'failed',
                'error': str(e)
            })
    
    def weekly_full_retrain(self):
        """Weekly full retraining with complete dataset"""
        try:
            logger.info("Starting weekly full retraining...")
            
            if not self.production_system:
                logger.error("Production system not available for retraining")
                return
            
            start_time = datetime.now()
            
            # Use full dataset for weekly retraining
            from enhanced_r2_model import EnhancedR2Model
            base_model = EnhancedR2Model()
            df = base_model.fetch_panel_data()
            
            # Run full training
            results = self.production_system.full_training_pipeline(df)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log retraining results
            retraining_record = {
                'timestamp': start_time.isoformat(),
                'type': 'weekly_full',
                'duration_seconds': duration,
                'results': results,
                'status': 'success'
            }
            
            self.retraining_history.append(retraining_record)
            
            # Check if we should deploy
            if self.retraining_config['auto_deploy_on_improvement']:
                self.check_and_deploy_if_improved(results)
            
            logger.info(f"Weekly full retraining completed in {duration:.2f} seconds")
            logger.info(f"Overall R²: {results.get('overall_r2', 0):.4f}")
            
        except Exception as e:
            logger.error(f"Weekly full retraining failed: {e}")
            self.retraining_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'weekly_full',
                'status': 'failed',
                'error': str(e)
            })
    
    def monthly_deep_retrain(self):
        """Monthly deep retraining with extended historical data"""
        try:
            logger.info("Starting monthly deep retraining...")
            
            if not self.production_system:
                logger.error("Production system not available for retraining")
                return
            
            start_time = datetime.now()
            
            # Use extended dataset for monthly retraining
            from enhanced_r2_model import EnhancedR2Model
            base_model = EnhancedR2Model()
            
            # Extend date range for monthly retraining
            base_model.start = "2010-01-01"  # Extended historical data
            df = base_model.fetch_panel_data()
            
            # Run full training with extended data
            results = self.production_system.full_training_pipeline(df)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log retraining results
            retraining_record = {
                'timestamp': start_time.isoformat(),
                'type': 'monthly_deep',
                'duration_seconds': duration,
                'results': results,
                'status': 'success'
            }
            
            self.retraining_history.append(retraining_record)
            
            # Check if we should deploy
            if self.retraining_config['auto_deploy_on_improvement']:
                self.check_and_deploy_if_improved(results)
            
            logger.info(f"Monthly deep retraining completed in {duration:.2f} seconds")
            logger.info(f"Overall R²: {results.get('overall_r2', 0):.4f}")
            
        except Exception as e:
            logger.error(f"Monthly deep retraining failed: {e}")
            self.retraining_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'monthly_deep',
                'status': 'failed',
                'error': str(e)
            })
    
    def performance_monitoring_check(self):
        """Check performance metrics and alert if degraded"""
        try:
            if not self.production_system:
                return
            
            # Get current performance summary
            perf_summary = self.production_system.get_performance_summary()
            
            if 'error' in perf_summary:
                logger.warning(f"Performance monitoring check failed: {perf_summary['error']}")
                return
            
            # Check performance thresholds
            current_r2 = perf_summary.get('latest_r2', 0)
            current_rank_ic = perf_summary.get('latest_rank_ic', 0)
            
            r2_threshold = self.retraining_config['performance_threshold_r2']
            rank_ic_threshold = self.retraining_config['performance_threshold_rank_ic']
            
            # Check for performance degradation
            if current_r2 < r2_threshold or current_rank_ic < rank_ic_threshold:
                alert = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'performance_degradation',
                    'current_r2': current_r2,
                    'current_rank_ic': current_rank_ic,
                    'r2_threshold': r2_threshold,
                    'rank_ic_threshold': rank_ic_threshold,
                    'severity': 'high' if current_r2 < r2_threshold * 0.5 else 'medium'
                }
                
                self.performance_alerts.append(alert)
                logger.warning(f"Performance degradation alert: R²={current_r2:.4f}, Rank-IC={current_rank_ic:.4f}")
                
                # Trigger emergency retraining if severe degradation
                if alert['severity'] == 'high':
                    logger.warning("Severe performance degradation detected - triggering emergency retraining")
                    self.emergency_retrain()
            
            logger.info(f"Performance monitoring check completed: R²={current_r2:.4f}, Rank-IC={current_rank_ic:.4f}")
            
        except Exception as e:
            logger.error(f"Performance monitoring check failed: {e}")
    
    def model_health_check(self):
        """Check model health and availability"""
        try:
            if not self.production_system:
                return
            
            # Check if models are loaded
            if not self.production_system.regime_models:
                logger.warning("No regime models loaded - attempting to load")
                self.production_system.load_models()
            
            # Check model file existence
            model_dir = "models"
            if not os.path.exists(model_dir):
                logger.warning("Models directory does not exist")
                return
            
            # Check for recent model files
            model_files = [f for f in os.listdir(model_dir) if f.endswith('.joblib')]
            if not model_files:
                logger.warning("No model files found - triggering emergency retraining")
                self.emergency_retrain()
                return
            
            # Check model file ages
            for model_file in model_files:
                file_path = os.path.join(model_dir, model_file)
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age.days > 7:  # Models older than 7 days
                    logger.warning(f"Model file {model_file} is {file_age.days} days old")
            
            logger.info(f"Model health check completed - {len(model_files)} model files found")
            
        except Exception as e:
            logger.error(f"Model health check failed: {e}")
    
    def emergency_retrain(self):
        """Emergency retraining when performance is severely degraded"""
        try:
            logger.warning("Starting emergency retraining...")
            
            if not self.production_system:
                logger.error("Production system not available for emergency retraining")
                return
            
            start_time = datetime.now()
            
            # Use full dataset for emergency retraining
            from enhanced_r2_model import EnhancedR2Model
            base_model = EnhancedR2Model()
            df = base_model.fetch_panel_data()
            
            # Run full training
            results = self.production_system.full_training_pipeline(df)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log emergency retraining
            retraining_record = {
                'timestamp': start_time.isoformat(),
                'type': 'emergency',
                'duration_seconds': duration,
                'results': results,
                'status': 'success'
            }
            
            self.retraining_history.append(retraining_record)
            
            logger.warning(f"Emergency retraining completed in {duration:.2f} seconds")
            logger.warning(f"Overall R²: {results.get('overall_r2', 0):.4f}")
            
        except Exception as e:
            logger.error(f"Emergency retraining failed: {e}")
            self.retraining_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'emergency',
                'status': 'failed',
                'error': str(e)
            })
    
    def check_and_deploy_if_improved(self, results: Dict[str, Any]):
        """Check if new model performance is improved and deploy if so"""
        try:
            current_r2 = results.get('overall_r2', 0)
            current_rank_ic = results.get('overall_rank_ic', 0)
            
            # Get previous performance for comparison
            if self.retraining_history:
                previous_results = None
                for record in reversed(self.retraining_history):
                    if record.get('status') == 'success' and 'results' in record:
                        previous_results = record['results']
                        break
                
                if previous_results:
                    previous_r2 = previous_results.get('overall_r2', 0)
                    previous_rank_ic = previous_results.get('overall_rank_ic', 0)
                    
                    # Check if performance improved
                    r2_improvement = current_r2 - previous_r2
                    rank_ic_improvement = current_rank_ic - previous_rank_ic
                    
                    if r2_improvement > 0.005 or rank_ic_improvement > 0.01:  # Significant improvement
                        logger.info(f"Performance improved - deploying new model")
                        logger.info(f"R² improvement: {r2_improvement:.4f}, Rank-IC improvement: {rank_ic_improvement:.4f}")
                        
                        # Deploy new model (in production, this would update the serving system)
                        self.deploy_model(results)
                    else:
                        logger.info(f"Performance not significantly improved - keeping current model")
                        logger.info(f"R² change: {r2_improvement:.4f}, Rank-IC change: {rank_ic_improvement:.4f}")
                else:
                    logger.info("No previous results for comparison - deploying new model")
                    self.deploy_model(results)
            else:
                logger.info("First training - deploying new model")
                self.deploy_model(results)
                
        except Exception as e:
            logger.error(f"Model deployment check failed: {e}")
    
    def deploy_model(self, results: Dict[str, Any]):
        """Deploy new model to production"""
        try:
            logger.info("Deploying new model to production...")
            
            # In a real production system, this would:
            # 1. Update model serving endpoints
            # 2. Update model version tags
            # 3. Notify monitoring systems
            # 4. Update model registry
            
            deployment_record = {
                'timestamp': datetime.now().isoformat(),
                'model_version': results.get('model_status', 'unknown'),
                'r2_score': results.get('overall_r2', 0),
                'rank_ic': results.get('overall_rank_ic', 0),
                'status': 'deployed'
            }
            
            # Save deployment record
            deployment_file = "models/deployment_history.json"
            os.makedirs("models", exist_ok=True)
            
            deployment_history = []
            if os.path.exists(deployment_file):
                with open(deployment_file, 'r') as f:
                    deployment_history = json.load(f)
            
            deployment_history.append(deployment_record)
            
            with open(deployment_file, 'w') as f:
                json.dump(deployment_history, f, indent=2)
            
            logger.info("Model deployment completed successfully")
            
        except Exception as e:
            logger.error(f"Model deployment failed: {e}")
    
    def save_scheduler_state(self):
        """Save scheduler state and history"""
        try:
            state = {
                'retraining_config': self.retraining_config,
                'retraining_history': self.retraining_history[-100:],  # Keep last 100 records
                'performance_alerts': self.performance_alerts[-50:],  # Keep last 50 alerts
                'last_updated': datetime.now().isoformat()
            }
            
            os.makedirs("models", exist_ok=True)
            with open("models/scheduler_state.json", 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info("Scheduler state saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")
    
    def load_scheduler_state(self):
        """Load scheduler state and history"""
        try:
            state_file = "models/scheduler_state.json"
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.retraining_config.update(state.get('retraining_config', {}))
                self.retraining_history = state.get('retraining_history', [])
                self.performance_alerts = state.get('performance_alerts', [])
                
                logger.info("Scheduler state loaded successfully")
            else:
                logger.info("No existing scheduler state found - starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load scheduler state: {e}")
    
    def run_scheduler(self):
        """Run the automated scheduler"""
        try:
            logger.info("Starting automated retraining scheduler...")
            
            # Load existing state
            self.load_scheduler_state()
            
            # Set up schedules
            self.setup_schedules()
            
            # Save state every hour
            schedule.every().hour.do(self.save_scheduler_state)
            
            logger.info("Automated retraining scheduler is running...")
            logger.info("Press Ctrl+C to stop")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.save_scheduler_state()
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")
            self.save_scheduler_state()
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'config': self.retraining_config,
            'retraining_history_count': len(self.retraining_history),
            'performance_alerts_count': len(self.performance_alerts),
            'production_system_available': PRODUCTION_SYSTEM_AVAILABLE,
            'next_jobs': [str(job) for job in schedule.jobs[:5]]  # Next 5 scheduled jobs
        }

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> AutomatedRetrainingScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutomatedRetrainingScheduler()
    return _scheduler_instance

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run the scheduler
    scheduler = get_scheduler()
    scheduler.run_scheduler()
