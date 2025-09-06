#!/usr/bin/env python3
"""
Stock Scoring Improvement Script
This script implements advanced techniques to improve stock scoring accuracy
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
import talib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedStockScorer:
    """Advanced stock scoring with improved features and models"""
    
    def __init__(self):
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        self.feature_selector = None
        self.models = {}
        self.feature_importance = {}
        
    def get_enhanced_market_data(self, symbols: list, days: int = 500) -> pd.DataFrame:
        """Fetch enhanced market data with more indicators"""
        logger.info(f"Fetching {days} days of enhanced market data for {len(symbols)} symbols...")
        
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty and len(hist) > 100:  # Need enough data for indicators
                    # Basic price data
                    hist['Returns'] = hist['Close'].pct_change()
                    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
                    
                    # Moving averages
                    hist['SMA_5'] = hist['Close'].rolling(window=5).mean()
                    hist['SMA_10'] = hist['Close'].rolling(window=10).mean()
                    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
                    
                    # Exponential moving averages
                    hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
                    hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
                    
                    # Technical indicators
                    hist['RSI'] = self.calculate_rsi(hist['Close'])
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
                    hist['Price_Volume'] = hist['Close'] * hist['Volume']
                    
                    # Volatility indicators
                    hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                    hist['ATR'] = self.calculate_atr(hist)
                    
                    # Momentum indicators
                    hist['Momentum'] = hist['Close'] / hist['Close'].shift(10)
                    hist['ROC'] = (hist['Close'] - hist['Close'].shift(10)) / hist['Close'].shift(10) * 100
                    
                    # Support and resistance
                    hist['Support'] = hist['Low'].rolling(window=20).min()
                    hist['Resistance'] = hist['High'].rolling(window=20).max()
                    hist['Support_Distance'] = (hist['Close'] - hist['Support']) / hist['Close']
                    hist['Resistance_Distance'] = (hist['Resistance'] - hist['Close']) / hist['Close']
                    
                    # Market regime indicators
                    hist['Trend_Strength'] = (hist['SMA_20'] - hist['SMA_50']) / hist['SMA_50']
                    hist['Trend_Consistency'] = hist['Returns'].rolling(window=10).apply(
                        lambda x: np.sum(np.sign(x) == np.sign(x.iloc[-1])) / len(x)
                    )
                    
                    # Price patterns
                    hist['Higher_Highs'] = (hist['High'] > hist['High'].shift(1)).rolling(window=5).sum()
                    hist['Lower_Lows'] = (hist['Low'] < hist['Low'].shift(1)).rolling(window=5).sum()
                    
                    # Market microstructure
                    hist['Bid_Ask_Spread'] = (hist['High'] - hist['Low']) / hist['Close']  # Proxy
                    hist['Price_Impact'] = abs(hist['Returns']) / np.sqrt(hist['Volume'])
                    
                    data[symbol] = hist
                    logger.info(f"✓ {symbol}: {len(hist)} days with {len(hist.columns)} features")
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
    
    def create_advanced_features(self, market_data: dict) -> Tuple[np.ndarray, np.ndarray]:
        """Create advanced feature set for stock scoring"""
        logger.info("Creating advanced feature set...")
        
        X = []
        y = []
        
        for symbol, data in market_data.items():
            for i in range(200, len(data) - 10):  # Need more history for advanced features
                # Price-based features
                features = [
                    # Basic price features
                    data['Close'].iloc[i],
                    data['Returns'].iloc[i],
                    data['Log_Returns'].iloc[i],
                    
                    # Moving average features
                    data['SMA_5'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_10'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_20'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_50'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_200'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    
                    # Technical indicators
                    data['RSI'].iloc[i],
                    data['MACD'].iloc[i],
                    data['MACD_Signal'].iloc[i],
                    data['MACD_Histogram'].iloc[i],
                    
                    # Bollinger Bands
                    data['BB_Width'].iloc[i],
                    data['BB_Position'].iloc[i],
                    
                    # Volume features
                    data['Volume_Ratio'].iloc[i],
                    data['Price_Volume'].iloc[i] / data['Price_Volume'].rolling(20).mean().iloc[i] if data['Price_Volume'].rolling(20).mean().iloc[i] > 0 else 1,
                    
                    # Volatility features
                    data['Volatility'].iloc[i],
                    data['ATR'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    
                    # Momentum features
                    data['Momentum'].iloc[i],
                    data['ROC'].iloc[i],
                    
                    # Support/Resistance
                    data['Support_Distance'].iloc[i],
                    data['Resistance_Distance'].iloc[i],
                    
                    # Market regime
                    data['Trend_Strength'].iloc[i],
                    data['Trend_Consistency'].iloc[i],
                    
                    # Price patterns
                    data['Higher_Highs'].iloc[i],
                    data['Lower_Lows'].iloc[i],
                    
                    # Market microstructure
                    data['Bid_Ask_Spread'].iloc[i],
                    data['Price_Impact'].iloc[i],
                ]
                
                # Add lagged features (previous day values)
                if i > 0:
                    features.extend([
                        data['Returns'].iloc[i-1],
                        data['RSI'].iloc[i-1],
                        data['Volume_Ratio'].iloc[i-1],
                        data['Volatility'].iloc[i-1],
                    ])
                else:
                    features.extend([0, 0, 0, 0])
                
                # Add rolling statistics
                features.extend([
                    data['Returns'].rolling(5).mean().iloc[i],
                    data['Returns'].rolling(5).std().iloc[i],
                    data['Volume_Ratio'].rolling(5).mean().iloc[i],
                    data['RSI'].rolling(5).mean().iloc[i],
                ])
                
                # Target: Future performance (10-day return)
                future_return = (data['Close'].iloc[i+10] - data['Close'].iloc[i]) / data['Close'].iloc[i]
                
                # Enhanced scoring based on risk-adjusted returns
                volatility_10d = data['Returns'].iloc[i:i+10].std()
                if volatility_10d > 0:
                    sharpe_ratio = future_return / volatility_10d
                    # Score based on risk-adjusted performance
                    if sharpe_ratio > 1.0:
                        score = 1.0  # Excellent
                    elif sharpe_ratio > 0.5:
                        score = 0.8  # Good
                    elif sharpe_ratio > 0:
                        score = 0.6  # Positive
                    elif sharpe_ratio > -0.5:
                        score = 0.4  # Slightly negative
                    else:
                        score = 0.2  # Poor
                else:
                    score = 0.5  # Neutral if no volatility
                
                X.append(features)
                y.append(score)
        
        return np.array(X), np.array(y)
    
    def train_ensemble_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train ensemble of models for better performance"""
        logger.info("Training ensemble models...")
        
        # Use time series split for financial data
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Feature selection
        self.feature_selector = SelectKBest(score_func=mutual_info_regression, k=min(20, X.shape[1]))
        X_selected = self.feature_selector.fit_transform(X_scaled, y)
        
        # Define models
        models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                min_samples_split=5,
                random_state=42
            ),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=0.1),
            'svr': SVR(kernel='rbf', C=1.0, gamma='scale'),
            'mlp': MLPRegressor(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            )
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_selected, y, cv=tscv, scoring='r2')
            
            # Train on full data
            model.fit(X_selected, y)
            
            # Predictions
            y_pred = model.predict(X_selected)
            
            # Metrics
            r2 = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            results[name] = {
                'model': model,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'r2': r2,
                'mse': mse,
                'mae': mae,
                'predictions': y_pred
            }
            
            # Feature importance (for tree-based models)
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = model.feature_importances_
            
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
        
        self.models = results
        return results
    
    def run_improved_validation(self) -> Dict[str, Any]:
        """Run improved stock scoring validation"""
        logger.info("Starting improved stock scoring validation...")
        
        # Get enhanced market data
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM', 'BAC', 'WMT', 'JNJ', 'PG', 'V']
        market_data = self.get_enhanced_market_data(symbols, days=500)
        
        if not market_data:
            return {"error": "No market data available"}
        
        # Create advanced features
        X, y = self.create_advanced_features(market_data)
        
        if len(X) == 0:
            return {"error": "No training data available"}
        
        logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
        
        # Train models
        results = self.train_ensemble_models(X, y)
        
        # Summary
        summary = {
            "validation_timestamp": datetime.now().isoformat(),
            "data_sources": list(market_data.keys()),
            "total_samples": len(X),
            "total_features": X.shape[1],
            "selected_features": X.shape[1] if self.feature_selector is None else self.feature_selector.n_features_in_,
            "models": {}
        }
        
        for name, result in results.items():
            summary["models"][name] = {
                "r2_score": result["r2"],
                "mse": result["mse"],
                "mae": result["mae"],
                "cv_mean": result.get("cv_mean", None),
                "cv_std": result.get("cv_std", None)
            }
        
        return summary

