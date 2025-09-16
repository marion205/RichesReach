#!/usr/bin/env python3
"""
Simple AI Service for Personalized Stock Scoring
Works without Django dependencies
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SimpleAIService:
    """
    Simple AI service for personalized stock scoring based on user profile
    """
    
    def __init__(self):
        self.ml_available = True
        logger.info("Simple AI Service initialized")
    
    def score_stock_for_user(self, stock_data: Dict, user_profile: Dict) -> Optional[float]:
        """Score a stock for a specific user based on their profile and preferences"""
        try:
            # Extract user preferences
            age = user_profile.get('age', 30)
            income_bracket = user_profile.get('income_bracket', 'medium')
            risk_tolerance = user_profile.get('risk_tolerance', 'medium')
            investment_goals = user_profile.get('investment_goals', 'growth')
            investment_horizon = user_profile.get('investment_horizon', 'long_term')
            
            # Extract stock data
            market_cap = stock_data.get('market_cap', 0)
            current_price = stock_data.get('current_price', 0)
            pe_ratio = stock_data.get('pe_ratio', 25.0)
            dividend_yield = stock_data.get('dividend_yield', 2.5)
            volatility = stock_data.get('volatility', 0.2)
            debt_ratio = stock_data.get('debt_ratio', 0.3)
            sector = stock_data.get('sector', 'Unknown')
            
            # Calculate personalized score based on user profile
            score = 0.5  # Base score
            
            # Age-based adjustments
            if age < 25:
                # Younger investors can handle more risk
                score += 0.1 if volatility > 0.3 else 0.05
            elif age > 50:
                # Older investors prefer stability
                score += 0.1 if volatility < 0.2 else -0.05
            
            # Income bracket adjustments
            if income_bracket == 'high':
                # High income can afford higher-priced stocks
                score += 0.05 if current_price > 100 else 0.02
            elif income_bracket == 'low':
                # Lower income prefers affordable stocks
                score += 0.1 if current_price < 50 else 0.02
            
            # Risk tolerance adjustments
            if risk_tolerance == 'low':
                # Prefer stable, large-cap stocks
                score += 0.15 if market_cap > 100_000_000_000 else -0.1
                score += 0.1 if volatility < 0.2 else -0.05
            elif risk_tolerance == 'high':
                # Can handle more volatile stocks
                score += 0.05 if volatility > 0.3 else 0.02
            
            # Investment goals adjustments
            if investment_goals == 'growth':
                # Prefer growth stocks (higher P/E, lower dividends)
                score += 0.1 if pe_ratio > 20 else 0.02
                score += 0.05 if dividend_yield < 3.0 else 0.02
            elif investment_goals == 'income':
                # Prefer dividend stocks
                score += 0.15 if dividend_yield > 3.0 else 0.02
                score += 0.1 if pe_ratio < 20 else 0.02
            
            # Investment horizon adjustments
            if investment_horizon == 'long_term':
                # Can handle more volatility for long-term growth
                score += 0.05 if volatility > 0.2 else 0.02
            elif investment_horizon == 'short_term':
                # Prefer stable stocks
                score += 0.1 if volatility < 0.2 else -0.05
            
            # Sector preferences based on user profile
            if sector.lower() in ['technology', 'software']:
                if age < 40 and risk_tolerance in ['medium', 'high']:
                    score += 0.1
            elif sector.lower() in ['healthcare', 'utilities']:
                if age > 40 or risk_tolerance == 'low':
                    score += 0.1
            elif sector.lower() in ['financial', 'banking']:
                if income_bracket == 'high' and risk_tolerance in ['medium', 'high']:
                    score += 0.05
            
            # Market cap preferences
            if market_cap > 1_000_000_000_000:  # Mega cap
                score += 0.1  # Very stable
            elif market_cap > 100_000_000_000:  # Large cap
                score += 0.05  # Stable
            elif market_cap < 1_000_000_000:  # Small cap
                if risk_tolerance == 'high' and age < 35:
                    score += 0.05  # High risk, high reward for young risk-takers
                else:
                    score -= 0.1  # Too risky for most users
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            logger.info(f"AI/ML scoring for {stock_data.get('symbol', 'Unknown')}: {score:.3f}")
            return score
            
        except Exception as e:
            logger.error(f"Error in AI/ML scoring: {e}")
            return None

# Test the service
if __name__ == "__main__":
    # Test the AI/ML service
    service = SimpleAIService()
    
    # Test stock data
    stock_data = {
        'symbol': 'AAPL',
        'name': 'Apple Inc',
        'sector': 'Technology',
        'market_cap': 3500000000000,
        'current_price': 238.15,
        'pe_ratio': 25.0,
        'dividend_yield': 2.5,
        'volatility': 0.2,
        'debt_ratio': 0.3
    }
    
    # Test user profiles
    young_user = {'age': 25, 'income_bracket': 'high', 'risk_tolerance': 'high', 'investment_goals': 'growth', 'investment_horizon': 'long_term'}
    old_user = {'age': 55, 'income_bracket': 'medium', 'risk_tolerance': 'low', 'investment_goals': 'income', 'investment_horizon': 'short_term'}
    
    # Test scoring
    score1 = service.score_stock_for_user(stock_data, young_user)
    score2 = service.score_stock_for_user(stock_data, old_user)
    
    print(f'Young user score: {score1:.3f}')
    print(f'Old user score: {score2:.3f}')
    print(f'Scores different: {score1 != score2}')
