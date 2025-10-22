"""
Performance Monitoring Dashboard for Production Alpha System
Real-time monitoring of R², Rank-IC, and model performance metrics
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dataclasses import asdict

# Import the production alpha system
try:
    from production_alpha_system import ProductionAlphaSystem, PerformanceMetrics
    PRODUCTION_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Production Alpha System not available: {e}")
    PRODUCTION_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)

class PerformanceDashboard:
    """
    Performance monitoring dashboard with real-time metrics and alerts
    """
    
    def __init__(self):
        self.production_system = None
        self.dashboard_config = {
            'refresh_interval_seconds': 300,  # 5 minutes
            'performance_thresholds': {
                'r2_min': 0.02,
                'r2_target': 0.05,
                'rank_ic_min': 0.05,
                'rank_ic_target': 0.10,
                'sharpe_min': 1.0,
                'sharpe_target': 1.5
            },
            'alert_config': {
                'enable_alerts': True,
                'alert_cooldown_minutes': 30,
                'email_alerts': False,
                'slack_alerts': False
            }
        }
        
        self.performance_history = []
        self.alerts_history = []
        self.dashboard_metrics = {}
        
        if PRODUCTION_SYSTEM_AVAILABLE:
            self.production_system = ProductionAlphaSystem()
            logger.info("Performance Dashboard initialized with Production Alpha System")
        else:
            logger.warning("Performance Dashboard initialized without Production Alpha System")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            if not self.production_system:
                return {'error': 'Production system not available'}
            
            # Get performance summary
            perf_summary = self.production_system.get_performance_summary()
            
            if 'error' in perf_summary:
                return perf_summary
            
            # Get economic indicators
            economic_data = self.production_system.fetch_economic_indicators()
            
            # Get model status
            model_status = {
                'regime_models_loaded': len(self.production_system.regime_models),
                'model_configs': len(self.production_system.model_configs),
                'liquid_tickers': len(self.production_system.liquid_tickers)
            }
            
            # Combine all metrics
            current_metrics = {
                'timestamp': datetime.now().isoformat(),
                'performance': perf_summary,
                'economic_indicators': economic_data,
                'model_status': model_status,
                'system_health': self.get_system_health()
            }
            
            # Store in history
            self.performance_history.append(current_metrics)
            
            # Keep only last 1000 records
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
            
            return current_metrics
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {'error': str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health_status = {
                'status': 'healthy',
                'issues': [],
                'warnings': []
            }
            
            # Check model files
            model_dir = "models"
            if not os.path.exists(model_dir):
                health_status['issues'].append("Models directory does not exist")
                health_status['status'] = 'critical'
            else:
                model_files = [f for f in os.listdir(model_dir) if f.endswith('.joblib')]
                if not model_files:
                    health_status['issues'].append("No model files found")
                    health_status['status'] = 'critical'
                else:
                    # Check model file ages
                    for model_file in model_files:
                        file_path = os.path.join(model_dir, model_file)
                        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_age.days > 7:
                            health_status['warnings'].append(f"Model {model_file} is {file_age.days} days old")
                            if health_status['status'] == 'healthy':
                                health_status['status'] = 'warning'
            
            # Check performance history
            if len(self.performance_history) > 0:
                latest_perf = self.performance_history[-1]
                if 'performance' in latest_perf:
                    perf = latest_perf['performance']
                    r2 = perf.get('latest_r2', 0)
                    rank_ic = perf.get('latest_rank_ic', 0)
                    
                    if r2 < self.dashboard_config['performance_thresholds']['r2_min']:
                        health_status['issues'].append(f"R² below threshold: {r2:.4f}")
                        health_status['status'] = 'critical'
                    elif r2 < self.dashboard_config['performance_thresholds']['r2_target']:
                        health_status['warnings'].append(f"R² below target: {r2:.4f}")
                        if health_status['status'] == 'healthy':
                            health_status['status'] = 'warning'
                    
                    if rank_ic < self.dashboard_config['performance_thresholds']['rank_ic_min']:
                        health_status['issues'].append(f"Rank-IC below threshold: {rank_ic:.4f}")
                        health_status['status'] = 'critical'
                    elif rank_ic < self.dashboard_config['performance_thresholds']['rank_ic_target']:
                        health_status['warnings'].append(f"Rank-IC below target: {rank_ic:.4f}")
                        if health_status['status'] == 'healthy':
                            health_status['status'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                'status': 'error',
                'issues': [f"Health check failed: {e}"],
                'warnings': []
            }
    
    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over specified days"""
        try:
            if not self.performance_history:
                return {'error': 'No performance history available'}
            
            # Filter recent data
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_data = [
                record for record in self.performance_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_date
            ]
            
            if not recent_data:
                return {'error': f'No data available for last {days} days'}
            
            # Extract metrics
            timestamps = []
            r2_scores = []
            rank_ic_scores = []
            sharpe_ratios = []
            
            for record in recent_data:
                if 'performance' in record:
                    perf = record['performance']
                    timestamps.append(record['timestamp'])
                    r2_scores.append(perf.get('latest_r2', 0))
                    rank_ic_scores.append(perf.get('latest_rank_ic', 0))
                    sharpe_ratios.append(perf.get('latest_sharpe', 0))
            
            # Calculate trends
            trends = {
                'r2_trend': self._calculate_trend(r2_scores),
                'rank_ic_trend': self._calculate_trend(rank_ic_scores),
                'sharpe_trend': self._calculate_trend(sharpe_ratios),
                'r2_volatility': np.std(r2_scores) if len(r2_scores) > 1 else 0,
                'rank_ic_volatility': np.std(rank_ic_scores) if len(rank_ic_scores) > 1 else 0,
                'data_points': len(recent_data)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear trend
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.001:
            return 'improving'
        elif slope < -0.001:
            return 'declining'
        else:
            return 'stable'
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        try:
            alerts = []
            
            if not self.performance_history:
                return alerts
            
            latest_metrics = self.performance_history[-1]
            
            if 'performance' in latest_metrics:
                perf = latest_metrics['performance']
                thresholds = self.dashboard_config['performance_thresholds']
                
                # R² alerts
                r2 = perf.get('latest_r2', 0)
                if r2 < thresholds['r2_min']:
                    alerts.append({
                        'type': 'critical',
                        'metric': 'r2',
                        'value': r2,
                        'threshold': thresholds['r2_min'],
                        'message': f'R² critically low: {r2:.4f} < {thresholds["r2_min"]:.4f}',
                        'timestamp': datetime.now().isoformat()
                    })
                elif r2 < thresholds['r2_target']:
                    alerts.append({
                        'type': 'warning',
                        'metric': 'r2',
                        'value': r2,
                        'threshold': thresholds['r2_target'],
                        'message': f'R² below target: {r2:.4f} < {thresholds["r2_target"]:.4f}',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Rank-IC alerts
                rank_ic = perf.get('latest_rank_ic', 0)
                if rank_ic < thresholds['rank_ic_min']:
                    alerts.append({
                        'type': 'critical',
                        'metric': 'rank_ic',
                        'value': rank_ic,
                        'threshold': thresholds['rank_ic_min'],
                        'message': f'Rank-IC critically low: {rank_ic:.4f} < {thresholds["rank_ic_min"]:.4f}',
                        'timestamp': datetime.now().isoformat()
                    })
                elif rank_ic < thresholds['rank_ic_target']:
                    alerts.append({
                        'type': 'warning',
                        'metric': 'rank_ic',
                        'value': rank_ic,
                        'threshold': thresholds['rank_ic_target'],
                        'message': f'Rank-IC below target: {rank_ic:.4f} < {thresholds["rank_ic_target"]:.4f}',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Sharpe ratio alerts
                sharpe = perf.get('latest_sharpe', 0)
                if sharpe < thresholds['sharpe_min']:
                    alerts.append({
                        'type': 'warning',
                        'metric': 'sharpe',
                        'value': sharpe,
                        'threshold': thresholds['sharpe_min'],
                        'message': f'Sharpe ratio low: {sharpe:.4f} < {thresholds["sharpe_min"]:.4f}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Store alerts
            for alert in alerts:
                self.alerts_history.append(alert)
            
            # Keep only last 100 alerts
            if len(self.alerts_history) > 100:
                self.alerts_history = self.alerts_history[-100:]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return []
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive dashboard summary"""
        try:
            current_metrics = self.get_current_metrics()
            trends = self.get_performance_trends()
            alerts = self.check_alerts()
            system_health = self.get_system_health()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'current_metrics': current_metrics,
                'performance_trends': trends,
                'active_alerts': alerts,
                'system_health': system_health,
                'dashboard_config': self.dashboard_config,
                'history_size': len(self.performance_history),
                'alerts_count': len(self.alerts_history)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {'error': str(e)}
    
    def save_dashboard_state(self):
        """Save dashboard state and history"""
        try:
            state = {
                'dashboard_config': self.dashboard_config,
                'performance_history': self.performance_history[-500:],  # Keep last 500 records
                'alerts_history': self.alerts_history[-100:],  # Keep last 100 alerts
                'last_updated': datetime.now().isoformat()
            }
            
            os.makedirs("models", exist_ok=True)
            with open("models/dashboard_state.json", 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info("Dashboard state saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save dashboard state: {e}")
    
    def load_dashboard_state(self):
        """Load dashboard state and history"""
        try:
            state_file = "models/dashboard_state.json"
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.dashboard_config.update(state.get('dashboard_config', {}))
                self.performance_history = state.get('performance_history', [])
                self.alerts_history = state.get('alerts_history', [])
                
                logger.info("Dashboard state loaded successfully")
            else:
                logger.info("No existing dashboard state found - starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load dashboard state: {e}")
    
    def generate_performance_report(self) -> str:
        """Generate a text-based performance report"""
        try:
            summary = self.get_dashboard_summary()
            
            if 'error' in summary:
                return f"Error generating report: {summary['error']}"
            
            report = []
            report.append("=" * 60)
            report.append("PRODUCTION ALPHA SYSTEM PERFORMANCE REPORT")
            report.append("=" * 60)
            report.append(f"Generated: {summary['timestamp']}")
            report.append("")
            
            # Current Metrics
            if 'current_metrics' in summary and 'performance' in summary['current_metrics']:
                perf = summary['current_metrics']['performance']
                report.append("CURRENT PERFORMANCE METRICS:")
                report.append("-" * 30)
                report.append(f"R² Score: {perf.get('latest_r2', 0):.4f}")
                report.append(f"Rank-IC: {perf.get('latest_rank_ic', 0):.4f}")
                report.append(f"Sharpe Ratio: {perf.get('latest_sharpe', 0):.4f}")
                report.append(f"Performance Trend: {perf.get('performance_trend', 'unknown')}")
                report.append(f"Total Predictions: {perf.get('total_predictions', 0)}")
                report.append("")
            
            # System Health
            if 'system_health' in summary:
                health = summary['system_health']
                report.append("SYSTEM HEALTH:")
                report.append("-" * 15)
                report.append(f"Status: {health['status'].upper()}")
                if health['issues']:
                    report.append("Issues:")
                    for issue in health['issues']:
                        report.append(f"  - {issue}")
                if health['warnings']:
                    report.append("Warnings:")
                    for warning in health['warnings']:
                        report.append(f"  - {warning}")
                report.append("")
            
            # Performance Trends
            if 'performance_trends' in summary and 'error' not in summary['performance_trends']:
                trends = summary['performance_trends']
                report.append("PERFORMANCE TRENDS (7 days):")
                report.append("-" * 30)
                report.append(f"R² Trend: {trends.get('r2_trend', 'unknown')}")
                report.append(f"Rank-IC Trend: {trends.get('rank_ic_trend', 'unknown')}")
                report.append(f"Sharpe Trend: {trends.get('sharpe_trend', 'unknown')}")
                report.append(f"Data Points: {trends.get('data_points', 0)}")
                report.append("")
            
            # Active Alerts
            if 'active_alerts' in summary and summary['active_alerts']:
                report.append("ACTIVE ALERTS:")
                report.append("-" * 15)
                for alert in summary['active_alerts']:
                    report.append(f"[{alert['type'].upper()}] {alert['message']}")
                report.append("")
            else:
                report.append("ACTIVE ALERTS: None")
                report.append("")
            
            # Economic Indicators
            if 'current_metrics' in summary and 'economic_indicators' in summary['current_metrics']:
                econ = summary['current_metrics']['economic_indicators']
                report.append("ECONOMIC INDICATORS:")
                report.append("-" * 20)
                for key, value in econ.items():
                    report.append(f"{key.upper()}: {value}")
                report.append("")
            
            report.append("=" * 60)
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return f"Error generating report: {e}"

# Global dashboard instance
_dashboard_instance = None

def get_dashboard() -> PerformanceDashboard:
    """Get global dashboard instance"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = PerformanceDashboard()
    return _dashboard_instance

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the dashboard
    dashboard = get_dashboard()
    
    print("=== Performance Dashboard Test ===")
    
    # Get current metrics
    print("\n📊 Getting current metrics...")
    metrics = dashboard.get_current_metrics()
    if 'error' not in metrics:
        print("✅ Current metrics retrieved successfully")
    else:
        print(f"❌ Error: {metrics['error']}")
    
    # Generate performance report
    print("\n📋 Generating performance report...")
    report = dashboard.generate_performance_report()
    print(report)
    
    # Save dashboard state
    print("\n💾 Saving dashboard state...")
    dashboard.save_dashboard_state()
    print("✅ Dashboard state saved")
