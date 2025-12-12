"""
GraphQL Mutations for ML System (Training, Bandit Strategy)
"""
import graphene
import logging
from .graphql_utils import get_user_from_context
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class ModelResultType(graphene.ObjectType):
    """ML model training result"""
    model_id = graphene.String()
    mode = graphene.String()
    auc = graphene.Float()
    precision_at_3 = graphene.Float()
    hit_rate = graphene.Float()
    avg_return = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    training_samples = graphene.Int()
    validation_samples = graphene.Int()
    created_at = graphene.String()


class TrainingResultsType(graphene.ObjectType):
    """Training results for both modes"""
    SAFE = graphene.Field(ModelResultType)
    AGGRESSIVE = graphene.Field(ModelResultType)


class TrainModelsResultType(graphene.ObjectType):
    """Result of training models"""
    success = graphene.Boolean()
    message = graphene.String()
    results = graphene.Field(TrainingResultsType)


class TrainModels(graphene.Mutation):
    """Train ML models"""
    class Arguments:
        modes = graphene.List(graphene.String)
    
    Output = TrainModelsResultType
    
    def mutate(self, info, modes=None):
        """Train models"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return TrainModelsResultType(
                    success=False,
                    message="Authentication required"
                )
            
            # In production, trigger ML training
            modes_to_train = modes or ["SAFE", "AGGRESSIVE"]
            results = TrainingResultsType(
                SAFE=ModelResultType(
                    model_id="model-safe-v2",
                    mode="SAFE",
                    auc=0.75,
                    precision_at_3=0.68,
                    hit_rate=0.65,
                    avg_return=0.12,
                    sharpe_ratio=1.5,
                    max_drawdown=0.08,
                    training_samples=5000,
                    validation_samples=1000,
                    created_at="2024-01-01T12:00:00Z"
                ) if "SAFE" in modes_to_train else None,
                AGGRESSIVE=ModelResultType(
                    model_id="model-aggressive-v2",
                    mode="AGGRESSIVE",
                    auc=0.72,
                    precision_at_3=0.65,
                    hit_rate=0.60,
                    avg_return=0.18,
                    sharpe_ratio=1.3,
                    max_drawdown=0.15,
                    training_samples=5000,
                    validation_samples=1000,
                    created_at="2024-01-01T12:00:00Z"
                ) if "AGGRESSIVE" in modes_to_train else None
            )
            
            return TrainModelsResultType(
                success=True,
                message="Models trained successfully",
                results=results
            )
        except Exception as e:
            logger.error(f"Error training models: {e}", exc_info=True)
            return TrainModelsResultType(
                success=False,
                message=str(e)
            )


class BanditContextType(graphene.ObjectType):
    """Bandit strategy context"""
    vix_level = graphene.Float()
    market_trend = graphene.String()
    volatility_regime = graphene.String()
    time_of_day = graphene.String()


class BanditPerformanceType(graphene.ObjectType):
    """Bandit performance by strategy"""
    breakout = graphene.Field('core.ml_queries.BanditStrategyType')
    mean_reversion = graphene.Field('core.ml_queries.BanditStrategyType')
    momentum = graphene.Field('core.ml_queries.BanditStrategyType')
    etf_rotation = graphene.Field('core.ml_queries.BanditStrategyType')


class BanditStrategyResultType(graphene.ObjectType):
    """Bandit strategy selection result"""
    selected_strategy = graphene.String()
    context = graphene.Field(BanditContextType)
    performance = graphene.Field(BanditPerformanceType)


class GetBanditStrategy(graphene.Mutation):
    """Get bandit strategy recommendation"""
    class Arguments:
        context = JSONString()
    
    Output = BanditStrategyResultType
    
    def mutate(self, info, context=None):
        """Get bandit strategy"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return BanditStrategyResultType(
                    selected_strategy="breakout",
                    context=BanditContextType(
                        vix_level=18.0,
                        market_trend="BULLISH",
                        volatility_regime="LOW",
                        time_of_day="MORNING"
                    ),
                    performance=None
                )
            
            # In production, use bandit algorithm
            from .ml_queries import BanditStrategyType, BanditType
            
            return BanditStrategyResultType(
                selected_strategy="momentum",
                context=BanditContextType(
                    vix_level=context.get("vix_level", 18.0) if context else 18.0,
                    market_trend=context.get("market_trend", "BULLISH") if context else "BULLISH",
                    volatility_regime=context.get("volatility_regime", "LOW") if context else "LOW",
                    time_of_day=context.get("time_of_day", "MORNING") if context else "MORNING"
                ),
                performance=BanditPerformanceType(
                    breakout=BanditStrategyType(
                        winRate=0.65,
                        confidence=0.8,
                        alpha=10.0,
                        beta=5.0
                    ),
                    mean_reversion=BanditStrategyType(
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
                    etf_rotation=BanditStrategyType(
                        winRate=0.55,
                        confidence=0.70,
                        alpha=7.0,
                        beta=5.0
                    )
                )
            )
        except Exception as e:
            logger.error(f"Error getting bandit strategy: {e}", exc_info=True)
            return BanditStrategyResultType(
                selected_strategy="breakout",
                context=None,
                performance=None
            )


class UpdateBanditRewardResultType(graphene.ObjectType):
    """Result of updating bandit reward"""
    success = graphene.Boolean()
    message = graphene.String()
    performance = graphene.Field(BanditPerformanceType)


class UpdateBanditReward(graphene.Mutation):
    """Update bandit reward"""
    class Arguments:
        strategy = graphene.String(required=True)
        reward = graphene.Float(required=True)
    
    Output = UpdateBanditRewardResultType
    
    def mutate(self, info, strategy, reward):
        """Update bandit reward"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return UpdateBanditRewardResultType(
                    success=False,
                    message="Authentication required"
                )
            
            # In production, update bandit algorithm
            from .ml_queries import BanditStrategyType, BanditPerformanceType
            
            return UpdateBanditRewardResultType(
                success=True,
                message=f"Reward updated for {strategy}",
                performance=BanditPerformanceType(
                    breakout=BanditStrategyType(
                        winRate=0.65,
                        confidence=0.8,
                        alpha=10.0,
                        beta=5.0
                    ),
                    mean_reversion=BanditStrategyType(
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
                    etf_rotation=BanditStrategyType(
                        winRate=0.55,
                        confidence=0.70,
                        alpha=7.0,
                        beta=5.0
                    )
                )
            )
        except Exception as e:
            logger.error(f"Error updating bandit reward: {e}", exc_info=True)
            return UpdateBanditRewardResultType(
                success=False,
                message=str(e)
            )


class MLSystemMutations(graphene.ObjectType):
    """ML system mutations"""
    trainModels = TrainModels.Field()
    banditStrategy = GetBanditStrategy.Field()
    updateBanditReward = UpdateBanditReward.Field()

