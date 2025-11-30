"""
GraphQL Mutations for Options Alerts
"""
import graphene
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .options_alert_types import OptionsAlertType
from .options_alert_models import OptionsAlert

User = get_user_model()
logger = logging.getLogger(__name__)


class CreateOptionsAlert(graphene.Mutation):
    """Create an options alert"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        strike = graphene.Float(required=False)
        expiration = graphene.String(required=False)
        option_type = graphene.String(required=False)  # CALL or PUT
        alert_type = graphene.String(required=True)  # PRICE, IV, EXPIRATION
        target_value = graphene.Float(required=False)  # For PRICE and IV
        direction = graphene.String(required=False)  # 'above' or 'below' for PRICE/IV
    
    success = graphene.Boolean()
    alert = graphene.Field(OptionsAlertType)
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, symbol, alert_type, strike=None, expiration=None, 
               option_type=None, target_value=None, direction=None, **kwargs):
        user = info.context.user
        if not user or user.is_anonymous:
            return CreateOptionsAlert(success=False, error="Authentication required")
        
        try:
            # Validate alert type
            if alert_type.upper() not in ['PRICE', 'IV', 'EXPIRATION']:
                return CreateOptionsAlert(
                    success=False,
                    error="Alert type must be PRICE, IV, or EXPIRATION"
                )
            
            # Validate target value for PRICE and IV alerts
            if alert_type.upper() in ['PRICE', 'IV']:
                if target_value is None:
                    return CreateOptionsAlert(
                        success=False,
                        error=f"Target value required for {alert_type} alerts"
                    )
                if direction and direction.lower() not in ['above', 'below']:
                    return CreateOptionsAlert(
                        success=False,
                        error="Direction must be 'above' or 'below'"
                    )
            
            # Create alert
            alert = OptionsAlert.objects.create(
                user=user,
                symbol=symbol.upper(),
                strike=Decimal(str(strike)) if strike else None,
                expiration=expiration,
                option_type=option_type.upper() if option_type else None,
                alert_type=alert_type.upper(),
                target_value=Decimal(str(target_value)) if target_value else None,
                direction=direction.lower() if direction else None,
                status='ACTIVE'
            )
            
            return CreateOptionsAlert(success=True, alert=alert)
            
        except Exception as e:
            logger.error(f"Error creating options alert: {e}", exc_info=True)
            return CreateOptionsAlert(success=False, error=str(e))


class UpdateOptionsAlert(graphene.Mutation):
    """Update an options alert"""
    
    class Arguments:
        id = graphene.ID(required=True)
        target_value = graphene.Float(required=False)
        direction = graphene.String(required=False)
        status = graphene.String(required=False)
    
    success = graphene.Boolean()
    alert = graphene.Field(OptionsAlertType)
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, id, target_value=None, direction=None, status=None, **kwargs):
        user = info.context.user
        if not user or user.is_anonymous:
            return UpdateOptionsAlert(success=False, error="Authentication required")
        
        try:
            alert = OptionsAlert.objects.get(id=id, user=user)
            
            if target_value is not None:
                alert.target_value = Decimal(str(target_value))
            
            if direction:
                alert.direction = direction.lower()
            
            if status:
                alert.status = status.upper()
            
            alert.save()
            
            return UpdateOptionsAlert(success=True, alert=alert)
            
        except OptionsAlert.DoesNotExist:
            return UpdateOptionsAlert(success=False, error="Alert not found")
        except Exception as e:
            logger.error(f"Error updating options alert: {e}", exc_info=True)
            return UpdateOptionsAlert(success=False, error=str(e))


class DeleteOptionsAlert(graphene.Mutation):
    """Delete an options alert"""
    
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, id):
        user = info.context.user
        if not user or user.is_anonymous:
            return DeleteOptionsAlert(success=False, error="Authentication required")
        
        try:
            alert = OptionsAlert.objects.get(id=id, user=user)
            alert.status = 'CANCELLED'
            alert.save()
            return DeleteOptionsAlert(success=True)
        except OptionsAlert.DoesNotExist:
            return DeleteOptionsAlert(success=False, error="Alert not found")
        except Exception as e:
            logger.error(f"Error deleting options alert: {e}", exc_info=True)
            return DeleteOptionsAlert(success=False, error=str(e))


class OptionsAlertMutations(graphene.ObjectType):
    """Options alert mutations"""
    create_options_alert = CreateOptionsAlert.Field()
    update_options_alert = UpdateOptionsAlert.Field()
    delete_options_alert = DeleteOptionsAlert.Field()

