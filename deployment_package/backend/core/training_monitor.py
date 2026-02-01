"""
Training Monitor for Hybrid LSTM + XGBoost
Tracks loss curves, accuracy metrics, reliability curves, and training progress.
Critical for verifying training success and identifying issues early.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os
import json
import time

logger = logging.getLogger(__name__)

# Try to import visualization
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("Matplotlib not available - visualizations disabled")


class TrainingMonitor:
    """
    Monitors and visualizes training progress for hybrid LSTM + XGBoost model.
    Tracks loss curves, accuracy, reliability, and feature importance.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize training monitor.
        
        Args:
            output_dir: Directory to save plots and logs (default: ml_models/training_logs)
        """
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__),
                'ml_models',
                'training_logs',
                datetime.now().strftime('%Y%m%d_%H%M%S')
            )
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Training history
        self.lstm_history = {
            'train_loss': [],
            'val_loss': [],
            'epochs': []
        }
        
        self.xgboost_history = {
            'train_accuracy': [],
            'val_accuracy': [],
            'cv_scores': [],
            'feature_importance': {}
        }
        
        self.net_costs_stats = {
            'total_samples': 0,
            'wins_after_costs': 0,
            'win_rate': 0.0,
            'avg_net_return': 0.0
        }
        
        self.reliability_data = {
            'probabilities': [],
            'actual_outcomes': []
        }
        
        self.start_time = None
        self.training_phase = None
    
    def start_training(self, phase: str = 'LSTM'):
        """Mark start of training phase"""
        self.start_time = time.time()
        self.training_phase = phase
        logger.info(f"🚀 Starting {phase} training phase")
    
    def log_lstm_epoch(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float = None
    ):
        """Log LSTM training epoch"""
        self.lstm_history['epochs'].append(epoch)
        self.lstm_history['train_loss'].append(train_loss)
        if val_loss is not None:
            self.lstm_history['val_loss'].append(val_loss)
        
        # Print progress
        if epoch % 10 == 0 or epoch == 1:
            msg = f"Epoch {epoch}: Train Loss = {train_loss:.6f}"
            if val_loss is not None:
                msg += f", Val Loss = {val_loss:.6f}"
            logger.info(msg)
    
    def log_lstm_complete(
        self,
        final_train_loss: float,
        final_val_loss: float,
        epochs: int
    ):
        """Log LSTM training completion"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        summary = {
            'phase': 'LSTM',
            'final_train_loss': final_train_loss,
            'final_val_loss': final_val_loss,
            'total_epochs': epochs,
            'elapsed_seconds': elapsed,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ LSTM training complete: {epochs} epochs in {elapsed:.1f}s")
        logger.info(f"   Final train loss: {final_train_loss:.6f}, val loss: {final_val_loss:.6f}")
        
        # Save summary
        self._save_summary('lstm_training', summary)
    
    def log_net_costs_labeling(
        self,
        total_samples: int,
        wins_after_costs: int,
        avg_net_return: float
    ):
        """Log net-of-costs labeling statistics"""
        self.net_costs_stats = {
            'total_samples': total_samples,
            'wins_after_costs': wins_after_costs,
            'win_rate': wins_after_costs / total_samples if total_samples > 0 else 0.0,
            'avg_net_return': avg_net_return
        }
        
        logger.info(f"📊 Net-of-Costs Labeling:")
        logger.info(f"   Total samples: {total_samples}")
        logger.info(f"   Wins after costs: {wins_after_costs} ({self.net_costs_stats['win_rate']:.2%})")
        logger.info(f"   Avg net return: {avg_net_return:.4f}")
    
    def log_xgboost_training(
        self,
        train_accuracy: float,
        val_accuracy: float,
        cv_scores: List[float],
        feature_importance: Dict[str, float]
    ):
        """Log XGBoost training metrics"""
        self.xgboost_history['train_accuracy'].append(train_accuracy)
        self.xgboost_history['val_accuracy'].append(val_accuracy)
        self.xgboost_history['cv_scores'] = cv_scores
        self.xgboost_history['feature_importance'] = feature_importance
        
        logger.info(f"📊 XGBoost Training:")
        logger.info(f"   Train accuracy: {train_accuracy:.4f}")
        logger.info(f"   Val accuracy: {val_accuracy:.4f}")
        logger.info(f"   CV accuracy: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
        
        # Top features
        top_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        logger.info(f"   Top 5 features:")
        for feat, importance in top_features:
            logger.info(f"     - {feat}: {importance:.4f}")
    
    def log_reliability_data(
        self,
        probabilities: np.ndarray,
        actual_outcomes: np.ndarray
    ):
        """Log reliability data for calibration curve"""
        self.reliability_data['probabilities'] = probabilities.tolist()
        self.reliability_data['actual_outcomes'] = actual_outcomes.tolist()
    
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate comprehensive training report"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        report = {
            'training_summary': {
                'start_time': self.start_time,
                'elapsed_seconds': elapsed,
                'phases_completed': ['LSTM', 'XGBoost'] if self.xgboost_history.get('train_accuracy') else ['LSTM']
            },
            'lstm_metrics': {
                'final_train_loss': self.lstm_history['train_loss'][-1] if self.lstm_history['train_loss'] else None,
                'final_val_loss': self.lstm_history['val_loss'][-1] if self.lstm_history['val_loss'] else None,
                'total_epochs': len(self.lstm_history['epochs']),
                'overfitting_detected': self._check_overfitting()
            },
            'net_costs_stats': self.net_costs_stats,
            'xgboost_metrics': {
                'train_accuracy': self.xgboost_history.get('train_accuracy', [None])[-1],
                'val_accuracy': self.xgboost_history.get('val_accuracy', [None])[-1],
                'cv_mean': np.mean(self.xgboost_history.get('cv_scores', [0])),
                'cv_std': np.std(self.xgboost_history.get('cv_scores', [0])),
                'top_features': dict(sorted(
                    self.xgboost_history.get('feature_importance', {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10])
            },
            'reliability': {
                'calibration_score': self._calculate_calibration_score(),
                'optimal_threshold': self._find_optimal_threshold()
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        report_path = os.path.join(self.output_dir, 'training_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Training report saved to: {report_path}")
        
        return report
    
    def plot_training_curves(self) -> Optional[str]:
        """Plot and save training curves"""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Matplotlib not available - skipping plots")
            return None
        
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Hybrid LSTM + XGBoost Training Metrics', fontsize=16)
            
            # 1. LSTM Loss Curves
            if self.lstm_history['train_loss']:
                ax1 = axes[0, 0]
                epochs = self.lstm_history['epochs']
                ax1.plot(epochs, self.lstm_history['train_loss'], label='Train Loss', linewidth=2)
                if self.lstm_history['val_loss']:
                    ax1.plot(epochs, self.lstm_history['val_loss'], label='Val Loss', linewidth=2)
                ax1.set_xlabel('Epoch')
                ax1.set_ylabel('Loss')
                ax1.set_title('LSTM Training Loss')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # 2. XGBoost Accuracy
            if self.xgboost_history.get('train_accuracy'):
                ax2 = axes[0, 1]
                ax2.bar(['Train', 'Val'], [
                    self.xgboost_history['train_accuracy'][-1],
                    self.xgboost_history['val_accuracy'][-1]
                ], color=['blue', 'green'], alpha=0.7)
                ax2.set_ylabel('Accuracy')
                ax2.set_title('XGBoost Accuracy')
                ax2.set_ylim([0, 1])
                ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. Feature Importance
            if self.xgboost_history.get('feature_importance'):
                ax3 = axes[1, 0]
                features = self.xgboost_history['feature_importance']
                top_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:10]
                names, importances = zip(*top_features)
                ax3.barh(range(len(names)), importances, color='purple', alpha=0.7)
                ax3.set_yticks(range(len(names)))
                ax3.set_yticklabels(names)
                ax3.set_xlabel('Importance')
                ax3.set_title('Top 10 Feature Importance')
                ax3.grid(True, alpha=0.3, axis='x')
            
            # 4. Reliability Curve (Calibration)
            if self.reliability_data.get('probabilities'):
                ax4 = axes[1, 1]
                probs = np.array(self.reliability_data['probabilities'])
                outcomes = np.array(self.reliability_data['actual_outcomes'])
                
                # Bin probabilities
                bins = np.linspace(0, 1, 11)
                bin_indices = np.digitize(probs, bins) - 1
                bin_indices = np.clip(bin_indices, 0, len(bins) - 2)
                
                bin_centers = []
                bin_actuals = []
                for i in range(len(bins) - 1):
                    mask = bin_indices == i
                    if np.sum(mask) > 0:
                        bin_centers.append((bins[i] + bins[i+1]) / 2)
                        bin_actuals.append(np.mean(outcomes[mask]))
                
                if bin_centers:
                    ax4.plot(bin_centers, bin_actuals, 'o-', linewidth=2, markersize=8, label='Actual')
                    ax4.plot([0, 1], [0, 1], '--', color='gray', label='Perfect Calibration')
                    ax4.set_xlabel('Predicted Probability')
                    ax4.set_ylabel('Actual Outcome')
                    ax4.set_title('Reliability Curve (Calibration)')
                    ax4.legend()
                    ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = os.path.join(self.output_dir, 'training_curves.png')
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Training curves saved to: {plot_path}")
            return plot_path
            
        except Exception as e:
            logger.error(f"Error generating plots: {e}")
            return None
    
    def _check_overfitting(self) -> bool:
        """Check if LSTM is overfitting"""
        if not self.lstm_history['train_loss'] or not self.lstm_history['val_loss']:
            return False
        
        if len(self.lstm_history['train_loss']) < 2:
            return False
        
        # Check if train loss is significantly lower than val loss
        train_loss = self.lstm_history['train_loss'][-1]
        val_loss = self.lstm_history['val_loss'][-1]
        
        gap = train_loss - val_loss
        if gap < -0.2:  # Val loss much higher than train loss
            return True
        
        return False
    
    def _calculate_calibration_score(self) -> float:
        """Calculate calibration score (Brier score)"""
        if not self.reliability_data.get('probabilities'):
            return None
        
        probs = np.array(self.reliability_data['probabilities'])
        outcomes = np.array(self.reliability_data['actual_outcomes'])
        
        # Brier score: mean squared error between probabilities and outcomes
        brier_score = np.mean((probs - outcomes) ** 2)
        
        return float(brier_score)
    
    def _find_optimal_threshold(self) -> float:
        """Find optimal confidence threshold for abstention"""
        if not self.reliability_data.get('probabilities'):
            return 0.78  # Default
        
        probs = np.array(self.reliability_data['probabilities'])
        outcomes = np.array(self.reliability_data['actual_outcomes'])
        
        # Test different thresholds
        thresholds = np.linspace(0.5, 0.95, 20)
        accuracies = []
        
        for threshold in thresholds:
            predictions = (probs >= threshold).astype(int)
            accuracy = np.mean(predictions == outcomes)
            accuracies.append(accuracy)
        
        # Find threshold with highest accuracy
        best_idx = np.argmax(accuracies)
        optimal_threshold = thresholds[best_idx]
        
        return float(optimal_threshold)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate training recommendations"""
        recommendations = []
        
        # Check overfitting
        if self._check_overfitting():
            recommendations.append("⚠️ Overfitting detected: Consider adding dropout or reducing model complexity")
        
        # Check win rate
        if self.net_costs_stats.get('win_rate', 0) < 0.5:
            recommendations.append("⚠️ Low win rate after costs: Review fee/slippage assumptions or data quality")
        
        # Check calibration
        calibration_score = self._calculate_calibration_score()
        if calibration_score and calibration_score > 0.25:
            recommendations.append("⚠️ Poor calibration: Model probabilities may not be reliable")
        
        # Check feature importance
        if self.xgboost_history.get('feature_importance'):
            features = self.xgboost_history['feature_importance']
            lstm_importance = features.get('lstm_temporal_momentum_score', 0)
            if lstm_importance < 0.05:
                recommendations.append("⚠️ LSTM momentum score has low importance: May need more training data or different architecture")
        
        # Positive recommendations
        if not recommendations:
            recommendations.append("✅ Training looks good! Ready for validation testing")
        else:
            recommendations.append("✅ Review recommendations above before deploying to production")
        
        return recommendations
    
    def _save_summary(self, name: str, data: Dict[str, Any]):
        """Save summary to JSON file"""
        summary_path = os.path.join(self.output_dir, f'{name}_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)


# Global instance
_training_monitor = None

def get_training_monitor(output_dir: str = None) -> TrainingMonitor:
    """Get global training monitor instance"""
    global _training_monitor
    if _training_monitor is None:
        _training_monitor = TrainingMonitor(output_dir=output_dir)
    return _training_monitor

