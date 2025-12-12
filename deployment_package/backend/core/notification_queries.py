"""
GraphQL Queries and Mutations for Notifications
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from django.utils import timezone
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class NotificationType(graphene.ObjectType):
    """Notification type"""
    id = graphene.String()
    title = graphene.String()
    message = graphene.String()
    type = graphene.String()
    is_read = graphene.Boolean()
    created_at = graphene.DateTime()
    data = JSONString


class NotificationSettingsType(graphene.ObjectType):
    """Notification settings type"""
    price_alerts = graphene.Boolean()
    order_updates = graphene.Boolean()
    news_updates = graphene.Boolean()
    system_updates = graphene.Boolean()


class NotificationQueries(graphene.ObjectType):
    """Notification queries"""
    
    notifications = graphene.List(NotificationType)
    notification_settings = graphene.Field(NotificationSettingsType)
    
    @login_required
    def resolve_notifications(self, info):
        """Get user's notifications"""
        user = info.context.user
        # This would fetch from actual notification model
        # For now, return empty list
        return []
    
    @login_required
    def resolve_notification_settings(self, info):
        """Get user's notification settings"""
        user = info.context.user
        # This would fetch from actual settings model
        return NotificationSettingsType(
            price_alerts=True,
            order_updates=True,
            news_updates=True,
            system_updates=False
        )


class MarkNotificationRead(graphene.Mutation):
    """Mark a notification as read"""
    
    class Arguments:
        notification_id = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()
    
    @login_required
    def mutate(self, info, notification_id):
        user = info.context.user
        
        # This would update the actual notification
        return MarkNotificationRead(
            success=True,
            message="Notification marked as read"
        )


class MarkAllNotificationsRead(graphene.Mutation):
    """Mark all notifications as read"""
    
    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()
    
    @login_required
    def mutate(self, info):
        user = info.context.user
        
        # This would update all notifications for the user
        return MarkAllNotificationsRead(
            success=True,
            message="All notifications marked as read"
        )


class NotificationMutations(graphene.ObjectType):
    """Notification mutations"""
    mark_notification_read = MarkNotificationRead.Field()
    mark_all_notifications_read = MarkAllNotificationsRead.Field()
    # CamelCase aliases for GraphQL schema
    markNotificationRead = MarkNotificationRead.Field()
    markAllNotificationsRead = MarkAllNotificationsRead.Field()
