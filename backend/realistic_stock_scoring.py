#!/usr/bin/env python3
"""
Realistic Stock Scoring Improvement Script
This script implements honest, realistic techniques to improve stock scoring accuracy
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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.feature_selection import SelectKBest, f_regression
import talib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealisticStockScorer:
    """Realistic stock scoring with proper validation and honest metrics"""
    
    def __init__(self):
        self.scaler = RobustScaler()
        self.feature_selector = None
        self.models = {}
        
    def get_market_data(self, symbols: list, days: int = 365) -> pd.DataFrame:
        """Fetch market data with essential indicators only"""
        logger.info(f"Fetching {days} days of market data for {len(symbols)} symbols...")
        
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty and len(hist) > 100:
                    # Essential features only
                    hist['Returns'] = hist['Close'].pct_change()
                    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
                    
                    # Moving averages
                    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    
                    # Technical indicators
                    hist['RSI'] = self.calculate_rsi(hist['Close'])
                    hist['Volatility'] = hist['Returns'].rolling(window=20).std()
                    
                    # Volume
                    hist['Volume_MA'] = hist['Volume'].rolling(window=20).mean()
                    hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA']
                    
                    # Price momentum
                    hist['Momentum_5'] = hist['Close'] / hist['Close'].shift(5)
                    hist['Momentum_10'] = hist['Close'] / hist['Close'].shift(10)
                    
                    data[symbol] = hist
                    logger.info(f"✓ {symbol}: {len(hist)} days")
                else:
                    logger.warning(f"✗ {symbol}: Insufficient data")
                    
            except Exception as e:
                logger.error(f"✗ {symbol}: Error - {e}")
        
        return data
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def create_features(self, market_data: dict) -> Tuple[np.ndarray, np.ndarray]:
        """Create realistic feature set"""
        logger.info("Creating realistic feature set...")
        
        X = []
        y = []
        
        for symbol, data in market_data.items():
            for i in range(50, len(data) - 5):  # 5-day prediction horizon
                # Core features only
                features = [
                    # Price features
                    data['Returns'].iloc[i],
                    data['Log_Returns'].iloc[i],
                    
                    # Technical indicators
                    data['RSI'].iloc[i],
                    data['Volatility'].iloc[i],
                    
                    # Volume
                    data['Volume_Ratio'].iloc[i],
                    
                    # Momentum
                    data['Momentum_5'].iloc[i],
                    data['Momentum_10'].iloc[i],
                    
                    # Moving averages
                    data['SMA_20'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                    data['SMA_50'].iloc[i] / data['Close'].iloc[i] if data['Close'].iloc[i] > 0 else 0,
                ]
                
                # Target: 5-day future return
                future_return = (data['Close'].iloc[i+5] - data['Close'].iloc[i]) / data['Close'].iloc[i]
                
                # Realistic scoring based on risk-adjusted returns
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
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train models with proper time series validation"""
        logger.info("Training models with proper validation...")
        
        # Use time series split for financial data
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Feature selection
        self.feature_selector = SelectKBest(score_func=f_regression, k=min(8, X.shape[1]))
        X_selected = self.feature_selector.fit_transform(X_scaled, y)
        
        # Define models with conservative parameters
        models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=5,  # Prevent overfitting
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,  # Prevent overfitting
                min_samples_split=10,
                random_state=42
            ),
            'ridge': Ridge(alpha=10.0),  # Strong regularization
            'elastic_net': ElasticNet(alpha=1.0, l1_ratio=0.5)
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Cross-validation (this is the honest metric)
            cv_scores = cross_val_score(model, X_selected, y, cv=tscv, scoring='r2')
            
            # Train on full data for final metrics
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
        
        self.models = results
        return results
    
    def run_realistic_validation(self) -> Dict[str, Any]:
        """Run realistic stock scoring validation"""
        logger.info("Starting realistic stock scoring validation...")
        
        # Get market data
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
        market_data = self.get_market_data(symbols, days=365)
        
        if not market_data:
            return {"error": "No market data available"}
        
        # Create features
        X, y = self.create_features(market_data)
        
        if len(X) == 0:
            return {"error": "No training data available"}
        
        logger.info(f"Created {len(X)} samples with {X.shape[1]} features")
        
        # Train models
        results = self.train_models(X, y)
        
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
                "cv_r2_mean": result["cv_mean"],
                "cv_r2_std": result["cv_std"],
                "cv_r2_scores": result["cv_scores"].tolist(),
                "training_r2": result["r2"],
                "mse": result["mse"],
                "mae": result["mae"]
            }
        
        return summary

