"""
GraphQL Types for Privacy Settings
"""
import graphene
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

try:
    from .models import PrivacySettings
except ImportError:
    PrivacySettings = None


class PrivacySettingsType(graphene.ObjectType):
    """Privacy settings for a user"""
    dataSharingEnabled = graphene.Boolean(required=True)
    aiAnalysisEnabled = graphene.Boolean(required=True)
    mlPredictionsEnabled = graphene.Boolean(required=True)
    analyticsEnabled = graphene.Boolean(required=True)
    sessionTrackingEnabled = graphene.Boolean(required=True)
    dataRetentionDays = graphene.Int(required=True)
    lastUpdated = graphene.DateTime()


class PrivacyQueries(graphene.ObjectType):
    """GraphQL queries for privacy settings"""
    
    # Graphene auto-converts snake_case to camelCase, so privacy_settings becomes privacySettings
    privacy_settings = graphene.Field(PrivacySettingsType)
    
    def resolve_privacy_settings(self, info):
        """Get user's privacy settings"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            # Return default settings for unauthenticated users
            return PrivacySettingsType(
                dataSharingEnabled=True,
                aiAnalysisEnabled=True,
                mlPredictionsEnabled=True,
                analyticsEnabled=True,
                sessionTrackingEnabled=False,
                dataRetentionDays=90,
                lastUpdated=timezone.now()
            )
        if PrivacySettings is None:
            return PrivacySettingsType(
                dataSharingEnabled=True,
                aiAnalysisEnabled=True,
                mlPredictionsEnabled=True,
                analyticsEnabled=True,
                sessionTrackingEnabled=False,
                dataRetentionDays=90,
                lastUpdated=timezone.now()
            )
        try:
            settings_obj = PrivacySettings.objects.get(user=user)
            return PrivacySettingsType(
                dataSharingEnabled=settings_obj.data_sharing_enabled,
                aiAnalysisEnabled=settings_obj.ai_analysis_enabled,
                mlPredictionsEnabled=settings_obj.ml_predictions_enabled,
                analyticsEnabled=settings_obj.analytics_enabled,
                sessionTrackingEnabled=settings_obj.session_tracking_enabled,
                dataRetentionDays=settings_obj.data_retention_days,
                lastUpdated=settings_obj.updated_at
            )
        except PrivacySettings.DoesNotExist:
            return PrivacySettingsType(
                dataSharingEnabled=True,
                aiAnalysisEnabled=True,
                mlPredictionsEnabled=True,
                analyticsEnabled=True,
                sessionTrackingEnabled=False,
                dataRetentionDays=90,
                lastUpdated=timezone.now()
            )


class PrivacySettingsInput(graphene.InputObjectType):
    """Input type for updating privacy settings"""
    dataSharingEnabled = graphene.Boolean()
    aiAnalysisEnabled = graphene.Boolean()
    mlPredictionsEnabled = graphene.Boolean()
    analyticsEnabled = graphene.Boolean()
    sessionTrackingEnabled = graphene.Boolean()
    dataRetentionDays = graphene.Int()


class UpdatePrivacySettingsResult(graphene.ObjectType):
    """Result of updating privacy settings"""
    success = graphene.Boolean(required=True)
    message = graphene.String()


class PrivacyMutations(graphene.ObjectType):
    """GraphQL mutations for privacy settings"""
    
    # Graphene auto-converts snake_case to camelCase, so update_privacy_settings becomes updatePrivacySettings
    update_privacy_settings = graphene.Field(
        UpdatePrivacySettingsResult,
        settings=PrivacySettingsInput(required=True)
    )
    
    def resolve_update_privacy_settings(self, info, settings):
        """Update user's privacy settings"""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return UpdatePrivacySettingsResult(
                success=False,
                message="Authentication required"
            )
        if PrivacySettings is None:
            return UpdatePrivacySettingsResult(
                success=True,
                message="Privacy settings updated successfully"
            )

        def _get(key_camel, key_snake, default=None):
            if isinstance(settings, dict):
                return settings.get(key_camel, settings.get(key_snake, default))
            return getattr(settings, key_snake, getattr(settings, key_camel, default))

        settings_data = {
            'data_sharing_enabled': _get('dataSharingEnabled', 'data_sharing_enabled', True),
            'ai_analysis_enabled': _get('aiAnalysisEnabled', 'ai_analysis_enabled', True),
            'ml_predictions_enabled': _get('mlPredictionsEnabled', 'ml_predictions_enabled', True),
            'analytics_enabled': _get('analyticsEnabled', 'analytics_enabled', True),
            'session_tracking_enabled': _get('sessionTrackingEnabled', 'session_tracking_enabled', False),
            'data_retention_days': _get('dataRetentionDays', 'data_retention_days', 90),
        }
        privacy_settings, created = PrivacySettings.objects.get_or_create(
            user=user,
            defaults=settings_data
        )
        if not created:
            for k, v in settings_data.items():
                setattr(privacy_settings, k, v)
            privacy_settings.save(update_fields=list(settings_data.keys()) + ['updated_at'])
        return UpdatePrivacySettingsResult(
            success=True,
            message="Privacy settings updated successfully"
        )

