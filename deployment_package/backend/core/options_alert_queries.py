"""
GraphQL Queries for Options Alerts
"""
import graphene
from django.contrib.auth import get_user_model
from .options_alert_types import OptionsAlertType, OptionsAlertNotificationType
from .options_alert_models import OptionsAlert, OptionsAlertNotification

User = get_user_model()


class OptionsAlertQueries(graphene.ObjectType):
    """Queries for options alerts"""
    
    options_alerts = graphene.List(
        OptionsAlertType,
        status=graphene.String(required=False),
        symbol=graphene.String(required=False)
    )
    
    options_alert = graphene.Field(
        OptionsAlertType,
        id=graphene.ID(required=True)
    )
    
    def resolve_options_alerts(self, info, status=None, symbol=None):
        """Get user's options alerts"""
        user = info.context.user
        if not user or user.is_anonymous:
            return []
        
        queryset = OptionsAlert.objects.filter(user=user)
        
        if status:
            queryset = queryset.filter(status=status.upper())
        
        if symbol:
            queryset = queryset.filter(symbol=symbol.upper())
        
        return queryset.order_by('-created_at')
    
    def resolve_options_alert(self, info, id):
        """Get a specific options alert"""
        user = info.context.user
        if not user or user.is_anonymous:
            return None
        
        try:
            return OptionsAlert.objects.get(id=id, user=user)
        except OptionsAlert.DoesNotExist:
            return None

