#!/usr/bin/env python3
"""
Optimized R² Final - Building on the proven 0.023 approach
Enhancing the winning methodology with advanced techniques
"""

import os
import sys
import django
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

# ML imports
try:
    import yfinance as yf
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor, BaggingRegressor
    from sklearn.linear_model import Ridge, Lasso, ElasticNet, HuberRegressor, BayesianRidge
    from sklearn.preprocessing import StandardScaler, RobustScaler, QuantileTransformer
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.pipeline import Pipeline
    
    # XGBoost import
    try:
        from xgboost import XGBRegressor
        _HAS_XGB = True
    except ImportError:
        _HAS_XGB = False
    
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedR2Final:
    """
    Optimized R² model building on the proven 0.023 approach
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.has_xgb = _HAS_XGB
        self.scaler = QuantileTransformer(output_distribution='normal')
        self.feature_selector = None
        self.best_model = None
        self.best_score = -999
        self.ensemble_model = None
    
    def _winsor(self, s: pd.Series, q: float) -> pd.Series:
        """Winsorize series to reduce outlier impact"""
        if q is None or q <= 0: 
            return s
        lo, hi = s.quantile(q), s.quantile(1 - q)
        return s.clip(lo, hi)
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def get_enhanced_stock_data(self, symbols: List[str], days: int = 1000) -> Dict[str, pd.DataFrame]:
        """Get enhanced stock data with comprehensive features"""
        logger.info(f"Fetching enhanced stock data for {len(symbols)} symbols...")
        
        # Get market index (SPY as proxy)
        try:
            spy = yf.Ticker("SPY")
            market_data = spy.history(period=f"{days}d")
            market_data.columns = [f"market_{col.lower()}" for col in market_data.columns]
        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")
            market_data = None
        
        stock_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty and len(hist) > 100:
                    # Rename columns to lowercase
                    hist.columns = [col.lower() for col in hist.columns]
                    
                    # Add market data if available
                    if market_data is not None:
                        # Align dates
                        common_dates = hist.index.intersection(market_data.index)
                        if len(common_dates) > 50:
                            hist = hist.loc[common_dates]
                            market_aligned = market_data.loc[common_dates]
                            
                            # Add market columns
                            for col in market_aligned.columns:
                                hist[col] = market_aligned[col]
                    
                    stock_data[symbol] = hist
                    logger.info(f"✓ {symbol}: {len(hist)} days")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        return stock_data
    
    def create_optimized_features(self, stock_data: Dict[str, pd.DataFrame], prediction_days: int = 4) -> Tuple[np.ndarray, np.ndarray]:
        """Create optimized features building on the proven approach"""
        logger.info("Creating optimized features...")
        
        X = []
        y = []
        
        for symbol, data in stock_data.items():
            for i in range(50, len(data) - prediction_days):  # 50-day lookback
                features = []
                
                # Price features (normalized)
                current_price = data['close'].iloc[i]
                if current_price > 0:
                    # Core returns and volatility
                    hist = data.iloc[max(0, i-50):i+1].copy()
                    hist['Returns'] = hist['close'].pct_change()
                    hist['Log_Returns'] = np.log(hist['close'] / hist['close'].shift(1))
                    hist['Price_Range'] = (hist['high'] - hist['low']) / hist['close']
                    hist['Price_Position'] = (hist['close'] - hist['low']) / (hist['high'] - hist['low'])
                    
                    # Technical indicators
                    hist['RSI'] = self._calculate_rsi(hist['close'], 14)
                    
                    # Calculate specific EMAs for MACD
                    hist['EMA_12'] = hist['close'].ewm(span=12).mean()
                    hist['EMA_26'] = hist['close'].ewm(span=26).mean()
                    
                    hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
                    hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
                    hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
                    
                    # Bollinger Bands
                    hist['BB_Upper'], hist['BB_Middle'], hist['BB_Lower'] = self._calculate_bollinger_bands(hist['close'])
                    hist['BB_Width'] = (hist['BB_Upper'] - hist['BB_Lower']) / hist['BB_Middle']
                    hist['BB_Position'] = (hist['close'] - hist['BB_Lower']) / (hist['BB_Upper'] - hist['BB_Lower'])
                    
                    # Volume indicators
                    hist['Volume_MA'] = hist['volume'].rolling(window=20).mean()
                    hist['Volume_Ratio'] = hist['volume'] / hist['Volume_MA']
                    
                    # Volatility and momentum
                    hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                    hist['Momentum_3'] = hist['close'] / hist['close'].shift(3) - 1
                    hist['Momentum_5'] = hist['close'] / hist['close'].shift(5) - 1
                    hist['Momentum_10'] = hist['close'] / hist['close'].shift(10) - 1
                    hist['Momentum_20'] = hist['close'] / hist['close'].shift(20) - 1
                    
                    # Price acceleration
                    hist['Price_Acceleration'] = hist['Returns'].diff()
                    
                    # Trend indicators
                    hist['Trend_5'] = (hist['close'] > hist['close'].rolling(5).mean()).astype(int)
                    hist['Trend_20'] = (hist['close'] > hist['close'].rolling(20).mean()).astype(int)
                    hist['Trend_50'] = (hist['close'] > hist['close'].rolling(50).mean()).astype(int)
                    
                    # Support and resistance levels
                    hist['Support'] = hist['low'].rolling(window=20).min()
                    hist['Resistance'] = hist['high'].rolling(window=20).max()
                    hist['Support_Distance'] = (hist['close'] - hist['Support']) / hist['close']
                    hist['Resistance_Distance'] = (hist['Resistance'] - hist['close']) / hist['close']
                    
                    # Market regime indicators
                    hist['Market_Regime'] = self._calculate_market_regime(hist)
                    
                    # Fill NaN values
                    hist = hist.fillna(method='ffill').fillna(method='bfill').fillna(0)
                    
                    # Extract features for current time point
                    current_idx = len(hist) - 1
                    features.extend([
                        hist['Returns'].iloc[current_idx],
                        hist['Log_Returns'].iloc[current_idx],
                        hist['Price_Range'].iloc[current_idx],
                        hist['Price_Position'].iloc[current_idx],
                        hist['RSI'].iloc[current_idx] / 100.0,  # Normalize RSI
                        hist['MACD'].iloc[current_idx] / current_price,  # Normalize MACD
                        hist['MACD_Signal'].iloc[current_idx] / current_price,
                        hist['MACD_Histogram'].iloc[current_idx] / current_price,
                        hist['BB_Width'].iloc[current_idx],
                        hist['BB_Position'].iloc[current_idx],
                        hist['Volume_Ratio'].iloc[current_idx],
                        hist['Volatility'].iloc[current_idx],
                        hist['Momentum_3'].iloc[current_idx],
                        hist['Momentum_5'].iloc[current_idx],
                        hist['Momentum_10'].iloc[current_idx],
                        hist['Momentum_20'].iloc[current_idx],
                        hist['Price_Acceleration'].iloc[current_idx],
                        hist['Trend_5'].iloc[current_idx],
                        hist['Trend_20'].iloc[current_idx],
                        hist['Trend_50'].iloc[current_idx],
                        hist['Support_Distance'].iloc[current_idx],
                        hist['Resistance_Distance'].iloc[current_idx],
                        hist['Market_Regime'].iloc[current_idx] / 2.0,  # Normalize to [0,1]
                    ])
                    
                    # Moving averages (normalized)
                    for window in [5, 10, 20, 50]:
                        sma = hist['close'].rolling(window).mean().iloc[current_idx]
                        ema = hist['close'].ewm(span=window).mean().iloc[current_idx]
                        features.append(sma / current_price)
                        features.append(ema / current_price)
                    
                    # Target: prediction_days return with optimal scaling
                    future_price = data['close'].iloc[i + prediction_days]
                    future_return = (future_price - current_price) / current_price
                    
                    # Risk adjustment using recent volatility
                    recent_volatility = hist['Returns'].iloc[-20:].std()
                    if recent_volatility > 0:
                        risk_adjusted_return = future_return / recent_volatility
                        # Optimal mapping: Map [-2, 2] to [0, 1] with clipping
                        target = max(0, min(1, (risk_adjusted_return + 2) / 4))
                    else:
                        target = 0.5  # Neutral
                    
                    X.append(features)
                    y.append(target)
        
        return np.array(X), np.array(y)
    
    def _calculate_market_regime(self, data: pd.DataFrame) -> pd.Series:
        """Calculate market regime (0=bull, 1=bear, 2=sideways)"""
        returns = data['Returns'].rolling(window=20).mean()
        volatility = data['Returns'].rolling(window=20).std()
        
        regime = pd.Series(index=data.index, dtype=int)
        regime[(returns > 0.001) & (volatility < 0.02)] = 0  # Bull market
        regime[(returns < -0.001) & (volatility < 0.02)] = 1  # Bear market
        regime[volatility >= 0.02] = 2  # High volatility/sideways
        regime = regime.fillna(2)  # Default to sideways
        
        return regime
    
    def train_optimized_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train optimized models building on proven approach"""
        logger.info("Training optimized models...")
        
        if len(X) == 0:
            logger.error("No training data available")
            return {}
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Feature selection (keep top 25 features)
        n_features = min(25, X.shape[1])
        self.feature_selector = SelectKBest(score_func=f_regression, k=n_features)
        X_selected = self.feature_selector.fit_transform(X_scaled, y)
        
        logger.info(f"Selected {n_features} features from {X.shape[1]} total features")
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        results = {}
        
        # Optimized models based on proven approach
        optimized_models = {
            'gbr_optimized': GradientBoostingRegressor(
                n_estimators=800, 
                learning_rate=0.05, 
                max_depth=3, 
                subsample=0.9, 
                random_state=42
            ),
            'ridge_strong': Ridge(alpha=100.0, random_state=42),
            'ridge_medium': Ridge(alpha=10.0, random_state=42),
            'lasso_strong': Lasso(alpha=1.0, random_state=42),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42),
            'bayesian_ridge': BayesianRidge(),
            'huber': HuberRegressor(epsilon=1.35, alpha=0.01),
            'random_forest': RandomForestRegressor(
                n_estimators=300,
                max_depth=8,
                min_samples_split=15,
                min_samples_leaf=8,
                max_features='sqrt',
                random_state=42
            ),
        }
        
        # Add XGBoost if available
        if self.has_xgb:
            optimized_models['xgb_optimized'] = XGBRegressor(
                n_estimators=1000,
                learning_rate=0.03,
                max_depth=4,
                subsample=0.9,
                colsample_bytree=0.8,
                reg_lambda=2.0,
                reg_alpha=0.0,
                random_state=42
            )
        
        # Train models
        for name, model in optimized_models.items():
            logger.info(f"Training {name}...")
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_selected, y, cv=tscv, scoring='r2')
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            
            # Train on full data
            model.fit(X_selected, y)
            
            # Predictions
            y_pred = model.predict(X_selected)
            train_r2 = r2_score(y, y_pred)
            train_mse = mean_squared_error(y, y_pred)
            
            results[name] = {
                'model': model,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'cv_scores': cv_scores,
                'train_r2': train_r2,
                'train_mse': train_mse,
                'predictions': y_pred
            }
            
            logger.info(f"  {name}: CV R² = {cv_mean:.3f} ± {cv_std:.3f}, Train R² = {train_r2:.3f}")
            
            # Track best model
            if cv_mean > self.best_score:
                self.best_score = cv_mean
                self.best_model = name
        
        # Create ensemble model
        logger.info("Creating optimized ensemble model...")
        ensemble_models = []
        for name, result in results.items():
            if result['cv_mean'] > 0.005:  # Only include models with good performance
                ensemble_models.append((name, result['model']))
        
        if len(ensemble_models) > 1:
            self.ensemble_model = VotingRegressor(ensemble_models)
            
            # Cross-validate ensemble
            cv_scores = cross_val_score(self.ensemble_model, X_selected, y, cv=tscv, scoring='r2')
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            
            # Train ensemble
            self.ensemble_model.fit(X_selected, y)
            
            # Predictions
            y_pred = self.ensemble_model.predict(X_selected)
            train_r2 = r2_score(y, y_pred)
            train_mse = mean_squared_error(y, y_pred)
            
            results['optimized_ensemble'] = {
                'model': self.ensemble_model,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'cv_scores': cv_scores,
                'train_r2': train_r2,
                'train_mse': train_mse,
                'predictions': y_pred
            }
            
            logger.info(f"  optimized_ensemble: CV R² = {cv_mean:.3f} ± {cv_std:.3f}, Train R² = {train_r2:.3f}")
            
            # Update best model if ensemble is better
            if cv_mean > self.best_score:
                self.best_score = cv_mean
                self.best_model = 'optimized_ensemble'
        
        return results
    
    def run_optimized_analysis(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Run optimized R² analysis"""
        logger.info("Starting optimized R² analysis...")
        
        if not self.ml_available:
            logger.error("ML libraries not available")
            return {'error': 'ML libraries not available'}
        
        # Default symbols if none provided
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
        
        try:
            # Get stock data
            stock_data = self.get_enhanced_stock_data(symbols, days=1000)
            
            if not stock_data:
                logger.error("No stock data available")
                return {'error': 'No stock data available'}
            
            # Create features and targets
            X, y = self.create_optimized_features(stock_data)
            
            if len(X) == 0:
                logger.error("No features created")
                return {'error': 'No features created'}
            
            logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
            
            # Train models
            results = self.train_optimized_models(X, y)
            
            if not results:
                logger.error("No models trained")
                return {'error': 'No models trained'}
            
            # Find best model
            best_model_name = max(results.keys(), key=lambda k: results[k]['cv_mean'])
            best_score = results[best_model_name]['cv_mean']
            
            logger.info(f"Best model: {best_model_name} with CV R² = {best_score:.3f}")
            
            return {
                'best_model': best_model_name,
                'best_score': best_score,
                'all_results': results,
                'n_samples': len(X),
                'n_features': X.shape[1],
                'symbols_processed': list(stock_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Error in optimized R² analysis: {e}")
            return {'error': str(e)}

def main():
    """Main function to run optimized R² analysis"""
    print("\n" + "="*60)
    print("OPTIMIZED R² FINAL - BUILDING ON PROVEN 0.023 APPROACH")
    print("="*60)
    
    optimizer = OptimizedR2Final()
    
    # Run analysis
    results = optimizer.run_optimized_analysis()
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"\n📊 RESULTS:")
    print(f"  Best Model: {results['best_model']}")
    print(f"  Best CV R²: {results['best_score']:.3f}")
    print(f"  Samples: {results['n_samples']}")
    print(f"  Features: {results['n_features']}")
    print(f"  Symbols: {len(results['symbols_processed'])}")
    
    print(f"\n📈 ALL MODEL PERFORMANCE:")
    for model_name, model_results in results['all_results'].items():
        cv_r2 = model_results['cv_mean']
        cv_std = model_results['cv_std']
        train_r2 = model_results['train_r2']
        print(f"  {model_name}: CV R² = {cv_r2:.3f} ± {cv_std:.3f}, Train R² = {train_r2:.3f}")
    
    # Improvement analysis
    original_r2 = 0.023  # Your previous best score
    improvement = results['best_score'] - original_r2
    improvement_pct = (improvement / abs(original_r2)) * 100 if original_r2 != 0 else 0
    
    print(f"\n🎯 IMPROVEMENT ANALYSIS:")
    print(f"  Previous R²: {original_r2:.3f}")
    print(f"  New R²: {results['best_score']:.3f}")
    print(f"  Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    
    if results['best_score'] > 0.035:
        print("  🎉 EXCELLENT: R² > 0.035 achieved!")
    elif results['best_score'] > 0.025:
        print("  ✅ VERY GOOD: R² > 0.025 achieved!")
    elif results['best_score'] > 0.02:
        print("  📈 GOOD: R² > 0.02 achieved!")
    elif results['best_score'] > 0:
        print("  📈 POSITIVE: R² > 0 achieved!")
    else:
        print("  ⚠️  Still needs improvement")
    
    print(f"\n💡 KEY SUCCESS FACTORS:")
    print(f"  ✓ Building on proven 0.023 approach")
    print(f"  ✓ Enhanced feature engineering")
    print(f"  ✓ Optimized model parameters")
    print(f"  ✓ Advanced ensemble methods")
    print(f"  ✓ Risk-adjusted targets")
    print(f"  ✓ QuantileTransformer normalization")
    print(f"  ✓ Time series cross-validation")
    
    print(f"\n🚀 NEXT STEPS:")
    if results['best_score'] > 0.025:
        print("  ✅ You've improved beyond 0.025! Now you can:")
        print("    1. Deploy this enhanced model to production")
        print("    2. Implement real-time data feeds")
        print("    3. Add model monitoring and retraining")
        print("    4. Scale to more symbols and timeframes")
    else:
        print("  📈 To get R² > 0.025:")
        print("    1. Try different prediction horizons (2-8 days)")
        print("    2. Add more alternative data sources")
        print("    3. Implement more sophisticated ensemble methods")
        print("    4. Use reinforcement learning approaches")
        print("    5. Add more sophisticated feature engineering")

if __name__ == "__main__":
    main()
