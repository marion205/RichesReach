"""
GraphQL Types for Options Alerts
"""
import graphene
from django.utils import timezone


class OptionsAlertType(graphene.ObjectType):
    """Options alert GraphQL type"""
    id = graphene.ID()
    symbol = graphene.String()
    strike = graphene.Float()
    expiration = graphene.String()
    optionType = graphene.String()
    alertType = graphene.String()
    targetValue = graphene.Float()
    direction = graphene.String()
    status = graphene.String()
    triggeredAt = graphene.String()
    notificationSent = graphene.Boolean()
    createdAt = graphene.String()
    updatedAt = graphene.String()
    
    def resolve_id(self, info):
        return self.id
    
    def resolve_symbol(self, info):
        return self.symbol
    
    def resolve_strike(self, info):
        return float(self.strike) if self.strike else None
    
    def resolve_expiration(self, info):
        return self.expiration
    
    def resolve_optionType(self, info):
        return self.option_type
    
    def resolve_alertType(self, info):
        return self.alert_type
    
    def resolve_targetValue(self, info):
        return float(self.target_value) if self.target_value else None
    
    def resolve_direction(self, info):
        return self.direction
    
    def resolve_status(self, info):
        return self.status
    
    def resolve_triggeredAt(self, info):
        return self.triggered_at.isoformat() if self.triggered_at else None
    
    def resolve_notificationSent(self, info):
        return self.notification_sent
    
    def resolve_createdAt(self, info):
        return self.created_at.isoformat() if self.created_at else None
    
    def resolve_updatedAt(self, info):
        return self.updated_at.isoformat() if self.updated_at else None


class OptionsAlertNotificationType(graphene.ObjectType):
    """Options alert notification GraphQL type"""
    id = graphene.ID()
    notificationType = graphene.String()
    sentAt = graphene.String()
    message = graphene.String()
    
    def resolve_id(self, info):
        return self.id
    
    def resolve_notificationType(self, info):
        return self.notification_type
    
    def resolve_sentAt(self, info):
        return self.sent_at.isoformat() if self.sent_at else None
    
    def resolve_message(self, info):
        return self.message
