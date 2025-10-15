"""
GraphQL Types for ML Stock Recommendations
"""

import graphene
from graphene_django import DjangoObjectType
from .models import Stock
from .ml_stock_recommender import ml_recommender, StockRecommendation

class MLStockRecommendationType(graphene.ObjectType):
    """ML Stock Recommendation Type"""
    stock = graphene.Field('core.types.StockType')
    confidence_score = graphene.Float()
    risk_level = graphene.String()
    expected_return = graphene.Float()
    reasoning = graphene.String()
    ml_insights = graphene.JSONString()

class MLStockRecommendationQuery(graphene.ObjectType):
    """ML Stock Recommendation Queries"""
    
    get_ml_stock_recommendations = graphene.List(
        MLStockRecommendationType,
        limit=graphene.Int(default_value=10),
        description="Get AI/ML stock recommendations based on user profile"
    )
    
    get_beginner_friendly_stocks = graphene.List(
        MLStockRecommendationType,
        limit=graphene.Int(default_value=10),
        description="Get stocks specifically filtered for beginner investors"
    )
    
    get_ml_service_status = graphene.JSONString(
        description="Get ML service status and health"
    )
    
    def resolve_get_ml_stock_recommendations(self, info, limit):
        """Resolve ML stock recommendations"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            recommendations = ml_recommender.generate_ml_recommendations(user, limit)
            return recommendations
        except Exception as e:
            print(f"Error resolving ML recommendations: {e}")
            return []
    
    def resolve_get_beginner_friendly_stocks(self, info, limit):
        """Resolve beginner-friendly stocks"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            recommendations = ml_recommender.get_beginner_friendly_stocks(user, limit)
            return recommendations
        except Exception as e:
            print(f"Error resolving beginner-friendly stocks: {e}")
            return []
    
    def resolve_get_ml_service_status(self, info):
        """Resolve ML service status"""
        try:
            return ml_recommender.get_ml_service_status()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}

class GenerateMLStockRecommendation(graphene.Mutation):
    """Generate ML Stock Recommendations Mutation"""
    
    class Arguments:
        limit = graphene.Int(default_value=10)
    
    success = graphene.Boolean()
    recommendations = graphene.List(MLStockRecommendationType)
    error = graphene.String()
    
    def mutate(self, info, limit):
        user = info.context.user
        if not user.is_authenticated:
            return GenerateMLStockRecommendation(
                success=False,
                recommendations=[],
                error="Authentication required"
            )
        
        try:
            recommendations = ml_recommender.generate_ml_recommendations(user, limit)
            return GenerateMLStockRecommendation(
                success=True,
                recommendations=recommendations,
                error=None
            )
        except Exception as e:
            return GenerateMLStockRecommendation(
                success=False,
                recommendations=[],
                error=str(e)
            )

class MLStockRecommendationMutations(graphene.ObjectType):
    """ML Stock Recommendation Mutations"""
    generate_ml_stock_recommendation = GenerateMLStockRecommendation.Field()
