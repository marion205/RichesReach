"""
Day Trading ML Learner - Learns from past performance to improve future picks
Uses machine learning to identify patterns in successful day trading setups
"""
import os
import json
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from django.db import models
from django.utils import timezone as django_timezone
from django.core.cache import cache
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Try to import ML libraries (optional - graceful degradation if not available)
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("scikit-learn not available - ML features disabled. Install with: pip install scikit-learn")


class DayTradingMLearner:
    """
    Machine Learning system that learns from past day trading picks and their outcomes.
    
    Features:
    - Tracks which picks were successful (hit targets, positive returns)
    - Learns patterns in successful vs. unsuccessful picks
    - Adjusts scoring weights based on historical performance
    - Predicts success probability for new picks
    - Auto-retrains daily/weekly from SignalPerformance data
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_weights = {}
        self.model_path = os.path.join(
            os.path.dirname(__file__),
            'ml_models',
            'day_trading_predictor.pkl'
        )
        self.scaler_path = os.path.join(
            os.path.dirname(__file__),
            'ml_models',
            'day_trading_scaler.pkl'
        )
        
        # Ensure ML models directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load trained model and scaler from disk"""
        if not ML_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("✅ Loaded pre-trained day trading ML model")
            else:
                logger.info("No pre-trained model found - will train on first use")
        except Exception as e:
            logger.warning(f"Error loading ML model: {e}")
    
    def _save_model(self):
        """Save trained model and scaler to disk"""
        if not ML_AVAILABLE or not self.model or not self.scaler:
            return
        
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info("✅ Saved day trading ML model")
        except Exception as e:
            logger.error(f"Error saving ML model: {e}")
    
    def extract_features_from_signal(self, signal) -> Dict:
        """
        Extract ML features from a DayTradingSignal.
        These features will be used to predict success.
        Includes execution features (spread, slippage, fill quality).
        """
        features_dict = signal.features if isinstance(signal.features, dict) else {}
        
        # Extract execution features (for separating signal quality from execution quality)
        spread_bps = float(features_dict.get('spreadBps', features_dict.get('spread_bps', 5.0)))
        execution_quality = float(features_dict.get('executionQualityScore', features_dict.get('execution_quality_score', 5.0)))
        
        return {
            'momentum_15m': float(features_dict.get('momentum15m', 0.0)),
            'rvol_10m': float(features_dict.get('rvol10m', 0.0)),
            'vwap_dist': float(features_dict.get('vwapDist', 0.0)),
            'spread_bps': spread_bps,  # Execution feature
            'execution_quality_score': execution_quality,  # Execution feature
            'breakout_pct': float(features_dict.get('breakoutPct', 0.0)),
            'spread_bps': float(features_dict.get('spreadBps', 0.0)),
            'catalyst_score': float(features_dict.get('catalystScore', 0.0)),
            'volume_ratio': float(features_dict.get('volumeRatio', 1.0)),
            'volume_zscore': float(features_dict.get('volumeZscore', 0.0)),
            'rsi_14': float(features_dict.get('rsi14', 50.0)),
            'is_trend_regime': float(features_dict.get('isTrendRegime', 0.0)),
            'is_range_regime': float(features_dict.get('isRangeRegime', 0.0)),
            'is_high_vol_chop': float(features_dict.get('isHighVolChop', 0.0)),
            'regime_confidence': float(features_dict.get('regimeConfidence', 0.5)),
            'is_vol_expansion': float(features_dict.get('isVolExpansion', 0.0)),
            'is_breakout': float(features_dict.get('isBreakout', 0.0)),
            'is_three_white_soldiers': float(features_dict.get('isThreeWhiteSoldiers', 0.0)),
            'is_engulfing_bull': float(features_dict.get('isEngulfingBull', 0.0)),
            'is_engulfing_bear': float(features_dict.get('isEngulfingBear', 0.0)),
            'is_hammer': float(features_dict.get('isHammer', 0.0)),
            'is_doji': float(features_dict.get('isDoji', 0.0)),
            'vwap_dist_pct': float(features_dict.get('vwapDistPct', 0.0)),
            'macd_hist': float(features_dict.get('macdHist', 0.0)),
            'bb_position': float(features_dict.get('bbPosition', 0.5)),
            'trend_strength': float(features_dict.get('trendStrength', 0.0)),
            'price_above_sma20': float(features_dict.get('priceAboveSma20', 0.0)),
            'price_above_sma50': float(features_dict.get('priceAboveSma50', 0.0)),
            'sma20_above_sma50': float(features_dict.get('sma20AboveSma50', 0.0)),
            'is_opening_hour': float(features_dict.get('isOpeningHour', 0.0)),
            'is_closing_hour': float(features_dict.get('isClosingHour', 0.0)),
            'is_midday': float(features_dict.get('isMidday', 0.0)),
            'sentiment_score': float(features_dict.get('sentimentScore', 0.0)),
            'sentiment_volume': float(features_dict.get('sentimentVolume', 0.0)),
            'sentiment_divergence': float(features_dict.get('sentimentDivergence', 0.0)),
            'score': float(signal.score),
            'mode_safe': 1.0 if signal.mode == 'SAFE' else 0.0,
            'side_long': 1.0 if signal.side == 'LONG' else 0.0,
            'hour_of_day': (signal.generated_at.hour if hasattr(signal.generated_at, 'hour') else datetime.now().hour) / 24.0,  # Normalize hour
            'day_of_week': (signal.generated_at.weekday() if hasattr(signal.generated_at, 'weekday') else datetime.now().weekday()) / 7.0,  # Normalize day
        }
    
    def load_training_data_from_database(self, days_back: int = 30, min_records: int = 50) -> Tuple[List[Dict], List[float]]:
        """
        Load training data from DayTradingSignal and SignalPerformance models.
        
        Args:
            days_back: How many days of history to load
            min_records: Minimum number of records needed to train
        
        Returns:
            Tuple of (feature_dicts, success_labels) where success_labels are 1.0 for wins, 0.0 for losses
        """
        try:
            from .signal_performance_models import DayTradingSignal, SignalPerformance
            
            # Get signals from last N days
            cutoff_date = django_timezone.now() - timedelta(days=days_back)
            signals = DayTradingSignal.objects.filter(
                generated_at__gte=cutoff_date
            ).select_related().order_by('-generated_at')
            
            logger.info(f"📊 Loading training data: {signals.count()} signals found from last {days_back} days")
            
            if signals.count() < min_records:
                logger.warning(f"⚠️ Not enough signals for training: {signals.count()} < {min_records}")
                return [], []
            
            X = []
            y = []
            
            for signal in signals:
                # Get performance at EOD (end of day) - most relevant for day trading
                try:
                    perf = SignalPerformance.objects.filter(
                        signal=signal,
                        horizon='EOD'  # End of day performance
                    ).first()
                    
                    if not perf:
                        # Try 2h horizon if EOD not available
                        perf = SignalPerformance.objects.filter(
                            signal=signal,
                            horizon='2h'
                        ).first()
                    
                    if not perf:
                        continue  # Skip signals without performance data
                    
                    # Extract features (includes execution features: spread_bps, execution_quality_score)
                    features = self.extract_features_from_signal(signal)
                    X.append(features)
                    
                    # CRITICAL: Label that separates signal from execution
                    # Outcome = sign(return over horizon - estimated costs)
                    # This prevents the learner from learning execution quirks as if they were alpha
                    
                    # Estimate costs (spread + fees + slippage)
                    spread_bps = features.get('spread_bps', 5.0)  # Basis points
                    spread_cost_pct = spread_bps / 10000.0  # Convert to percentage
                    
                    # Estimate commission (typical: $0.01 per share or $1 per trade)
                    # For day trading, assume ~$1 per trade (entry + exit = $2)
                    # Convert to percentage based on position size
                    entry_price = float(signal.entry_price) if hasattr(signal, 'entry_price') else 100.0
                    position_size = entry_price * 100  # Assume 100 shares (typical day trade size)
                    commission_pct = (2.0 / position_size) * 100  # $2 commission as % of position
                    
                    # Estimate slippage (from execution quality score)
                    execution_quality = features.get('execution_quality_score', 5.0)
                    # Map quality score (0-10) to slippage estimate (0.5% worst, 0.05% best)
                    slippage_pct = 0.005 - (execution_quality / 10.0) * 0.0045  # 0.5% to 0.05%
                    
                    # Total estimated costs
                    total_costs_pct = spread_cost_pct + commission_pct + slippage_pct
                    
                    # Net return after costs
                    gross_return_pct = float(perf.pnl_percent) if perf.pnl_percent else 0.0
                    net_return_pct = gross_return_pct - total_costs_pct
                    
                    # Success label: net return > threshold (e.g., 0.1% to account for noise)
                    # This ensures we only label as "win" if the signal was profitable AFTER costs
                    cost_threshold = 0.001  # 0.1% minimum to be considered a win
                    success = 1.0 if (
                        net_return_pct > cost_threshold or 
                        (perf.hit_target_1 and net_return_pct > -0.002)  # Hit target with minimal cost drag
                    ) else 0.0
                    
                    # Store cost breakdown for debugging/analysis
                    features['estimated_costs_pct'] = total_costs_pct
                    features['net_return_pct'] = net_return_pct
                    features['gross_return_pct'] = gross_return_pct
                    
                    y.append(success)
                    
                except Exception as e:
                    logger.debug(f"Error processing signal {signal.symbol}: {e}")
                    continue
            
            logger.info(f"✅ Loaded {len(X)} training records ({sum(y)} wins, {len(y) - sum(y)} losses)")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Error loading training data: {e}", exc_info=True)
            return [], []
    
    def train_model(self, days_back: int = 30, force_retrain: bool = False) -> Dict:
        """
        Train ML model on historical performance data from database.
        Returns training metrics.
        
        Args:
            days_back: How many days of history to use for training
            force_retrain: Force retraining even if model exists
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - cannot train model")
            return {'error': 'ML libraries not available'}
        
        # Check cache to avoid retraining too frequently
        cache_key = f"day_trading_ml_last_train"
        if not force_retrain:
            last_train = cache.get(cache_key)
            if last_train:
                hours_since_train = (django_timezone.now() - last_train).total_seconds() / 3600
                if hours_since_train < 6:  # Don't retrain more than once every 6 hours
                    logger.info(f"⏭️ Skipping retrain - last trained {hours_since_train:.1f} hours ago")
                    return {'message': 'Skipped - trained recently', 'hours_ago': hours_since_train}
        
        # Load training data
        X_dicts, y = self.load_training_data_from_database(days_back=days_back, min_records=50)
        
        if len(X_dicts) < 50:
            logger.warning(f"Not enough data to train (need 50+, have {len(X_dicts)})")
            return {'error': 'Insufficient data', 'records': len(X_dicts)}
        
        try:
            # Convert feature dicts to arrays
            # Use consistent feature order
            feature_names = [
                'momentum_15m', 'rvol_10m', 'vwap_dist', 'breakout_pct', 'spread_bps',
                'catalyst_score', 'volume_ratio', 'volume_zscore', 'rsi_14',
                'is_trend_regime', 'is_range_regime', 'is_high_vol_chop', 'regime_confidence',
                'is_vol_expansion', 'is_breakout', 'is_three_white_soldiers',
                'is_engulfing_bull', 'is_engulfing_bear', 'is_hammer', 'is_doji',
                'vwap_dist_pct', 'macd_hist', 'bb_position', 'trend_strength',
                'price_above_sma20', 'price_above_sma50', 'sma20_above_sma50',
                'is_opening_hour', 'is_closing_hour', 'is_midday',
                'sentiment_score', 'sentiment_volume', 'sentiment_divergence',
                'score', 'mode_safe', 'side_long', 'hour_of_day', 'day_of_week'
            ]
            
            X = []
            for feat_dict in X_dicts:
                feature_vector = [feat_dict.get(name, 0.0) for name in feature_names]
                X.append(feature_vector)
            
            X = np.array(X)
            y = np.array(y)
            
            # Split into train/test
            if len(X) > 100:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                X_train, X_test, y_train, y_test = X, X, y, y
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test) if len(X_test) > 0 else X_train_scaled
            
            # Train model (Gradient Boosting for better performance)
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test) if len(X_test) > 0 else train_score
            
            # Calculate feature importance
            importances = self.model.feature_importances_
            self.feature_weights = dict(zip(feature_names, importances))
            
            # Auto-Stop on Overfit Detection
            overfit_detected = self._check_overfit(train_score, test_score)
            
            if overfit_detected:
                logger.error("🚨 OVERFIT DETECTED: train_score - test_score > 0.20")
                # Revert to previous model if available
                if os.path.exists(self.model_path + '.backup'):
                    logger.warning("🔄 Reverting to previous model due to overfit")
                    import shutil
                    shutil.copy(self.model_path + '.backup', self.model_path)
                    shutil.copy(self.scaler_path + '.backup', self.scaler_path)
                    self._load_model()
                    return {
                        'error': 'overfit_detected',
                        'message': 'Model overfit detected - reverted to previous model',
                        'train_score': float(train_score),
                        'test_score': float(test_score),
                        'delta': float(train_score - test_score),
                    }
            
            # Save backup before saving new model
            if os.path.exists(self.model_path):
                import shutil
                shutil.copy(self.model_path, self.model_path + '.backup')
                shutil.copy(self.scaler_path, self.scaler_path + '.backup')
            
            # Save model
            self._save_model()
            
            # Update cache
            cache.set(cache_key, django_timezone.now(), timeout=86400)  # 24 hours
            
            metrics = {
                'train_score': float(train_score),
                'test_score': float(test_score),
                'records_used': len(X),
                'feature_importances': {k: float(v) for k, v in self.feature_weights.items()},
                'success_rate': float(np.mean(y)),
                'overfit_detected': overfit_detected,
                'overfit_delta': float(train_score - test_score) if overfit_detected else None,
            }
            
            logger.info(f"✅ Trained day trading ML model: train_score={train_score:.3f}, test_score={test_score:.3f}, records={len(X)}")
            
            # Log top patterns learned (for observability)
            top_features = sorted(
                self.feature_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            logger.info(f"🧠 Top patterns learned:")
            for feat, importance in top_features:
                logger.info(f"   - {feat}: {importance:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _check_overfit(self, train_score: float, test_score: float) -> bool:
        """
        Auto-Stop on Overfit Detection.
        If train_accuracy - validation_accuracy > 0.20 for two consecutive days → overfit detected.
        """
        delta = train_score - test_score
        
        # Store overfit history (last 2 days)
        overfit_history_path = os.path.join(
            os.path.dirname(self.model_path),
            'day_trading_overfit_history.json'
        )
        
        overfit_history = []
        if os.path.exists(overfit_history_path):
            try:
                with open(overfit_history_path, 'r') as f:
                    overfit_history = json.load(f)
            except:
                overfit_history = []
        
        # Add current delta
        overfit_history.append({
            'delta': delta,
            'timestamp': django_timezone.now().isoformat(),
        })
        
        # Keep only last 2 days
        overfit_history = overfit_history[-2:]
        
        # Save history
        try:
            with open(overfit_history_path, 'w') as f:
                json.dump(overfit_history, f)
        except:
            pass
        
        # Check if last 2 days both have delta > 0.20
        if len(overfit_history) >= 2:
            last_two_deltas = [h['delta'] for h in overfit_history[-2:]]
            if all(d > 0.20 for d in last_two_deltas):
                return True
        
        return False
    
    def predict_success_probability(self, features: Dict[str, float]) -> float:
        """
        Predict the probability that a pick will be successful based on features.
        Returns float between 0 and 1.
        
        Args:
            features: Feature dictionary from DayTradingFeatureService
        """
        if not ML_AVAILABLE or not self.model or not self.scaler:
            # Fallback: use simple heuristic
            return self._heuristic_score(features)
        
        try:
            # Feature names in same order as training
            feature_names = [
                'momentum_15m', 'rvol_10m', 'vwap_dist', 'breakout_pct', 'spread_bps',
                'catalyst_score', 'volume_ratio', 'volume_zscore', 'rsi_14',
                'is_trend_regime', 'is_range_regime', 'is_high_vol_chop', 'regime_confidence',
                'is_vol_expansion', 'is_breakout', 'is_three_white_soldiers',
                'is_engulfing_bull', 'is_engulfing_bear', 'is_hammer', 'is_doji',
                'vwap_dist_pct', 'macd_hist', 'bb_position', 'trend_strength',
                'price_above_sma20', 'price_above_sma50', 'sma20_above_sma50',
                'is_opening_hour', 'is_closing_hour', 'is_midday',
                'sentiment_score', 'sentiment_volume', 'sentiment_divergence',
                'score', 'mode_safe', 'side_long', 'hour_of_day', 'day_of_week'
            ]
            
            # Map feature dict to array (handle different naming conventions)
            feature_mapping = {
                'momentum_15m': ['momentum_15m', 'momentum15m'],
                'rvol_10m': ['rvol_10m', 'rvol10m'],
                'vwap_dist': ['vwap_dist', 'vwapDist'],
                'breakout_pct': ['breakout_pct', 'breakoutPct'],
                'spread_bps': ['spread_bps', 'spreadBps'],
                'catalyst_score': ['catalyst_score', 'catalystScore'],
                'volume_ratio': ['volume_ratio', 'volumeRatio'],
                'volume_zscore': ['volume_zscore', 'volumeZscore'],
                'rsi_14': ['rsi_14', 'rsi14'],
                'is_trend_regime': ['is_trend_regime', 'isTrendRegime'],
                'is_range_regime': ['is_range_regime', 'isRangeRegime'],
                'is_high_vol_chop': ['is_high_vol_chop', 'isHighVolChop'],
                'regime_confidence': ['regime_confidence', 'regimeConfidence'],
                'is_vol_expansion': ['is_vol_expansion', 'isVolExpansion'],
                'is_breakout': ['is_breakout', 'isBreakout'],
                'is_three_white_soldiers': ['is_three_white_soldiers', 'isThreeWhiteSoldiers'],
                'is_engulfing_bull': ['is_engulfing_bull', 'isEngulfingBull'],
                'is_engulfing_bear': ['is_engulfing_bear', 'isEngulfingBear'],
                'is_hammer': ['is_hammer', 'isHammer'],
                'is_doji': ['is_doji', 'isDoji'],
                'vwap_dist_pct': ['vwap_dist_pct', 'vwapDistPct'],
                'macd_hist': ['macd_hist', 'macdHist'],
                'bb_position': ['bb_position', 'bbPosition'],
                'trend_strength': ['trend_strength', 'trendStrength'],
                'price_above_sma20': ['price_above_sma20', 'priceAboveSma20'],
                'price_above_sma50': ['price_above_sma50', 'priceAboveSma50'],
                'sma20_above_sma50': ['sma20_above_sma50', 'sma20AboveSma50'],
                'is_opening_hour': ['is_opening_hour', 'isOpeningHour'],
                'is_closing_hour': ['is_closing_hour', 'isClosingHour'],
                'is_midday': ['is_midday', 'isMidday'],
                'sentiment_score': ['sentiment_score', 'sentimentScore'],
                'sentiment_volume': ['sentiment_volume', 'sentimentVolume'],
                'sentiment_divergence': ['sentiment_divergence', 'sentimentDivergence'],
            }
            
            feature_vector = []
            for name in feature_names:
                value = 0.0
                if name in features:
                    value = float(features[name])
                elif name in feature_mapping:
                    # Try alternative names
                    for alt_name in feature_mapping[name]:
                        if alt_name in features:
                            value = float(features[alt_name])
                            break
                feature_vector.append(value)
            
            # Handle special cases
            if 'score' in features:
                feature_vector[feature_names.index('score')] = float(features['score'])
            if 'mode' in features:
                feature_vector[feature_names.index('mode_safe')] = 1.0 if features['mode'] == 'SAFE' else 0.0
            if 'side' in features:
                feature_vector[feature_names.index('side_long')] = 1.0 if features['side'] == 'LONG' else 0.0
            
            # Get current time features
            now = django_timezone.now()
            feature_vector[feature_names.index('hour_of_day')] = now.hour / 24.0
            feature_vector[feature_names.index('day_of_week')] = now.weekday() / 7.0
            
            feature_vector = np.array([feature_vector])
            
            # Scale and predict
            feature_vector_scaled = self.scaler.transform(feature_vector)
            probability = self.model.predict(feature_vector_scaled)[0]
            
            # Clamp to [0, 1]
            probability = max(0.0, min(1.0, probability))
            
            return float(probability)
            
        except Exception as e:
            logger.warning(f"Error predicting success probability: {e}, using heuristic")
            return self._heuristic_score(features)
    
    def _heuristic_score(self, features: Dict[str, float]) -> float:
        """
        Fallback heuristic score when ML model is not available.
        Based on simple rules learned from experience.
        """
        momentum = abs(features.get('momentum_15m', features.get('momentum15m', 0.0)))
        volume_ratio = features.get('volume_ratio', features.get('volumeRatio', 1.0))
        breakout_pct = features.get('breakout_pct', features.get('breakoutPct', 0.0))
        
        score = 0.5  # Base probability
        
        # Positive factors
        if 0.01 <= momentum <= 0.05:  # Moderate momentum
            score += 0.2
        if volume_ratio > 1.5:  # High volume
            score += 0.15
        if 0.02 <= breakout_pct <= 0.15:  # Good breakout
            score += 0.1
        
        # Negative factors
        if momentum > 0.10:  # Too extreme (likely to reverse)
            score -= 0.2
        if momentum < 0.005:  # Too weak (no momentum)
            score -= 0.1
        if volume_ratio < 0.8:  # Low volume
            score -= 0.15
        
        return max(0.0, min(1.0, score))
    
    def enhance_score_with_ml(self, base_score: float, features: Dict[str, float]) -> float:
        """
        Enhance base score with ML prediction.
        Uses weighted combination: 40% base signal, 60% ML probability
        """
        ml_prob = self.predict_success_probability(features)
        
        # Normalize base_score to 0-1 range (assuming max is 10)
        normalized_base_score = min(base_score / 10.0, 1.0)
        
        # Weighted combination: 40% base signal, 60% ML probability
        weighted_score = (normalized_base_score * 0.4) + (ml_prob * 0.6)
        
        # Scale back to 0-10 range
        enhanced_score = weighted_score * 10.0
        
        return float(enhanced_score)
    
    def get_learning_insights(self) -> Dict:
        """
        Get insights from what the model has learned.
        Returns feature importances and patterns.
        """
        if not self.feature_weights:
            return {'message': 'Model not trained yet'}
        
        # Sort features by importance
        sorted_features = sorted(
            self.feature_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'top_features': sorted_features[:10],
            'model_available': self.model is not None,
            'model_path': self.model_path if os.path.exists(self.model_path) else None,
        }


# Global instance
_ml_learner_instance = None

def get_day_trading_ml_learner() -> DayTradingMLearner:
    """Get or create global ML learner instance"""
    global _ml_learner_instance
    if _ml_learner_instance is None:
        _ml_learner_instance = DayTradingMLearner()
    return _ml_learner_instance

