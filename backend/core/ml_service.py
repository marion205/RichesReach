"""
ML Service for Enhanced AI Portfolio Recommendations
Handles machine learning models for market analysis, portfolio optimization, and stock scoring
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

logger = logging.getLogger(__name__)

class MLService:
    """
    Machine Learning service for enhanced AI portfolio recommendations
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.production_r2_available = PRODUCTION_R2_AVAILABLE
        if not self.ml_available:
            logger.warning("ML Service initialized in fallback mode")
        
        # Initialize models
        self.market_regime_model = None
        self.portfolio_optimizer = None
        self.stock_scorer = None
        self.scaler = StandardScaler()
        
        # Initialize production R² model
        if self.production_r2_available:
            try:
                self.production_r2_model = ProductionR2Model()
                logger.info("Production R² model initialized (R² = 0.023)")
            except Exception as e:
                logger.warning(f"Failed to initialize production R² model: {e}")
                self.production_r2_available = False
        else:
            self.production_r2_model = None
        
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
            'early_bull_market',      # Strong growth, low volatility
            'late_bull_market',       # High growth, increasing volatility
            'correction',              # Temporary pullback in bull market
            'bear_market',             # Declining market
            'sideways_consolidation',  # Range-bound, low volatility
            'high_volatility',         # Uncertain, high volatility
            'recovery',                # Bouncing back from decline
            'bubble_formation'         # Excessive optimism, high valuations
        ]
        
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
            
            # Generate optimal allocation
            optimal_allocation = self._generate_optimal_allocation(features, user_profile)
            
            return {
                'allocation': optimal_allocation,
                'expected_return': self._calculate_ml_expected_return(optimal_allocation, features),
                'risk_score': self._calculate_ml_risk_score(optimal_allocation, features),
                'method': 'ml_optimization'
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return self._fallback_portfolio_optimization(user_profile, market_conditions)
    
    def score_stocks_production_r2(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using the production R² model (R² = 0.023)
        This is the highest-performing model we've developed
        """
        if not self.production_r2_available or not self.production_r2_model:
            logger.warning("Production R² model not available, falling back to standard ML scoring")
            return self.score_stocks_ml(stocks, market_conditions, user_profile)
        
        try:
            # Extract symbols from stocks
            symbols = [stock.get('symbol', stock.get('ticker', '')) for stock in stocks if stock.get('symbol') or stock.get('ticker')]
            
            if not symbols:
                logger.warning("No valid symbols found for production R² scoring")
                return self.score_stocks_ml(stocks, market_conditions, user_profile)
            
            # Train the production model if not already trained
            if not self.production_r2_model.is_trained:
                logger.info("Training production R² model...")
                train_results = self.production_r2_model.train(symbols)
                if 'error' in train_results:
                    logger.error(f"Failed to train production R² model: {train_results['error']}")
                    return self.score_stocks_ml(stocks, market_conditions, user_profile)
                logger.info(f"Production R² model trained successfully (R² = {train_results.get('train_r2', 'unknown')})")
            
            # Score each stock
            scored_stocks = []
            for stock in stocks:
                symbol = stock.get('symbol', stock.get('ticker', ''))
                if not symbol:
                    continue
                
                try:
                    # Get predictions for this symbol
                    pred_results = self.production_r2_model.predict(symbol)
                    
                    if 'error' in pred_results:
                        logger.warning(f"Error predicting {symbol}: {pred_results['error']}")
                        # Fallback to standard scoring
                        scored_stock = self._fallback_stock_scoring([stock], market_conditions, user_profile)[0]
                    else:
                        # Use the latest prediction as the ML score
                        latest_pred = pred_results.get('latest_prediction', {})
                        predicted_return = latest_pred.get('predicted_return', 0.0)
                        confidence = latest_pred.get('confidence', 'low')
                        
                        # Convert prediction to score (0-10 scale)
                        # Map predicted return to score: -0.2 to +0.2 maps to 0-10
                        ml_score = max(0, min(10, 5 + (predicted_return * 25)))
                        
                        scored_stock = {
                            **stock,
                            'ml_score': float(ml_score),
                            'ml_confidence': confidence,
                            'ml_reasoning': f"Production R² model prediction: {predicted_return:.3f} return (R² = 0.023)",
                            'predicted_return': float(predicted_return),
                            'model_type': 'production_r2'
                        }
                    
                    scored_stocks.append(scored_stock)
                    
                except Exception as e:
                    logger.error(f"Error scoring {symbol} with production R² model: {e}")
                    # Fallback to standard scoring
                    scored_stock = self._fallback_stock_scoring([stock], market_conditions, user_profile)[0]
                    scored_stocks.append(scored_stock)
            
            # Sort by ML score
            scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
            
            logger.info(f"Scored {len(scored_stocks)} stocks using production R² model")
            return scored_stocks
            
        except Exception as e:
            logger.error(f"Error in production R² scoring: {e}")
            return self.score_stocks_ml(stocks, market_conditions, user_profile)

    def score_stocks_ml(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using the best available ML model
        Defaults to production R² model (R² = 0.023) if available

        Args:
            stocks: List of stocks to score
            market_conditions: Current market conditions
            user_profile: User's financial profile

        Returns:
            List of scored stocks with ML scores
        """
        # Use production R² model if available (best performance)
        if self.production_r2_available and self.production_r2_model:
            return self.score_stocks_production_r2(stocks, market_conditions, user_profile)
        
        if not self.ml_available:
            return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
        
        try:
            # Try to use improved ML service first
            from .improved_ml_service import ImprovedMLService
            
            improved_ml = ImprovedMLService()
            if improved_ml.is_available():
                # Use improved ML service with real data and proper validation
                scored_stocks = improved_ml.score_stocks_improved(stocks, market_conditions, user_profile)
                if scored_stocks:
                    logger.info("Used improved ML service for stock scoring")
                    return scored_stocks
            
            # Fallback to original method
            # Create feature matrix for stocks
            stock_features = self._create_stock_features(stocks, market_conditions, user_profile)
            
            # Train stock scorer if needed
            if self.stock_scorer is None:
                self._train_stock_scorer()
            
            # Score stocks
            scores = self.stock_scorer.predict(stock_features)
            
            # Create scored stock list
            scored_stocks = []
            for i, stock in enumerate(stocks):
                scored_stocks.append({
                    **stock,
                    'ml_score': float(scores[i]),
                    'ml_confidence': self._calculate_stock_confidence(stock_features[i]),
                    'ml_reasoning': self._generate_ml_reasoning(stock_features[i], scores[i])
                })
            
            # Sort by ML score
            scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
            
            return scored_stocks
            
        except Exception as e:
            logger.error(f"Error in ML stock scoring: {e}")
            return self._fallback_stock_scoring(stocks, market_conditions, user_profile)
    
    def _extract_market_features(self, market_data: Dict[str, Any]) -> List[float]:
        """Extract enhanced numerical features from market data for ML models"""
        features = []
        
        # Core market indicators
        if 'sp500_return' in market_data:
            features.append(float(market_data['sp500_return']))
        else:
            features.append(0.0)
            
        if 'volatility' in market_data:
            features.append(float(market_data['volatility']))
        else:
            features.append(0.15)  # Default volatility
            
        if 'interest_rate' in market_data:
            features.append(float(market_data['interest_rate']))
        else:
            features.append(0.05)  # Default interest rate
        
        # Enhanced market indicators
        if 'vix_index' in market_data:
            features.append(float(market_data['vix_index']) / 50.0)  # Normalize VIX (0-50 range)
        else:
            features.append(0.25)  # Default VIX level
            
        if 'bond_yield_10y' in market_data:
            features.append(float(market_data['bond_yield_10y']) / 10.0)  # Normalize 10Y yield
        else:
            features.append(0.05)  # Default 10Y yield
            
        if 'dollar_strength' in market_data:
            features.append(float(market_data['dollar_strength']))  # DXY index normalized
        else:
            features.append(0.5)  # Default dollar strength
            
        if 'oil_price' in market_data:
            features.append(float(market_data['oil_price']) / 100.0)  # Normalize oil price
        else:
            features.append(0.7)  # Default oil price
            
        # Sector performance (convert to numerical)
        sector_performance = market_data.get('sector_performance', {})
        sector_scores = []
        for sector in ['technology', 'healthcare', 'financials', 'consumer_discretionary', 'utilities', 'energy']:
            perf = sector_performance.get(sector, 'neutral')
            if perf == 'outperforming':
                sector_scores.append(1.0)
            elif perf == 'neutral':
                sector_scores.append(0.0)
            else:
                sector_scores.append(-1.0)
        features.extend(sector_scores)
        
        # Economic indicators
        if 'gdp_growth' in market_data:
            features.append(float(market_data['gdp_growth']))
        else:
            features.append(0.02)  # Default GDP growth
            
        if 'unemployment_rate' in market_data:
            features.append(float(market_data['unemployment_rate']))
        else:
            features.append(0.05)  # Default unemployment rate
            
        if 'inflation_rate' in market_data:
            features.append(float(market_data['inflation_rate']) / 10.0)  # Normalize inflation
        else:
            features.append(0.03)  # Default inflation rate
            
        if 'consumer_sentiment' in market_data:
            features.append(float(market_data['consumer_sentiment']) / 100.0)  # Normalize sentiment
        else:
            features.append(0.6)  # Default consumer sentiment
        
        # Ensure we always return exactly 20 features for enhanced market regime model
        while len(features) < 20:
            features.append(0.0)  # Pad with zeros if needed
        
        return features[:20]  # Truncate if more than 20
    
    def _create_portfolio_features(
        self, 
        user_profile: Dict[str, Any], 
        market_conditions: Dict[str, Any],
        available_stocks: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Create feature matrix for portfolio optimization"""
        features = []
        
        # Enhanced user profile features
        age = user_profile.get('age', 30)
        income_bracket = user_profile.get('income_bracket', 'Under $50,000')
        risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
        investment_horizon = user_profile.get('investment_horizon', '5-10 years')
        investment_experience = user_profile.get('investment_experience', 'Beginner')
        tax_bracket = user_profile.get('tax_bracket', '22%')
        specific_goals = user_profile.get('investment_goals', [])
        
        # Encode categorical variables
        income_encoding = {
            'Under $30,000': 0.2,
            '$30,000 - $50,000': 0.4,
            '$50,000 - $75,000': 0.6,
            '$75,000 - $100,000': 0.8,
            '$100,000 - $150,000': 0.9,
            'Over $150,000': 1.0
        }
        
        risk_encoding = {
            'Conservative': 0.3,
            'Moderate': 0.6,
            'Aggressive': 0.9
        }
        
        horizon_encoding = {
            '1-3 years': 0.2,
            '3-5 years': 0.5,
            '5-10 years': 0.7,
            '10+ years': 1.0
        }
        
        experience_encoding = {
            'Beginner': 0.2,
            'Intermediate': 0.5,
            'Advanced': 0.8,
            'Expert': 1.0
        }
        
        tax_encoding = {
            '10%': 0.1,
            '12%': 0.2,
            '22%': 0.4,
            '24%': 0.6,
            '32%': 0.8,
            '35%': 0.9,
            '37%': 1.0
        }
        
        # Goal encoding (multiple goals can be selected)
        goal_weights = {
            'Retirement Savings': 0.3,
            'Buy a Home': 0.2,
            'Emergency Fund': 0.1,
            'Wealth Building': 0.3,
            'Passive Income': 0.4,
            'Tax Benefits': 0.2,
            'College Fund': 0.2,
            'Travel Fund': 0.1
        }
        
        goal_score = sum(goal_weights.get(goal, 0.1) for goal in specific_goals) / len(specific_goals) if specific_goals else 0.2
        
        # Create enhanced feature vector
        user_features = [
            age / 100.0,  # Normalize age
            income_encoding.get(income_bracket, 0.5),
            risk_encoding.get(risk_tolerance, 0.6),
            horizon_encoding.get(investment_horizon, 0.7),
            experience_encoding.get(investment_experience, 0.2),
            tax_encoding.get(tax_bracket, 0.4),
            goal_score
        ]
        
        # Market condition features
        market_features = self._extract_market_features(market_conditions)
        
        # Stock market features (aggregate)
        if available_stocks:
            stock_features = [
                np.mean([s.get('beginner_friendly_score', 5.0) for s in available_stocks]),
                np.std([s.get('beginner_friendly_score', 5.0) for s in available_stocks]),
                len([s for s in available_stocks if s.get('beginner_friendly_score', 0) >= 7.0])
            ]
        else:
            stock_features = [5.0, 1.0, 0]
        
        # Combine all features
        all_features = user_features + market_features + stock_features
        
        # Ensure we always return exactly 25 features for enhanced portfolio optimization
        while len(all_features) < 25:
            all_features.append(0.0)  # Pad with zeros if needed
        
        return np.array(all_features[:25]).reshape(1, -1)
    
    def _create_stock_features(
        self, 
        stocks: List[Dict[str, Any]], 
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> np.ndarray:
        """Create enhanced feature matrix for stock scoring with ESG, momentum, and value factors"""
        features = []
        
        for stock in stocks:
            stock_features = []
            
            # Core stock features
            stock_features.append(stock.get('beginner_friendly_score', 5.0) / 10.0)
            
            # ESG factors (Environmental, Social, Governance)
            esg_score = stock.get('esg_score', 5.0) / 10.0
            sustainability_rating = stock.get('sustainability_rating', 5.0) / 10.0
            governance_score = stock.get('governance_score', 5.0) / 10.0
            stock_features.extend([esg_score, sustainability_rating, governance_score])
            
            # Value factors
            pe_ratio = stock.get('pe_ratio', 15.0) / 30.0  # Normalize P/E ratio
            pb_ratio = stock.get('pb_ratio', 1.5) / 5.0    # Normalize P/B ratio
            debt_to_equity = stock.get('debt_to_equity', 0.5) / 2.0  # Normalize D/E
            stock_features.extend([pe_ratio, pb_ratio, debt_to_equity])
            
            # Momentum factors
            price_momentum = stock.get('price_momentum', 0.0)  # 6-month price change
            volume_momentum = stock.get('volume_momentum', 0.0)  # Volume trend
            stock_features.extend([price_momentum, volume_momentum])
            
            # Market condition features (subset for stock scoring)
            market_features = self._extract_market_features(market_conditions)[:6]  # Use first 6 features
            stock_features.extend(market_features)
            
            # User profile features (normalized)
            age = user_profile.get('age', 30) / 100.0
            risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
            risk_encoding = {'Conservative': 0.3, 'Moderate': 0.6, 'Aggressive': 0.9}
            risk_score = risk_encoding.get(risk_tolerance, 0.6)
            
            stock_features.extend([age, risk_score])
            
            # Ensure each stock has exactly 20 features (increased from 15)
            while len(stock_features) < 20:
                stock_features.append(0.0)  # Pad with zeros if needed
            
            features.append(stock_features[:20])  # Truncate if more than 20
        
        return np.array(features)
    
    def _train_market_regime_model(self):
        """Train the enhanced market regime prediction model with 20 features"""
        try:
            # Generate synthetic training data (in production, use real historical data)
            n_samples = 1000
            np.random.seed(42)
            
            # Create synthetic market data with 20 features
            X = np.random.randn(n_samples, 20)  # 20 features (enhanced market indicators)
            y = np.random.choice(len(self.regime_labels), n_samples)
            
            # Train Random Forest classifier
            self.market_regime_model = RandomForestClassifier(
                **self.model_params['market_regime']
            )
            self.market_regime_model.fit(X, y)
            
            logger.info("Enhanced market regime model trained successfully with 20 features")
            
        except Exception as e:
            logger.error(f"Error training enhanced market regime model: {e}")
            self.market_regime_model = None
    
    def _train_portfolio_optimizer(self):
        """Train the enhanced portfolio optimization model with 25 features"""
        try:
            # Generate synthetic training data
            n_samples = 500
            np.random.seed(42)
            
            # Create synthetic portfolio data with 25 features
            X = np.random.randn(n_samples, 25)  # 25 features (enhanced user + market + stock)
            y = np.random.rand(n_samples)  # Expected returns
            
            # Train Gradient Boosting Regressor
            self.portfolio_optimizer = GradientBoostingRegressor(
                **self.model_params['portfolio_optimization']
            )
            self.portfolio_optimizer.fit(X, y)
            
            logger.info("Enhanced portfolio optimizer trained successfully with 25 features")
            
        except Exception as e:
            logger.error(f"Error training enhanced portfolio optimizer: {e}")
            self.portfolio_optimizer = None
    
    def _train_stock_scorer(self):
        """Train the enhanced stock scoring model with proper validation and regularization"""
        try:
            # Import improved ML service
            from .improved_ml_service import ImprovedMLService
            
            # Use improved ML service for training
            improved_ml = ImprovedMLService()
            if improved_ml.is_available():
                # Get real market data
                symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM']
                market_data = improved_ml.get_enhanced_stock_data(symbols, days=365)
                
                if market_data:
                    # Create enhanced features
                    X, y = improved_ml.create_enhanced_features(market_data)
                    
                    if len(X) > 0:
                        # Train with proper validation and regularization
                        results = improved_ml.train_improved_models(X, y)
                        
                        # Use the best model
                        best_model_name = max(results.keys(), key=lambda k: results[k]['cv_mean'] if 'cv_mean' in results[k] else -999)
                        self.stock_scorer = results[best_model_name]['model']
                        
                        logger.info(f"Enhanced stock scorer trained with {best_model_name} (CV R²: {results[best_model_name]['cv_mean']:.3f})")
                        return
            
            # Fallback to synthetic data if improved ML fails
            n_samples = 2000
            np.random.seed(42)
            
            # Create synthetic stock data with 20 features
            X = np.random.randn(n_samples, 20)  # 20 features (ESG + Value + Momentum + Market + User)
            y = np.random.uniform(1, 10, n_samples)  # Scores 1-10
            
            # Train with regularization
            from sklearn.linear_model import Ridge
            self.stock_scorer = Ridge(alpha=10.0)  # Strong regularization
            self.stock_scorer.fit(X, y)
            
            logger.info("Enhanced stock scorer trained with Ridge regularization (fallback)")
            
        except Exception as e:
            logger.error(f"Error training enhanced stock scorer: {e}")
            self.stock_scorer = None
    
    def _generate_optimal_allocation(
        self, 
        features: np.ndarray, 
        user_profile: Dict[str, Any]
    ) -> Dict[str, float]:
        """Generate optimal portfolio allocation using ML model"""
        # This is a simplified version - in production, use more sophisticated optimization
        risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
        
        # Enhanced base allocations with more asset classes
        base_allocations = {
            'Conservative': {
                'stocks': 35, 'bonds': 40, 'etfs': 10, 'reits': 8, 'commodities': 2, 'international': 3, 'cash': 2
            },
            'Moderate': {
                'stocks': 55, 'bonds': 20, 'etfs': 10, 'reits': 8, 'commodities': 3, 'international': 2, 'cash': 2
            },
            'Aggressive': {
                'stocks': 70, 'bonds': 8, 'etfs': 8, 'reits': 6, 'commodities': 4, 'international': 2, 'cash': 2
            }
        }
        
        allocation = base_allocations.get(risk_tolerance, base_allocations['Moderate']).copy()
        
        # Adjust based on ML model output (simplified)
        if self.portfolio_optimizer:
            prediction = self.portfolio_optimizer.predict(features)[0]
            # Adjust allocation based on prediction
            if prediction > 0.6:  # High expected return
                allocation['stocks'] += 5
                allocation['bonds'] -= 5
            elif prediction < 0.4:  # Low expected return
                allocation['cash'] += 5
                allocation['stocks'] -= 5
        
        return allocation
    
    def _calculate_ml_expected_return(self, allocation: Dict[str, float], features: np.ndarray) -> str:
        """Calculate expected return using ML model"""
        if self.portfolio_optimizer:
            base_return = self.portfolio_optimizer.predict(features)[0]
            # Adjust based on allocation
            stock_weight = allocation.get('stocks', 60) / 100.0
            adjusted_return = base_return * (0.8 + 0.4 * stock_weight)
            return f"{adjusted_return*100:.1f}-{(adjusted_return*100)*1.3:.1f}%"
        else:
            return "8-12%"  # Fallback
    
    def _calculate_ml_risk_score(self, allocation: Dict[str, float], features: np.ndarray) -> float:
        """Calculate risk score using ML model"""
        # Simplified risk calculation
        stock_weight = allocation.get('stocks', 60) / 100.0
        bond_weight = allocation.get('bonds', 25) / 100.0
        cash_weight = allocation.get('cash', 3) / 100.0
        
        # Risk score: 0 (low risk) to 1 (high risk)
        risk_score = stock_weight * 0.8 + bond_weight * 0.3 + cash_weight * 0.1
        return min(1.0, max(0.0, risk_score))
    
    def _calculate_stock_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence score for stock prediction"""
        # Simplified confidence calculation
        # In production, use model uncertainty estimation
        return 0.8  # Placeholder
    
    def _generate_ml_reasoning(self, features: np.ndarray, score: float) -> str:
        """Generate reasoning for ML-based stock score"""
        reasoning_parts = []
        
        if score >= 8.0:
            reasoning_parts.append("Exceptional ML score")
        elif score >= 7.0:
            reasoning_parts.append("Strong ML prediction")
        else:
            reasoning_parts.append("Good ML fundamentals")
        
        # Add feature-based reasoning
        if features[0] >= 0.7:  # High beginner-friendly score
            reasoning_parts.append("High beginner-friendly rating")
        
        if len(features) > 1 and features[1] > 0:  # Positive market conditions
            reasoning_parts.append("Favorable market conditions")
        
        return " | ".join(reasoning_parts)
    
    # Fallback methods when ML is not available
    def _fallback_market_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback market regime prediction with granular labels"""
        return {
            'regime': 'sideways_consolidation',
            'confidence': 0.5,
            'all_probabilities': {
                'early_bull_market': 0.15,
                'late_bull_market': 0.10,
                'correction': 0.15,
                'bear_market': 0.15,
                'sideways_consolidation': 0.20,
                'high_volatility': 0.10,
                'recovery': 0.10,
                'bubble_formation': 0.05
            },
            'method': 'fallback'
        }
    
    def _fallback_portfolio_optimization(
        self, 
        user_profile: Dict[str, Any], 
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced fallback portfolio optimization with more asset classes"""
        risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
        
        base_allocations = {
            'Conservative': {
                'stocks': 35, 'bonds': 40, 'etfs': 10, 'reits': 8, 'commodities': 2, 'international': 3, 'cash': 2
            },
            'Moderate': {
                'stocks': 55, 'bonds': 20, 'etfs': 10, 'reits': 8, 'commodities': 3, 'international': 2, 'cash': 2
            },
            'Aggressive': {
                'stocks': 70, 'bonds': 8, 'etfs': 8, 'reits': 6, 'commodities': 4, 'international': 2, 'cash': 2
            }
        }
        
        allocation = base_allocations.get(risk_tolerance, base_allocations['Moderate'])
        
        return {
            'allocation': allocation,
            'expected_return': '8-15%',  # Enhanced range with more asset classes
            'risk_score': 0.6,
            'method': 'fallback'
        }
    
    def _fallback_stock_scoring(
        self, 
        stocks: List[Dict[str, Any]], 
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhanced fallback stock scoring with ESG, momentum, and value factors"""
        scored_stocks = []
        
        for stock in stocks:
            base_score = stock.get('beginner_friendly_score', 5.0)
            
            # Enhanced scoring factors
            esg_bonus = stock.get('esg_score', 5.0) / 10.0 * 0.5  # ESG contribution
            value_bonus = self._calculate_value_bonus(stock)  # Value factor bonus
            momentum_bonus = self._calculate_momentum_bonus(stock)  # Momentum factor bonus
            
            # Calculate enhanced score
            enhanced_score = min(10.0, base_score + esg_bonus + value_bonus + momentum_bonus)
            
            # Generate enhanced reasoning
            reasoning_parts = [f"Base score: {base_score:.1f}"]
            if esg_bonus > 0:
                reasoning_parts.append("ESG positive")
            if value_bonus > 0:
                reasoning_parts.append("Value attractive")
            if momentum_bonus > 0:
                reasoning_parts.append("Momentum positive")
            
            scored_stocks.append({
                **stock,
                'ml_score': enhanced_score,
                'ml_confidence': 0.6,  # Slightly higher confidence with enhanced factors
                'ml_reasoning': " | ".join(reasoning_parts)
            })
        
        # Sort by enhanced score
        scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
        return scored_stocks
    
    def _calculate_value_bonus(self, stock: Dict[str, Any]) -> float:
        """Calculate value factor bonus for stock scoring"""
        bonus = 0.0
        
        # P/E ratio bonus (lower is better for value)
        pe_ratio = stock.get('pe_ratio', 15.0)
        if pe_ratio < 12.0:
            bonus += 0.5
        elif pe_ratio < 15.0:
            bonus += 0.3
        elif pe_ratio < 20.0:
            bonus += 0.1
        
        # P/B ratio bonus (lower is better for value)
        pb_ratio = stock.get('pb_ratio', 1.5)
        if pb_ratio < 1.0:
            bonus += 0.3
        elif pb_ratio < 1.5:
            bonus += 0.2
        
        # Debt-to-equity bonus (lower is better)
        debt_equity = stock.get('debt_to_equity', 0.5)
        if debt_equity < 0.3:
            bonus += 0.2
        elif debt_equity < 0.5:
            bonus += 0.1
        
        return min(1.0, bonus)  # Cap at 1.0
    
    def _calculate_momentum_bonus(self, stock: Dict[str, Any]) -> float:
        """Calculate momentum factor bonus for stock scoring"""
        bonus = 0.0
        
        # Price momentum bonus
        momentum = stock.get('price_momentum', 0.0)
        if momentum > 0.1:  # 10%+ price increase
            bonus += 0.4
        elif momentum > 0.05:  # 5%+ price increase
            bonus += 0.2
        
        # Volume momentum bonus
        volume_momentum = stock.get('volume_momentum', 0.0)
        if volume_momentum > 0.2:  # 20%+ volume increase
            bonus += 0.2
        elif volume_momentum > 0.1:  # 10%+ volume increase
            bonus += 0.1
        
        return min(0.6, bonus)  # Cap at 0.6
