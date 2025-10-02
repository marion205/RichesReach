"""
Notification GraphQL Schema
GraphQL types and resolvers for notification system
"""
import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Mock notification data for development
MOCK_NOTIFICATIONS = [
    {
        "id": "notif_001",
        "title": "Price Alert: AAPL",
        "message": "Apple Inc. (AAPL) has reached your target price of $150.00",
        "type": "price_alert",
        "isRead": False,
        "createdAt": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "data": {"symbol": "AAPL", "targetPrice": 150.00, "currentPrice": 150.25}
    },
    {
        "id": "notif_002",
        "title": "Order Filled",
        "message": "Your buy order for 10 shares of MSFT has been filled at $300.50",
        "type": "order_filled",
        "isRead": False,
        "createdAt": (datetime.now() - timedelta(hours=1)).isoformat(),
        "data": {"symbol": "MSFT", "quantity": 10, "fillPrice": 300.50, "orderId": "order_123"}
    },
    {
        "id": "notif_003",
        "title": "SBLOC Opportunity",
        "message": "Your portfolio has grown 15% this month! You now have $25,000 in additional borrowing power available.",
        "type": "sbloc_opportunity",
        "isRead": False,
        "createdAt": (datetime.now() - timedelta(hours=3)).isoformat(),
        "data": {"portfolioGrowth": 15.0, "newBorrowingPower": 25000, "previousBorrowingPower": 20000}
    },
    {
        "id": "notif_004",
        "title": "System Update",
        "message": "New features are now available! Check out our enhanced portfolio analytics.",
        "type": "system_update",
        "isRead": True,
        "createdAt": (datetime.now() - timedelta(days=1)).isoformat(),
        "data": {"version": "2.1.0", "features": ["Enhanced Analytics", "SBLOC Integration"]}
    },
    {
        "id": "notif_005",
        "title": "SBLOC Application Status",
        "message": "Your SBLOC application with Chase Bank has been approved! You can now access your line of credit.",
        "type": "sbloc_approved",
        "isRead": False,
        "createdAt": (datetime.now() - timedelta(hours=6)).isoformat(),
        "data": {"bank": "Chase Bank", "approvedAmount": 50000, "applicationId": "sbloc_123"}
    }
]

MOCK_NOTIFICATION_SETTINGS = {
    "priceAlerts": True,
    "orderUpdates": True,
    "newsUpdates": False,
    "systemUpdates": True
}

# GraphQL Types
class NotificationType(graphene.ObjectType):
    id = graphene.String()
    title = graphene.String()
    message = graphene.String()
    type = graphene.String()
    isRead = graphene.Boolean()
    createdAt = graphene.String()
    data = graphene.JSONString()

class NotificationSettingsType(graphene.ObjectType):
    priceAlerts = graphene.Boolean()
    orderUpdates = graphene.Boolean()
    newsUpdates = graphene.Boolean()
    systemUpdates = graphene.Boolean()

class NotificationSettingsInput(graphene.InputObjectType):
    priceAlerts = graphene.Boolean()
    orderUpdates = graphene.Boolean()
    newsUpdates = graphene.Boolean()
    systemUpdates = graphene.Boolean()

class NotificationResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()

class NotificationSettingsResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    settings = graphene.Field(NotificationSettingsType)

# Queries
class NotificationQuery(graphene.ObjectType):
    notifications = graphene.List(NotificationType, description="Get user notifications")
    notificationSettings = graphene.Field(NotificationSettingsType, description="Get notification settings")
    
    def resolve_notifications(self, info):
        """Get user notifications"""
        # In a real implementation, this would query the database
        # For now, return mock data
        return MOCK_NOTIFICATIONS
    
    def resolve_notificationSettings(self, info):
        """Get notification settings"""
        # In a real implementation, this would query the database
        # For now, return mock data
        return NotificationSettingsType(**MOCK_NOTIFICATION_SETTINGS)

# Mutations
class MarkNotificationRead(graphene.Mutation):
    class Arguments:
        notificationId = graphene.String(required=True, description="Notification ID")
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, notificationId):
        """Mark a notification as read"""
        # In a real implementation, this would update the database
        # For now, just return success
        return MarkNotificationRead(
            success=True,
            message=f"Notification {notificationId} marked as read"
        )

class MarkAllNotificationsRead(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info):
        """Mark all notifications as read"""
        # In a real implementation, this would update the database
        # For now, just return success
        return MarkAllNotificationsRead(
            success=True,
            message="All notifications marked as read"
        )

class UpdateNotificationSettings(graphene.Mutation):
    class Arguments:
        settings = NotificationSettingsInput(required=True, description="Notification settings")
    
    success = graphene.Boolean()
    message = graphene.String()
    settings = graphene.Field(NotificationSettingsType)
    
    def mutate(self, info, settings):
        """Update notification settings"""
        # In a real implementation, this would update the database
        # For now, just return success with the updated settings
        return UpdateNotificationSettings(
            success=True,
            message="Notification settings updated",
            settings=NotificationSettingsType(**settings)
        )

class NotificationMutation(graphene.ObjectType):
    markNotificationRead = MarkNotificationRead.Field(description="Mark a notification as read")
    markAllNotificationsRead = MarkAllNotificationsRead.Field(description="Mark all notifications as read")
    updateNotificationSettings = UpdateNotificationSettings.Field(description="Update notification settings")
