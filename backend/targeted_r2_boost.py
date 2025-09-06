#!/usr/bin/env python3
"""
Targeted R² Boost - Optimizing for 0.05+ R² Score
Focused approach using the best techniques from previous success
"""

import os
import sys
import django
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

# ML imports
try:
    import yfinance as yf
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor, BaggingRegressor, ExtraTreesRegressor
    from sklearn.linear_model import Ridge, Lasso, ElasticNet, HuberRegressor, BayesianRidge, LinearRegression
    from sklearn.preprocessing import StandardScaler, RobustScaler, QuantileTransformer
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.pipeline import Pipeline
    from sklearn.decomposition import PCA
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetedR2Booster:
    """
    Targeted approach to achieve 0.05+ R² scores
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.scaler = QuantileTransformer(output_distribution='normal')
        self.feature_selector = None
        self.best_model = None
        self.best_score = -999
        self.ensemble_model = None
    
    def get_targeted_stock_data(self, symbols: List[str], days: int = 400) -> Dict[str, pd.DataFrame]:
        """Get targeted stock data with optimized features"""
        logger.info(f"Fetching targeted stock data for {len(symbols)} symbols...")
        
        stock_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty and len(hist) > 100:
                    # Core price features
                    hist['Returns'] = hist['Close'].pct_change()
                    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
                    hist['Price_Range'] = (hist['High'] - hist['Low']) / hist['Close']
                    hist['Price_Position'] = (hist['Close'] - hist['Low']) / (hist['High'] - hist['Low'])
                    
                    # Multiple moving averages
                    for window in [3, 5, 8, 10, 13, 20, 34, 50]:
                        hist[f'SMA_{window}'] = hist['Close'].rolling(window=window).mean()
                        hist[f'EMA_{window}'] = hist['Close'].ewm(span=window).mean()
                    
                    # Technical indicators
                    hist['RSI'] = self._calculate_rsi(hist['Close'], 14)
                    
                    # Calculate specific EMAs for MACD
                    hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
                    hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
                    
                    hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
                    hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
                    hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
                    
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
                    
                    # Volatility and momentum
                    hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                    hist['Momentum_3'] = hist['Close'] / hist['Close'].shift(3) - 1
                    hist['Momentum_5'] = hist['Close'] / hist['Close'].shift(5) - 1
                    hist['Momentum_10'] = hist['Close'] / hist['Close'].shift(10) - 1
                    hist['Momentum_20'] = hist['Close'] / hist['Close'].shift(20) - 1
                    
                    # Price acceleration
                    hist['Price_Acceleration'] = hist['Returns'].diff()
                    
                    # Trend indicators
                    hist['Trend_5'] = (hist['Close'] > hist['SMA_5']).astype(int)
                    hist['Trend_20'] = (hist['Close'] > hist['SMA_20']).astype(int)
                    hist['Trend_50'] = (hist['Close'] > hist['SMA_50']).astype(int)
                    
                    # Support and resistance levels
                    hist['Support'] = hist['Low'].rolling(window=20).min()
                    hist['Resistance'] = hist['High'].rolling(window=20).max()
                    hist['Support_Distance'] = (hist['Close'] - hist['Support']) / hist['Close']
                    hist['Resistance_Distance'] = (hist['Resistance'] - hist['Close']) / hist['Close']
                    
                    # Market regime indicators
                    hist['Market_Regime'] = self._calculate_market_regime(hist)
                    
                    # Fill NaN values
                    hist = hist.fillna(method='ffill').fillna(method='bfill').fillna(0)
                    
                    stock_data[symbol] = hist
                    logger.info(f"✓ {symbol}: {len(hist)} days with {len(hist.columns)} features")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        return stock_data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
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
    
    def create_targeted_features(self, stock_data: Dict[str, pd.DataFrame], prediction_days: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Create targeted features for 0.05+ R²"""
        logger.info("Creating targeted features...")
        
        X = []
        y = []
        
        for symbol, data in stock_data.items():
            for i in range(50, len(data) - prediction_days):  # 50-day lookback, 3-day prediction
                features = []
                
                # Price features (normalized)
                current_price = data['Close'].iloc[i]
                if current_price > 0:
                    features.extend([
                        data['Returns'].iloc[i],
                        data['Log_Returns'].iloc[i],
                        data['Price_Range'].iloc[i],
                        data['Price_Position'].iloc[i],
                        data['RSI'].iloc[i] / 100.0,  # Normalize RSI
                        data['MACD'].iloc[i] / current_price,  # Normalize MACD
                        data['MACD_Signal'].iloc[i] / current_price,
                        data['MACD_Histogram'].iloc[i] / current_price,
                        data['BB_Width'].iloc[i],
                        data['BB_Position'].iloc[i],
                        data['Volume_Ratio'].iloc[i],
                        data['Volatility'].iloc[i],
                        data['Momentum_3'].iloc[i],
                        data['Momentum_5'].iloc[i],
                        data['Momentum_10'].iloc[i],
                        data['Momentum_20'].iloc[i],
                        data['Price_Acceleration'].iloc[i],
                        data['Trend_5'].iloc[i],
                        data['Trend_20'].iloc[i],
                        data['Trend_50'].iloc[i],
                        data['Support_Distance'].iloc[i],
                        data['Resistance_Distance'].iloc[i],
                        data['Market_Regime'].iloc[i] / 2.0,  # Normalize to [0,1]
                    ])
                    
                    # Moving averages (normalized)
                    for window in [3, 5, 8, 10, 13, 20, 34, 50]:
                        if f'SMA_{window}' in data.columns:
                            features.append(data[f'SMA_{window}'].iloc[i] / current_price)
                            features.append(data[f'EMA_{window}'].iloc[i] / current_price)
                        else:
                            features.extend([1.0, 1.0])  # Default values
                    
                    # Target: Risk-adjusted future return with optimal scaling
                    future_price = data['Close'].iloc[i + prediction_days]
                    future_return = (future_price - current_price) / current_price
                    
                    # Risk adjustment using recent volatility
                    recent_volatility = data['Returns'].iloc[i-20:i].std()
                    if recent_volatility > 0:
                        risk_adjusted_return = future_return / recent_volatility
                        # Optimal mapping: Map [-1.5, 1.5] to [0, 1] with clipping
                        target = max(0, min(1, (risk_adjusted_return + 1.5) / 3))
                    else:
                        target = 0.5  # Neutral
                    
                    X.append(features)
                    y.append(target)
        
        return np.array(X), np.array(y)
    
    def train_targeted_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train targeted models for 0.05+ R²"""
        logger.info("Training targeted models...")
        
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
        
        # Targeted models with highly optimized parameters
        models = {
            'ridge_ultra': Ridge(alpha=1000.0, random_state=42),
            'ridge_strong': Ridge(alpha=100.0, random_state=42),
            'ridge_medium': Ridge(alpha=10.0, random_state=42),
            'lasso_ultra': Lasso(alpha=10.0, random_state=42),
            'lasso_strong': Lasso(alpha=1.0, random_state=42),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42),
            'bayesian_ridge': BayesianRidge(),
            'huber': HuberRegressor(epsilon=1.35, alpha=0.01),
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=6,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features='sqrt',
                random_state=42
            ),
            'extra_trees': ExtraTreesRegressor(
                n_estimators=200,
                max_depth=6,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features='sqrt',
                random_state=42
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.01,
                max_depth=3,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            ),
            'bagging_ridge': BaggingRegressor(
                estimator=Ridge(alpha=10.0),
                n_estimators=100,
                random_state=42
            )
        }
        
        results = {}
        
        for name, model in models.items():
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
        
        # Create targeted ensemble model
        logger.info("Creating targeted ensemble model...")
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
            
            results['targeted_ensemble'] = {
                'model': self.ensemble_model,
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'cv_scores': cv_scores,
                'train_r2': train_r2,
                'train_mse': train_mse,
                'predictions': y_pred
            }
            
            logger.info(f"  targeted_ensemble: CV R² = {cv_mean:.3f} ± {cv_std:.3f}, Train R² = {train_r2:.3f}")
            
            # Update best model if ensemble is better
            if cv_mean > self.best_score:
                self.best_score = cv_mean
                self.best_model = 'targeted_ensemble'
        
        return results
    
    def run_targeted_analysis(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Run targeted R² analysis"""
        logger.info("Starting targeted R² analysis...")
        
        if not self.ml_available:
            logger.error("ML libraries not available")
            return {'error': 'ML libraries not available'}
        
        # Default symbols if none provided
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
        
        try:
            # Get stock data
            stock_data = self.get_targeted_stock_data(symbols, days=400)
            
            if not stock_data:
                logger.error("No stock data available")
                return {'error': 'No stock data available'}
            
            # Create features and targets
            X, y = self.create_targeted_features(stock_data)
            
            if len(X) == 0:
                logger.error("No features created")
                return {'error': 'No features created'}
            
            logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
            
            # Train models
            results = self.train_targeted_models(X, y)
            
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
            logger.error(f"Error in targeted R² analysis: {e}")
            return {'error': str(e)}

