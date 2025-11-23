"""
GraphQL Types for Privacy Settings
"""
import graphene
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


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
        
        # TODO: Replace with actual database model when PrivacySettings model is created
        # For now, return default settings
        # In the future, this would be:
        # try:
        #     settings = PrivacySettings.objects.get(user=user)
        #     return PrivacySettingsType(
        #         dataSharingEnabled=settings.data_sharing_enabled,
        #         aiAnalysisEnabled=settings.ai_analysis_enabled,
        #         mlPredictionsEnabled=settings.ml_predictions_enabled,
        #         analyticsEnabled=settings.analytics_enabled,
        #         sessionTrackingEnabled=settings.session_tracking_enabled,
        #         dataRetentionDays=settings.data_retention_days,
        #         lastUpdated=settings.updated_at
        #     )
        # except PrivacySettings.DoesNotExist:
        #     return default settings
        
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
        
        # TODO: Replace with actual database update when PrivacySettings model is created
        # For now, just return success
        # In the future, this would be:
        # privacy_settings, created = PrivacySettings.objects.get_or_create(user=user)
        # privacy_settings.data_sharing_enabled = settings.get('dataSharingEnabled', privacy_settings.data_sharing_enabled)
        # privacy_settings.ai_analysis_enabled = settings.get('aiAnalysisEnabled', privacy_settings.ai_analysis_enabled)
        # privacy_settings.ml_predictions_enabled = settings.get('mlPredictionsEnabled', privacy_settings.ml_predictions_enabled)
        # privacy_settings.analytics_enabled = settings.get('analyticsEnabled', privacy_settings.analytics_enabled)
        # privacy_settings.session_tracking_enabled = settings.get('sessionTrackingEnabled', privacy_settings.session_tracking_enabled)
        # privacy_settings.data_retention_days = settings.get('dataRetentionDays', privacy_settings.data_retention_days)
        # privacy_settings.updated_at = timezone.now()
        # privacy_settings.save()
        
        return UpdatePrivacySettingsResult(
            success=True,
            message="Privacy settings updated successfully"
        )

