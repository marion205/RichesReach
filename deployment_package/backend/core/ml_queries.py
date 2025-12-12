"""
GraphQL Queries for ML System
"""
import graphene
import logging
from .graphql_utils import get_user_from_context
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class OutcomeTrackingType(graphene.ObjectType):
    """Outcome tracking information"""
    totalOutcomes = graphene.Int()
    recentOutcomes = graphene.Int()


class ModelsType(graphene.ObjectType):
    """ML models information"""
    safeModel = graphene.String()
    aggressiveModel = graphene.String()


class BanditStrategyType(graphene.ObjectType):
    """Bandit strategy performance"""
    winRate = graphene.Float()
    confidence = graphene.Float()
    alpha = graphene.Float()
    beta = graphene.Float()


class BanditType(graphene.ObjectType):
    """Bandit performance by strategy"""
    breakout = graphene.Field(BanditStrategyType)
    meanReversion = graphene.Field(BanditStrategyType)
    momentum = graphene.Field(BanditStrategyType)
    etfRotation = graphene.Field(BanditStrategyType)


class LastTrainingType(graphene.ObjectType):
    """Last training timestamps"""
    SAFE = graphene.String()
    AGGRESSIVE = graphene.String()


class MLSystemStatusType(graphene.ObjectType):
    """ML system status"""
    outcomeTracking = graphene.Field(OutcomeTrackingType)
    models = graphene.Field(ModelsType)
    bandit = graphene.Field(BanditType)
    lastTraining = graphene.Field(LastTrainingType)
    mlAvailable = graphene.Boolean()


class MLQueries(graphene.ObjectType):
    """ML system queries"""
    
    mlSystemStatus = graphene.Field(
        MLSystemStatusType,
        description="Get ML system status"
    )
    
    def resolve_mlSystemStatus(self, info):
        """Get ML system status"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return None
            
            # In production, query from ML service
            return MLSystemStatusType(
                outcomeTracking=OutcomeTrackingType(
                    totalOutcomes=1000,
                    recentOutcomes=50
                ),
                models=ModelsType(
                    safeModel="model-safe-v1",
                    aggressiveModel="model-aggressive-v1"
                ),
                bandit=BanditType(
                    breakout=BanditStrategyType(
                        winRate=0.65,
                        confidence=0.8,
                        alpha=10.0,
                        beta=5.0
                    ),
                    meanReversion=BanditStrategyType(
                        winRate=0.60,
                        confidence=0.75,
                        alpha=8.0,
                        beta=5.0
                    ),
                    momentum=BanditStrategyType(
                        winRate=0.70,
                        confidence=0.85,
                        alpha=12.0,
                        beta=5.0
                    ),
                    etfRotation=BanditStrategyType(
                        winRate=0.55,
                        confidence=0.70,
                        alpha=7.0,
                        beta=5.0
                    )
                ),
                lastTraining=LastTrainingType(
                    SAFE="2024-01-01T00:00:00Z",
                    AGGRESSIVE="2024-01-01T00:00:00Z"
                ),
                mlAvailable=True
            )
        except Exception as e:
            logger.error(f"Error resolving ML system status: {e}", exc_info=True)
            return None

