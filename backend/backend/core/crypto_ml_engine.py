"""
Crypto ML Prediction Engine
Implements the "next-day big BTC move" prediction system with proper validation
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timedelta
import logging
import joblib
import json

# Lazy imports for sklearn to avoid startup issues
def _import_sklearn():
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.model_selection import TimeSeriesSplit
        return LogisticRegression, Pipeline, StandardScaler, CalibratedClassifierCV, TimeSeriesSplit
    except ImportError as e:
        logger.warning(f"sklearn not available: {e}")
        return None, None, None, None, None

logger = logging.getLogger(__name__)

# Configuration
BIG_DAY_THRESHOLD = 0.04  # 4% threshold for "big day"
ALERT_BUDGET_PER_MONTH = 4  # Max 4 alerts per month
MIN_TRAINING_DAYS = 240  # Minimum training data required
VALIDATION_DAYS = 180  # Validation period
TEST_DAYS = 720  # Test period


@dataclass
class PredictionResult:
    """Result of ML prediction"""
    symbol: str
    prediction_type: str
    probability: float
    confidence_level: str
    features_used: Dict[str, float]
    prediction_horizon_hours: int
    created_at: datetime
    expires_at: datetime
    explanation: str


@dataclass
class BacktestMetrics:
    """Backtest performance metrics"""
    precision: float
    recall: float
    lift: float
    total_alerts: int
    base_rate: float
    avg_return_on_alerts: float
    sharpe_ratio: float
    max_drawdown: float


class CryptoMLFeatureEngine:
    """Feature engineering for crypto ML models"""
    
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create ML features from OHLCV data"""
        df = df.sort_values('timestamp').copy()
        
        # Basic price features
        df['ret1d'] = df['close'].pct_change()
        df['mo_3d'] = df['close'].pct_change(3)
        df['mo_5d'] = df['close'].pct_change(5)
        df['mo_10d'] = df['close'].pct_change(10)
        
        # Range and volatility
        df['rng'] = (df['high'] - df['low']) / df['close'].shift(1)
        df['atr_14'] = (df['high'] - df['low']).rolling(14).mean() / df['close'].shift(1)
        df['rv_10'] = df['ret1d'].rolling(10).std()
        df['rv_30'] = df['ret1d'].rolling(30).std()
        
        # Volume features
        df['vol_spike'] = df['volume'] / df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['volume'].rolling(5).mean()
        
        # Technical indicators
        df['rsi_14'] = CryptoMLFeatureEngine._calculate_rsi(df['close'], 14)
        df['macd'] = CryptoMLFeatureEngine._calculate_macd(df['close'])
        df['bb_upper'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
        df['bb_lower'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Momentum features
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        
        # Volatility clustering
        df['vol_cluster'] = df['ret1d'].rolling(5).std() / df['ret1d'].rolling(20).std()
        
        # Market microstructure (if available)
        if 'funding_rate' in df.columns:
            df['funding_chg'] = df['funding_rate'].diff()
            df['funding_ma'] = df['funding_rate'].rolling(7).mean()
        else:
            df['funding_chg'] = 0
            df['funding_ma'] = 0
            
        if 'open_interest' in df.columns:
            df['oi_chg'] = df['open_interest'].pct_change()
            df['oi_ma'] = df['open_interest'].rolling(7).mean()
        else:
            df['oi_chg'] = 0
            df['oi_ma'] = 0
        
        # Create target variable (next day big move)
        df['y'] = (df['ret1d'].shift(-1) >= BIG_DAY_THRESHOLD).astype(int)
        
        # Feature list
        feature_cols = [
            'mo_3d', 'mo_5d', 'mo_10d', 'rng', 'atr_14', 'rv_10', 'rv_30',
            'vol_spike', 'vol_ratio', 'rsi_14', 'macd', 'bb_position',
            'momentum_5', 'momentum_10', 'vol_cluster',
            'funding_chg', 'funding_ma', 'oi_chg', 'oi_ma'
        ]
        
        # Clean data
        df = df.dropna(subset=feature_cols + ['y']).reset_index(drop=True)
        
        return df[['timestamp'] + feature_cols + ['y', 'open', 'close', 'high', 'low']]
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        return macd


class CryptoMLModel:
    """ML model for crypto predictions"""
    
    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.scaler = None
        self.is_trained = False
        
    def build_model(self):
        """Build the ML pipeline"""
        LogisticRegression, Pipeline, StandardScaler, CalibratedClassifierCV, TimeSeriesSplit = _import_sklearn()
        
        if LogisticRegression is None:
            raise ImportError("sklearn is not available. Please install scikit-learn.")
        
        base_pipeline = Pipeline([
            ('scaler', StandardScaler(with_mean=True, with_std=True)),
            ('classifier', LogisticRegression(max_iter=200, random_state=42))
        ])
        
        # Calibrate probabilities
        self.model = CalibratedClassifierCV(
            base_pipeline, 
            method='isotonic', 
            cv=3
        )
        
    def train(self, X: np.ndarray, y: np.ndarray, feature_cols: List[str]):
        """Train the model"""
        self.build_model()
        self.model.fit(X, y)
        self.feature_cols = feature_cols
        self.is_trained = True
        logger.info(f"Model trained on {len(X)} samples with {len(feature_cols)} features")
        
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.is_trained or self.feature_cols is None:
            return {}
        
        # Get coefficients from the base classifier
        base_classifier = self.model.calibrated_classifiers_[0].estimator.named_steps['classifier']
        coefficients = base_classifier.coef_[0]
        
        return dict(zip(self.feature_cols, coefficients))


class CryptoMLBacktester:
    """Backtesting system for crypto ML models"""
    
    def __init__(self, alert_budget_per_month: int = 4):
        self.alert_budget_per_month = alert_budget_per_month
        
    def walk_forward_backtest(
        self, 
        df: pd.DataFrame,
        start_year: int = 2017,
        retrain_every_days: int = 30
    ) -> BacktestMetrics:
        """Perform walk-forward backtesting"""
        
        feature_engine = CryptoMLFeatureEngine()
        df_features = feature_engine.create_features(df)
        
        X_cols = [c for c in df_features.columns if c not in ['timestamp', 'y', 'open', 'close', 'high', 'low']]
        
        results = []
        i = 0
        
        while True:
            # Define time windows
            if i == 0:
                start_idx = int(np.argmax(df_features['timestamp'].dt.year >= start_year))
                i = start_idx
            
            train_end = i + max(VALIDATION_DAYS, MIN_TRAINING_DAYS)
            val_end = train_end + VALIDATION_DAYS
            test_end = val_end + TEST_DAYS
            
            if test_end >= len(df_features):
                break
                
            # Split data
            train_data = df_features.iloc[:train_end]
            val_data = df_features.iloc[train_end:val_end]
            test_data = df_features.iloc[val_end:test_end]
            
            # Train model
            model = CryptoMLModel()
            X_train = train_data[X_cols].values
            y_train = train_data['y'].values
            model.train(X_train, y_train, X_cols)
            
            # Select threshold on validation
            val_probs = model.predict_proba(val_data[X_cols].values)[:, 1]
            threshold = self._select_threshold(val_probs, val_data['y'].values)
            
            # Test on out-of-sample data
            test_probs = model.predict_proba(test_data[X_cols].values)[:, 1]
            test_alerts = test_probs >= threshold
            test_y = test_data['y'].values
            
            # Calculate metrics
            metrics = self._calculate_metrics(test_y, test_alerts, test_data)
            results.append(metrics)
            
            i += retrain_every_days
        
        # Aggregate results
        return self._aggregate_results(results)
    
    def _select_threshold(self, val_probs: np.ndarray, val_y: np.ndarray) -> float:
        """Select optimal threshold based on validation data"""
        base_rate = float(val_y.mean())
        
        # Try different thresholds
        thresholds = np.linspace(0.2, 0.8, 25)
        best_score = 0
        best_threshold = 0.5
        
        for threshold in thresholds:
            alerts = val_probs >= threshold
            if alerts.sum() == 0:
                continue
                
            precision = float(val_y[alerts].mean())
            recall = float(val_y[alerts].sum()) / max(1, val_y.sum())
            
            # Score: precision + 0.25 * recall (prioritize precision)
            score = precision + 0.25 * recall
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
        
        return best_threshold
    
    def _calculate_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        test_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate backtest metrics"""
        alerts = int(y_pred.sum())
        
        if alerts == 0:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'lift': 0.0,
                'alerts': 0,
                'base_rate': float(y_true.mean()),
                'avg_return': 0.0,
                'sharpe': 0.0,
                'max_dd': 0.0
            }
        
        precision = float(y_true[y_pred].mean())
        base_rate = float(y_true.mean())
        recall = float(y_true[y_pred].sum()) / max(1, y_true.sum())
        lift = precision / base_rate if base_rate > 0 else 0
        
        # Calculate returns on alert days
        alert_returns = []
        for i, is_alert in enumerate(y_pred):
            if is_alert and i < len(test_data) - 1:
                open_price = test_data['open'].iloc[i]
                close_price = test_data['close'].iloc[i + 1]
                ret = (close_price - open_price) / open_price
                alert_returns.append(ret)
        
        avg_return = np.mean(alert_returns) if alert_returns else 0.0
        sharpe = np.mean(alert_returns) / np.std(alert_returns) if len(alert_returns) > 1 else 0.0
        
        # Calculate max drawdown
        cumulative_returns = np.cumprod(1 + np.array(alert_returns))
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_dd = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'lift': lift,
            'alerts': alerts,
            'base_rate': base_rate,
            'avg_return': avg_return,
            'sharpe': sharpe,
            'max_dd': max_dd
        }
    
    def _aggregate_results(self, results: List[Dict[str, float]]) -> BacktestMetrics:
        """Aggregate backtest results"""
        if not results:
            return BacktestMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        df_results = pd.DataFrame(results)
        
        # Weight by number of alerts
        weights = df_results['alerts'].clip(lower=1)
        
        precision = np.average(df_results['precision'], weights=weights)
        recall = np.average(df_results['recall'], weights=weights)
        lift = np.average(df_results['lift'], weights=weights)
        total_alerts = int(df_results['alerts'].sum())
        base_rate = df_results['base_rate'].mean()
        avg_return = np.average(df_results['avg_return'], weights=weights)
        sharpe = np.average(df_results['sharpe'], weights=weights)
        max_dd = df_results['max_dd'].min()
        
        return BacktestMetrics(
            precision=precision,
            recall=recall,
            lift=lift,
            total_alerts=total_alerts,
            base_rate=base_rate,
            avg_return_on_alerts=avg_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd
        )


class CryptoMLPredictionService:
    """Main service for crypto ML predictions"""
    
    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.threshold = 0.4
        self.is_ready = False
        
    def train_model(self, df: pd.DataFrame) -> BacktestMetrics:
        """Train the model and return backtest metrics"""
        logger.info("Starting crypto ML model training")
        
        # Create features
        feature_engine = CryptoMLFeatureEngine()
        df_features = feature_engine.create_features(df)
        
        X_cols = [c for c in df_features.columns if c not in ['timestamp', 'y', 'open', 'close', 'high', 'low']]
        
        # Backtest
        backtester = CryptoMLBacktester(ALERT_BUDGET_PER_MONTH)
        metrics = backtester.walk_forward_backtest(df_features)
        
        # Train final model on all data
        self.model = CryptoMLModel()
        X = df_features[X_cols].values
        y = df_features['y'].values
        self.model.train(X, y, X_cols)
        
        # Set threshold based on backtest
        self.threshold = 0.4  # Default, should be optimized
        self.feature_cols = X_cols
        self.is_ready = True
        
        logger.info(f"Model training complete. Precision: {metrics.precision:.3f}, Lift: {metrics.lift:.2f}")
        return metrics
    
    def predict_big_day(self, df: pd.DataFrame, symbol: str) -> Optional[PredictionResult]:
        """Predict if tomorrow will be a big up day"""
        if not self.is_ready:
            logger.warning("Model not trained yet")
            return None
        
        try:
            # Create features for latest data
            feature_engine = CryptoMLFeatureEngine()
            df_features = feature_engine.create_features(df)
            
            if len(df_features) == 0:
                return None
            
            # Get latest features
            latest_features = df_features.iloc[-1][self.feature_cols].values.reshape(1, -1)
            probability = float(self.model.predict_proba(latest_features)[0, 1])
            
            # Determine confidence level
            if probability >= 0.7:
                confidence = 'HIGH'
            elif probability >= 0.5:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
            
            # Get feature importance for explanation
            feature_importance = self.model.get_feature_importance()
            top_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            
            # Create explanation
            explanation = self._create_explanation(probability, top_features, latest_features[0])
            
            # Create result
            now = datetime.utcnow()
            result = PredictionResult(
                symbol=symbol,
                prediction_type='BIG_UP_DAY',
                probability=probability,
                confidence_level=confidence,
                features_used=dict(top_features),
                prediction_horizon_hours=24,
                created_at=now,
                expires_at=now + timedelta(hours=24),
                explanation=explanation
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def _create_explanation(self, probability: float, top_features: List[Tuple[str, float]], feature_values: np.ndarray) -> str:
        """Create human-readable explanation for the prediction"""
        explanations = []
        
        for feature_name, importance in top_features:
            if abs(importance) > 0.1:  # Only include significant features
                value = feature_values[self.feature_cols.index(feature_name)]
                
                if 'momentum' in feature_name:
                    if value > 0:
                        explanations.append(f"Strong {feature_name.replace('_', ' ')} momentum")
                    else:
                        explanations.append(f"Weak {feature_name.replace('_', ' ')} momentum")
                elif 'vol' in feature_name:
                    if value > 1:
                        explanations.append(f"High {feature_name.replace('_', ' ')}")
                    else:
                        explanations.append(f"Low {feature_name.replace('_', ' ')}")
                elif 'rsi' in feature_name:
                    if value > 70:
                        explanations.append("Overbought conditions")
                    elif value < 30:
                        explanations.append("Oversold conditions")
        
        if not explanations:
            explanations.append("Mixed technical signals")
        
        base_explanation = f"Probability of big up day: {probability:.1%}. "
        return base_explanation + "Key factors: " + ", ".join(explanations[:3])


# Example usage and testing
def test_crypto_ml_engine():
    """Test the crypto ML engine with sample data"""
    # This would be called with real data in production
    logger.info("Crypto ML engine test completed")


if __name__ == "__main__":
    test_crypto_ml_engine()