def main():
    """Main function to run realistic stock scoring"""
    scorer = RealisticStockScorer()
    results = scorer.run_realistic_validation()
    
    print("\n" + "="*70)
    print("REALISTIC STOCK SCORING VALIDATION RESULTS")
    print("="*70)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"Validation Date: {results['validation_timestamp']}")
    print(f"Data Sources: {', '.join(results['data_sources'])}")
    print(f"Total Samples: {results['total_samples']:,}")
    print(f"Total Features: {results['total_features']}")
    print(f"Selected Features: {results['selected_features']}")
    
    print("\nMODEL PERFORMANCE (Cross-Validation R² - HONEST METRIC):")
    print("-" * 60)
    
    best_cv_r2 = -999
    best_model = None
    
    for model_name, model_results in results["models"].items():
        cv_r2 = model_results["cv_r2_mean"]
        cv_std = model_results["cv_r2_std"]
        training_r2 = model_results["training_r2"]
        mae = model_results["mae"]
        
        print(f"\n{model_name.upper().replace('_', ' ')}:")
        print(f"  📊 CV R² (Honest): {cv_r2:.3f} ± {cv_std:.3f}")
        print(f"  🎯 Training R²: {training_r2:.3f}")
        print(f"  📈 MAE: {mae:.4f}")
        
        # Check for overfitting
        overfitting = training_r2 - cv_r2
        if overfitting > 0.1:
            print(f"  ⚠️  Overfitting: {overfitting:.3f}")
        else:
            print(f"  ✅ Good generalization")
        
        if cv_r2 > best_cv_r2:
            best_cv_r2 = cv_r2
            best_model = model_name
    
    print(f"\n🏆 BEST MODEL: {best_model.upper()} with CV R² = {best_cv_r2:.3f}")
    
    # Improvement analysis
    original_r2 = 0.069
    improvement = ((best_cv_r2 - original_r2) / abs(original_r2)) * 100 if original_r2 != 0 else 0
    
    print(f"\n📈 IMPROVEMENT ANALYSIS:")
    print(f"  Original R²: {original_r2:.3f}")
    print(f"  Improved CV R²: {best_cv_r2:.3f}")
    print(f"  Improvement: {improvement:+.1f}%")
    
    # Realistic assessment
    if best_cv_r2 > 0.2:
        print("  🎉 EXCELLENT: Significant improvement achieved!")
    elif best_cv_r2 > 0.1:
        print("  ✅ GOOD: Meaningful improvement achieved!")
    elif best_cv_r2 > 0.05:
        print("  📈 MODERATE: Some improvement achieved!")
    elif best_cv_r2 > 0:
        print("  📊 POSITIVE: Better than random!")
    else:
        print("  ⚠️  CHALLENGING: Financial prediction is inherently difficult")
    
    # Honest assessment
    print(f"\n💡 HONEST ASSESSMENT:")
    print(f"  • Financial prediction is inherently difficult")
    print(f"  • R² > 0.1 is considered good in finance")
    print(f"  • R² > 0.2 is considered excellent")
    print(f"  • Focus on risk-adjusted returns, not just accuracy")
    print(f"  • Cross-validation is the only honest metric")
    
    # Save results
    import json
    with open('realistic_stock_scoring_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full results saved to: realistic_stock_scoring_results.json")
    print("="*70)

if __name__ == "__main__":
    main()
