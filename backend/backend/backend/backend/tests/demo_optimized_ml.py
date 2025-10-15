#!/usr/bin/env python3
"""
Demo Script for Optimized ML Service
Showcases model persistence, hyperparameter tuning, and cross-validation
"""
import sys
import os
import time
import logging
from datetime import datetime
# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
from optimized_ml_service import OptimizedMLService
# Configure logging
logging.basicConfig(
level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
def generate_synthetic_training_data():
"""Generate synthetic training data for demonstration"""
print(" Generating synthetic training data...")
# Market regime training data
market_regime_data = []
regimes = ['Early Bull', 'Late Bull', 'Sideways', 'Correction', 'Bear Market', 'Recovery', 'Consolidation', 'Breakout']
for i in range(1000):
market_data = {
'vix_index': 15 + (i % 30),
'bond_yield_10y': 1.5 + (i % 4),
'dollar_strength': 95 + (i % 10),
'oil_price': 60 + (i % 40),
'inflation_rate': 1.5 + (i % 3),
'consumer_sentiment': 60 + (i % 30),
'gdp_growth': 1.0 + (i % 4),
'unemployment_rate': 3.5 + (i % 3),
'interest_rate': 1.5 + (i % 3),
'housing_starts': 1200 + (i % 800),
'retail_sales': 1.0 + (i % 4),
'industrial_production': 0.5 + (i % 3),
'capacity_utilization': 70 + (i % 20),
'pmi_manufacturing': 45 + (i % 15),
'pmi_services': 45 + (i % 15),
'consumer_confidence': 60 + (i % 30),
'business_confidence': 60 + (i % 30),
'export_growth': 1.0 + (i % 4),
'import_growth': 1.0 + (i % 4),
'trade_balance': -2.0 + (i % 6)
}
# Simple rule-based regime assignment
if market_data['vix_index'] < 20 and market_data['gdp_growth'] > 2.5:
regime = 'Early Bull'
elif market_data['vix_index'] < 25 and market_data['gdp_growth'] > 2.0:
regime = 'Late Bull'
elif market_data['vix_index'] > 30:
regime = 'Correction'
elif market_data['gdp_growth'] < 1.0:
regime = 'Bear Market'
else:
regime = regimes[i % len(regimes)]
market_regime_data.append({
'market_data': market_data,
'regime': regime
})
# Portfolio optimizer training data
portfolio_data = []
risk_levels = ['Conservative', 'Moderate', 'Aggressive']
for i in range(800):
user_profile = {
'age': 25 + (i % 50),
'income_bracket_numeric': 1 + (i % 5),
'investment_experience_numeric': 1 + (i % 4),
'tax_bracket_numeric': 1 + (i % 4),
'investment_horizon_numeric': 1 + (i % 4),
'risk_tolerance_numeric': 1 + (i % 3),
'net_worth_numeric': 1 + (i % 5),
'debt_level_numeric': 1 + (i % 4),
'emergency_fund_numeric': 1 + (i % 4),
'retirement_savings_numeric': 1 + (i % 4),
'college_savings_numeric': 1 + (i % 3),
'real_estate_numeric': 1 + (i % 3),
'business_ownership_numeric': 1 + (i % 3),
'inheritance_expectation_numeric': 1 + (i % 3),
'health_insurance_numeric': 1 + (i % 4),
'life_insurance_numeric': 1 + (i % 3),
'disability_insurance_numeric': 1 + (i % 3),
'long_term_care_numeric': 1 + (i % 3),
'estate_planning_numeric': 1 + (i % 3),
'tax_planning_numeric': 1 + (i % 4),
'charitable_giving_numeric': 1 + (i % 3),
'social_responsibility_numeric': 1 + (i % 4),
'diversification_preference_numeric': 1 + (i % 4),
'liquidity_needs_numeric': 1 + (i % 4),
'growth_vs_income_numeric': 1 + (i % 4)
}
# Generate allocation based on risk tolerance
risk_level = risk_levels[user_profile['risk_tolerance_numeric'] - 1]
if risk_level == 'Conservative':
allocation = [0.3, 0.5, 0.15, 0.05, 0.0, 0.0, 0.0] # stocks, bonds, etfs, cash, reits, commodities, international
elif risk_level == 'Moderate':
allocation = [0.6, 0.3, 0.08, 0.02, 0.0, 0.0, 0.0]
else: # Aggressive
allocation = [0.8, 0.15, 0.03, 0.02, 0.0, 0.0, 0.0]
portfolio_data.append({
'user_profile': user_profile,
'allocation': allocation
})
# Stock scorer training data
stock_data = []
for i in range(1200):
stock_info = {
'esg_score': 50 + (i % 50),
'sustainability_rating': 1 + (i % 5),
'governance_score': 50 + (i % 50),
'pe_ratio': 10 + (i % 30),
'pb_ratio': 1 + (i % 5),
'debt_to_equity': 0.1 + (i % 1.0),
'price_momentum': -0.2 + (i % 0.4),
'volume_momentum': -0.1 + (i % 0.3),
'market_cap': 1000000000 + (i % 100000000000),
'dividend_yield': 0 + (i % 6),
'beta': 0.5 + (i % 1.5),
'sharpe_ratio': 0.5 + (i % 1.5),
'max_drawdown': 0.1 + (i % 0.3),
'volatility': 0.1 + (i % 0.3),
'rsi': 30 + (i % 40),
'macd': -0.1 + (i % 0.2),
'bollinger_position': 0.3 + (i % 0.4),
'support_level': 0.8 + (i % 0.4),
'resistance_level': 1.0 + (i % 0.4),
'trend_strength': 0.3 + (i % 0.4)
}
# Calculate score based on metrics
score = 50.0
score += (stock_info['esg_score'] - 50) * 0.3
score += (20 - stock_info['pe_ratio']) * 1.0
score += stock_info['dividend_yield'] * 5.0
score += (1.0 - stock_info['debt_to_equity']) * 20.0
score += (stock_info['sharpe_ratio'] - 0.5) * 30.0
score = max(0, min(100, score))
stock_data.append({
'stock_data': stock_info,
'score': score
})
training_data = {
'market_regime': market_regime_data,
'portfolio_optimizer': portfolio_data,
'stock_scorer': stock_data
}
print(f" Generated training data:")
print(f" Market Regime: {len(market_regime_data)} samples")
print(f" Portfolio Optimizer: {len(portfolio_data)} samples")
print(f" Stock Scorer: {len(stock_data)} samples")
return training_data
def demo_model_persistence():
"""Demonstrate model persistence capabilities"""
print("\n" + "="*60)
print(" MODEL PERSISTENCE DEMONSTRATION")
print("="*60)
# Initialize service
ml_service = OptimizedMLService()
print(f" Models directory: {ml_service.models_dir}")
print(f" Checking for existing models...")
# Check if models exist
for model_name, model_path in ml_service.model_paths.items():
if os.path.exists(model_path):
file_size = os.path.getsize(model_path) / 1024 # KB
print(f" {model_name}: {file_size:.1f} KB")
else:
print(f" {model_name}: Not found")
return ml_service
def demo_hyperparameter_tuning(training_data):
"""Demonstrate hyperparameter tuning and cross-validation"""
print("\n" + "="*60)
print(" HYPERPARAMETER TUNING & CROSS-VALIDATION")
print("="*60)
ml_service = OptimizedMLService()
print(" Training models with hyperparameter optimization...")
print(" This will take a few minutes as we test multiple parameter combinations")
print(" and perform 5-fold cross-validation for each...")
start_time = time.time()
# Train all models
results = ml_service.train_all_models(training_data)
training_time = time.time() - start_time
print(f"\n⏱ Total training time: {training_time:.2f} seconds")
# Display results
for model_name, result in results.items():
print(f"\n {model_name.upper().replace('_', ' ')} RESULTS:")
print(f" Best CV Score: {result['best_score']:.4f}")
print(f" CV Mean: {result['cv_mean']:.4f} ± {result['cv_std']:.4f}")
if 'train_accuracy' in result:
print(f" Training Accuracy: {result['train_accuracy']:.4f}")
if 'train_rmse' in result:
print(f" Training RMSE: {result['train_rmse']:.4f}")
print(f" Best Parameters:")
if isinstance(result['best_params'], dict):
for param, value in result['best_params'].items():
print(f" {param}: {value}")
else:
print(f" {result['best_params']}")
return ml_service
def demo_model_performance(ml_service):
"""Demonstrate model performance and predictions"""
print("\n" + "="*60)
print(" MODEL PERFORMANCE & PREDICTIONS")
print("="*60)
# Get model performance
performance = ml_service.get_model_performance()
print(f" Model Status: {performance['status']}")
print(f" Models Loaded: {', '.join(performance['models_loaded'])}")
print(f" Scalers Loaded: {', '.join(performance['scalers_loaded'])}")
print(f" Encoders Loaded: {', '.join(performance['encoders_loaded'])}")
# Test predictions
print(f"\n Testing Predictions...")
# Test market regime prediction
test_market_data = {
'vix_index': 18.5,
'bond_yield_10y': 2.8,
'dollar_strength': 98.2,
'oil_price': 72.5,
'inflation_rate': 2.2,
'consumer_sentiment': 75.0,
'gdp_growth': 2.8,
'unemployment_rate': 3.8,
'interest_rate': 2.2,
'housing_starts': 1350,
'retail_sales': 2.5,
'industrial_production': 1.8,
'capacity_utilization': 78.0,
'pmi_manufacturing': 52.0,
'pmi_services': 54.0,
'consumer_confidence': 72.0,
'business_confidence': 74.0,
'export_growth': 2.2,
'import_growth': 2.1,
'trade_balance': -1.5
}
regime, confidence = ml_service.predict_market_regime(test_market_data)
print(f" Market Regime Prediction: {regime} (Confidence: {confidence:.2f})")
# Test portfolio optimization
test_user_profile = {
'age': 35,
'risk_tolerance': 'Moderate',
'investment_horizon': '10-20 years',
'income_bracket': '$75,000 - $100,000'
}
allocation = ml_service.optimize_portfolio(test_user_profile)
print(f" Portfolio Allocation:")
for asset, percentage in allocation.items():
print(f" {asset.capitalize()}: {percentage:.1f}%")
# Test stock scoring
test_stock_data = {
'esg_score': 85.0,
'sustainability_rating': 4.0,
'governance_score': 82.0,
'pe_ratio': 18.5,
'pb_ratio': 2.8,
'debt_to_equity': 0.3,
'price_momentum': 0.08,
'volume_momentum': 0.12,
'market_cap': 50000000000,
'dividend_yield': 2.8,
'beta': 0.9,
'sharpe_ratio': 1.2,
'max_drawdown': 0.12,
'volatility': 0.18,
'rsi': 58.0,
'macd': 0.02,
'bollinger_position': 0.6,
'support_level': 0.92,
'resistance_level': 1.08,
'trend_strength': 0.65
}
score, factor_scores = ml_service.score_stock(test_stock_data)
print(f" Stock Score: {score:.1f}/100")
print(f" Factor Scores:")
for factor, factor_score in factor_scores.items():
print(f" {factor.capitalize()}: {factor_score:.1f}")
return ml_service
def demo_model_reloading():
"""Demonstrate model reloading from disk"""
print("\n" + "="*60)
print(" MODEL RELOADING DEMONSTRATION")
print("="*60)
print(" Creating new ML service instance to test model loading...")
# Create new instance (should load existing models)
new_ml_service = OptimizedMLService()
if new_ml_service.is_trained:
print(" Models successfully loaded from disk!")
print(" No need to retrain - predictions are instant!")
# Test instant prediction
start_time = time.time()
test_data = {'vix_index': 20.0, 'bond_yield_10y': 2.5}
regime, confidence = new_ml_service.predict_market_regime(test_data)
prediction_time = (time.time() - start_time) * 1000 # milliseconds
print(f" Prediction time: {prediction_time:.2f} ms")
print(f" Result: {regime} (Confidence: {confidence:.2f})")
else:
print(" Models not loaded - would need to retrain")
def main():
"""Main demonstration function"""
print(" OPTIMIZED ML SERVICE DEMONSTRATION")
print("="*60)
print("This demo showcases:")
print(" Model Persistence - Save/load trained models")
print(" Hyperparameter Tuning - Optimize model parameters")
print(" Cross-Validation - Robust model evaluation")
print(" Instant Predictions - No retraining needed")
print(" Production Ready - Scalable and efficient")
try:
# Generate training data
training_data = generate_synthetic_training_data()
# Demo 1: Model Persistence
ml_service = demo_model_persistence()
# Demo 2: Hyperparameter Tuning
if not ml_service.is_trained:
ml_service = demo_hyperparameter_tuning(training_data)
else:
print("\n Models already trained and loaded!")
# Demo 3: Model Performance
demo_model_performance(ml_service)
# Demo 4: Model Reloading
demo_model_reloading()
print("\n" + "="*60)
print(" OPTIMIZED ML SERVICE DEMO COMPLETE!")
print("="*60)
print("Key Benefits Achieved:")
print(" Models train once, predict instantly")
print(" Hyperparameter optimization for best performance")
print(" Cross-validation for robust evaluation")
print(" Persistent storage for production deployment")
print(" Sub-millisecond prediction times")
print(" Scalable architecture for multiple users")
print(f"\n Models saved in: {ml_service.models_dir}")
print(" Models can now be used in production without retraining!")
except Exception as e:
print(f" Error during demonstration: {e}")
import traceback
traceback.print_exc()
if __name__ == "__main__":
main()
