"""
Advanced ML Models for Options Strategy Optimization
Hedge Fund-Level Machine Learning for Options Trading
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class OptionsMLModels:
    """Advanced ML models for options strategy optimization"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_performance = {}
        
    async def train_price_prediction_model(self, symbol: str, lookback_days: int = 252) -> Dict:
        """Train LSTM model for price prediction"""
        try:
            logger.info(f"Training price prediction model for {symbol}")
            
            # Get historical data
            stock = yf.Ticker(symbol)
            hist = stock.history(period=f"{lookback_days}d")
            
            if len(hist) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return {}
            
            # Prepare features
            features = self._create_price_features(hist)
            target = hist['Close'].pct_change().shift(-1).dropna()  # Next day return
            
            # Align features and target
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train multiple models
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            }
            
            best_model = None
            best_score = -np.inf
            best_model_name = None
            
            for name, model in models.items():
                try:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    score = r2_score(y_test, y_pred)
                    
                    self.model_performance[f"{symbol}_{name}"] = {
                        'r2_score': score,
                        'mse': mean_squared_error(y_test, y_pred),
                        'feature_importance': getattr(model, 'feature_importances_', None)
                    }
                    
                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_model_name = name
                        
                except Exception as e:
                    logger.error(f"Error training {name} for {symbol}: {e}")
                    continue
            
            if best_model is not None:
                # Save the best model
                model_key = f"{symbol}_price_prediction"
                self.models[model_key] = best_model
                self.scalers[model_key] = scaler
                
                logger.info(f"Best model for {symbol}: {best_model_name} (R² = {best_score:.3f})")
                
                return {
                    'model_name': best_model_name,
                    'r2_score': best_score,
                    'features_used': list(features.columns),
                    'training_samples': len(X_train),
                    'test_samples': len(X_test)
                }
            
        except Exception as e:
            logger.error(f"Error training price prediction model for {symbol}: {e}")
        
        return {}
    
    async def train_volatility_prediction_model(self, symbol: str, lookback_days: int = 252) -> Dict:
        """Train model for volatility prediction"""
        try:
            logger.info(f"Training volatility prediction model for {symbol}")
            
            # Get historical data
            stock = yf.Ticker(symbol)
            hist = stock.history(period=f"{lookback_days}d")
            
            if len(hist) < 50:
                return {}
            
            # Calculate realized volatility
            returns = hist['Close'].pct_change().dropna()
            realized_vol = returns.rolling(window=20).std() * np.sqrt(252)
            
            # Prepare features
            features = self._create_volatility_features(hist, returns)
            
            # Align features and target
            min_len = min(len(features), len(realized_vol))
            features = features.iloc[:min_len]
            target = realized_vol.iloc[:min_len]
            
            # Remove NaN values
            valid_idx = ~(target.isna() | features.isna().any(axis=1))
            features = features[valid_idx]
            target = target[valid_idx]
            
            if len(features) < 30:
                return {}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            
            # Save model
            model_key = f"{symbol}_volatility_prediction"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            
            logger.info(f"Volatility model for {symbol}: R² = {r2:.3f}")
            
            return {
                'r2_score': r2,
                'mse': mse,
                'features_used': list(features.columns),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training volatility model for {symbol}: {e}")
            return {}
    
    async def predict_price_movement(
        self, 
        symbol: str, 
        current_price: float, 
        days_ahead: int = 30
    ) -> Dict:
        """Predict price movement using trained models"""
        try:
            model_key = f"{symbol}_price_prediction"
            if model_key not in self.models:
                # Train model if not exists
                await self.train_price_prediction_model(symbol)
            
            if model_key not in self.models:
                return {}
            
            # Get recent data for prediction
            stock = yf.Ticker(symbol)
            hist = stock.history(period="60d")
            
            if len(hist) < 30:
                return {}
            
            # Create features
            features = self._create_price_features(hist)
            latest_features = features.iloc[-1:].values
            
            # Scale features
            scaler = self.scalers[model_key]
            scaled_features = scaler.transform(latest_features)
            
            # Make prediction
            model = self.models[model_key]
            predicted_return = model.predict(scaled_features)[0]
            
            # Calculate predicted price
            predicted_price = current_price * (1 + predicted_return)
            
            # Calculate confidence based on model performance
            confidence = min(95, max(50, self.model_performance.get(model_key, {}).get('r2_score', 0.5) * 100))
            
            return {
                'predicted_price': predicted_price,
                'predicted_return': predicted_return,
                'confidence': confidence,
                'direction': 'up' if predicted_return > 0 else 'down',
                'magnitude': abs(predicted_return)
            }
            
        except Exception as e:
            logger.error(f"Error predicting price movement for {symbol}: {e}")
            return {}
    
    async def predict_volatility(self, symbol: str) -> Dict:
        """Predict future volatility"""
        try:
            model_key = f"{symbol}_volatility_prediction"
            if model_key not in self.models:
                await self.train_volatility_prediction_model(symbol)
            
            if model_key not in self.models:
                return {}
            
            # Get recent data
            stock = yf.Ticker(symbol)
            hist = stock.history(period="60d")
            returns = hist['Close'].pct_change().dropna()
            
            if len(hist) < 30:
                return {}
            
            # Create features
            features = self._create_volatility_features(hist, returns)
            latest_features = features.iloc[-1:].values
            
            # Scale and predict
            scaler = self.scalers[model_key]
            scaled_features = scaler.transform(latest_features)
            
            model = self.models[model_key]
            predicted_vol = model.predict(scaled_features)[0]
            
            return {
                'predicted_volatility': predicted_vol,
                'confidence': min(95, max(50, self.model_performance.get(model_key, {}).get('r2_score', 0.5) * 100))
            }
            
        except Exception as e:
            logger.error(f"Error predicting volatility for {symbol}: {e}")
            return {}
    
    def _create_price_features(self, hist: pd.DataFrame) -> pd.DataFrame:
        """Create features for price prediction"""
        try:
            features = pd.DataFrame(index=hist.index)
            
            # Price-based features
            features['close'] = hist['Close']
            features['volume'] = hist['Volume']
            features['high'] = hist['High']
            features['low'] = hist['Low']
            features['open'] = hist['Open']
            
            # Technical indicators
            features['sma_5'] = hist['Close'].rolling(5).mean()
            features['sma_10'] = hist['Close'].rolling(10).mean()
            features['sma_20'] = hist['Close'].rolling(20).mean()
            features['sma_50'] = hist['Close'].rolling(50).mean()
            
            features['ema_12'] = hist['Close'].ewm(span=12).mean()
            features['ema_26'] = hist['Close'].ewm(span=26).mean()
            
            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            macd_line = features['ema_12'] - features['ema_26']
            signal_line = macd_line.ewm(span=9).mean()
            features['macd'] = macd_line
            features['macd_signal'] = signal_line
            features['macd_histogram'] = macd_line - signal_line
            
            # Bollinger Bands
            bb_middle = hist['Close'].rolling(20).mean()
            bb_std = hist['Close'].rolling(20).std()
            features['bb_upper'] = bb_middle + (bb_std * 2)
            features['bb_lower'] = bb_middle - (bb_std * 2)
            features['bb_position'] = (hist['Close'] - bb_lower) / (bb_upper - bb_lower)
            
            # Volatility
            features['volatility_5'] = hist['Close'].pct_change().rolling(5).std()
            features['volatility_10'] = hist['Close'].pct_change().rolling(10).std()
            features['volatility_20'] = hist['Close'].pct_change().rolling(20).std()
            
            # Price momentum
            features['momentum_5'] = hist['Close'].pct_change(5)
            features['momentum_10'] = hist['Close'].pct_change(10)
            features['momentum_20'] = hist['Close'].pct_change(20)
            
            # Volume indicators
            features['volume_sma'] = hist['Volume'].rolling(20).mean()
            features['volume_ratio'] = hist['Volume'] / features['volume_sma']
            
            # Price position
            features['price_position_20'] = (hist['Close'] - hist['Close'].rolling(20).min()) / (hist['Close'].rolling(20).max() - hist['Close'].rolling(20).min())
            features['price_position_50'] = (hist['Close'] - hist['Close'].rolling(50).min()) / (hist['Close'].rolling(50).max() - hist['Close'].rolling(50).min())
            
            return features.dropna()
            
        except Exception as e:
            logger.error(f"Error creating price features: {e}")
            return pd.DataFrame()
    
    def _create_volatility_features(self, hist: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
        """Create features for volatility prediction"""
        try:
            features = pd.DataFrame(index=hist.index)
            
            # Historical volatility
            features['vol_5'] = returns.rolling(5).std()
            features['vol_10'] = returns.rolling(10).std()
            features['vol_20'] = returns.rolling(20).std()
            features['vol_30'] = returns.rolling(30).std()
            
            # Volatility of volatility
            features['vol_of_vol_10'] = features['vol_10'].rolling(10).std()
            features['vol_of_vol_20'] = features['vol_20'].rolling(20).std()
            
            # Price-based features
            features['close'] = hist['Close']
            features['high_low_ratio'] = hist['High'] / hist['Low']
            features['close_open_ratio'] = hist['Close'] / hist['Open']
            
            # Volume features
            features['volume'] = hist['Volume']
            features['volume_volatility'] = hist['Volume'].pct_change().rolling(10).std()
            
            # Trend features
            features['sma_20'] = hist['Close'].rolling(20).mean()
            features['trend_strength'] = (hist['Close'] - features['sma_20']) / features['sma_20']
            
            # Market regime features
            features['regime_vol'] = returns.rolling(60).std()
            features['regime_trend'] = hist['Close'].rolling(60).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
            
            return features.dropna()
            
        except Exception as e:
            logger.error(f"Error creating volatility features: {e}")
            return pd.DataFrame()
    
    async def optimize_strategy_parameters(
        self, 
        strategy_type: str, 
        symbol: str, 
        current_price: float,
        options_data: Dict
    ) -> Dict:
        """Optimize strategy parameters using ML"""
        try:
            # Get predictions
            price_pred = await self.predict_price_movement(symbol, current_price)
            vol_pred = await self.predict_volatility(symbol)
            
            if not price_pred or not vol_pred:
                return {}
            
            # Strategy-specific optimization
            if strategy_type == 'covered_call':
                return self._optimize_covered_call(
                    symbol, current_price, price_pred, vol_pred, options_data
                )
            elif strategy_type == 'protective_put':
                return self._optimize_protective_put(
                    symbol, current_price, price_pred, vol_pred, options_data
                )
            elif strategy_type == 'iron_condor':
                return self._optimize_iron_condor(
                    symbol, current_price, price_pred, vol_pred, options_data
                )
            
        except Exception as e:
            logger.error(f"Error optimizing strategy parameters: {e}")
        
        return {}
    
    def _optimize_covered_call(
        self, 
        symbol: str, 
        current_price: float, 
        price_pred: Dict, 
        vol_pred: Dict, 
        options_data: Dict
    ) -> Dict:
        """Optimize covered call parameters"""
        try:
            best_strike = None
            best_expiration = None
            best_score = 0
            
            predicted_price = price_pred.get('predicted_price', current_price)
            predicted_vol = vol_pred.get('predicted_volatility', 0.2)
            
            for exp_date, data in options_data.items():
                calls = data.get('calls', [])
                
                for call in calls:
                    if not call or 'strike' not in call:
                        continue
                    
                    strike = call['strike']
                    bid = call.get('bid', 0)
                    ask = call.get('ask', 0)
                    mid_price = (bid + ask) / 2 if bid and ask else 0
                    
                    if mid_price <= 0 or strike <= current_price:
                        continue
                    
                    # Calculate optimization score
                    days_to_exp = self._days_to_expiration(exp_date)
                    
                    # Probability of profit
                    prob_profit = self._calculate_probability_of_profit(
                        current_price, strike, predicted_vol, days_to_exp
                    )
                    
                    # Expected return
                    annual_return = (mid_price / current_price) * (365 / days_to_exp)
                    
                    # Risk-adjusted score
                    risk_score = 1 - (strike - current_price) / current_price  # Lower strike = higher risk
                    score = (prob_profit * 0.4 + annual_return * 0.4 + risk_score * 0.2) * 100
                    
                    if score > best_score:
                        best_score = score
                        best_strike = strike
                        best_expiration = exp_date
            
            return {
                'optimal_strike': best_strike,
                'optimal_expiration': best_expiration,
                'optimization_score': best_score,
                'predicted_price': predicted_price,
                'predicted_volatility': predicted_vol
            }
            
        except Exception as e:
            logger.error(f"Error optimizing covered call: {e}")
            return {}
    
    def _optimize_protective_put(
        self, 
        symbol: str, 
        current_price: float, 
        price_pred: Dict, 
        vol_pred: Dict, 
        options_data: Dict
    ) -> Dict:
        """Optimize protective put parameters"""
        try:
            best_strike = None
            best_expiration = None
            best_score = 0
            
            predicted_price = price_pred.get('predicted_price', current_price)
            predicted_vol = vol_pred.get('predicted_volatility', 0.2)
            
            for exp_date, data in options_data.items():
                puts = data.get('puts', [])
                
                for put in puts:
                    if not put or 'strike' not in put:
                        continue
                    
                    strike = put['strike']
                    bid = put.get('bid', 0)
                    ask = put.get('ask', 0)
                    mid_price = (bid + ask) / 2 if bid and ask else 0
                    
                    if mid_price <= 0 or strike >= current_price:
                        continue
                    
                    days_to_exp = self._days_to_expiration(exp_date)
                    
                    # Calculate protection level
                    protection_level = (current_price - strike) / current_price
                    
                    # Cost efficiency
                    cost_ratio = mid_price / current_price
                    
                    # Optimization score
                    score = (protection_level * 0.6 - cost_ratio * 0.4) * 100
                    
                    if score > best_score:
                        best_score = score
                        best_strike = strike
                        best_expiration = exp_date
            
            return {
                'optimal_strike': best_strike,
                'optimal_expiration': best_expiration,
                'optimization_score': best_score,
                'protection_level': (current_price - best_strike) / current_price if best_strike else 0
            }
            
        except Exception as e:
            logger.error(f"Error optimizing protective put: {e}")
            return {}
    
    def _optimize_iron_condor(
        self, 
        symbol: str, 
        current_price: float, 
        price_pred: Dict, 
        vol_pred: Dict, 
        options_data: Dict
    ) -> Dict:
        """Optimize iron condor parameters"""
        try:
            # Iron condor optimization is complex
            # For now, return a simplified version
            predicted_price = price_pred.get('predicted_price', current_price)
            predicted_vol = vol_pred.get('predicted_volatility', 0.2)
            
            # Calculate optimal strikes based on predicted price and volatility
            price_range = predicted_vol * current_price * 0.5  # 0.5 standard deviations
            
            return {
                'optimal_short_call_strike': current_price + price_range,
                'optimal_long_call_strike': current_price + price_range * 1.5,
                'optimal_short_put_strike': current_price - price_range,
                'optimal_long_put_strike': current_price - price_range * 1.5,
                'predicted_price': predicted_price,
                'predicted_volatility': predicted_vol
            }
            
        except Exception as e:
            logger.error(f"Error optimizing iron condor: {e}")
            return {}
    
    def _days_to_expiration(self, exp_date: str) -> int:
        """Calculate days to expiration"""
        try:
            exp_dt = datetime.strptime(exp_date, '%Y-%m-%d')
            return (exp_dt - datetime.now()).days
        except:
            return 30
    
    def _calculate_probability_of_profit(
        self, 
        current_price: float, 
        strike: float, 
        volatility: float, 
        days_to_exp: int
    ) -> float:
        """Calculate probability of profit using Black-Scholes"""
        try:
            if days_to_exp <= 0:
                return 0.0
            
            time_to_exp = days_to_exp / 365.0
            risk_free_rate = 0.05
            
            d1 = (np.log(current_price / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_exp) / (volatility * np.sqrt(time_to_exp))
            d2 = d1 - volatility * np.sqrt(time_to_exp)
            
            from scipy.stats import norm
            prob_above_strike = norm.cdf(d1)
            return prob_above_strike
        except:
            return 0.5

# Export the main class
__all__ = ['OptionsMLModels']
