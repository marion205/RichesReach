"""
Improved ML Service with Proper Validation, Regularization, and Enhanced Features
Implements TimeSeriesSplit, Ridge/Lasso regularization, and advanced technical indicators
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
    from sklearn.linear_model import Ridge, Lasso, ElasticNet
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from sklearn.feature_selection import SelectKBest, f_regression
    import yfinance as yf
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImprovedMLService:
    """
    Improved ML Service with proper validation, regularization, and enhanced features
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        if not self.ml_available:
            logger.warning("Improved ML Service initialized in fallback mode")
        
        # Initialize models with regularization
        self.stock_scorer = None
        self.scaler = RobustScaler()  # More robust to outliers
        self.feature_selector = None
        
        # Model parameters with regularization
        self.model_params = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 5,  # Prevent overfitting
                'min_samples_split': 10,
                'min_samples_leaf': 5,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 3,  # Prevent overfitting
                'min_samples_split': 10,
                'random_state': 42
            },
            'ridge': {
                'alpha': 10.0  # Strong regularization
            },
            'lasso': {
                'alpha': 1.0
            },
            'elastic_net': {
                'alpha': 1.0,
                'l1_ratio': 0.5
            }
        }
        
    def is_available(self) -> bool:
        """Check if ML capabilities are available"""
        return self.ml_available
    
    def get_enhanced_stock_data(self, symbols: list, days: int = 365) -> Dict[str, pd.DataFrame]:
        """Fetch enhanced stock data with advanced technical indicators"""
        logger.info(f"Fetching {days} days of enhanced stock data for {len(symbols)} symbols...")
        
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty and len(hist) > 100:
                    # Basic price data
                    hist['Returns'] = hist['Close'].pct_change()
                    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
                    
                    # Moving averages
                    hist['SMA_5'] = hist['Close'].rolling(window=5).mean()
                    hist['SMA_10'] = hist['Close'].rolling(window=10).mean()
                    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    
                    # Exponential moving averages
                    hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
                    hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
                    
                    # MACD (Moving Average Convergence Divergence)
                    hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
                    hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
                    hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
                    
                    # RSI (Relative Strength Index)
                    hist['RSI'] = self.calculate_rsi(hist['Close'])
                    
                    # Bollinger Bands
                    hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
                    bb_std = hist['Close'].rolling(window=20).std()
                    hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
                    hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
                    hist['BB_Width'] = (hist['BB_Upper'] - hist['BB_Lower']) / hist['BB_Middle']
                    hist['BB_Position'] = (hist['Close'] - hist['BB_Lower']) / (hist['BB_Upper'] - hist['BB_Lower'])
                    
                    # Volume indicators
                    hist['Volume_MA'] = hist['Volume'].rolling(window=20).mean()
                    hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA']
                    hist['Volume_Momentum'] = hist['Volume_Ratio'].rolling(window=5).mean()
                    
                    # Volatility indicators
                    hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                    hist['ATR'] = self.calculate_atr(hist)
                    
                    # Momentum indicators
                    hist['Momentum_5'] = hist['Close'] / hist['Close'].shift(5)
                    hist['Momentum_10'] = hist['Close'] / hist['Close'].shift(10)
                    hist['ROC'] = (hist['Close'] - hist['Close'].shift(10)) / hist['Close'].shift(10) * 100
                    
                    data[symbol] = hist
                    logger.info(f"✓ {symbol}: {len(hist)} days with enhanced indicators")
                else:
                    logger.warning(f"✗ {symbol}: Insufficient data")
                    
            except Exception as e:
                logger.error(f"✗ {symbol}: Error - {e}")
        
        return data
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI with proper implementation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=window).mean()
        return atr
    
    def create_enhanced_features(self, market_data: dict) -> Tuple[np.ndarray, np.ndarray]:
        """Create enhanced feature set with MACD, Bollinger Bands, and volume momentum"""
        logger.info("Creating enhanced feature set...")
        
        X = []
        y = []
        
        for symbol, data in market_data.items():
            for i in range(50, len(data) - 5):  # 5-day prediction horizon
                # Enhanced features including MACD, Bollinger Bands, volume momentum
                features = [
                    # Price features
                    data['Returns'].iloc[i],
                    data['Log_Returns'].iloc[i],
                    
                    # Moving averages
                    data['SMA_5'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_10'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_20'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_50'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    
                    # MACD features
                    data['MACD'].iloc[i],
                    data['MACD_Signal'].iloc[i],
                    data['MACD_Histogram'].iloc[i],
                    
                    # RSI
                    data['RSI'].iloc[i],
                    
                    # Bollinger Bands
                    data['BB_Width'].iloc[i],
                    data['BB_Position'].iloc[i],
                    
                    # Volume features
                    data['Volume_Ratio'].iloc[i],
                    data['Volume_Momentum'].iloc[i],
                    
                    # Volatility
                    data['Volatility'].iloc[i],
                    data['ATR'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    
                    # Momentum
                    data['Momentum_5'].iloc[i],
                    data['Momentum_10'].iloc[i],
                    data['ROC'].iloc[i],
                ]
                
                # Target: 5-day future return
                future_return = (data['Close'].iloc[i+5] - data['Close'].iloc[i]) / data['Close'].iloc[i]
                
                # Risk-adjusted scoring
                volatility_5d = data['Returns'].iloc[i:i+5].std()
                if volatility_5d > 0:
                    sharpe_ratio = future_return / volatility_5d
                    # More conservative scoring
                    if sharpe_ratio > 2.0:
                        score = 1.0  # Excellent
                    elif sharpe_ratio > 1.0:
                        score = 0.8  # Good
                    elif sharpe_ratio > 0.5:
                        score = 0.6  # Positive
                    elif sharpe_ratio > 0:
                        score = 0.4  # Slightly positive
                    elif sharpe_ratio > -0.5:
                        score = 0.2  # Slightly negative
                    else:
                        score = 0.0  # Poor
                else:
                    score = 0.5  # Neutral
                
                X.append(features)
                y.append(score)
        
        return np.array(X), np.array(y)
    
    def train_improved_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train models with proper time series validation and regularization"""
        logger.info("Training improved models with proper validation...")
        
        # Use TimeSeriesSplit for financial data (CRITICAL FIX)
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Feature selection
        self.feature_selector = SelectKBest(score_func=f_regression, k=min(19, X.shape[1]))
        X_selected = self.feature_selector.fit_transform(X_scaled, y)
        
        # Define models with regularization
        models = {
            'random_forest': RandomForestRegressor(**self.model_params['random_forest']),
            'gradient_boosting': GradientBoostingRegressor(**self.model_params['gradient_boosting']),
            'ridge': Ridge(**self.model_params['ridge']),
            'lasso': Lasso(**self.model_params['lasso']),
            'elastic_net': ElasticNet(**self.model_params['elastic_net'])
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Cross-validation with TimeSeriesSplit (HONEST METRIC)
            cv_scores = cross_val_score(model, X_selected, y, cv=tscv, scoring='r2')
            
            # Train on full data
            model.fit(X_selected, y)
            y_pred = model.predict(X_selected)
            
            # Metrics
            r2 = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            results[name] = {
                'model': model,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'cv_scores': cv_scores,
                'r2': r2,
                'mse': mse,
                'mae': mae,
                'predictions': y_pred
            }
            
            logger.info(f"  {name}: CV R² = {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Create ensemble
        logger.info("Creating ensemble model...")
        ensemble_models = [
            ('rf', results['random_forest']['model']),
            ('gb', results['gradient_boosting']['model']),
            ('ridge', results['ridge']['model'])
        ]
        
        ensemble = VotingRegressor(ensemble_models)
        ensemble.fit(X_selected, y)
        
        # Ensemble predictions
        y_pred_ensemble = ensemble.predict(X_selected)
        ensemble_r2 = r2_score(y, y_pred_ensemble)
        ensemble_mse = mean_squared_error(y, y_pred_ensemble)
        ensemble_mae = mean_absolute_error(y, y_pred_ensemble)
        
        results['ensemble'] = {
            'model': ensemble,
            'r2': ensemble_r2,
            'mse': ensemble_mse,
            'mae': ensemble_mae,
            'predictions': y_pred_ensemble
        }
        
        self.stock_scorer = results['ensemble']['model']  # Use ensemble as default
        return results
    
    def score_stocks_improved(
        self, 
        stocks: List[Dict[str, Any]], 
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using improved ML models with proper validation
        """
        if not self.ml_available:
            return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
        
        try:
            # Get real market data for the stocks
            symbols = [stock.get('symbol', 'AAPL') for stock in stocks]
            market_data = self.get_enhanced_stock_data(symbols, days=365)
            
            if not market_data:
                return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
            
            # Create enhanced features
            X, y = self.create_enhanced_features(market_data)
            
            if len(X) == 0:
                return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
            
            # Train improved models
            results = self.train_improved_models(X, y)
            
            # Use the best model for scoring
            best_model_name = max(results.keys(), key=lambda k: results[k]['cv_mean'] if 'cv_mean' in results[k] else -999)
            best_model = results[best_model_name]['model']
            
            # Score stocks
            scored_stocks = []
            for i, stock in enumerate(stocks):
                symbol = stock.get('symbol', 'AAPL')
                if symbol in market_data:
                    # Get latest features for this stock
                    latest_features = self._get_latest_features(market_data[symbol])
                    if latest_features is not None:
                        score = best_model.predict([latest_features])[0]
                        confidence = self._calculate_confidence(latest_features, results[best_model_name])
                    else:
                        score = stock.get('beginner_friendly_score', 5.0) / 10.0
                        confidence = 0.5
                else:
                    score = stock.get('beginner_friendly_score', 5.0) / 10.0
                    confidence = 0.5
                
                scored_stocks.append({
                    **stock,
                    'ml_score': float(score),
                    'ml_confidence': float(confidence),
                    'ml_reasoning': f"Enhanced ML model with {best_model_name} (CV R²: {results[best_model_name]['cv_mean']:.3f})"
                })
            
            # Sort by ML score
            scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
            
            return scored_stocks
            
        except Exception as e:
            logger.error(f"Error in improved ML stock scoring: {e}")
            return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
    
    def _get_latest_features(self, data: pd.DataFrame) -> Optional[np.ndarray]:
        """Get latest features for a stock"""
        if len(data) < 50:
            return None
        
        i = len(data) - 1  # Latest data point
        
        try:
            features = [
                # Price features
                data['Returns'].iloc[i],
                data['Log_Returns'].iloc[i],
                
                # Moving averages
                data['SMA_5'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                data['SMA_10'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                data['SMA_20'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                data['SMA_50'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                
                # MACD features
                data['MACD'].iloc[i],
                data['MACD_Signal'].iloc[i],
                data['MACD_Histogram'].iloc[i],
                
                # RSI
                data['RSI'].iloc[i],
                
                # Bollinger Bands
                data['BB_Width'].iloc[i],
                data['BB_Position'].iloc[i],
                
                # Volume features
                data['Volume_Ratio'].iloc[i],
                data['Volume_Momentum'].iloc[i],
                
                # Volatility
                data['Volatility'].iloc[i],
                data['ATR'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                
                # Momentum
                data['Momentum_5'].iloc[i],
                data['Momentum_10'].iloc[i],
                data['ROC'].iloc[i],
            ]
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error getting latest features: {e}")
            return None
    
    def _calculate_confidence(self, features: np.ndarray, model_results: Dict[str, Any]) -> float:
        """Calculate confidence score based on model performance"""
        # Use cross-validation performance as confidence indicator
        cv_mean = model_results.get('cv_mean', 0)
        cv_std = model_results.get('cv_std', 0)
        
        # Higher CV R² and lower std = higher confidence
        confidence = max(0.1, min(0.9, cv_mean + (1 - cv_std)))
        return confidence
    
    def _fallback_stock_scoring(
        self, 
        stocks: List[Dict[str, Any]], 
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback stock scoring when ML is not available"""
        scored_stocks = []
        
        for stock in stocks:
            base_score = stock.get('beginner_friendly_score', 5.0) / 10.0
            
            scored_stocks.append({
                **stock,
                'ml_score': base_score,
                'ml_confidence': 0.5,
                'ml_reasoning': "Fallback scoring - ML not available"
            })
        
        return scored_stocks
    
    def run_improved_validation(self) -> Dict[str, Any]:
        """Run improved stock scoring validation with proper metrics"""
        logger.info("Starting improved stock scoring validation...")
        
        # Get enhanced market data
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
        market_data = self.get_enhanced_stock_data(symbols, days=365)
        
        if not market_data:
            return {"error": "No market data available"}
        
        # Create enhanced features
        X, y = self.create_enhanced_features(market_data)
        
        if len(X) == 0:
            return {"error": "No training data available"}
        
        logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
        
        # Train improved models
        results = self.train_improved_models(X, y)
        
        # Summary
        summary = {
            "validation_timestamp": datetime.now().isoformat(),
            "data_sources": list(market_data.keys()),
            "total_samples": len(X),
            "total_features": X.shape[1],
            "selected_features": X.shape[1] if self.feature_selector is None else self.feature_selector.n_features_in_,
            "improvements": {
                "time_series_validation": "TimeSeriesSplit instead of random splits",
                "regularization": "Ridge/Lasso/ElasticNet to prevent overfitting",
                "enhanced_features": "MACD, Bollinger Bands, volume momentum"
            },
            "models": {}
        }
        
        for name, result in results.items():
            summary["models"][name] = {
                "cv_r2_mean": result.get("cv_mean", None),
                "cv_r2_std": result.get("cv_std", None),
                "training_r2": result["r2"],
                "mse": result["mse"],
                "mae": result["mae"]
            }
        
        return summary
