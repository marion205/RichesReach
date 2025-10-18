"""
SimpleJWT GraphQL Mutations
"""
import graphene
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from graphql import GraphQLError

User = get_user_model()

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
        data = {"username": email, "password": password}
        serializer = TokenObtainPairSerializer(data=data)
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
