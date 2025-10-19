# Test mutations file
import graphene
from graphql import GraphQLError

class GenerateAIRecommendations(graphene.Mutation):
    """Generate AI portfolio recommendations based on user's income profile using ML/AI"""
    success = graphene.Boolean()
    message = graphene.String()
    recommendations = graphene.List('core.types.AIPortfolioRecommendationType')

    def mutate(self, info):
        print("DEBUG: GenerateAIRecommendations mutation called!")
        
        # For now, return a simple success response to test if the mutation works
        return GenerateAIRecommendations(
            success=True,
            message="AI recommendations generated successfully (test mode)",
            recommendations=[]
        )
