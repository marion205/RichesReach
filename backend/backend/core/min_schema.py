import graphene
# import graphql_jwt  # Removed - using SimpleJWT
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "email", "username")
    
    # Add computed fields for the mobile app
    name = graphene.String()
    hasPremiumAccess = graphene.Boolean()
    subscriptionTier = graphene.String()
    
    def resolve_name(self, info):
        return getattr(self, 'name', self.username or self.email.split('@')[0])
    
    def resolve_hasPremiumAccess(self, info):
        return True  # Mock premium access
    
    def resolve_subscriptionTier(self, info):
        return "PREMIUM"  # Mock subscription tier

# class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):  # Disabled - using SimpleJWT
    user = graphene.Field(UserType)
    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)

class Query(graphene.ObjectType):
    ping = graphene.String(default_value="pong")
    me = graphene.Field(UserType)
    
    def resolve_me(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

class Mutation(graphene.ObjectType):
    # token_auth = ObtainJSONWebToken.Field()  # Disabled - using SimpleJWT
    # verify_token = graphql_jwt.Verify.Field()  # Disabled - using SimpleJWT
    # refresh_token = graphql_jwt.Refresh.Field()  # Disabled - using SimpleJWT
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)