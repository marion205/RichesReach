#!/usr/bin/env python3
"""
ML Algorithms Demonstration and Customization
This script shows how the ML algorithms work and allows you to customize them
"""
import os
import sys
import django
from pathlib import Path
import json
# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()
def demonstrate_ml_algorithms():
"""Demonstrate how the ML algorithms work"""
print(" ML Algorithms Demonstration")
print("=" * 50)
try:
from core.ml_service import MLService
from core.market_data_service import MarketDataService
ml_service = MLService()
market_service = MarketDataService()
print(f" ML Service Available: {ml_service.is_available()}")
if not ml_service.is_available():
print(" ML Service not available. Please install dependencies.")
return
# Demonstrate Market Regime Prediction
print("\n 1. Market Regime Prediction Algorithm")
print("-" * 40)
# Show current algorithm parameters
print(f"Current Algorithm: Random Forest Classifier")
print(f"Parameters: {ml_service.model_params['market_regime']}")
print(f"Features: 12 market indicators")
print(f"Outputs: {ml_service.regime_labels}")
# Test with different market conditions
test_scenarios = [
{
'name': 'Bull Market',
'data': {
'sp500_return': 0.15,
'volatility': 0.12,
'interest_rate': 0.03,
'gdp_growth': 0.04,
'unemployment_rate': 0.04
}
},
{
'name': 'Bear Market',
'data': {
'sp500_return': -0.12,
'volatility': 0.25,
'interest_rate': 0.08,
'gdp_growth': -0.01,
'unemployment_rate': 0.08
}
},
{
'name': 'Sideways Market',
'data': {
'sp500_return': 0.02,
'volatility': 0.15,
'interest_rate': 0.05,
'gdp_growth': 0.02,
'unemployment_rate': 0.06
}
}
]
for scenario in test_scenarios:
prediction = ml_service.predict_market_regime(scenario['data'])
print(f"\n{scenario['name']}:")
print(f" Predicted Regime: {prediction['regime']}")
print(f" Confidence: {prediction['confidence']:.2f}")
print(f" Method: {prediction['method']}")
# Demonstrate Portfolio Optimization
print("\n 2. Portfolio Optimization Algorithm")
print("-" * 40)
print(f"Current Algorithm: Gradient Boosting Regressor")
print(f"Parameters: {ml_service.model_params['portfolio_optimization']}")
print(f"Features: 20 (user profile + market + stocks)")
print(f"Output: Optimal asset allocation")
# Test with different user profiles
user_profiles = [
{
'name': 'Conservative Investor',
'profile': {
'age': 55,
'income_bracket': '$100,000 - $150,000',
'risk_tolerance': 'Conservative',
'investment_horizon': '5-10 years'
}
},
{
'name': 'Moderate Investor',
'profile': {
'age': 35,
'income_bracket': '$75,000 - $100,000',
'risk_tolerance': 'Moderate',
'investment_horizon': '10+ years'
}
},
{
'name': 'Aggressive Investor',
'profile': {
'age': 25,
'income_bracket': '$50,000 - $75,000',
'risk_tolerance': 'Aggressive',
'investment_horizon': '10+ years'
}
}
]
market_conditions = market_service.get_market_regime_indicators()
available_stocks = [{'beginner_friendly_score': 7.5}]
for profile in user_profiles:
optimization = ml_service.optimize_portfolio_allocation(
profile['profile'], market_conditions, available_stocks
)
print(f"\n{profile['name']}:")
print(f" Method: {optimization['method']}")
print(f" Expected Return: {optimization['expected_return']}")
print(f" Risk Score: {optimization['risk_score']:.2f}")
print(f" Allocation: {json.dumps(optimization['allocation'], indent=2)}")
# Demonstrate Stock Scoring
print("\n 3. Stock Scoring Algorithm")
print("-" * 40)
print(f"Current Algorithm: Gradient Boosting Regressor")
print(f"Parameters: {ml_service.model_params['portfolio_optimization']}")
print(f"Features: 15 (stock + market + user)")
print(f"Output: ML Score (1-10) + Confidence")
# Test with different stocks
test_stocks = [
{'beginner_friendly_score': 9.0, 'symbol': 'AAPL'},
{'beginner_friendly_score': 7.5, 'symbol': 'MSFT'},
{'beginner_friendly_score': 6.0, 'symbol': 'TSLA'},
{'beginner_friendly_score': 8.5, 'symbol': 'GOOGL'}
]
scored_stocks = ml_service.score_stocks_ml(
test_stocks, market_conditions, user_profiles[1]['profile']
)
print(f"\nStock Scoring Results:")
for stock in scored_stocks:
print(f" {stock['symbol']}:")
print(f" ML Score: {stock['ml_score']:.2f}")
print(f" Confidence: {stock['ml_confidence']:.2f}")
print(f" Reasoning: {stock['ml_reasoning']}")
print("\n" + "=" * 50)
print(" ML Algorithms Demonstration Complete!")
except Exception as e:
print(f" Error in demonstration: {e}")
def customize_algorithms():
"""Allow customization of ML algorithms"""
print("\n Algorithm Customization")
print("=" * 50)
try:
from core.ml_service import MLService
ml_service = MLService()
if not ml_service.is_available():
print(" ML Service not available for customization")
return
print("Current ML Service Parameters:")
print(f"Market Regime Model: {ml_service.model_params['market_regime']}")
print(f"Portfolio Optimizer: {ml_service.model_params['portfolio_optimization']}")
print("\nWould you like to customize the algorithms? (y/n): ", end="")
response = input().lower().strip()
if response == 'y':
print("\n Algorithm Customization Options:")
print("1. Market Regime Classification")
print("2. Portfolio Optimization")
print("3. Stock Scoring")
print("4. Feature Engineering")
print("5. Model Parameters")
print("\nEnter your choice (1-5): ", end="")
choice = input().strip()
if choice == '1':
customize_market_regime(ml_service)
elif choice == '2':
customize_portfolio_optimization(ml_service)
elif choice == '3':
customize_stock_scoring(ml_service)
elif choice == '4':
customize_feature_engineering(ml_service)
elif choice == '5':
customize_model_parameters(ml_service)
else:
print("Invalid choice. Exiting customization.")
except Exception as e:
print(f" Error in customization: {e}")
def customize_market_regime(ml_service):
"""Customize market regime classification"""
print("\n Market Regime Classification Customization")
print("-" * 40)
print("Current regime labels:", ml_service.regime_labels)
print("\nCustomization options:")
print("1. Add new regime labels")
print("2. Modify feature weights")
print("3. Change classification thresholds")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
print("Enter new regime label: ", end="")
new_label = input().strip()
ml_service.regime_labels.append(new_label)
print(f" Added new regime: {new_label}")
elif choice == '2':
print("Feature weighting customization would go here...")
print("This would involve modifying the feature extraction logic")
elif choice == '3':
print("Threshold customization would go here...")
print("This would involve modifying the classification logic")
def customize_portfolio_optimization(ml_service):
"""Customize portfolio optimization"""
print("\n Portfolio Optimization Customization")
print("-" * 40)
print("Current optimization parameters:", ml_service.model_params['portfolio_optimization'])
print("\nCustomization options:")
print("1. Modify risk tolerance mapping")
print("2. Adjust allocation ranges")
print("3. Change optimization weights")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
print("Risk tolerance customization would go here...")
print("This would involve modifying the risk calculation logic")
elif choice == '2':
print("Allocation range customization would go here...")
print("This would involve modifying the allocation logic")
elif choice == '3':
print("Weight customization would go here...")
print("This would involve modifying the optimization logic")
def customize_stock_scoring(ml_service):
"""Customize stock scoring"""
print("\n Stock Scoring Customization")
print("-" * 40)
print("Current scoring parameters:", ml_service.model_params['portfolio_optimization'])
print("\nCustomization options:")
print("1. Modify scoring factors")
print("2. Adjust confidence calculation")
print("3. Change reasoning generation")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
print("Scoring factor customization would go here...")
print("This would involve modifying the scoring logic")
elif choice == '2':
print("Confidence calculation customization would go here...")
print("This would involve modifying the confidence logic")
elif choice == '3':
print("Reasoning generation customization would go here...")
print("This would involve modifying the reasoning logic")
def customize_feature_engineering(ml_service):
"""Customize feature engineering"""
print("\n Feature Engineering Customization")
print("-" * 40)
print("Feature engineering customization options:")
print("1. Add new market indicators")
print("2. Modify user profile features")
print("3. Change stock metrics")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
print("New market indicators would go here...")
print("Examples: VIX, bond yields, currency strength")
elif choice == '2':
print("User profile features would go here...")
print("Examples: investment experience, tax bracket, goals")
elif choice == '3':
print("Stock metrics would go here...")
print("Examples: P/E ratio, debt levels, growth rate")
def customize_model_parameters(ml_service):
"""Customize model parameters"""
print("\n Model Parameters Customization")
print("-" * 40)
print("Current parameters:")
for model_type, params in ml_service.model_params.items():
print(f"{model_type}: {params}")
print("\nCustomization options:")
print("1. Modify Random Forest parameters")
print("2. Adjust Gradient Boosting parameters")
print("3. Change training settings")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
print("Random Forest customization would go here...")
print("Examples: n_estimators, max_depth, min_samples_split")
elif choice == '2':
print("Gradient Boosting customization would go here...")
print("Examples: learning_rate, n_estimators, max_depth")
elif choice == '3':
print("Training settings customization would go here...")
print("Examples: cross-validation folds, random state")
def main():
"""Main function"""
print(" ML Algorithms Demo & Customization Tool")
print("=" * 60)
while True:
print("\nOptions:")
print("1. Demonstrate ML Algorithms")
print("2. Customize Algorithms")
print("3. Exit")
print("\nEnter your choice (1-3): ", end="")
choice = input().strip()
if choice == '1':
demonstrate_ml_algorithms()
elif choice == '2':
customize_algorithms()
elif choice == '3':
print(" Goodbye!")
break
else:
print("Invalid choice. Please try again.")
if __name__ == "__main__":
main()
