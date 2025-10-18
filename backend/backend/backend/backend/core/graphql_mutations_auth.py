"""
SimpleJWT GraphQL Mutations
"""
import graphene
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from graphql import GraphQLError

User = get_user_model()

class EmailTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    """
    If USERNAME_FIELD='email', accept 'email' and map it to 'username'
    so we don't have to pass 'username' from the client.
    """
    def validate(self, attrs):
        if "email" in attrs and "username" not in attrs:
            attrs["username"] = attrs["email"]
        return super().validate(attrs)

class TokenPairType(graphene.ObjectType):
    access = graphene.String(required=True)
    refresh = graphene.String(required=True)

class ObtainTokenPair(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = TokenPairType

    @classmethod
    def mutate(cls, root, info, email, password):
        data = {"email": email, "password": password}
        serializer = EmailTokenObtainPairSerializer(data=data)
        if serializer.is_valid():
            tokens = serializer.validated_data
            return TokenPairType(access=tokens["access"], refresh=tokens["refresh"])
        raise GraphQLError("Invalid credentials.")

class RefreshToken(graphene.Mutation):
    class Arguments:
        refresh = graphene.String(required=True)

    access = graphene.String(required=True)
    refresh = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, refresh):
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        if serializer.is_valid():
            data = serializer.validated_data
            # If ROTATE_REFRESH_TOKENS=True, new refresh may be present
            new_access = data["access"]
            new_refresh = data.get("refresh", refresh)
            return RefreshToken(access=new_access, refresh=new_refresh)
        raise GraphQLError("Invalid refresh token.")

class VerifyToken(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, token):
        serializer = TokenVerifySerializer(data={"token": token})
        if serializer.is_valid():
            return VerifyToken(ok=True)
        raise GraphQLError("Token invalid or expired.")
