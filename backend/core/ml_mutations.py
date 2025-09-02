"""
ML-Enhanced Mutations for Portfolio Recommendations
Uses machine learning models for better AI portfolio suggestions
"""

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from django.db import transaction
from typing import Dict, List, Any
import logging

from .models import AIPortfolioRecommendation, StockRecommendation, Stock, IncomeProfile
from .ai_service import AIService

logger = logging.getLogger(__name__)
User = get_user_model()

class MLPortfolioRecommendationType(DjangoObjectType):
    """Enhanced AI Portfolio Recommendation with ML insights"""
    class Meta:
        model = AIPortfolioRecommendation
        fields = '__all__'
    
    # Additional ML-specific fields
    ml_confidence = graphene.Float()
    ml_market_regime = graphene.String()
    ml_expected_return_range = graphene.String()
    ml_risk_score = graphene.Float()
    ml_optimization_method = graphene.String()
    market_conditions = graphene.JSONString()
    user_profile_analysis = graphene.JSONString()

class GenerateMLPortfolioRecommendation(graphene.Mutation):
    """
    Generate AI portfolio recommendations using ML models
    """
    
    class Arguments:
        use_advanced_ml = graphene.Boolean(default=True)
        include_market_analysis = graphene.Boolean(default=True)
        include_risk_optimization = graphene.Boolean(default=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    recommendation = graphene.Field(MLPortfolioRecommendationType)
    market_analysis = graphene.JSONString()
    ml_insights = graphene.JSONString()
    
    def mutate(self, info, use_advanced_ml=True, include_market_analysis=True, include_risk_optimization=True):
        user = info.context.user
        if user.is_anonymous:
            return GenerateMLPortfolioRecommendation(
                success=False, 
                message="You must be logged in to generate ML portfolio recommendations"
            )
        
        try:
            # Check if user has income profile
            try:
                income_profile = user.incomeProfile
            except IncomeProfile.DoesNotExist:
                return GenerateMLPortfolioRecommendation(
                    success=False, 
                    message="Please create your income profile first to get personalized ML recommendations"
                )
            
            # Initialize AI service
            ai_service = AIService()
            
            # Get user profile data
            user_profile = {
                'age': income_profile.age,
                'income_bracket': income_profile.income_bracket,
                'investment_goals': income_profile.investment_goals,
                'risk_tolerance': income_profile.risk_tolerance,
                'investment_horizon': income_profile.investment_horizon
            }
            
            # Get available stocks for analysis
            available_stocks = list(Stock.objects.filter(
                beginner_friendly_score__isnull=False
            ).values('id', 'symbol', 'name', 'beginner_friendly_score', 'current_price'))
            
            # Generate ML-enhanced portfolio recommendation
            if use_advanced_ml and ai_service.ml_service:
                # Use advanced ML optimization
                portfolio_optimization = ai_service.optimize_portfolio_ml(
                    user_profile, available_stocks
                )
                
                # Get ML-enhanced stock scoring
                scored_stocks = ai_service.score_stocks_ml(
                    available_stocks, user_profile
                )
                
                # Get market analysis
                market_analysis = {}
                if include_market_analysis:
                    market_analysis = ai_service.get_enhanced_market_analysis()
                
                # Create enhanced recommendation
                recommendation_data = self._create_ml_enhanced_recommendation(
                    user, user_profile, portfolio_optimization, scored_stocks, market_analysis
                )
                
                # Create stock recommendations
                stock_recommendations = self._create_ml_stock_recommendations(
                    recommendation_data, scored_stocks
                )
                
                # Prepare ML insights
                ml_insights = {
                    'optimization_method': portfolio_optimization.get('method', 'ml_optimization'),
                    'market_regime': market_analysis.get('ml_regime_prediction', {}).get('regime', 'unknown'),
                    'confidence_score': portfolio_optimization.get('risk_score', 0.6),
                    'ml_features_used': len(portfolio_optimization.get('allocation', {})),
                    'stock_analysis_count': len(scored_stocks),
                    'market_indicators_count': len(market_analysis.get('regime_indicators', {}))
                }
                
                return GenerateMLPortfolioRecommendation(
                    success=True,
                    message="ML-enhanced portfolio recommendation generated successfully!",
                    recommendation=recommendation_data,
                    market_analysis=market_analysis,
                    ml_insights=ml_insights
                )
            
            else:
                # Fallback to basic AI recommendation
                return self._generate_basic_recommendation(user, user_profile, available_stocks)
                
        except Exception as e:
            logger.error(f"Error generating ML portfolio recommendation: {e}")
            return GenerateMLPortfolioRecommendation(
                success=False,
                message=f"Error generating ML recommendation: {str(e)}"
            )
    
    def _create_ml_enhanced_recommendation(
        self, 
        user: User, 
        user_profile: Dict[str, Any], 
        portfolio_optimization: Dict[str, Any],
        scored_stocks: List[Dict[str, Any]],
        market_analysis: Dict[str, Any]
    ) -> AIPortfolioRecommendation:
        """Create ML-enhanced portfolio recommendation"""
        
        # Extract optimization results
        allocation = portfolio_optimization.get('allocation', {})
        expected_return = portfolio_optimization.get('expected_return', '8-12%')
        risk_score = portfolio_optimization.get('risk_score', 0.6)
        
        # Determine risk profile based on ML analysis
        if risk_score >= 0.7:
            risk_profile = 'High'
        elif risk_score >= 0.4:
            risk_profile = 'Medium'
        else:
            risk_profile = 'Low'
        
        # Create risk assessment
        risk_assessment = self._create_ml_risk_assessment(
            risk_score, allocation, market_analysis
        )
        
        # Create the recommendation
        recommendation = AIPortfolioRecommendation.objects.create(
            user=user,
            risk_profile=risk_profile,
            portfolio_allocation=allocation,
            expected_portfolio_return=expected_return,
            risk_assessment=risk_assessment
        )
        
        return recommendation
    
    def _create_ml_stock_recommendations(
        self, 
        recommendation: AIPortfolioRecommendation,
        scored_stocks: List[Dict[str, Any]]
    ) -> List[StockRecommendation]:
        """Create ML-enhanced stock recommendations"""
        
        stock_recommendations = []
        
        # Take top stocks based on ML scores
        top_stocks = scored_stocks[:10]  # Top 10 stocks
        
        for i, stock_data in enumerate(top_stocks):
            # Calculate allocation based on ML score and position
            base_allocation = 15 if i < 5 else 10 if i < 8 else 5
            
            # Adjust based on ML score
            ml_score = stock_data.get('ml_score', 5.0)
            if ml_score >= 8.0:
                allocation = base_allocation + 5
            elif ml_score >= 7.0:
                allocation = base_allocation + 2
            else:
                allocation = base_allocation
            
            # Get stock object
            try:
                stock = Stock.objects.get(id=stock_data['id'])
            except Stock.DoesNotExist:
                continue
            
            # Create stock recommendation
            stock_rec = StockRecommendation.objects.create(
                portfolio_recommendation=recommendation,
                stock=stock,
                allocation=allocation,
                reasoning=stock_data.get('ml_reasoning', 'ML-enhanced recommendation'),
                risk_level=self._determine_ml_risk_level(ml_score),
                expected_return=self._calculate_ml_expected_return(ml_score)
            )
            
            stock_recommendations.append(stock_rec)
        
        return stock_recommendations
    
    def _create_ml_risk_assessment(
        self, 
        risk_score: float, 
        allocation: Dict[str, Any], 
        market_analysis: Dict[str, Any]
    ) -> str:
        """Create ML-enhanced risk assessment"""
        
        risk_factors = []
        
        # Portfolio composition risk
        stock_weight = allocation.get('stocks', 60) / 100.0
        if stock_weight > 0.7:
            risk_factors.append("High equity concentration")
        elif stock_weight < 0.3:
            risk_factors.append("Conservative equity allocation")
        else:
            risk_factors.append("Balanced equity allocation")
        
        # Market regime risk
        market_regime = market_analysis.get('ml_regime_prediction', {}).get('regime', 'unknown')
        if market_regime == 'bear_market':
            risk_factors.append("Bear market conditions detected")
        elif market_regime == 'volatile':
            risk_factors.append("High market volatility")
        
        # ML confidence risk
        if risk_score > 0.8:
            risk_level = "High Risk - High Growth Potential"
        elif risk_score > 0.5:
            risk_level = "Moderate Risk - Balanced Growth"
        else:
            risk_level = "Low Risk - Stable Growth"
        
        # Combine all factors
        risk_assessment = f"{risk_level} | ML Risk Score: {risk_score:.2f} | {' | '.join(risk_factors)}"
        
        return risk_assessment
    
    def _determine_ml_risk_level(self, ml_score: float) -> str:
        """Determine risk level based on ML score"""
        if ml_score >= 8.0:
            return 'Low'
        elif ml_score >= 6.5:
            return 'Medium'
        else:
            return 'Medium-High'
    
    def _calculate_ml_expected_return(self, ml_score: float) -> str:
        """Calculate expected return based on ML score"""
        if ml_score >= 8.5:
            return '20-30%'
        elif ml_score >= 7.5:
            return '15-25%'
        elif ml_score >= 6.5:
            return '10-18%'
        else:
            return '8-15%'
    
    def _generate_basic_recommendation(
        self, 
        user: User, 
        user_profile: Dict[str, Any], 
        available_stocks: List[Dict[str, Any]]
    ) -> GenerateMLPortfolioRecommendation:
        """Generate basic recommendation when ML is not available"""
        
        # This would use the existing AI logic
        # For now, return a message
        return GenerateMLPortfolioRecommendation(
            success=False,
            message="ML service not available. Please ensure ML dependencies are installed."
        )

class GetMLMarketAnalysis(graphene.Mutation):
    """
    Get ML-enhanced market analysis
    """
    
    class Arguments:
        include_regime_prediction = graphene.Boolean(default=True)
        include_sector_analysis = graphene.Boolean(default=True)
        include_economic_indicators = graphene.Boolean(default=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    market_analysis = graphene.JSONString()
    ml_predictions = graphene.JSONString()
    
    def mutate(self, info, include_regime_prediction=True, include_sector_analysis=True, include_economic_indicators=True):
        try:
            # Initialize AI service
            ai_service = AIService()
            
            # Get enhanced market analysis
            market_analysis = ai_service.get_enhanced_market_analysis()
            
            # Extract ML predictions
            ml_predictions = {}
            if include_regime_prediction:
                ml_predictions['regime_prediction'] = market_analysis.get('ml_regime_prediction', {})
            
            if include_sector_analysis:
                ml_predictions['sector_analysis'] = market_analysis.get('sector_performance', {})
            
            if include_economic_indicators:
                ml_predictions['economic_indicators'] = market_analysis.get('economic_indicators', {})
            
            return GetMLMarketAnalysis(
                success=True,
                message="ML market analysis generated successfully",
                market_analysis=market_analysis,
                ml_predictions=ml_predictions
            )
            
        except Exception as e:
            logger.error(f"Error getting ML market analysis: {e}")
            return GetMLMarketAnalysis(
                success=False,
                message=f"Error generating ML market analysis: {str(e)}"
            )

class GetMLServiceStatus(graphene.Mutation):
    """
    Get status of ML services
    """
    
    success = graphene.Boolean()
    message = graphene.String()
    service_status = graphene.JSONString()
    
    def mutate(self, info):
        try:
            # Initialize AI service
            ai_service = AIService()
            
            # Get service status
            service_status = ai_service.get_service_status()
            
            return GetMLServiceStatus(
                success=True,
                message="ML service status retrieved successfully",
                service_status=service_status
            )
            
        except Exception as e:
            logger.error(f"Error getting ML service status: {e}")
            return GetMLServiceStatus(
                success=False,
                message=f"Error retrieving ML service status: {str(e)}"
            )
