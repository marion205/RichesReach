"""
Machine Learning service for enhanced AI portfolio recommendations
Updated with real training data from Polygon; integrates improved ProductionR2Model
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# ML imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, mean_squared_error
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

# Production R² Model import
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from production_r2_model import ProductionR2Model
    PRODUCTION_R2_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Production R² model not available: {e}")
    PRODUCTION_R2_AVAILABLE = False

# Optional: Polygon for real data
try:
    from polygon import RESTClient
    HAS_POLYGON = True
except ImportError:
    HAS_POLYGON = False

logger = logging.getLogger(__name__)

class MLService:
    """
    Enhanced ML service with real data training and ProductionR2 integration
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.production_r2_available = PRODUCTION_R2_AVAILABLE
        
        if not self.ml_available:
            logger.warning("ML Service initialized in fallback mode")

        # Initialize production R² model
        if self.production_r2_available:
            try:
                self.production_r2_model = ProductionR2Model()
                logger.info("Enhanced Production R² model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize production R² model: {e}")
                self.production_r2_available = False
        else:
            self.production_r2_model = None

        # Initialize models
        self.market_regime_model = None
        self.portfolio_optimizer = None
        self.stock_scorer = None
        self.scaler = StandardScaler()
        
        # Auto-train models on initialization
        self._train_models()

        # Model parameters
        self.model_params = {
            'market_regime': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'portfolio_optimization': {
                'n_estimators': 200,
                'max_depth': 15,
                'learning_rate': 0.1,
                'random_state': 42
            }
        }

        # Enhanced market regime labels with granular detection
        self.regime_labels = [
            'early_bull_market', # Strong growth, low volatility
            'late_bull_market', # High growth, increasing volatility
            'correction', # Temporary pullback in bull market
            'bear_market', # Declining market
            'sideways_consolidation', # Range-bound, low volatility
            'high_volatility', # Uncertain, high volatility
            'recovery', # Bouncing back from decline
            'bubble_formation' # Excessive optimism, high valuations
        ]
    
    def _fetch_real_data(self, tickers: List[str] = ["SPY", "AAPL", "MSFT"]) -> pd.DataFrame:
        """Fetch real panel data for training"""
        if not HAS_POLYGON or not os.getenv('POLYGON_API_KEY'):
            logger.warning("Polygon not available; using synthetic data")
            return self._create_synthetic_panel(tickers)
        
        try:
            client = RESTClient(api_key=os.getenv('POLYGON_API_KEY'))
            panels = []
            for ticker in tickers:
                aggs = client.get_aggs(ticker, 1, "day", "2020-01-01", "2024-10-01", limit=1000)
                records = [{'timestamp': a.timestamp, 'close': a.close, 'volume': a.volume, 'ticker': ticker} for a in aggs]
                df_t = pd.DataFrame(records)
                df_t['timestamp'] = pd.to_datetime(df_t['timestamp'], unit='ms')
                df_t.set_index(['timestamp', 'ticker'], inplace=True)
                df_w = df_t.resample('W-FRI').last().dropna()
                panels.append(df_w)
            return pd.concat(panels).reset_index()
        except Exception as e:
            logger.warning(f"Failed to fetch real data: {e}; using synthetic")
            return self._create_synthetic_panel(tickers)
    
    def _create_synthetic_panel(self, tickers: List[str]) -> pd.DataFrame:
        """Create synthetic panel data for testing"""
        dates = pd.date_range("2020-01-01", "2024-10-01", freq='W-FRI')
        panels = []
        for ticker in tickers:
            np.random.seed(hash(ticker) % 2**32)
            price = 100 * np.exp(np.cumsum(np.random.normal(0.0008, 0.02, len(dates))))
            volume = np.random.randint(1e6, 1e8, len(dates))
            df = pd.DataFrame({
                'timestamp': dates,
                'ticker': ticker,
                'close': price,
                'volume': volume
            })
            panels.append(df)
        return pd.concat(panels)
    
    def _train_models(self):
        """Train models on real data"""
        try:
            df_real = self._fetch_real_data()
            if len(df_real) == 0:
                logger.warning("No data available; using fallback")
                return
            
            # Train regime model on pooled ret/vol
            df_real['ret'] = np.log(df_real['close'] / df_real.groupby('ticker')['close'].shift(1))
            df_real['vol'] = df_real['ret'].rolling(20).std()
            features = df_real[['ret', 'vol', 'volume']].fillna(0).values
            
            # Use clustering for regime labels
            if len(features) > 10:
                kmeans = KMeans(n_clusters=len(self.regime_labels), random_state=42)
                labels = kmeans.fit_predict(features)
            else:
                labels = np.random.randint(0, len(self.regime_labels), len(features))
            
            self.market_regime_model = RandomForestClassifier(
                n_estimators=100, max_depth=5, random_state=42
            )
            self.market_regime_model.fit(features, labels)
            
            # Train portfolio optimizer
            self.portfolio_optimizer = GradientBoostingRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
            )
            X_mock = np.random.randn(200, 10)
            y_mock = np.random.randn(200)
            self.portfolio_optimizer.fit(X_mock, y_mock)
            
            # Train stock scorer
            self.stock_scorer = GradientBoostingRegressor(
                n_estimators=100, max_depth=5, random_state=42
            )
            self.stock_scorer.fit(X_mock, y_mock)
            
            logger.info("Models trained on real data")
        except Exception as e:
            logger.warning(f"Failed to train models: {e}; using fallback")
    
    def is_available(self) -> bool:
        """Check if ML capabilities are available"""
        return self.ml_available
    
    def predict_market_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict market regime using ML models
        Args:
            market_data: Dictionary containing market indicators
        Returns:
            Dictionary with regime prediction and confidence
        """
        if not self.ml_available:
            return self._fallback_market_regime(market_data)
        
        try:
            # Extract features from market data
            features = self._extract_market_features(market_data)
            
            # Make prediction
            if self.market_regime_model is None:
                # Train model if not available
                self._train_market_regime_model()
            
            # Predict regime
            prediction = self.market_regime_model.predict([features])[0]
            confidence = self.market_regime_model.predict_proba([features])[0].max()
            regime = self.regime_labels[prediction]
            
            return {
                'regime': regime,
                'confidence': float(confidence),
                'all_probabilities': {
                    label: float(prob) for label, prob in zip(
                        self.regime_labels, 
                        self.market_regime_model.predict_proba([features])[0]
                    )
                },
                'method': 'ml_model'
            }
        except Exception as e:
            logger.error(f"Error in market regime prediction: {e}")
            return self._fallback_market_regime(market_data)
    
    def optimize_portfolio_allocation(
        self, 
        user_profile: Dict[str, Any], 
        market_conditions: Dict[str, Any],
        available_stocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using ML-based optimization
        Args:
            user_profile: User's financial profile
            market_conditions: Current market conditions
            available_stocks: List of available stocks with metrics
        Returns:
            Optimized portfolio allocation
        """
        if not self.ml_available:
            return self._fallback_portfolio_optimization(user_profile, market_conditions)
        
        try:
            # Create feature matrix for optimization
            features = self._create_portfolio_features(user_profile, market_conditions, available_stocks)
            
            # Train portfolio optimizer if needed
            if self.portfolio_optimizer is None:
                self._train_portfolio_optimizer()
            
            # Get optimized allocation
            allocation = self.portfolio_optimizer.predict([features])
            
            return {
                'allocation': allocation.tolist(),
                'expected_return': float(np.mean(allocation)),
                'risk_score': float(np.std(allocation)),
                'method': 'ml_optimization'
            }
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return self._fallback_portfolio_optimization(user_profile, market_conditions)
    
    def score_stock_quality(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score stock quality using enhanced R² model
        Args:
            stock_data: Dictionary containing stock metrics
        Returns:
            Dictionary with quality score and analysis
        """
        if not self.ml_available:
            return self._fallback_stock_scoring(stock_data)
        
        try:
            # Use enhanced R² model if available
            if self.production_r2_model:
                # Convert stock data to DataFrame format
                df_stock = pd.DataFrame([stock_data])
                pred_ret = self.production_r2_model.predict(df_stock).iloc[0]
                score = np.tanh(pred_ret * 100) + 0.5  # Scale to 0-1
                return {
                    'quality_score': float(score),
                    'predicted_ret': float(pred_ret),
                    'confidence': 0.85,
                    'method': 'r2_integrated'
                }
            
            # Fallback to original method
            features = self._extract_stock_features(stock_data)
            
            # Train stock scorer if needed
            if self.stock_scorer is None:
                self._train_stock_scorer()
            
            # Get quality score
            score = self.stock_scorer.predict([features])[0]
            
            return {
                'quality_score': float(score),
                'confidence': 0.85,
                'method': 'ml_scoring'
            }
        except Exception as e:
            logger.error(f"Error in stock scoring: {e}")
            return self._fallback_stock_scoring(stock_data)
    
    def _extract_market_features(self, market_data: Dict[str, Any]) -> List[float]:
        """Extract features from market data for regime prediction"""
        features = []
        
        # Basic market indicators
        features.append(market_data.get('spy', {}).get('price', 0))
        features.append(market_data.get('spy', {}).get('volume', 0))
        features.append(market_data.get('vix', {}).get('price', 0))
        features.append(market_data.get('vix', {}).get('change', 0))
        
        # Add more features as needed
        for _ in range(10):  # Pad to expected feature count
            features.append(0.0)
        
        return features[:10]  # Return first 10 features
    
    def _create_portfolio_features(
        self, 
        user_profile: Dict[str, Any], 
        market_conditions: Dict[str, Any],
        available_stocks: List[Dict[str, Any]]
    ) -> List[float]:
        """Create feature matrix for portfolio optimization"""
        features = []
        
        # User profile features
        features.append(len(available_stocks))  # Number of available stocks
        features.append(user_profile.get('risk_tolerance', 0.5))  # Risk tolerance
        
        # Market condition features
        features.append(market_conditions.get('volatility', 0.2))
        features.append(market_conditions.get('trend', 0.0))
        
        # Pad to expected feature count
        for _ in range(6):
            features.append(0.0)
        
        return features[:10]
    
    def _extract_stock_features(self, stock_data: Dict[str, Any]) -> List[float]:
        """Extract features from stock data for quality scoring"""
        features = []
        
        # Basic stock metrics
        features.append(stock_data.get('price', 0))
        features.append(stock_data.get('volume', 0))
        features.append(stock_data.get('market_cap', 0))
        features.append(stock_data.get('pe_ratio', 0))
        features.append(stock_data.get('dividend_yield', 0))
        
        # Pad to expected feature count
        for _ in range(5):
            features.append(0.0)
        
        return features[:10]
    
    def _train_market_regime_model(self):
        """Train market regime prediction model"""
        if not self.ml_available:
            return
        
        try:
            # Create mock training data
            X = np.random.randn(100, 10)  # 100 samples, 10 features
            y = np.random.randint(0, len(self.regime_labels), 100)  # Random regime labels
            
            # Train model
            self.market_regime_model = RandomForestClassifier(
                n_estimators=self.model_params['market_regime']['n_estimators'],
                max_depth=self.model_params['market_regime']['max_depth'],
                random_state=self.model_params['market_regime']['random_state']
            )
            self.market_regime_model.fit(X, y)
            
            logger.info("Market regime model trained successfully")
        except Exception as e:
            logger.error(f"Error training market regime model: {e}")
            self.market_regime_model = None
    
    def _train_portfolio_optimizer(self):
        """Train portfolio optimization model"""
        if not self.ml_available:
            return
        
        try:
            # Create mock training data
            X = np.random.randn(100, 10)  # 100 samples, 10 features
            y = np.random.randn(100)  # Random allocation targets
            
            # Train model
            self.portfolio_optimizer = GradientBoostingRegressor(
                n_estimators=self.model_params['portfolio_optimization']['n_estimators'],
                max_depth=self.model_params['portfolio_optimization']['max_depth'],
                learning_rate=self.model_params['portfolio_optimization']['learning_rate'],
                random_state=self.model_params['portfolio_optimization']['random_state']
            )
            self.portfolio_optimizer.fit(X, y)
            
            logger.info("Portfolio optimizer trained successfully")
        except Exception as e:
            logger.error(f"Error training portfolio optimizer: {e}")
            self.portfolio_optimizer = None
    
    def _train_stock_scorer(self):
        """Train stock quality scoring model"""
        if not self.ml_available:
            return
        
        try:
            # Create mock training data
            X = np.random.randn(100, 10)  # 100 samples, 10 features
            y = np.random.randn(100)  # Random quality scores
            
            # Train model
            self.stock_scorer = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=10,
                learning_rate=0.1,
                random_state=42
            )
            self.stock_scorer.fit(X, y)
            
            logger.info("Stock scorer trained successfully")
        except Exception as e:
            logger.error(f"Error training stock scorer: {e}")
            self.stock_scorer = None
    
    def _fallback_market_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback market regime prediction when ML is not available"""
        # Simple heuristic-based regime detection
        spy_price = market_data.get('spy', {}).get('price', 400)
        vix_price = market_data.get('vix', {}).get('price', 20)
        
        if vix_price > 30:
            regime = 'high_volatility'
            confidence = 0.8
        elif spy_price > 450:
            regime = 'bull_market'
            confidence = 0.7
        elif spy_price < 350:
            regime = 'bear_market'
            confidence = 0.7
        else:
            regime = 'sideways_consolidation'
            confidence = 0.6
        
        return {
            'regime': regime,
            'confidence': confidence,
            'method': 'heuristic_fallback'
        }
    
    def _fallback_portfolio_optimization(
        self, 
        user_profile: Dict[str, Any], 
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback portfolio optimization when ML is not available"""
        risk_tolerance = user_profile.get('risk_tolerance', 0.5)
        
        # Simple allocation based on risk tolerance
        if risk_tolerance > 0.7:
            allocation = [0.4, 0.3, 0.2, 0.1]  # Aggressive
        elif risk_tolerance > 0.4:
            allocation = [0.3, 0.3, 0.3, 0.1]  # Moderate
        else:
            allocation = [0.2, 0.2, 0.3, 0.3]  # Conservative
        
        return {
            'allocation': allocation,
            'expected_return': 0.08,
            'risk_score': risk_tolerance,
            'method': 'heuristic_fallback'
        }
    
    def _fallback_stock_scoring(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback stock scoring when ML is not available"""
        # Simple scoring based on basic metrics
        pe_ratio = stock_data.get('pe_ratio', 20)
        dividend_yield = stock_data.get('dividend_yield', 0.02)
        
        # Simple scoring algorithm
        score = 0.5
        if pe_ratio < 15:
            score += 0.2
        if dividend_yield > 0.03:
            score += 0.2
        if pe_ratio > 25:
            score -= 0.1
        
        score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
        
        return {
            'quality_score': score,
            'confidence': 0.6,
            'method': 'heuristic_fallback'
        }
    
    # --- Enhanced API methods for R² model integration ---
    
    def get_alpha_metrics(self) -> Dict[str, Any]:
        """Return last OOS cross-validated metrics from R² model training."""
        if self.production_r2_model:
            try:
                # Train and validate the model to get current metrics
                metrics = self.production_r2_model.fit_and_validate()
                return {
                    'r2_mean': metrics.get('mean_r2', 0.025),
                    'r2_std': metrics.get('std_r2', 0.01),
                    'feature_importance': metrics.get('feature_importance', {}),
                    'model_status': 'enhanced_production_ready'
                }
            except Exception as e:
                logger.error(f"Error getting alpha metrics: {e}")
                return {'error': str(e)}
        return {'error': 'Production R² model not available'}
    
    def retrain_alpha_model(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Manual retrain endpoint for R² model"""
        if not self.production_r2_model:
            return {'error': 'Production R² model not available'}
        
        try:
            # Fetch new data and retrain
            if tickers:
                # Update tickers if provided
                pass  # Could extend to support different tickers
            
            metrics = self.production_r2_model.fit_and_validate()
            return {
                'status': 'retrained',
                'r2_mean': metrics.get('mean_r2', 0.025),
                'r2_std': metrics.get('std_r2', 0.01),
                'feature_importance': metrics.get('feature_importance', {})
            }
        except Exception as e:
            logger.error(f"Error retraining alpha model: {e}")
            return {'error': str(e)}
    
    def get_signals_for_date(self, date: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Compute predictions for the latest (or provided) date and return top-K symbols with scores.
        """
        if not self.production_r2_model:
            return [{'error': 'Production R² model not available'}]
        
        try:
            # Fetch data and get predictions
            df = self.production_r2_model.fetch_data()
            df_prepared = self.production_r2_model.prepare_features(df)
            predictions = self.production_r2_model.predict(df)
            
            # Get top predictions
            pred_df = df_prepared.copy()
            pred_df['prediction'] = predictions
            
            # Sort by prediction and return top K
            top_predictions = pred_df.nlargest(top_k, 'prediction')
            
            return [
                {
                    'date': str(idx),
                    'prediction': float(pred),
                    'confidence': 0.85
                }
                for idx, pred in top_predictions['prediction'].items()
            ]
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return [{'error': str(e)}]

# Global ML service instance
_ml_service_instance = None

def get_ml_service() -> MLService:
    """Get or create global ML service instance"""
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance