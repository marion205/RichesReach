# core/schema.py
import graphene
import graphql_jwt
from .queries import Query
from .mutations import Mutation, GenerateAIRecommendations
from .types import * # Ensure all types are imported
from .premium_types import PremiumQueries, PremiumMutations
from .ml_mutations import GenerateMLPortfolioRecommendation, GetMLMarketAnalysis, GetMLServiceStatus, GenerateInstitutionalPortfolioRecommendation
from .monitoring_types import MonitoringMutations
from .ml_stock_types import MLStockRecommendationQuery, MLStockRecommendationMutations
from .crypto_graphql import CryptoQuery, CryptoMutation
# Create schema with explicit introspection (legacy)
schema = graphene.Schema(
query=Query, 
mutation=Mutation,
types=[] # Let Graphene auto-discover types
)
# Add premium features to the main schema
class ExtendedQuery(Query, PremiumQueries, MLStockRecommendationQuery, CryptoQuery):
    pass

class ExtendedMutation(Mutation, PremiumMutations, MonitoringMutations, MLStockRecommendationMutations, CryptoMutation):
    # Add ML mutations
    generate_ml_portfolio_recommendation = GenerateMLPortfolioRecommendation.Field()
    get_ml_market_analysis = GetMLMarketAnalysis.Field()
    get_ml_service_status = GetMLServiceStatus.Field()
    generate_institutional_portfolio_recommendation = GenerateInstitutionalPortfolioRecommendation.Field()
    generate_ai_recommendations = GenerateAIRecommendations.Field()
# Create extended schema with premium features
extended_schema = graphene.Schema(
query=ExtendedQuery,
mutation=ExtendedMutation,
types=[]
)
# Use the extended schema as the main schema
schema = extended_schema