"""
ML Configuration for Fine-tuning Algorithms
Centralized configuration for risk tolerance, ESG weights, regime thresholds, and allocation ranges
"""
from typing import Dict, List, Any
import json
class MLConfig:
"""Configuration class for ML algorithm fine-tuning"""
def __init__(self):
# Risk Tolerance Mappings
self.risk_tolerance_config = {
'Conservative': {
'risk_score': 0.3,
'max_stock_allocation': 0.40,
'min_bond_allocation': 0.35,
'max_commodity_allocation': 0.05,
'volatility_tolerance': 0.15,
'drawdown_tolerance': 0.10
},
'Moderate': {
'risk_score': 0.6,
'max_stock_allocation': 0.65,
'min_bond_allocation': 0.15,
'max_commodity_allocation': 0.08,
'volatility_tolerance': 0.25,
'drawdown_tolerance': 0.20
},
'Aggressive': {
'risk_score': 0.9,
'max_stock_allocation': 0.80,
'min_bond_allocation': 0.05,
'max_commodity_allocation': 0.12,
'volatility_tolerance': 0.40,
'drawdown_tolerance': 0.35
}
}
# ESG Factor Weights
self.esg_weights = {
'environmental': {
'carbon_footprint': 0.25,
'renewable_energy': 0.20,
'waste_management': 0.15,
'water_usage': 0.15,
'biodiversity': 0.10,
'climate_policy': 0.15
},
'social': {
'labor_rights': 0.20,
'diversity_inclusion': 0.20,
'community_impact': 0.15,
'data_privacy': 0.15,
'supply_chain': 0.15,
'human_rights': 0.15
},
'governance': {
'board_independence': 0.25,
'executive_compensation': 0.20,
'shareholder_rights': 0.20,
'corruption_policy': 0.15,
'tax_transparency': 0.20
}
}
# Market Regime Thresholds
self.regime_thresholds = {
'early_bull_market': {
'min_return': 0.08,
'max_volatility': 0.18,
'min_gdp_growth': 0.025,
'max_unemployment': 0.055,
'min_consumer_sentiment': 0.65
},
'late_bull_market': {
'min_return': 0.15,
'min_volatility': 0.20,
'min_gdp_growth': 0.03,
'max_unemployment': 0.05,
'min_consumer_sentiment': 0.75
},
'correction': {
'max_return': -0.05,
'min_volatility': 0.25,
'max_gdp_growth': 0.02,
'min_unemployment': 0.055,
'max_consumer_sentiment': 0.60
},
'bear_market': {
'max_return': -0.10,
'min_volatility': 0.30,
'max_gdp_growth': 0.01,
'min_unemployment': 0.065,
'max_consumer_sentiment': 0.50
},
'sideways_consolidation': {
'max_return_abs': 0.05,
'max_volatility': 0.20,
'gdp_growth_range': (0.01, 0.03),
'unemployment_range': (0.05, 0.07),
'consumer_sentiment_range': (0.55, 0.70)
},
'high_volatility': {
'min_volatility': 0.35,
'max_volatility': 0.60,
'vix_threshold': 0.30,
'max_confidence': 0.40
},
'recovery': {
'min_return': 0.05,
'max_volatility': 0.25,
'min_gdp_growth': 0.015,
'max_unemployment': 0.06,
'min_consumer_sentiment': 0.55
},
'bubble_formation': {
'min_return': 0.20,
'min_volatility': 0.25,
'min_gdp_growth': 0.035,
'max_unemployment': 0.045,
'min_consumer_sentiment': 0.80,
'max_pe_ratio': 25.0
}
}
# Asset Allocation Ranges
self.allocation_ranges = {
'stocks': {
'Conservative': {'min': 0.25, 'max': 0.45, 'target': 0.35},
'Moderate': {'min': 0.45, 'max': 0.70, 'target': 0.55},
'Aggressive': {'min': 0.60, 'max': 0.85, 'target': 0.70}
},
'bonds': {
'Conservative': {'min': 0.35, 'max': 0.55, 'target': 0.40},
'Moderate': {'min': 0.15, 'max': 0.35, 'target': 0.20},
'Aggressive': {'min': 0.05, 'max': 0.20, 'target': 0.08}
},
'etfs': {
'Conservative': {'min': 0.08, 'max': 0.15, 'target': 0.10},
'Moderate': {'min': 0.08, 'max': 0.15, 'target': 0.10},
'Aggressive': {'min': 0.06, 'max': 0.12, 'target': 0.08}
},
'reits': {
'Conservative': {'min': 0.06, 'max': 0.12, 'target': 0.08},
'Moderate': {'min': 0.06, 'max': 0.12, 'target': 0.08},
'Aggressive': {'min': 0.04, 'max': 0.10, 'target': 0.06}
},
'commodities': {
'Conservative': {'min': 0.01, 'max': 0.05, 'target': 0.02},
'Moderate': {'min': 0.02, 'max': 0.06, 'target': 0.03},
'Aggressive': {'min': 0.03, 'max': 0.08, 'target': 0.04}
},
'international': {
'Conservative': {'min': 0.02, 'max': 0.06, 'target': 0.03},
'Moderate': {'min': 0.02, 'max': 0.06, 'target': 0.02},
'Aggressive': {'min': 0.01, 'max': 0.05, 'target': 0.02}
},
'cash': {
'Conservative': {'min': 0.01, 'max': 0.05, 'target': 0.02},
'Moderate': {'min': 0.01, 'max': 0.05, 'target': 0.02},
'Aggressive': {'min': 0.01, 'max': 0.05, 'target': 0.02}
}
}
# Technical Indicators Configuration
self.technical_indicators = {
'moving_averages': {
'short_term': [5, 10, 20],
'medium_term': [50, 100],
'long_term': [200]
},
'momentum': {
'rsi_periods': [14, 21],
'macd_fast': 12,
'macd_slow': 26,
'macd_signal': 9
},
'volatility': {
'bollinger_periods': [20],
'atr_periods': [14]
},
'volume': {
'volume_sma_periods': [20, 50],
'obv_enabled': True
}
}
# Economic Data Sources
self.economic_sources = {
'federal_reserve': {
'interest_rates': True,
'money_supply': True,
'employment_data': True
},
'bureau_labor': {
'cpi': True,
'unemployment': True,
'wage_growth': True
},
'bureau_economic': {
'gdp': True,
'consumer_spending': True,
'business_investment': True
},
'market_data': {
'vix': True,
'bond_yields': True,
'dollar_index': True,
'commodity_prices': True
}
}
# Alternative Data Sources
self.alternative_data = {
'social_media': {
'twitter_sentiment': True,
'reddit_sentiment': True,
'stocktwits': True
},
'news_sentiment': {
'financial_news': True,
'earnings_calls': True,
'analyst_reports': True
},
'satellite_data': {
'retail_parking': False,
'shipping_activity': False,
'agricultural_yields': False
},
'web_traffic': {
'company_websites': False,
'ecommerce_activity': False
}
}
# User Behavior Patterns
self.user_behavior = {
'portfolio_changes': {
'track_rebalancing': True,
'track_buy_sell': True,
'track_hold_periods': True
},
'risk_adjustment': {
'track_risk_changes': True,
'track_goal_changes': True,
'track_life_events': True
},
'learning_patterns': {
'track_education_usage': True,
'track_tool_usage': True,
'track_community_engagement': True
}
}
def get_risk_config(self, risk_tolerance: str) -> Dict[str, Any]:
"""Get risk tolerance configuration"""
return self.risk_tolerance_config.get(risk_tolerance, self.risk_tolerance_config['Moderate'])
def get_esg_weights(self) -> Dict[str, Any]:
"""Get ESG factor weights"""
return self.esg_weights
def get_regime_thresholds(self, regime: str) -> Dict[str, Any]:
"""Get market regime thresholds"""
return self.regime_thresholds.get(regime, {})
def get_allocation_range(self, asset: str, risk_tolerance: str) -> Dict[str, float]:
"""Get asset allocation range for risk tolerance"""
return self.allocation_ranges.get(asset, {}).get(risk_tolerance, {'min': 0.0, 'max': 0.0, 'target': 0.0})
def update_risk_config(self, risk_tolerance: str, new_config: Dict[str, Any]):
"""Update risk tolerance configuration"""
if risk_tolerance in self.risk_tolerance_config:
self.risk_tolerance_config[risk_tolerance].update(new_config)
def update_esg_weights(self, category: str, new_weights: Dict[str, float]):
"""Update ESG factor weights"""
if category in self.esg_weights:
self.esg_weights[category].update(new_weights)
def update_regime_thresholds(self, regime: str, new_thresholds: Dict[str, Any]):
"""Update market regime thresholds"""
if regime in self.regime_thresholds:
self.regime_thresholds[regime].update(new_thresholds)
def update_allocation_range(self, asset: str, risk_tolerance: str, new_range: Dict[str, float]):
"""Update asset allocation range"""
if asset in self.allocation_ranges and risk_tolerance in self.allocation_ranges[asset]:
self.allocation_ranges[asset][risk_tolerance].update(new_range)
def save_config(self, filepath: str = 'ml_config.json'):
"""Save configuration to file"""
config_data = {
'risk_tolerance_config': self.risk_tolerance_config,
'esg_weights': self.esg_weights,
'regime_thresholds': self.regime_thresholds,
'allocation_ranges': self.allocation_ranges,
'technical_indicators': self.technical_indicators,
'economic_sources': self.economic_sources,
'alternative_data': self.alternative_data,
'user_behavior': self.user_behavior
}
with open(filepath, 'w') as f:
json.dump(config_data, f, indent=2)
def load_config(self, filepath: str = 'ml_config.json'):
"""Load configuration from file"""
try:
with open(filepath, 'r') as f:
config_data = json.load(f)
self.risk_tolerance_config = config_data.get('risk_tolerance_config', self.risk_tolerance_config)
self.esg_weights = config_data.get('esg_weights', self.esg_weights)
self.regime_thresholds = config_data.get('regime_thresholds', self.regime_thresholds)
self.allocation_ranges = config_data.get('allocation_ranges', self.allocation_ranges)
self.technical_indicators = config_data.get('technical_indicators', self.technical_indicators)
self.economic_sources = config_data.get('economic_sources', self.economic_sources)
self.alternative_data = config_data.get('alternative_data', self.alternative_data)
self.user_behavior = config_data.get('user_behavior', self.user_behavior)
except FileNotFoundError:
print(f"Configuration file {filepath} not found. Using default configuration.")
except Exception as e:
print(f"Error loading configuration: {e}. Using default configuration.")
def get_config_summary(self) -> Dict[str, Any]:
"""Get configuration summary"""
return {
'risk_tolerance_levels': list(self.risk_tolerance_config.keys()),
'esg_categories': list(self.esg_weights.keys()),
'market_regimes': list(self.regime_thresholds.keys()),
'asset_classes': list(self.allocation_ranges.keys()),
'technical_indicators_count': len(self.technical_indicators),
'economic_sources_count': len(self.economic_sources),
'alternative_data_count': len(self.alternative_data),
'user_behavior_tracking': len(self.user_behavior)
}
