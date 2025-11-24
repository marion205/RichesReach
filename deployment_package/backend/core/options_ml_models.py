"""
Advanced ML Models for Options Strategy Optimization

Hedge Fund-Level Machine Learning for Options Trading

"""
import os

os.environ.setdefault("YFINANCE_CACHE_DISABLE", "1")  # disable yfinance cache

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class OptionsMLModels:
    """Advanced ML models for options strategy optimization"""

    def __init__(self) -> None:
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_importance: Dict[str, Any] = {}
        self.model_performance: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # Training: Price Prediction
    # ------------------------------------------------------------------ #
    async def train_price_prediction_model(self, symbol: str, lookback_days: int = 252) -> Dict[str, Any]:
        """Train ML models for next-day price return prediction."""
        try:
            logger.info("Training price prediction model for %s", symbol)

            # Get historical data
            stock = yf.Ticker(symbol)
            hist = stock.history(period=f"{lookback_days}d")
            if len(hist) < 50:
                logger.warning("Insufficient data for %s", symbol)
                return {}

            # Prepare features and target (next-day return)
            features = self._create_price_features(hist)
            target = hist["Close"].pct_change().shift(-1).dropna()

            # Align features and target
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]

            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                features,
                target,
                test_size=0.2,
                random_state=42,
                shuffle=False,
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train multiple models and pick the best by R²
            models = {
                "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
                "gradient_boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
                "neural_network": MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    max_iter=500,
                    random_state=42,
                ),
            }

            best_model = None
            best_score = -np.inf
            best_model_name: Optional[str] = None

            for name, model in models.items():
                try:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    score = r2_score(y_test, y_pred)

                    # Store per-model performance
                    perf_key = f"{symbol}_{name}"
                    self.model_performance[perf_key] = {
                        "r2_score": float(score),
                        "mse": float(mean_squared_error(y_test, y_pred)),
                        "feature_importance": getattr(model, "feature_importances_", None),
                    }

                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_model_name = name
                except Exception as e:
                    logger.error("Error training %s for %s: %s", name, symbol, e)
                    continue

            if best_model is not None:
                model_key = f"{symbol}_price_prediction"

                # Save best model + scaler
                self.models[model_key] = best_model
                self.scalers[model_key] = scaler

                # Save best performance under the key used by prediction
                self.model_performance[model_key] = {
                    "r2_score": float(best_score),
                    "mse": float(self.model_performance.get(f"{symbol}_{best_model_name}", {}).get("mse", 0.0)),
                    "model_name": best_model_name,
                    "features_used": list(features.columns),
                }

                logger.info(
                    "Best model for %s: %s (R² = %.3f)",
                    symbol,
                    best_model_name,
                    best_score,
                )

                return {
                    "model_name": best_model_name,
                    "r2_score": float(best_score),
                    "features_used": list(features.columns),
                    "training_samples": int(len(X_train)),
                    "test_samples": int(len(X_test)),
                }

            logger.warning("No valid price prediction model trained for %s", symbol)
            return {}

        except Exception as e:
            logger.error("Error training price prediction model for %s: %s", symbol, e)
            return {}

    # ------------------------------------------------------------------ #
    # Training: Volatility Prediction
    # ------------------------------------------------------------------ #
    async def train_volatility_prediction_model(self, symbol: str, lookback_days: int = 252) -> Dict[str, Any]:
        """Train model for realized volatility prediction."""
        try:
            logger.info("Training volatility prediction model for %s", symbol)

            stock = yf.Ticker(symbol)
            hist = stock.history(period=f"{lookback_days}d")
            if len(hist) < 50:
                logger.warning("Insufficient data for volatility model %s", symbol)
                return {}

            returns = hist["Close"].pct_change().dropna()
            realized_vol = returns.rolling(window=20).std() * np.sqrt(252)

            features = self._create_volatility_features(hist, returns)

            # Align features and target
            min_len = min(len(features), len(realized_vol))
            features = features.iloc[:min_len]
            target = realized_vol.iloc[:min_len]

            # Remove NaNs
            valid_idx = ~(target.isna() | features.isna().any(axis=1))
            features = features[valid_idx]
            target = target[valid_idx]

            if len(features) < 30:
                logger.warning("Not enough clean data for volatility model %s", symbol)
                return {}

            X_train, X_test, y_train, y_test = train_test_split(
                features,
                target,
                test_size=0.2,
                random_state=42,
                shuffle=False,
            )

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)

            y_pred = model.predict(X_test_scaled)
            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)

            model_key = f"{symbol}_volatility_prediction"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            self.model_performance[model_key] = {
                "r2_score": float(r2),
                "mse": float(mse),
                "features_used": list(features.columns),
            }

            logger.info("Volatility model for %s: R² = %.3f", symbol, r2)

            return {
                "r2_score": float(r2),
                "mse": float(mse),
                "features_used": list(features.columns),
                "training_samples": int(len(X_train)),
                "test_samples": int(len(X_test)),
            }

        except Exception as e:
            logger.error("Error training volatility prediction model for %s: %s", symbol, e)
            return {}

    # ------------------------------------------------------------------ #
    # Inference: Price / Volatility
    # ------------------------------------------------------------------ #
    async def predict_price_movement(
        self,
        symbol: str,
        current_price: float,
        days_ahead: int = 30,
    ) -> Dict[str, Any]:
        """Predict price movement using trained models."""
        try:
            model_key = f"{symbol}_price_prediction"

            if model_key not in self.models:
                # Train on-demand if not already trained
                await self.train_price_prediction_model(symbol)
            if model_key not in self.models:
                return {}

            stock = yf.Ticker(symbol)
            hist = stock.history(period="60d")
            if len(hist) < 30:
                return {}

            features = self._create_price_features(hist)
            if features.empty:
                return {}

            latest_features = features.iloc[-1:].values

            scaler = self.scalers[model_key]
            scaled_features = scaler.transform(latest_features)

            model = self.models[model_key]
            predicted_return = float(model.predict(scaled_features)[0])

            predicted_price = float(current_price * (1 + predicted_return))

            # Confidence based on model R²
            r2 = float(self.model_performance.get(model_key, {}).get("r2_score", 0.5))
            confidence = float(min(95, max(50, r2 * 100)))

            return {
                "predicted_price": predicted_price,
                "predicted_return": predicted_return,
                "confidence": confidence,
                "direction": "up" if predicted_return > 0 else "down",
                "magnitude": abs(predicted_return),
            }

        except Exception as e:
            logger.error("Error predicting price movement for %s: %s", symbol, e)
            return {}

    async def predict_volatility(self, symbol: str) -> Dict[str, Any]:
        """Predict future volatility."""
        try:
            model_key = f"{symbol}_volatility_prediction"

            if model_key not in self.models:
                await self.train_volatility_prediction_model(symbol)
            if model_key not in self.models:
                return {}

            stock = yf.Ticker(symbol)
            hist = stock.history(period="60d")
            if len(hist) < 30:
                return {}

            returns = hist["Close"].pct_change().dropna()

            features = self._create_volatility_features(hist, returns)
            if features.empty:
                return {}

            latest_features = features.iloc[-1:].values

            scaler = self.scalers[model_key]
            scaled_features = scaler.transform(latest_features)

            model = self.models[model_key]
            predicted_vol = float(model.predict(scaled_features)[0])

            r2 = float(self.model_performance.get(model_key, {}).get("r2_score", 0.5))
            confidence = float(min(95, max(50, r2 * 100)))

            return {
                "predicted_volatility": predicted_vol,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error("Error predicting volatility for %s: %s", symbol, e)
            return {}

    # ------------------------------------------------------------------ #
    # Feature Engineering
    # ------------------------------------------------------------------ #
    def _create_price_features(self, hist: pd.DataFrame) -> pd.DataFrame:
        """Create features for price prediction."""
        try:
            features = pd.DataFrame(index=hist.index)

            # Price-based
            features["close"] = hist["Close"]
            features["volume"] = hist["Volume"]
            features["high"] = hist["High"]
            features["low"] = hist["Low"]
            features["open"] = hist["Open"]

            # Moving averages
            features["sma_5"] = hist["Close"].rolling(5).mean()
            features["sma_10"] = hist["Close"].rolling(10).mean()
            features["sma_20"] = hist["Close"].rolling(20).mean()
            features["sma_50"] = hist["Close"].rolling(50).mean()

            # EMAs
            features["ema_12"] = hist["Close"].ewm(span=12).mean()
            features["ema_26"] = hist["Close"].ewm(span=26).mean()

            # RSI
            delta = hist["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features["rsi"] = 100 - (100 / (1 + rs))

            # MACD
            macd_line = features["ema_12"] - features["ema_26"]
            signal_line = macd_line.ewm(span=9).mean()
            features["macd"] = macd_line
            features["macd_signal"] = signal_line
            features["macd_histogram"] = macd_line - signal_line

            # Bollinger Bands
            bb_middle = hist["Close"].rolling(20).mean()
            bb_std = hist["Close"].rolling(20).std()
            features["bb_upper"] = bb_middle + (bb_std * 2)
            features["bb_lower"] = bb_middle - (bb_std * 2)
            # Use feature columns, not bare variables
            features["bb_position"] = (hist["Close"] - features["bb_lower"]) / (
                features["bb_upper"] - features["bb_lower"]
            )

            # Volatility
            returns = hist["Close"].pct_change()
            features["volatility_5"] = returns.rolling(5).std()
            features["volatility_10"] = returns.rolling(10).std()
            features["volatility_20"] = returns.rolling(20).std()

            # Momentum
            features["momentum_5"] = hist["Close"].pct_change(5)
            features["momentum_10"] = hist["Close"].pct_change(10)
            features["momentum_20"] = hist["Close"].pct_change(20)

            # Volume indicators
            features["volume_sma"] = hist["Volume"].rolling(20).mean()
            features["volume_ratio"] = hist["Volume"] / features["volume_sma"]

            # Price position
            roll_min_20 = hist["Close"].rolling(20).min()
            roll_max_20 = hist["Close"].rolling(20).max()
            features["price_position_20"] = (hist["Close"] - roll_min_20) / (roll_max_20 - roll_min_20)

            roll_min_50 = hist["Close"].rolling(50).min()
            roll_max_50 = hist["Close"].rolling(50).max()
            features["price_position_50"] = (hist["Close"] - roll_min_50) / (roll_max_50 - roll_min_50)

            return features.dropna()

        except Exception as e:
            logger.error("Error creating price features: %s", e)
            return pd.DataFrame()

    def _create_volatility_features(self, hist: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
        """Create features for volatility prediction."""
        try:
            features = pd.DataFrame(index=hist.index)

            # Historical volatility
            features["vol_5"] = returns.rolling(5).std()
            features["vol_10"] = returns.rolling(10).std()
            features["vol_20"] = returns.rolling(20).std()
            features["vol_30"] = returns.rolling(30).std()

            # Vol of vol
            features["vol_of_vol_10"] = features["vol_10"].rolling(10).std()
            features["vol_of_vol_20"] = features["vol_20"].rolling(20).std()

            # Price-based
            features["close"] = hist["Close"]
            features["high_low_ratio"] = hist["High"] / hist["Low"]
            features["close_open_ratio"] = hist["Close"] / hist["Open"]

            # Volume-based
            features["volume"] = hist["Volume"]
            features["volume_volatility"] = hist["Volume"].pct_change().rolling(10).std()

            # Trend features
            features["sma_20"] = hist["Close"].rolling(20).mean()
            features["trend_strength"] = (hist["Close"] - features["sma_20"]) / features["sma_20"]

            # Market regime features
            features["regime_vol"] = returns.rolling(60).std()
            features["regime_trend"] = (
                hist["Close"]
                .rolling(60)
                .apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0,
                    raw=False,
                )
            )

            return features.dropna()

        except Exception as e:
            logger.error("Error creating volatility features: %s", e)
            return pd.DataFrame()

    # ------------------------------------------------------------------ #
    # Strategy Optimization
    # ------------------------------------------------------------------ #
    async def optimize_strategy_parameters(
        self,
        strategy_type: str,
        symbol: str,
        current_price: float,
        options_data: Dict[str, Dict[str, List[Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Optimize strategy parameters using ML predictions."""
        try:
            # Get predictions
            price_pred = await self.predict_price_movement(symbol, current_price)
            vol_pred = await self.predict_volatility(symbol)

            if not price_pred or not vol_pred:
                return {}

            if strategy_type == "covered_call":
                return self._optimize_covered_call(symbol, current_price, price_pred, vol_pred, options_data)
            elif strategy_type == "protective_put":
                return self._optimize_protective_put(symbol, current_price, price_pred, vol_pred, options_data)
            elif strategy_type == "iron_condor":
                return self._optimize_iron_condor(symbol, current_price, price_pred, vol_pred, options_data)

            # Unknown strategy type
            logger.warning("Unknown strategy type: %s", strategy_type)
            return {}

        except Exception as e:
            logger.error("Error optimizing strategy parameters: %s", e)
            return {}

    def _optimize_covered_call(
        self,
        symbol: str,
        current_price: float,
        price_pred: Dict[str, Any],
        vol_pred: Dict[str, Any],
        options_data: Dict[str, Dict[str, List[Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Optimize covered call parameters."""
        try:
            best_strike = None
            best_expiration = None
            best_score = 0.0

            predicted_price = float(price_pred.get("predicted_price", current_price))
            predicted_vol = float(vol_pred.get("predicted_volatility", 0.2))

            for exp_date, data in options_data.items():
                calls = data.get("calls", [])
                for call in calls:
                    if not call or "strike" not in call:
                        continue

                    strike = float(call["strike"])
                    bid = float(call.get("bid", 0) or 0)
                    ask = float(call.get("ask", 0) or 0)
                    mid_price = (bid + ask) / 2 if (bid and ask) else 0.0

                    if mid_price <= 0 or strike <= current_price:
                        continue

                    days_to_exp = self._days_to_expiration(exp_date)
                    if days_to_exp <= 0:
                        continue

                    # Probability of profit
                    prob_profit = self._calculate_probability_of_profit(
                        current_price, strike, predicted_vol, days_to_exp
                    )

                    # Expected annualized return from premium
                    annual_return = (mid_price / current_price) * (365.0 / days_to_exp)

                    # Simple risk proxy: lower strike = higher risk
                    risk_score = 1.0 - (strike - current_price) / current_price

                    score = (prob_profit * 0.4 + annual_return * 0.4 + risk_score * 0.2) * 100.0

                    if score > best_score:
                        best_score = score
                        best_strike = strike
                        best_expiration = exp_date

            return {
                "optimal_strike": best_strike,
                "optimal_expiration": best_expiration,
                "optimization_score": best_score,
                "predicted_price": predicted_price,
                "predicted_volatility": predicted_vol,
            }

        except Exception as e:
            logger.error("Error optimizing covered call: %s", e)
            return {}

    def _optimize_protective_put(
        self,
        symbol: str,
        current_price: float,
        price_pred: Dict[str, Any],
        vol_pred: Dict[str, Any],
        options_data: Dict[str, Dict[str, List[Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Optimize protective put parameters."""
        try:
            best_strike = None
            best_expiration = None
            best_score = 0.0

            predicted_price = float(price_pred.get("predicted_price", current_price))
            predicted_vol = float(vol_pred.get("predicted_volatility", 0.2))

            for exp_date, data in options_data.items():
                puts = data.get("puts", [])
                for put in puts:
                    if not put or "strike" not in put:
                        continue

                    strike = float(put["strike"])
                    bid = float(put.get("bid", 0) or 0)
                    ask = float(put.get("ask", 0) or 0)
                    mid_price = (bid + ask) / 2 if (bid and ask) else 0.0

                    if mid_price <= 0 or strike >= current_price:
                        continue

                    days_to_exp = self._days_to_expiration(exp_date)
                    if days_to_exp <= 0:
                        continue

                    # Protection level: how far below spot
                    protection_level = (current_price - strike) / current_price

                    # Cost relative to underlying
                    cost_ratio = mid_price / current_price

                    # Higher protection, lower cost → better
                    score = (protection_level * 0.6 - cost_ratio * 0.4) * 100.0

                    if score > best_score:
                        best_score = score
                        best_strike = strike
                        best_expiration = exp_date

            protection_level = (current_price - best_strike) / current_price if best_strike else 0.0

            return {
                "optimal_strike": best_strike,
                "optimal_expiration": best_expiration,
                "optimization_score": best_score,
                "protection_level": protection_level,
            }

        except Exception as e:
            logger.error("Error optimizing protective put: %s", e)
            return {}

    def _optimize_iron_condor(
        self,
        symbol: str,
        current_price: float,
        price_pred: Dict[str, Any],
        vol_pred: Dict[str, Any],
        options_data: Dict[str, Dict[str, List[Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Optimize iron condor parameters (simplified)."""
        try:
            predicted_price = float(price_pred.get("predicted_price", current_price))
            predicted_vol = float(vol_pred.get("predicted_volatility", 0.2))

            # Super-simple range based on volatility
            price_range = predicted_vol * current_price * 0.5

            return {
                "optimal_short_call_strike": current_price + price_range,
                "optimal_long_call_strike": current_price + price_range * 1.5,
                "optimal_short_put_strike": current_price - price_range,
                "optimal_long_put_strike": current_price - price_range * 1.5,
                "predicted_price": predicted_price,
                "predicted_volatility": predicted_vol,
            }

        except Exception as e:
            logger.error("Error optimizing iron condor: %s", e)
            return {}

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #
    def _days_to_expiration(self, exp_date: str) -> int:
        """Calculate days to expiration from YYYY-MM-DD date string."""
        try:
            exp_dt = datetime.strptime(exp_date, "%Y-%m-%d")
            return max((exp_dt - datetime.now()).days, 0)
        except Exception:
            return 30

    def _calculate_probability_of_profit(
        self,
        current_price: float,
        strike: float,
        volatility: float,
        days_to_exp: int,
    ) -> float:
        """Approximate probability of finishing above strike using Black-Scholes-like logic."""
        try:
            if days_to_exp <= 0 or volatility <= 0 or current_price <= 0:
                return 0.5

            time_to_exp = days_to_exp / 365.0
            risk_free_rate = 0.05

            d1 = (np.log(current_price / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_exp) / (
                volatility * np.sqrt(time_to_exp)
            )
            d2 = d1 - volatility * np.sqrt(time_to_exp)

            from scipy.stats import norm

            prob_above_strike = float(norm.cdf(d2))
            return prob_above_strike
        except Exception:
            return 0.5


__all__ = ["OptionsMLModels"]
