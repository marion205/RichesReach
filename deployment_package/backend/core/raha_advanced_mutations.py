"""
RAHA Advanced GraphQL Mutations
Mutations for custom strategies, ML training, and strategy blends
"""
import graphene
import logging
import json
from typing import Dict, Any, Optional
from .raha_types import StrategyType, StrategyVersionType
from .raha_models import Strategy, StrategyVersion, StrategyBlend, MLModel
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()
logger = logging.getLogger(__name__)


class CreateCustomStrategy(graphene.Mutation):
    """Create a custom trading strategy"""
    
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        category = graphene.String(required=True)
        market_type = graphene.String(required=True)
        timeframe_supported = graphene.List(graphene.String, required=False)
        custom_logic = graphene.JSONString(required=True)
        config_schema = graphene.JSONString(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    strategy = graphene.Field(StrategyType)
    
    def mutate(self, info, name, description, category, market_type, custom_logic, timeframe_supported=None, config_schema=None):
        user = info.context.user
        if not user.is_authenticated:
            return CreateCustomStrategy(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Create strategy
            strategy = Strategy.objects.create(
                name=name,
                slug=slugify(name),
                description=description,
                category=category,
                market_type=market_type,
                timeframe_supported=timeframe_supported or ['5m', '15m', '1h'],
                enabled=True,
                is_custom=True,
                created_by=user
            )
            
            # Create default version with custom logic
            strategy_version = StrategyVersion.objects.create(
                strategy=strategy,
                version=1,
                is_default=True,
                config_schema=config_schema or {},
                custom_logic=custom_logic
            )
            
            return CreateCustomStrategy(
                success=True,
                message=f"Custom strategy '{name}' created successfully",
                strategy=strategy
            )
        except Exception as e:
            logger.error(f"Error creating custom strategy: {e}", exc_info=True)
            return CreateCustomStrategy(
                success=False,
                message=f"Error: {str(e)}"
            )


class TrainMlModel(graphene.Mutation):
    """Train a custom ML model on user's trading history"""
    
    class Arguments:
        strategy_version_id = graphene.ID(required=False)
        symbol = graphene.String(required=False)
        lookback_days = graphene.Int(required=True)
        model_type = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    training_samples = graphene.Int()
    metrics = graphene.JSONString()
    model_type = graphene.String()
    trained_at = graphene.DateTime()
    
    def mutate(self, info, lookback_days, model_type, strategy_version_id=None, symbol=None):
        user = info.context.user
        if not user.is_authenticated:
            return TrainMlModel(
                success=False,
                message="Authentication required"
            )
        
        try:
            from .ml_training_service import MLTrainingService
            
            training_service = MLTrainingService()
            result = training_service.train_model(
                user=user,
                strategy_version_id=strategy_version_id,
                symbol=symbol,
                lookback_days=lookback_days,
                model_type=model_type
            )
            
            if result.get('success'):
                # Save model to database
                MLModel.objects.create(
                    user=user,
                    strategy_version_id=strategy_version_id,
                    symbol=symbol,
                    model_type=model_type,
                    lookback_days=lookback_days,
                    training_samples=result.get('samples', 0),
                    metrics=result.get('metrics', {}),
                    model_data=result.get('model_data'),
                    is_active=True
                )
            
            return TrainMlModel(
                success=result.get('success', False),
                message=result.get('message', ''),
                training_samples=result.get('samples', 0),
                metrics=result.get('metrics', {}),
                model_type=model_type,
                trained_at=timezone.now() if result.get('success') else None
            )
        except Exception as e:
            logger.error(f"Error training ML model: {e}", exc_info=True)
            return TrainMlModel(
                success=False,
                message=f"Error: {str(e)}"
            )


class StrategyBlendComponentInput(graphene.InputObjectType):
    """Input for strategy blend component"""
    strategy_version_id = graphene.ID(required=True)
    weight = graphene.Float(required=True)


class StrategyBlendType(graphene.ObjectType):
    """GraphQL type for Strategy Blend"""
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    components = graphene.List(
        graphene.JSONString,
        description="List of {strategyVersionId, weight} objects"
    )
    is_active = graphene.Boolean()
    is_default = graphene.Boolean()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


class CreateStrategyBlend(graphene.Mutation):
    """Create a strategy blend"""
    
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        components = graphene.List(StrategyBlendComponentInput, required=True)
        is_default = graphene.Boolean(required=False, default_value=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    strategy_blend = graphene.Field(StrategyBlendType)
    
    def mutate(self, info, name, components, description=None, is_default=False):
        user = info.context.user
        if not user.is_authenticated:
            return CreateStrategyBlend(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Normalize weights
            total_weight = sum(c.weight for c in components)
            if total_weight == 0:
                return CreateStrategyBlend(
                    success=False,
                    message="Total weight must be greater than 0"
                )
            
            normalized_components = [
                {
                    'strategy_version_id': str(c.strategy_version_id),
                    'weight': c.weight / total_weight
                }
                for c in components
            ]
            
            # If this is set as default, unset other defaults
            if is_default:
                StrategyBlend.objects.filter(user=user, is_default=True).update(is_default=False)
            
            blend = StrategyBlend.objects.create(
                user=user,
                name=name,
                description=description or '',
                components=normalized_components,
                is_active=True,
                is_default=is_default
            )
            
            return CreateStrategyBlend(
                success=True,
                message=f"Strategy blend '{name}' created successfully",
                strategy_blend=blend
            )
        except Exception as e:
            logger.error(f"Error creating strategy blend: {e}", exc_info=True)
            return CreateStrategyBlend(
                success=False,
                message=f"Error: {str(e)}"
            )


class UpdateStrategyBlend(graphene.Mutation):
    """Update a strategy blend"""
    
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        description = graphene.String(required=False)
        components = graphene.List(StrategyBlendComponentInput, required=False)
        is_active = graphene.Boolean(required=False)
        is_default = graphene.Boolean(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    strategy_blend = graphene.Field(StrategyBlendType)
    
    def mutate(self, info, id, name=None, description=None, components=None, is_active=None, is_default=None):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateStrategyBlend(
                success=False,
                message="Authentication required"
            )
        
        try:
            blend = StrategyBlend.objects.get(id=id, user=user)
            
            if name is not None:
                blend.name = name
            if description is not None:
                blend.description = description
            if components is not None:
                # Normalize weights
                total_weight = sum(c.weight for c in components)
                if total_weight == 0:
                    return UpdateStrategyBlend(
                        success=False,
                        message="Total weight must be greater than 0"
                    )
                
                blend.components = [
                    {
                        'strategy_version_id': str(c.strategy_version_id),
                        'weight': c.weight / total_weight
                    }
                    for c in components
                ]
            if is_active is not None:
                blend.is_active = is_active
            if is_default is not None:
                if is_default:
                    StrategyBlend.objects.filter(user=user, is_default=True).exclude(id=id).update(is_default=False)
                blend.is_default = is_default
            
            blend.save()
            
            return UpdateStrategyBlend(
                success=True,
                message="Strategy blend updated successfully",
                strategy_blend=blend
            )
        except StrategyBlend.DoesNotExist:
            return UpdateStrategyBlend(
                success=False,
                message="Strategy blend not found"
            )
        except Exception as e:
            logger.error(f"Error updating strategy blend: {e}", exc_info=True)
            return UpdateStrategyBlend(
                success=False,
                message=f"Error: {str(e)}"
            )


class DeleteStrategyBlend(graphene.Mutation):
    """Delete a strategy blend"""
    
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return DeleteStrategyBlend(
                success=False,
                message="Authentication required"
            )
        
        try:
            blend = StrategyBlend.objects.get(id=id, user=user)
            blend.delete()
            
            return DeleteStrategyBlend(
                success=True,
                message="Strategy blend deleted successfully"
            )
        except StrategyBlend.DoesNotExist:
            return DeleteStrategyBlend(
                success=False,
                message="Strategy blend not found"
            )
        except Exception as e:
            logger.error(f"Error deleting strategy blend: {e}", exc_info=True)
            return DeleteStrategyBlend(
                success=False,
                message=f"Error: {str(e)}"
            )


class RAHAAdvancedMutations(graphene.ObjectType):
    """RAHA Advanced GraphQL mutations"""
    create_custom_strategy = CreateCustomStrategy.Field()
    train_ml_model = TrainMlModel.Field()
    create_strategy_blend = CreateStrategyBlend.Field()
    update_strategy_blend = UpdateStrategyBlend.Field()
    delete_strategy_blend = DeleteStrategyBlend.Field()

