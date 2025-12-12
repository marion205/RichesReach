"""
GraphQL Mutations for News Preferences
"""
import graphene
import logging
from .graphql_utils import get_user_from_context

logger = logging.getLogger(__name__)


class NewsPreferencesInputType(graphene.InputObjectType):
    """News preferences input"""
    breakingNews = graphene.Boolean()
    marketNews = graphene.Boolean()
    companyNews = graphene.Boolean()
    earningsNews = graphene.Boolean()
    cryptoNews = graphene.Boolean()
    personalStocks = graphene.Boolean()
    quietHours = graphene.Boolean()
    quietStart = graphene.String()
    quietEnd = graphene.String()
    frequency = graphene.String()


class NewsPreferencesType(graphene.ObjectType):
    """News preferences"""
    breakingNews = graphene.Boolean()
    marketNews = graphene.Boolean()
    companyNews = graphene.Boolean()
    earningsNews = graphene.Boolean()
    cryptoNews = graphene.Boolean()
    personalStocks = graphene.Boolean()
    quietHours = graphene.Boolean()
    quietStart = graphene.String()
    quietEnd = graphene.String()
    frequency = graphene.String()


class GetNewsPreferencesResultType(graphene.ObjectType):
    """Result of getting news preferences"""
    success = graphene.Boolean()
    error = graphene.String()
    preferences = graphene.Field(NewsPreferencesType)


class GetNewsPreferences(graphene.Mutation):
    """Get news preferences (mutation for consistency with update)"""
    Output = GetNewsPreferencesResultType
    
    def mutate(self, info):
        """Get news preferences"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return GetNewsPreferencesResultType(
                    success=False,
                    error="Authentication required"
                )
            
            # In production, query from database
            return GetNewsPreferencesResultType(
                success=True,
                preferences=NewsPreferencesType(
                    breakingNews=True,
                    marketNews=True,
                    companyNews=True,
                    earningsNews=False,
                    cryptoNews=False,
                    personalStocks=True,
                    quietHours=False,
                    quietStart="22:00",
                    quietEnd="08:00",
                    frequency="immediate"
                )
            )
        except Exception as e:
            logger.error(f"Error getting news preferences: {e}", exc_info=True)
            return GetNewsPreferencesResultType(
                success=False,
                error=str(e)
            )


class UpdateNewsPreferencesResultType(graphene.ObjectType):
    """Result of updating news preferences"""
    success = graphene.Boolean()
    error = graphene.String()
    preferences = graphene.Field(NewsPreferencesType)


class UpdateNewsPreferences(graphene.Mutation):
    """Update news preferences"""
    class Arguments:
        preferences = NewsPreferencesInputType(required=True)
    
    Output = UpdateNewsPreferencesResultType
    
    def mutate(self, info, preferences):
        """Update news preferences"""
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                return UpdateNewsPreferencesResultType(
                    success=False,
                    error="Authentication required"
                )
            
            # In production, save to database
            prefs = NewsPreferencesType(
                breakingNews=preferences.get("breakingNews", True),
                marketNews=preferences.get("marketNews", True),
                companyNews=preferences.get("companyNews", True),
                earningsNews=preferences.get("earningsNews", False),
                cryptoNews=preferences.get("cryptoNews", False),
                personalStocks=preferences.get("personalStocks", True),
                quietHours=preferences.get("quietHours", False),
                quietStart=preferences.get("quietStart", "22:00"),
                quietEnd=preferences.get("quietEnd", "08:00"),
                frequency=preferences.get("frequency", "immediate")
            )
            
            return UpdateNewsPreferencesResultType(
                success=True,
                preferences=prefs
            )
        except Exception as e:
            logger.error(f"Error updating news preferences: {e}", exc_info=True)
            return UpdateNewsPreferencesResultType(
                success=False,
                error=str(e)
            )


class NewsMutations(graphene.ObjectType):
    """News mutations"""
    getNewsPreferences = GetNewsPreferences.Field()
    updateNewsPreferences = UpdateNewsPreferences.Field()