def main():
    """Main function to run improved stock scoring"""
    scorer = AdvancedStockScorer()
    results = scorer.run_improved_validation()
    
    print("\n" + "="*70)
    print("IMPROVED STOCK SCORING VALIDATION RESULTS")
    print("="*70)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"Validation Date: {results['validation_timestamp']}")
    print(f"Data Sources: {', '.join(results['data_sources'])}")
    print(f"Total Samples: {results['total_samples']:,}")
    print(f"Total Features: {results['total_features']}")
    print(f"Selected Features: {results['selected_features']}")
    
    print("\nMODEL PERFORMANCE:")
    print("-" * 50)
    
    best_r2 = 0
    best_model = None
    
    for model_name, model_results in results["models"].items():
        r2 = model_results["r2_score"]
        mae = model_results["mae"]
        cv_mean = model_results.get("cv_mean")
        
        print(f"\n{model_name.upper().replace('_', ' ')}:")
        print(f"  ✅ R² Score: {r2:.3f}")
        print(f"  ✅ MAE: {mae:.4f}")
        
        if cv_mean is not None:
            cv_std = model_results.get("cv_std", 0)
            print(f"  📊 CV R²: {cv_mean:.3f} ± {cv_std:.3f}")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model = model_name
    
    print(f"\n🏆 BEST MODEL: {best_model.upper()} with R² = {best_r2:.3f}")
    
    # Improvement analysis
    original_r2 = 0.069
    improvement = ((best_r2 - original_r2) / original_r2) * 100
    
    print(f"\n📈 IMPROVEMENT ANALYSIS:")
    print(f"  Original R²: {original_r2:.3f}")
    print(f"  Improved R²: {best_r2:.3f}")
    print(f"  Improvement: {improvement:+.1f}%")
    
    if best_r2 > 0.3:
        print("  🎉 EXCELLENT: Significant improvement achieved!")
    elif best_r2 > 0.15:
        print("  ✅ GOOD: Meaningful improvement achieved!")
    elif best_r2 > 0.1:
        print("  📈 MODERATE: Some improvement achieved!")
    else:
        print("  ⚠️  LIMITED: Improvement needed")
    
    # Save results
    import json
    with open('improved_stock_scoring_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full results saved to: improved_stock_scoring_results.json")
    print("="*70)

if __name__ == "__main__":
    main()
