"""
Optimized ML Service with Model Persistence, Hyperparameter Tuning, and Cross-Validation
Enhanced version of the ML service with production-ready optimizations
"""
import os
import pickle
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
from sklearn.pipeline import Pipeline
import logging
logger = logging.getLogger(__name__)
class OptimizedMLService:
    """
    Optimized ML Service with model persistence, hyperparameter tuning, and cross-validation
    """
    def __init__(self, models_dir: str = "ml_models"):
# Initialize models directory
self.models_dir = os.path.join(os.getcwd(), 'ml_models')
self._ensure_models_directory()
# Initialize model storage
self.models = {}
self.scalers = {}
self.encoders = {}
self.is_trained = False
# Load existing models if available
try:
self._load_existing_models()
logger.info("Optimized ML Service initialized with model persistence")
except Exception as e:
logger.warning(f"Could not load existing models: {e}")
logger.info("Will train new models on first use")
def _ensure_models_directory(self):
"""Ensure the models directory exists"""
if not os.path.exists(self.models_dir):
os.makedirs(self.models_dir)
logger.info(f"Created models directory: {self.models_dir}")
def _load_existing_models(self):
"""Load existing trained models from disk"""
try:
# Load market regime model
regime_model_path = os.path.join(self.models_dir, 'market_regime_model.pkl')
if os.path.exists(regime_model_path):
with open(regime_model_path, 'rb') as f:
self.models['market_regime'] = pickle.load(f)
logger.info("Loaded existing market regime model")
# Load portfolio optimizer model
portfolio_model_path = os.path.join(self.models_dir, 'portfolio_optimizer_model.pkl')
if os.path.exists(portfolio_model_path):
with open(portfolio_model_path, 'rb') as f:
self.models['portfolio_optimizer'] = pickle.load(f)
logger.info("Loaded existing portfolio optimizer model")
# Load stock scorer model
stock_scorer_path = os.path.join(self.models_dir, 'stock_scorer_model.pkl')
if os.path.exists(stock_scorer_path):
with open(stock_scorer_path, 'rb') as f:
self.models['stock_scorer'] = pickle.load(f)
logger.info("Loaded existing stock scorer model")
# Load scalers
scalers_path = os.path.join(self.models_dir, 'scalers.pkl')
if os.path.exists(scalers_path):
with open(scalers_path, 'rb') as f:
self.scalers = pickle.load(f)
logger.info("Loaded existing scalers")
# Load encoders
encoders_path = os.path.join(self.models_dir, 'encoders.pkl')
if os.path.exists(encoders_path):
with open(encoders_path, 'rb') as f:
self.encoders = pickle.load(f)
logger.info("Loaded existing encoders")
# Check if we have all required models
if len(self.models) >= 3:
self.is_trained = True
logger.info("All models loaded successfully")
except Exception as e:
logger.warning(f"Could not load existing models: {e}")
self.is_trained = False
def _save_models(self):
"""Save all trained models to disk"""
try:
# Save individual models
for model_name, model in self.models.items():
model_path = os.path.join(self.models_dir, f'{model_name}_model.pkl')
with open(model_path, 'wb') as f:
pickle.dump(model, f)
# Save scalers
scalers_path = os.path.join(self.models_dir, 'scalers.pkl')
with open(scalers_path, 'wb') as f:
pickle.dump(self.scalers, f)
# Save encoders
encoders_path = os.path.join(self.models_dir, 'encoders.pkl')
with open(encoders_path, 'wb') as f:
pickle.dump(self.encoders, f)
except Exception as e:
logger.error(f"Error saving models: {e}")
def _extract_market_features(self, market_data: Dict[str, Any]) -> np.ndarray:
"""Extract and normalize market features"""
features = []
# Market indicators
features.extend([
market_data.get('vix_index', 20.0),
market_data.get('bond_yield_10y', 2.5),
market_data.get('dollar_strength', 100.0),
market_data.get('oil_price', 70.0),
market_data.get('inflation_rate', 2.0),
market_data.get('consumer_sentiment', 70.0),
market_data.get('gdp_growth', 2.5),
market_data.get('unemployment_rate', 4.0),
market_data.get('interest_rate', 2.5),
market_data.get('housing_starts', 1500),
market_data.get('retail_sales', 2.0),
market_data.get('industrial_production', 1.5),
market_data.get('capacity_utilization', 75.0),
market_data.get('pmi_manufacturing', 50.0),
market_data.get('pmi_services', 50.0),
market_data.get('consumer_confidence', 70.0),
market_data.get('business_confidence', 70.0),
market_data.get('export_growth', 2.0),
market_data.get('import_growth', 2.0),
market_data.get('trade_balance', 0.0)
])
# Ensure exactly 20 features
if len(features) < 20:
features.extend([0.0] * (20 - len(features)))
elif len(features) > 20:
features = features[:20]
return np.array(features).reshape(1, -1)
def _create_portfolio_features(self, user_profile: Dict[str, Any]) -> np.ndarray:
"""Create and normalize portfolio features"""
features = []
# User profile details
features.extend([
user_profile.get('age', 35),
user_profile.get('income_bracket_numeric', 3),
user_profile.get('investment_experience_numeric', 2),
user_profile.get('tax_bracket_numeric', 2),
user_profile.get('investment_horizon_numeric', 2),
user_profile.get('risk_tolerance_numeric', 2),
user_profile.get('net_worth_numeric', 3),
user_profile.get('debt_level_numeric', 2),
user_profile.get('emergency_fund_numeric', 2),
user_profile.get('retirement_savings_numeric', 2),
user_profile.get('college_savings_numeric', 1),
user_profile.get('real_estate_numeric', 1),
user_profile.get('business_ownership_numeric', 1),
user_profile.get('inheritance_expectation_numeric', 1),
user_profile.get('health_insurance_numeric', 2),
user_profile.get('life_insurance_numeric', 1),
user_profile.get('disability_insurance_numeric', 1),
user_profile.get('long_term_care_numeric', 1),
user_profile.get('estate_planning_numeric', 1),
user_profile.get('tax_planning_numeric', 2),
user_profile.get('charitable_giving_numeric', 1),
user_profile.get('social_responsibility_numeric', 2),
user_profile.get('diversification_preference_numeric', 2),
user_profile.get('liquidity_needs_numeric', 2),
user_profile.get('growth_vs_income_numeric', 2)
])
# Ensure exactly 25 features
if len(features) < 25:
features.extend([0] * (25 - len(features)))
elif len(features) > 25:
features = features[:25]
return np.array(features).reshape(1, -1)
def _create_stock_features(self, stock_data: Dict[str, Any]) -> np.ndarray:
"""Create and normalize stock features"""
features = []
# Stock metrics
features.extend([
stock_data.get('esg_score', 70.0),
stock_data.get('sustainability_rating', 3.0),
stock_data.get('governance_score', 70.0),
stock_data.get('pe_ratio', 20.0),
stock_data.get('pb_ratio', 3.0),
stock_data.get('debt_to_equity', 0.5),
stock_data.get('price_momentum', 0.05),
stock_data.get('volume_momentum', 0.1),
stock_data.get('market_cap', 10000000000),
stock_data.get('dividend_yield', 2.0),
stock_data.get('beta', 1.0),
stock_data.get('sharpe_ratio', 1.0),
stock_data.get('max_drawdown', 0.15),
stock_data.get('volatility', 0.2),
stock_data.get('rsi', 50.0),
stock_data.get('macd', 0.0),
stock_data.get('bollinger_position', 0.5),
stock_data.get('support_level', 0.9),
stock_data.get('resistance_level', 1.1),
stock_data.get('trend_strength', 0.5)
])
# Ensure exactly 20 features
if len(features) < 20:
features.extend([0.0] * (20 - len(features)))
elif len(features) > 20:
features = features[:20]
return np.array(features).reshape(1, -1)
def _normalize_features(self, features: np.ndarray, feature_type: str) -> np.ndarray:
"""Normalize features using fitted scalers"""
if feature_type not in self.scalers:
# Create and fit new scaler if not exists
self.scalers[feature_type] = StandardScaler()
self.scalers[feature_type].fit(features)
return features
# Use existing scaler
return self.scalers[feature_type].transform(features)
def _encode_categorical(self, value: Any, feature_type: str) -> int:
"""Encode categorical values using fitted encoders"""
if feature_type not in self.encoders:
# Create and fit new encoder if not exists
self.encoders[feature_type] = LabelEncoder()
self.encoders[feature_type].fit([value])
return 0
# Use existing encoder
try:
return self.encoders[feature_type].transform([value])[0]
except ValueError:
# Handle unseen values
return 0
def train_market_regime_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
"""Train market regime model with hyperparameter tuning and cross-validation"""
logger.info("Training market regime model with optimization...")
# Prepare training data
X = []
y = []
for data_point in training_data:
features = self._extract_market_features(data_point['market_data'])
X.append(features.flatten())
y.append(data_point['regime'])
X = np.array(X)
y = np.array(y)
# Normalize features
X = self._normalize_features(X, 'market_regime')
# Create pipeline with hyperparameter tuning
pipeline = Pipeline([
('classifier', RandomForestClassifier(random_state=42))
])
# Grid search with cross-validation
grid_search = GridSearchCV(
pipeline,
{'classifier__' + k: v for k, v in self.hyperparameter_grids['market_regime'].items()},
cv=self.cv_folds,
scoring='accuracy',
n_jobs=-1,
verbose=1
)
logger.info(" Performing hyperparameter optimization...")
grid_search.fit(X, y)
# Get best model
best_model = grid_search.best_estimator_
self.models['market_regime'] = best_model
# Cross-validation scores
cv_scores = cross_val_score(best_model, X, y, cv=self.cv_folds, scoring='accuracy')
# Training accuracy
train_accuracy = best_model.score(X, y)
results = {
'best_params': grid_search.best_params_,
'best_score': grid_search.best_score_,
'cv_scores': cv_scores.tolist(),
'cv_mean': cv_scores.mean(),
'cv_std': cv_scores.std(),
'train_accuracy': train_accuracy,
'model_type': 'RandomForestClassifier'
}
logger.info(f"Market regime model trained successfully!")
logger.info(f" Best CV Score: {grid_search.best_score_:.4f}")
logger.info(f" CV Mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
logger.info(f" Training Accuracy: {train_accuracy:.4f}")
return results
def train_portfolio_optimizer(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
"""Train portfolio optimizer with hyperparameter tuning and cross-validation"""
logger.info("Training portfolio optimizer with optimization...")
# Prepare training data
X = []
y_stocks = []
y_bonds = []
y_etfs = []
y_cash = []
for data_point in training_data:
features = self._create_portfolio_features(data_point['user_profile'])
X.append(features.flatten())
# Extract individual allocation targets
allocation = data_point['allocation']
y_stocks.append(allocation[0]) # stocks percentage
y_bonds.append(allocation[1]) # bonds percentage
y_etfs.append(allocation[2]) # etfs percentage
y_cash.append(allocation[3]) # cash percentage
X = np.array(X)
# Train separate models for each asset class
models = {}
results = {}
# Train stocks model
logger.info(" Training stocks allocation model...")
stocks_model = self._train_single_asset_model(X, y_stocks, 'stocks')
models['stocks'] = stocks_model['model']
results['stocks'] = stocks_model
# Train bonds model
logger.info(" Training bonds allocation model...")
bonds_model = self._train_single_asset_model(X, y_bonds, 'bonds')
models['bonds'] = bonds_model['model']
results['bonds'] = bonds_model
# Train ETFs model
logger.info(" Training ETFs allocation model...")
etfs_model = self._train_single_asset_model(X, y_etfs, 'etfs')
models['etfs'] = etfs_model['model']
results['etfs'] = etfs_model
# Train cash model
logger.info(" Training cash allocation model...")
cash_model = self._train_single_asset_model(X, y_cash, 'cash')
models['cash'] = cash_model['model']
results['cash'] = cash_model
# Store the models
self.models['portfolio_optimizer'] = models
# Calculate aggregate metrics
avg_cv_mean = np.mean([r['cv_mean'] for r in results.values()])
avg_cv_std = np.mean([r['cv_std'] for r in results.values()])
avg_train_rmse = np.mean([r['train_rmse'] for r in results.values()])
aggregate_results = {
'best_params': 'Multiple models trained',
'best_score': -avg_cv_mean**2, # Convert back to negative MSE
'cv_scores': [r['cv_scores'] for r in results.values()],
'cv_mean': avg_cv_mean,
'cv_std': avg_cv_std,
'train_rmse': avg_train_rmse,
'model_type': 'Multiple GradientBoostingRegressors',
'individual_results': results
}
logger.info(f"Portfolio optimizer trained successfully!")
logger.info(f" Average CV RMSE: {avg_cv_mean:.4f} ± {avg_cv_std:.4f}")
logger.info(f" Average Training RMSE: {avg_train_rmse:.4f}")
return aggregate_results
def _train_single_asset_model(self, X: np.ndarray, y: np.ndarray, asset_name: str) -> Dict[str, Any]:
"""Train a single asset allocation model"""
# Normalize features
X_normalized = self._normalize_features(X, f'portfolio_optimizer_{asset_name}')
# Create pipeline with hyperparameter tuning
pipeline = Pipeline([
('regressor', GradientBoostingRegressor(random_state=42))
])
# Grid search with cross-validation
grid_search = GridSearchCV(
pipeline,
{'regressor__' + k: v for k, v in self.hyperparameter_grids['portfolio_optimizer'].items()},
cv=self.cv_folds,
scoring='neg_mean_squared_error',
n_jobs=-1,
verbose=0 # Reduce verbosity for individual models
)
grid_search.fit(X_normalized, y)
# Get best model
best_model = grid_search.best_estimator_
# Cross-validation scores
cv_scores = cross_val_score(best_model, X_normalized, y, cv=self.cv_folds, scoring='neg_mean_squared_error')
cv_rmse = np.sqrt(-cv_scores)
# Training RMSE
train_predictions = best_model.predict(X_normalized)
train_rmse = np.sqrt(mean_squared_error(y, train_predictions))
return {
'model': best_model,
'best_params': grid_search.best_params_,
'best_score': grid_search.best_score_,
'cv_scores': cv_rmse.tolist(),
'cv_mean': cv_rmse.mean(),
'cv_std': cv_rmse.std(),
'train_rmse': train_rmse,
'model_type': 'GradientBoostingRegressor'
}
def train_stock_scorer(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
"""Train stock scorer with hyperparameter tuning and cross-validation"""
logger.info("Training stock scorer with optimization...")
# Prepare training data
X = []
y = []
for data_point in training_data:
features = self._create_stock_features(data_point['stock_data'])
X.append(features.flatten())
y.append(data_point['score'])
X = np.array(X)
y = np.array(y)
# Normalize features
X = self._normalize_features(X, 'stock_scorer')
# Create pipeline with hyperparameter tuning
pipeline = Pipeline([
('regressor', GradientBoostingRegressor(random_state=42))
])
# Grid search with cross-validation
grid_search = GridSearchCV(
pipeline,
{'regressor__' + k: v for k, v in self.hyperparameter_grids['stock_scorer'].items()},
cv=self.cv_folds,
scoring='neg_mean_squared_error',
n_jobs=-1,
verbose=1
)
logger.info(" Performing hyperparameter optimization...")
grid_search.fit(X, y)
# Get best model
best_model = grid_search.best_estimator_
self.models['stock_scorer'] = best_model
# Cross-validation scores
cv_scores = cross_val_score(best_model, X, y, cv=self.cv_folds, scoring='neg_mean_squared_error')
cv_rmse = np.sqrt(-cv_scores)
# Training RMSE
train_predictions = best_model.predict(X)
train_rmse = np.sqrt(mean_squared_error(y, train_predictions))
results = {
'best_params': grid_search.best_params_,
'best_score': grid_search.best_score_,
'cv_scores': cv_rmse.tolist(),
'cv_mean': cv_rmse.mean(),
'cv_std': cv_rmse.std(),
'train_rmse': train_rmse,
'model_type': 'GradientBoostingRegressor'
}
logger.info(f"Stock scorer trained successfully!")
logger.info(f" Best CV Score: {grid_search.best_score_:.4f}")
logger.info(f" CV RMSE: {cv_rmse.mean():.4f} ± {cv_rmse.std():.4f}")
logger.info(f" Training RMSE: {train_rmse:.4f}")
return results
def train_all_models(self, training_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
"""Train all models with optimization and save them"""
logger.info("Training all models with optimization...")
results = {}
# Train market regime model
if 'market_regime' in training_data:
results['market_regime'] = self.train_market_regime_model(training_data['market_regime'])
# Train portfolio optimizer
if 'portfolio_optimizer' in training_data:
results['portfolio_optimizer'] = self.train_portfolio_optimizer(training_data['portfolio_optimizer'])
# Train stock scorer
if 'stock_scorer' in training_data:
results['stock_scorer'] = self.train_stock_scorer(training_data['stock_scorer'])
# Mark as trained
self.is_trained = True
# Save models
self._save_models()
logger.info("All models trained and saved successfully!")
return results
def predict_market_regime(self, market_data: Dict[str, Any]) -> Tuple[str, float]:
"""Predict market regime using trained model"""
if not self.is_trained or 'market_regime' not in self.models:
return "Moderate", 0.5
try:
features = self._extract_market_features(market_data)
features = self._normalize_features(features, 'market_regime')
prediction = self.models['market_regime'].predict(features)[0]
confidence = np.max(self.models['market_regime'].predict_proba(features))
return prediction, confidence
except Exception as e:
logger.error(f"Error predicting market regime: {e}")
return "Moderate", 0.5
def optimize_portfolio(self, user_profile: Dict[str, Any]) -> Dict[str, float]:
"""Optimize portfolio using trained models"""
if not self.is_trained or 'portfolio_optimizer' not in self.models:
return self._fallback_portfolio_optimization(user_profile)
try:
features = self._create_portfolio_features(user_profile)
# Get predictions from each asset model
portfolio_models = self.models['portfolio_optimizer']
stocks_pred = portfolio_models['stocks'].predict(features)[0]
bonds_pred = portfolio_models['bonds'].predict(features)[0]
etfs_pred = portfolio_models['etfs'].predict(features)[0]
cash_pred = portfolio_models['cash'].predict(features)[0]
# Normalize to ensure percentages sum to 100
total = stocks_pred + bonds_pred + etfs_pred + cash_pred
if total > 0:
stocks_pred = (stocks_pred / total) * 100
bonds_pred = (bonds_pred / total) * 100
etfs_pred = (etfs_pred / total) * 100
cash_pred = (cash_pred / total) * 100
return {
'stocks': max(0, min(100, stocks_pred)),
'bonds': max(0, min(100, bonds_pred)),
'etfs': max(0, min(100, etfs_pred)),
'cash': max(0, min(100, cash_pred)),
'reits': 0.0, # Not trained yet
'commodities': 0.0, # Not trained yet
'international': 0.0 # Not trained yet
}
except Exception as e:
logger.error(f"Error optimizing portfolio: {e}")
return self._fallback_portfolio_optimization(user_profile)
def score_stock(self, stock_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
"""Score stock using trained model"""
if not self.is_trained or 'stock_scorer' not in self.models:
return self._fallback_stock_scoring(stock_data)
try:
features = self._create_stock_features(stock_data)
features = self._normalize_features(features, 'stock_scorer')
score = self.models['stock_scorer'].predict(features)[0]
# Calculate factor scores
factor_scores = {
'esg': self._calculate_esg_score(stock_data),
'value': self._calculate_value_score(stock_data),
'momentum': self._calculate_momentum_score(stock_data),
'quality': self._calculate_quality_score(stock_data),
'growth': self._calculate_growth_score(stock_data)
}
return score, factor_scores
except Exception as e:
logger.error(f"Error scoring stock: {e}")
return self._fallback_stock_scoring(stock_data)
def _fallback_portfolio_optimization(self, user_profile: Dict[str, Any]) -> Dict[str, float]:
"""Fallback portfolio optimization logic"""
risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
if risk_tolerance == 'Conservative':
return {'stocks': 30, 'bonds': 50, 'etfs': 15, 'cash': 5, 'reits': 0, 'commodities': 0, 'international': 0}
elif risk_tolerance == 'Moderate':
return {'stocks': 60, 'bonds': 30, 'etfs': 8, 'cash': 2, 'reits': 0, 'commodities': 0, 'international': 0}
else: # Aggressive
return {'stocks': 80, 'bonds': 15, 'etfs': 3, 'cash': 2, 'reits': 0, 'commodities': 0, 'international': 0}
def _fallback_stock_scoring(self, stock_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
"""Fallback stock scoring logic"""
base_score = 70.0
# Simple scoring based on basic metrics
if stock_data.get('pe_ratio', 20) < 15:
base_score += 10
if stock_data.get('dividend_yield', 0) > 3:
base_score += 5
if stock_data.get('esg_score', 70) > 80:
base_score += 10
factor_scores = {
'esg': stock_data.get('esg_score', 70),
'value': 75.0,
'momentum': 70.0,
'quality': 75.0,
'growth': 70.0
}
return min(100, max(0, base_score)), factor_scores
def _calculate_esg_score(self, stock_data: Dict[str, Any]) -> float:
"""Calculate ESG score"""
esg_score = stock_data.get('esg_score', 70.0)
sustainability = stock_data.get('sustainability_rating', 3.0) * 20
governance = stock_data.get('governance_score', 70.0)
return (esg_score + sustainability + governance) / 3
def _calculate_value_score(self, stock_data: Dict[str, Any]) -> float:
"""Calculate value score"""
pe_ratio = stock_data.get('pe_ratio', 20.0)
pb_ratio = stock_data.get('pb_ratio', 3.0)
dividend_yield = stock_data.get('dividend_yield', 2.0)
# Lower P/E and P/B ratios are better for value
pe_score = max(0, 100 - (pe_ratio - 10) * 5)
pb_score = max(0, 100 - (pb_ratio - 1) * 20)
dividend_score = min(100, dividend_yield * 20)
return (pe_score + pb_score + dividend_score) / 3
def _calculate_momentum_score(self, stock_data: Dict[str, Any]) -> float:
"""Calculate momentum score"""
price_momentum = stock_data.get('price_momentum', 0.05)
volume_momentum = stock_data.get('volume_momentum', 0.1)
rsi = stock_data.get('rsi', 50.0)
# Convert to 0-100 scale
momentum_score = max(0, min(100, (price_momentum + 0.2) * 250))
volume_score = max(0, min(100, (volume_momentum + 0.2) * 250))
rsi_score = max(0, min(100, 100 - abs(rsi - 50) * 2))
return (momentum_score + volume_score + rsi_score) / 3
def _calculate_quality_score(self, stock_data: Dict[str, Any]) -> float:
"""Calculate quality score"""
debt_to_equity = stock_data.get('debt_to_equity', 0.5)
beta = stock_data.get('beta', 1.0)
market_cap = stock_data.get('market_cap', 10000000000)
# Lower debt and beta are better for quality
debt_score = max(0, 100 - debt_to_equity * 100)
beta_score = max(0, 100 - (beta - 0.5) * 50)
size_score = min(100, market_cap / 100000000000 * 100)
return (debt_score + beta_score + size_score) / 3
def _calculate_growth_score(self, stock_data: Dict[str, Any]) -> float:
"""Calculate growth score"""
# Simple growth score based on momentum and market position
momentum = self._calculate_momentum_score(stock_data)
quality = self._calculate_quality_score(stock_data)
return (momentum + quality) / 2
def get_model_performance(self) -> Dict[str, Any]:
"""Get performance metrics for all models"""
if not self.is_trained:
return {'status': 'Models not trained yet'}
performance = {
'status': 'Models trained and ready',
'models_loaded': list(self.models.keys()),
'scalers_loaded': list(self.scalers.keys()),
'encoders_loaded': list(self.encoders.keys()),
'last_training': 'Unknown',
'model_info': {}
}
for model_name, model in self.models.items():
performance['model_info'][model_name] = {
'type': type(model).__name__,
'parameters': model.get_params() if hasattr(model, 'get_params') else 'N/A'
}
return performance
def retrain_models(self, training_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
"""Retrain all models with new data"""
logger.info(" Retraining all models...")
# Clear existing models
self.models = {}
self.scalers = {}
self.encoders = {}
self.is_trained = False
# Train new models
results = self.train_all_models(training_data)
logger.info("Models retrained successfully!")
return results
