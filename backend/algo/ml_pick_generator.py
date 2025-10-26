"""
Machine Learning Pick Generation Engine
ML-powered trading signal generation beyond rule-based systems
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json

from ..market.providers.enhanced_base import MarketDataProvider
from ..broker.adapters.enhanced_base import BrokerageAdapter


@dataclass
class MLPick:
    """ML-generated trading pick"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    
    # ML predictions
    ml_score: float  # 0 to 1
    confidence: float  # 0 to 1
    prediction_horizon: int  # minutes
    
    # Feature importance
    feature_importance: Dict[str, float]
    
    # Ensemble predictions
    rf_prediction: float
    gb_prediction: float
    ridge_prediction: float
    
    # Risk metrics
    predicted_volatility: float
    predicted_drawdown: float
    risk_score: float
    
    # Market context
    market_regime: str
    sector_momentum: float
    
    # Timestamps
    generated_at: datetime
    valid_until: datetime


class MLPickGenerator:
    """Machine learning-powered trading pick generation"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # ML Models
        self.rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.gb_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=8,
            random_state=42
        )
        
        self.ridge_model = Ridge(alpha=1.0)
        
        # Feature scaler
        self.scaler = StandardScaler()
        
        # Feature importance tracking
        self.feature_names = [
            "momentum_15m", "momentum_5m", "momentum_1m",
            "rvol_10m", "rvol_5m", "volume_spike",
            "rsi_14", "macd_signal", "bollinger_position", "vwap_distance",
            "spread_bps", "bid_ask_ratio", "order_flow_imbalance",
            "atr_5m", "atr_15m", "volatility_regime",
            "breakout_pct", "resistance_level", "support_level",
            "news_sentiment", "earnings_proximity", "catalyst_score",
            "sector_momentum", "market_regime", "vix_level"
        ]
        
        # Model performance tracking
        self.model_performance = {
            "rf": {"mse": 0.0, "r2": 0.0, "accuracy": 0.0},
            "gb": {"mse": 0.0, "r2": 0.0, "accuracy": 0.0},
            "ridge": {"mse": 0.0, "r2": 0.0, "accuracy": 0.0}
        }
        
        # Training data storage
        self.training_data = []
        self.is_trained = False
        
        # Initialize with training data
        self._train_models()
    
    def _train_models(self):
        """Train ML models on synthetic data (in production, use real historical data)"""
        try:
            # Generate synthetic training data
            np.random.seed(42)
            n_samples = 5000
            
            # Generate features
            X = np.random.randn(n_samples, len(self.feature_names))
            
            # Create realistic feature distributions
            X[:, 0] = np.random.normal(0, 0.02, n_samples)  # momentum_15m
            X[:, 1] = np.random.normal(0, 0.01, n_samples)   # momentum_5m
            X[:, 2] = np.random.normal(0, 0.005, n_samples) # momentum_1m
            X[:, 3] = np.random.uniform(0.5, 3.0, n_samples) # rvol_10m
            X[:, 4] = np.random.uniform(0.3, 2.0, n_samples) # rvol_5m
            X[:, 5] = np.random.uniform(0.5, 2.0, n_samples) # volume_spike
            X[:, 6] = np.random.uniform(20, 80, n_samples)    # rsi_14
            X[:, 7] = np.random.normal(0, 0.01, n_samples)  # macd_signal
            X[:, 8] = np.random.uniform(-0.1, 0.1, n_samples) # bollinger_position
            X[:, 9] = np.random.uniform(-0.05, 0.05, n_samples) # vwap_distance
            X[:, 10] = np.random.uniform(1, 20, n_samples)   # spread_bps
            X[:, 11] = np.random.uniform(0.8, 1.2, n_samples) # bid_ask_ratio
            X[:, 12] = np.random.uniform(-0.1, 0.1, n_samples) # order_flow_imbalance
            X[:, 13] = np.random.uniform(0.5, 3.0, n_samples) # atr_5m
            X[:, 14] = np.random.uniform(1.0, 5.0, n_samples) # atr_15m
            X[:, 15] = np.random.uniform(0, 2, n_samples)    # volatility_regime
            X[:, 16] = np.random.uniform(0, 0.05, n_samples) # breakout_pct
            X[:, 17] = np.random.uniform(0.95, 1.05, n_samples) # resistance_level
            X[:, 18] = np.random.uniform(0.95, 1.05, n_samples) # support_level
            X[:, 19] = np.random.uniform(-1, 1, n_samples)  # news_sentiment
            X[:, 20] = np.random.uniform(0, 1, n_samples)   # earnings_proximity
            X[:, 21] = np.random.uniform(0, 1, n_samples)   # catalyst_score
            X[:, 22] = np.random.uniform(-0.1, 0.1, n_samples) # sector_momentum
            X[:, 23] = np.random.uniform(0, 3, n_samples)   # market_regime
            X[:, 24] = np.random.uniform(10, 40, n_samples)  # vix_level
            
            # Generate target variable (trading success score)
            # Combine features to create realistic targets
            y = (
                X[:, 0] * 0.3 +  # momentum weight
                X[:, 3] * 0.2 +  # volume weight
                X[:, 6] * 0.1 +  # RSI weight
                X[:, 19] * 0.2 + # sentiment weight
                X[:, 21] * 0.2   # catalyst weight
            )
            
            # Add noise and normalize to [0, 1]
            y += np.random.normal(0, 0.1, n_samples)
            y = (y - y.min()) / (y.max() - y.min())
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train models
            self.rf_model.fit(X_train_scaled, y_train)
            self.gb_model.fit(X_train_scaled, y_train)
            self.ridge_model.fit(X_train_scaled, y_train)
            
            # Evaluate models
            self._evaluate_models(X_test_scaled, y_test)
            
            self.is_trained = True
            self.logger.info("ML models trained successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to train ML models: {e}")
    
    def _evaluate_models(self, X_test: np.ndarray, y_test: np.ndarray):
        """Evaluate model performance"""
        try:
            # Random Forest
            rf_pred = self.rf_model.predict(X_test)
            self.model_performance["rf"]["mse"] = mean_squared_error(y_test, rf_pred)
            self.model_performance["rf"]["r2"] = r2_score(y_test, rf_pred)
            self.model_performance["rf"]["accuracy"] = self._calculate_accuracy(y_test, rf_pred)
            
            # Gradient Boosting
            gb_pred = self.gb_model.predict(X_test)
            self.model_performance["gb"]["mse"] = mean_squared_error(y_test, gb_pred)
            self.model_performance["gb"]["r2"] = r2_score(y_test, gb_pred)
            self.model_performance["gb"]["accuracy"] = self._calculate_accuracy(y_test, gb_pred)
            
            # Ridge Regression
            ridge_pred = self.ridge_model.predict(X_test)
            self.model_performance["ridge"]["mse"] = mean_squared_error(y_test, ridge_pred)
            self.model_performance["ridge"]["r2"] = r2_score(y_test, ridge_pred)
            self.model_performance["ridge"]["accuracy"] = self._calculate_accuracy(y_test, ridge_pred)
            
            self.logger.info(f"Model performance: RF R²={self.model_performance['rf']['r2']:.3f}, "
                           f"GB R²={self.model_performance['gb']['r2']:.3f}, "
                           f"Ridge R²={self.model_performance['ridge']['r2']:.3f}")
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate models: {e}")
    
    def _calculate_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate accuracy for regression (percentage within threshold)"""
        threshold = 0.1  # Within 10% of actual value
        accuracy = np.mean(np.abs(y_true - y_pred) < threshold)
        return accuracy
    
    async def generate_ml_picks(self, symbols: List[str]) -> List[MLPick]:
        """Generate ML-powered trading picks"""
        try:
            picks = []
            
            for symbol in symbols:
                # Get features for symbol
                features = await self._get_symbol_features(symbol)
                
                if features is None:
                    continue
                
                # Generate ML predictions
                ml_pick = await self._generate_ml_pick(symbol, features)
                
                if ml_pick:
                    picks.append(ml_pick)
            
            # Sort by ML score
            picks.sort(key=lambda x: x.ml_score, reverse=True)
            
            self.logger.info(f"Generated {len(picks)} ML picks")
            
            return picks
            
        except Exception as e:
            self.logger.error(f"Failed to generate ML picks: {e}")
            return []
    
    async def _get_symbol_features(self, symbol: str) -> Optional[np.ndarray]:
        """Get features for a specific symbol"""
        try:
            # Get market data
            quotes = await self.market_data_provider.get_quotes([symbol])
            if symbol not in quotes:
                return None
            
            quote = quotes[symbol]
            
            # Get historical data for technical indicators
            ohlcv_data = await self.market_data_provider.get_ohlcv(symbol, "1m", limit=100)
            if not ohlcv_data:
                return None
            
            # Calculate features
            features = self._calculate_features(symbol, quote, ohlcv_data)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Failed to get features for {symbol}: {e}")
            return None
    
    def _calculate_features(self, symbol: str, quote: Any, ohlcv_data: List[Any]) -> np.ndarray:
        """Calculate features for ML model"""
        try:
            # Convert OHLCV to DataFrame for easier calculation
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate technical indicators
            features = np.zeros(len(self.feature_names))
            
            # Price momentum
            if len(df) >= 15:
                features[0] = (df['close'].iloc[-1] - df['close'].iloc[-15]) / df['close'].iloc[-15]  # momentum_15m
            if len(df) >= 5:
                features[1] = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]    # momentum_5m
            if len(df) >= 1:
                features[2] = (df['close'].iloc[-1] - df['open'].iloc[-1]) / df['open'].iloc[-1]      # momentum_1m
            
            # Volume features
            if len(df) >= 10:
                avg_volume = df['volume'].rolling(10).mean().iloc[-1]
                features[3] = df['volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1.0  # rvol_10m
            if len(df) >= 5:
                avg_volume = df['volume'].rolling(5).mean().iloc[-1]
                features[4] = df['volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1.0  # rvol_5m
            
            # Volume spike
            if len(df) >= 20:
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                features[5] = df['volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # Technical indicators (simplified calculations)
            features[6] = self._calculate_rsi(df['close'])  # RSI
            features[7] = self._calculate_macd(df['close'])  # MACD
            features[8] = self._calculate_bollinger_position(df['close'])  # Bollinger position
            features[9] = self._calculate_vwap_distance(df)  # VWAP distance
            
            # Market microstructure
            features[10] = (quote.ask - quote.bid) / quote.price * 10000 if quote.price > 0 else 0  # spread_bps
            features[11] = quote.bid_size / quote.ask_size if quote.ask_size > 0 else 1.0  # bid_ask_ratio
            features[12] = 0.0  # order_flow_imbalance (would need order book data)
            
            # Volatility features
            features[13] = self._calculate_atr(df, 5)   # ATR 5m
            features[14] = self._calculate_atr(df, 15)   # ATR 15m
            features[15] = 1.0 if features[13] > 0.02 else 0.0  # volatility_regime
            
            # Breakout features
            features[16] = self._calculate_breakout_pct(df)  # breakout_pct
            features[17] = df['high'].rolling(20).max().iloc[-1] / df['close'].iloc[-1] if len(df) >= 20 else 1.0  # resistance_level
            features[18] = df['low'].rolling(20).min().iloc[-1] / df['close'].iloc[-1] if len(df) >= 20 else 1.0   # support_level
            
            # Sentiment and catalyst features (would need external data)
            features[19] = 0.0  # news_sentiment
            features[20] = 0.0  # earnings_proximity
            features[21] = 0.5  # catalyst_score
            
            # Market context features
            features[22] = 0.0  # sector_momentum
            features[23] = 1.0  # market_regime
            features[24] = 20.0  # vix_level
            
            return features
            
        except Exception as e:
            self.logger.error(f"Failed to calculate features: {e}")
            return np.zeros(len(self.feature_names))
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            
        except Exception:
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> float:
        """Calculate MACD signal"""
        try:
            if len(prices) < 26:
                return 0.0
            
            ema12 = prices.ewm(span=12).mean()
            ema26 = prices.ewm(span=26).mean()
            macd = ema12 - ema26
            
            return macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_bollinger_position(self, prices: pd.Series, period: int = 20) -> float:
        """Calculate Bollinger Band position"""
        try:
            if len(prices) < period:
                return 0.0
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            current_price = prices.iloc[-1]
            position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
            
            return position if not pd.isna(position) else 0.5
            
        except Exception:
            return 0.5
    
    def _calculate_vwap_distance(self, df: pd.DataFrame) -> float:
        """Calculate VWAP distance"""
        try:
            if len(df) < 1:
                return 0.0
            
            vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
            current_price = df['close'].iloc[-1]
            
            return (current_price - vwap) / vwap if vwap > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Average True Range"""
        try:
            if len(df) < period + 1:
                return 0.0
            
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_breakout_pct(self, df: pd.DataFrame) -> float:
        """Calculate breakout percentage"""
        try:
            if len(df) < 20:
                return 0.0
            
            resistance = df['high'].rolling(20).max().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            return (current_price - resistance) / resistance if resistance > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _generate_ml_pick(self, symbol: str, features: np.ndarray) -> Optional[MLPick]:
        """Generate ML pick for a symbol"""
        try:
            if not self.is_trained:
                return None
            
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Get predictions from all models
            rf_pred = self.rf_model.predict(features_scaled)[0]
            gb_pred = self.gb_model.predict(features_scaled)[0]
            ridge_pred = self.ridge_model.predict(features_scaled)[0]
            
            # Ensemble prediction (weighted average)
            ml_score = (rf_pred * 0.4 + gb_pred * 0.4 + ridge_pred * 0.2)
            
            # Calculate confidence based on model agreement
            predictions = [rf_pred, gb_pred, ridge_pred]
            confidence = 1.0 - np.std(predictions)
            
            # Get feature importance
            feature_importance = dict(zip(self.feature_names, self.rf_model.feature_importances_))
            
            # Determine side based on momentum
            momentum_15m = features[0]
            side = "LONG" if momentum_15m > 0 else "SHORT"
            
            # Calculate risk metrics
            predicted_volatility = features[13]  # ATR 5m
            predicted_drawdown = predicted_volatility * 2.0  # Estimate
            risk_score = min(predicted_volatility * 10, 1.0)  # Normalize
            
            # Create ML pick
            ml_pick = MLPick(
                symbol=symbol,
                side=side,
                ml_score=ml_score,
                confidence=confidence,
                prediction_horizon=60,  # 1 hour
                feature_importance=feature_importance,
                rf_prediction=rf_pred,
                gb_prediction=gb_pred,
                ridge_prediction=ridge_pred,
                predicted_volatility=predicted_volatility,
                predicted_drawdown=predicted_drawdown,
                risk_score=risk_score,
                market_regime="NEUTRAL",  # Would be determined by regime detector
                sector_momentum=features[22],
                generated_at=datetime.now(),
                valid_until=datetime.now() + timedelta(minutes=60)
            )
            
            return ml_pick
            
        except Exception as e:
            self.logger.error(f"Failed to generate ML pick for {symbol}: {e}")
            return None
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        return {
            "models": self.model_performance,
            "is_trained": self.is_trained,
            "feature_count": len(self.feature_names),
            "training_samples": len(self.training_data) if self.training_data else 0
        }
    
    def save_models(self, filepath: str):
        """Save trained models"""
        try:
            model_data = {
                'rf_model': self.rf_model,
                'gb_model': self.gb_model,
                'ridge_model': self.ridge_model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_performance': self.model_performance
            }
            joblib.dump(model_data, filepath)
            self.logger.info(f"Models saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save models: {e}")
    
    def load_models(self, filepath: str):
        """Load trained models"""
        try:
            model_data = joblib.load(filepath)
            self.rf_model = model_data['rf_model']
            self.gb_model = model_data['gb_model']
            self.ridge_model = model_data['ridge_model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_performance = model_data['model_performance']
            self.is_trained = True
            self.logger.info(f"Models loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")


# Integration with existing trading engine
class MLEnhancedTradingEngine:
    """Trading engine enhanced with ML pick generation"""
    
    def __init__(self, ml_generator: MLPickGenerator):
        self.ml_generator = ml_generator
        self.logger = logging.getLogger(__name__)
    
    async def generate_ml_enhanced_picks(self, symbols: List[str]) -> List[Dict]:
        """Generate picks enhanced with ML predictions"""
        try:
            # Get ML picks
            ml_picks = await self.ml_generator.generate_ml_picks(symbols)
            
            # Convert to standard pick format
            enhanced_picks = []
            
            for ml_pick in ml_picks:
                # Create standard pick format
                pick = {
                    "symbol": ml_pick.symbol,
                    "side": ml_pick.side,
                    "score": ml_pick.ml_score,
                    "confidence": ml_pick.confidence,
                    "features": {
                        "momentum_15m": 0.0,  # Would be calculated from features
                        "rvol_10m": 0.0,
                        "vwap_dist": 0.0,
                        "breakout_pct": 0.0,
                        "spread_bps": 0.0,
                        "catalyst_score": 0.5
                    },
                    "risk": {
                        "atr_5m": ml_pick.predicted_volatility,
                        "size_shares": 100,
                        "stop": 0.95,
                        "targets": [1.02, 1.05],
                        "time_stop_min": ml_pick.prediction_horizon
                    },
                    "ml_context": {
                        "ml_score": ml_pick.ml_score,
                        "confidence": ml_pick.confidence,
                        "rf_prediction": ml_pick.rf_prediction,
                        "gb_prediction": ml_pick.gb_prediction,
                        "ridge_prediction": ml_pick.ridge_prediction,
                        "feature_importance": ml_pick.feature_importance,
                        "predicted_volatility": ml_pick.predicted_volatility,
                        "risk_score": ml_pick.risk_score
                    },
                    "notes": f"ML-enhanced pick: {ml_pick.side} {ml_pick.symbol} (ML Score: {ml_pick.ml_score:.3f})"
                }
                
                enhanced_picks.append(pick)
            
            return enhanced_picks
            
        except Exception as e:
            self.logger.error(f"Failed to generate ML-enhanced picks: {e}")
            return []