def main():
    """Main function to run targeted R² boosting"""
    print("\n" + "="*60)
    print("TARGETED R² BOOST - OPTIMIZING FOR 0.05+ R² SCORE")
    print("="*60)
    
    booster = TargetedR2Booster()
    
    # Run analysis
    results = booster.run_targeted_analysis()
    
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
    original_r2 = 0.007  # Your previous best score
    improvement = results['best_score'] - original_r2
    improvement_pct = (improvement / abs(original_r2)) * 100 if original_r2 != 0 else 0
    
    print(f"\n🎯 IMPROVEMENT ANALYSIS:")
    print(f"  Previous R²: {original_r2:.3f}")
    print(f"  New R²: {results['best_score']:.3f}")
    print(f"  Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    
    if results['best_score'] > 0.05:
        print("  🎉 EXCELLENT: R² > 0.05 achieved!")
    elif results['best_score'] > 0.03:
        print("  ✅ VERY GOOD: R² > 0.03 achieved!")
    elif results['best_score'] > 0.02:
        print("  📈 GOOD: R² > 0.02 achieved!")
    elif results['best_score'] > 0.01:
        print("  📈 POSITIVE: R² > 0.01 achieved!")
    else:
        print("  ⚠️  Still needs improvement")
    
    print(f"\n💡 KEY SUCCESS FACTORS:")
    print(f"  ✓ Optimized feature set (35+ features)")
    print(f"  ✓ 3-day prediction horizon (optimal)")
    print(f"  ✓ Multiple regularization strengths")
    print(f"  ✓ Advanced ensemble methods")
    print(f"  ✓ Risk-adjusted targets")
    print(f"  ✓ QuantileTransformer for normalization")
    print(f"  ✓ Time series cross-validation")
    print(f"  ✓ Extra Trees and Bagging")
    
    print(f"\n🚀 NEXT STEPS:")
    if results['best_score'] > 0.05:
        print("  ✅ You've achieved R² > 0.05! Now you can:")
        print("    1. Integrate this model into your production system")
        print("    2. Add real-time data feeds")
        print("    3. Implement model monitoring and retraining")
        print("    4. Add user feedback learning")
        print("    5. Scale to more symbols and timeframes")
    else:
        print("  📈 To get R² > 0.05:")
        print("    1. Try different prediction horizons (2-4 days)")
        print("    2. Add more alternative data sources")
        print("    3. Implement deep learning models")
        print("    4. Use reinforcement learning approaches")
        print("    5. Add more sophisticated feature engineering")

if __name__ == "__main__":
    main()
