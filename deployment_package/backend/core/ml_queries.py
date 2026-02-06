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
        """Get ML system status with real bandit data"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return None

            # Get real bandit arm data
            from .bandit_service import BanditService
            bandit = BanditService()
            arms_status = bandit.get_all_arms_status()
            arms_by_slug = {a['strategy']: a for a in arms_status}

            def _arm_type(slug):
                a = arms_by_slug.get(slug, {})
                return BanditStrategyType(
                    winRate=a.get('win_rate', 0.5),
                    confidence=a.get('weight', 0.25),
                    alpha=a.get('alpha', 1.0),
                    beta=a.get('beta', 1.0),
                )

            # Get real outcome counts
            from .signal_performance_models import SignalPerformance, UserFill
            from django.utils import timezone
            from datetime import timedelta
            total_outcomes = SignalPerformance.objects.count()
            recent_outcomes = UserFill.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()

            return MLSystemStatusType(
                outcomeTracking=OutcomeTrackingType(
                    totalOutcomes=total_outcomes,
                    recentOutcomes=recent_outcomes,
                ),
                models=ModelsType(
                    safeModel="model-safe-v1",
                    aggressiveModel="model-aggressive-v1",
                ),
                bandit=BanditType(
                    breakout=_arm_type('breakout'),
                    meanReversion=_arm_type('mean_reversion'),
                    momentum=_arm_type('momentum'),
                    etfRotation=_arm_type('etf_rotation'),
                ),
                lastTraining=LastTrainingType(
                    SAFE="auto-retrain-6h",
                    AGGRESSIVE="auto-retrain-6h",
                ),
                mlAvailable=True,
            )
        except Exception as e:
            logger.error(f"Error resolving ML system status: {e}", exc_info=True)
            return None

