# core/ai_service.py
import os
from django.conf import settings
from typing import List, Dict, Optional
import logging
logger = logging.getLogger(__name__)
# Try to import openai, but don't fail if it's not available
try:
import openai
OPENAI_AVAILABLE = True
except ImportError:
OPENAI_AVAILABLE = False
logger.warning("OpenAI package not installed. AI features will use fallback responses.")
# Import ML service
try:
from .optimized_ml_service import OptimizedMLService
from .market_data_service import MarketDataService
ML_AVAILABLE = True
except ImportError as e:
logger.warning(f"ML services not available: {e}")
ML_AVAILABLE = False
class AIService:
def __init__(self):
self.api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 1000)
if self.api_key and OPENAI_AVAILABLE:
openai.api_key = self.api_key
else:
logger.warning("OpenAI API key not found or package not available. AI features will use fallback responses.")
# Initialize ML services
if ML_AVAILABLE:
self.ml_service = OptimizedMLService()
self.market_data_service = MarketDataService()
logger.info("Optimized ML services initialized successfully")
else:
self.ml_service = None
self.market_data_service = None
logger.warning("ML services not available")
def get_chat_response(self, messages: List[Dict], user_context: Optional[str] = None) -> Dict:
"""
Get a response from OpenAI's chat completion API
Args:
messages: List of message dictionaries with 'role' and 'content'
user_context: Optional user context information
Returns:
Dictionary containing response content, confidence, and token usage
"""
if not self.api_key or not OPENAI_AVAILABLE:
return self._get_fallback_response(messages[-1]['content'] if messages else "")
try:
# Add system context if provided
system_messages = []
if user_context:
system_messages.append({
"role": "system",
"content": f"You are a helpful financial advisor. User context: {user_context}"
})
# Prepare messages for OpenAI
openai_messages = system_messages + messages
response = openai.ChatCompletion.create(
model=self.model,
messages=openai_messages,
max_tokens=self.max_tokens,
temperature=0.7
)
return {
"content": response.choices[0].message.content,
"confidence": 0.9, # OpenAI doesn't provide confidence scores
"tokens_used": response.usage.total_tokens,
"model_used": self.model
}
except Exception as e:
logger.error(f"OpenAI API error: {str(e)}")
return self._get_fallback_response(messages[-1]['content'] if messages else "")
def predict_market_regime(self, market_data: Optional[Dict] = None) -> Dict:
"""
Predict market regime using ML models
Args:
market_data: Optional market data, will fetch if not provided
Returns:
Dictionary with regime prediction and confidence
"""
if not ML_AVAILABLE or not self.ml_service:
return self._get_fallback_market_regime()
try:
# Get market data if not provided
if market_data is None:
market_data = self.market_data_service.get_market_regime_indicators()
# Use ML service to predict regime
prediction = self.ml_service.predict_market_regime(market_data)
return {
**prediction,
'ai_service': 'ml_enhanced',
'timestamp': self._get_current_timestamp()
}
except Exception as e:
logger.error(f"Error in market regime prediction: {e}")
return self._get_fallback_market_regime()
def optimize_portfolio_ml(
self, 
user_profile: Dict, 
available_stocks: Optional[List[Dict]] = None,
spending_analysis: Optional[Dict] = None
) -> Dict:
"""
Optimize portfolio using ML models with spending habits analysis
Args:
user_profile: User's financial profile
available_stocks: Optional list of available stocks
spending_analysis: Optional spending habits analysis from transactions
Returns:
Optimized portfolio allocation
"""
if not ML_AVAILABLE or not self.ml_service:
return self._get_fallback_portfolio_optimization(user_profile)
try:
# Get market conditions
market_conditions = self.market_data_service.get_market_regime_indicators()
# Use ML service to optimize portfolio (with spending analysis if available)
optimization = self.ml_service.optimize_portfolio_allocation(
user_profile, market_conditions, available_stocks or [], spending_analysis
)
return {
**optimization,
'ai_service': 'ml_enhanced',
'market_conditions': market_conditions,
'timestamp': self._get_current_timestamp()
}
except Exception as e:
logger.error(f"Error in ML portfolio optimization: {e}")
return self._get_fallback_portfolio_optimization(user_profile)
def score_stocks_ml(
self, 
stocks: List[Dict], 
user_profile: Dict,
spending_analysis: Optional[Dict] = None
) -> List[Dict]:
"""
Score stocks using ML models with spending habits analysis
Args:
stocks: List of stocks to score
user_profile: User's financial profile
spending_analysis: Optional spending habits analysis from transactions
Returns:
List of scored stocks with ML scores
"""
if not ML_AVAILABLE or not self.ml_service:
return self._get_fallback_stock_scoring(stocks, user_profile)
try:
# Get market conditions
market_conditions = self.market_data_service.get_market_regime_indicators()
# Use ML service to score stocks (with spending analysis if available)
scored_stocks = self.ml_service.score_stocks_ml(
stocks, market_conditions, user_profile, spending_analysis
)
return scored_stocks
except Exception as e:
logger.error(f"Error in ML stock scoring: {e}")
return self._get_fallback_stock_scoring(stocks, user_profile)
def get_enhanced_market_analysis(self) -> Dict:
"""
Get enhanced market analysis using ML models
Returns:
Comprehensive market analysis
"""
if not ML_AVAILABLE or not self.market_data_service:
return self._get_fallback_market_analysis()
try:
# Get comprehensive market data
market_overview = self.market_data_service.get_market_overview()
sector_performance = self.market_data_service.get_sector_performance()
economic_indicators = self.market_data_service.get_economic_indicators()
regime_indicators = self.market_data_service.get_market_regime_indicators()
# Predict market regime using ML
regime_prediction = self.predict_market_regime(regime_indicators)
return {
'market_overview': market_overview,
'sector_performance': sector_performance,
'economic_indicators': economic_indicators,
'regime_indicators': regime_indicators,
'ml_regime_prediction': regime_prediction,
'ai_service': 'ml_enhanced',
'timestamp': self._get_current_timestamp()
}
except Exception as e:
logger.error(f"Error in enhanced market analysis: {e}")
return self._get_fallback_market_analysis()
def generate_session_title(self, first_message: str) -> str:
"""Generate a title for a chat session based on the first message"""
if not self.api_key or not OPENAI_AVAILABLE:
return "Financial Chat Session"
try:
response = openai.ChatCompletion.create(
model=self.model,
messages=[
{"role": "system", "content": "Generate a short, descriptive title (max 50 chars) for a financial chat session based on the user's first message."},
{"role": "user", "content": f"First message: {first_message}"}
],
max_tokens=20,
temperature=0.3
)
title = response.choices[0].message.content.strip()
# Clean up the title
title = title.replace('"', '').replace("'", "")
if len(title) > 50:
title = title[:47] + "..."
return title
except Exception as e:
logger.error(f"Error generating title: {str(e)}")
return "Financial Chat Session"
def _get_fallback_response(self, user_message: str) -> Dict:
"""Fallback response when OpenAI is not available"""
return {
"content": f"I'm currently in offline mode. You asked: '{user_message}'. "
f"Here are some general financial tips:\n"
f"• Always diversify your investments\n"
f"• Consider your time horizon and risk tolerance\n"
f"• Research fees and expenses\n"
f"• Visit investor.gov for educational resources",
"confidence": 0.5,
"tokens_used": 0,
"model_used": "fallback"
}
def _get_fallback_market_regime(self) -> Dict:
"""Fallback market regime prediction"""
return {
'regime': 'sideways',
'confidence': 0.5,
'all_probabilities': {
'bull_market': 0.25,
'bear_market': 0.25,
'sideways': 0.3,
'volatile': 0.2
},
'method': 'fallback',
'ai_service': 'fallback'
}
def _get_fallback_portfolio_optimization(self, user_profile: Dict) -> Dict:
"""Fallback portfolio optimization"""
risk_tolerance = user_profile.get('risk_tolerance', 'Moderate')
base_allocations = {
'Conservative': {'stocks': 40, 'bonds': 45, 'etfs': 12, 'cash': 3},
'Moderate': {'stocks': 60, 'bonds': 25, 'etfs': 12, 'cash': 3},
'Aggressive': {'stocks': 80, 'bonds': 10, 'etfs': 8, 'cash': 2}
}
allocation = base_allocations.get(risk_tolerance, base_allocations['Moderate'])
return {
'allocation': allocation,
'expected_return': '8-12%',
'risk_score': 0.6,
'method': 'fallback',
'ai_service': 'fallback'
}
def _get_fallback_stock_scoring(self, stocks: List[Dict], user_profile: Dict) -> List[Dict]:
"""Fallback stock scoring"""
scored_stocks = []
for stock in stocks:
base_score = stock.get('beginner_friendly_score', 5.0)
scored_stocks.append({
**stock,
'ml_score': base_score,
'ml_confidence': 0.5,
'ml_reasoning': f"Fallback score based on beginner-friendly rating: {base_score}"
})
# Sort by score
scored_stocks.sort(key=lambda x: x['ml_score'], reverse=True)
return scored_stocks
def _get_fallback_market_analysis(self) -> Dict:
"""Fallback market analysis"""
return {
'market_overview': {'sp500_return': 0.0, 'volatility': 0.15, 'method': 'fallback'},
'sector_performance': {'technology': 'neutral', 'healthcare': 'neutral', 'financials': 'neutral'},
'economic_indicators': {'interest_rate': 0.05, 'gdp_growth': 0.02, 'method': 'fallback'},
'regime_indicators': {'market_regime': 'sideways', 'method': 'fallback'},
'ai_service': 'fallback'
}
def _get_current_timestamp(self) -> str:
"""Get current timestamp in ISO format"""
from datetime import datetime
return datetime.now().isoformat()
def get_service_status(self) -> Dict:
"""Get status of all AI services"""
return {
'openai_available': OPENAI_AVAILABLE and bool(self.api_key),
'ml_available': ML_AVAILABLE and bool(self.ml_service),
'market_data_available': ML_AVAILABLE and bool(self.market_data_service),
'api_key_configured': bool(self.api_key),
'timestamp': self._get_current_timestamp()
}
