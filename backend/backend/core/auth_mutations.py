"""
Authentication Mutations for RichesReach
Provides user registration and login mutations
"""
import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenObtainPairSerializer,
)
from graphql import GraphQLError
import logging

logger = logging.getLogger(__name__)

class EmailTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    """
    If USERNAME_FIELD='email', accept 'email' and map it to 'username'
    so we don't have to pass 'username' from the client.
    """
    def validate(self, attrs):
        if "email" in attrs and "username" not in attrs:
            attrs["username"] = attrs["email"]
        return super().validate(attrs)

class UserType(graphene.ObjectType):
    """User type for GraphQL responses"""
    id = graphene.ID()
    email = graphene.String()
    username = graphene.String()
    firstName = graphene.String()
    lastName = graphene.String()
    name = graphene.String()
    isActive = graphene.Boolean()
    dateJoined = graphene.DateTime()

class TokenType(graphene.ObjectType):
    """Token type for authentication responses"""
    access = graphene.String(required=True)
    refresh = graphene.String(required=True)

class RegisterUserResult(graphene.ObjectType):
    """Result type for user registration"""
    success = graphene.Boolean(required=True)
    message = graphene.String()
    user = graphene.Field(UserType)
    token = graphene.Field(TokenType)

class LoginUserResult(graphene.ObjectType):
    """Result type for user login"""
    success = graphene.Boolean(required=True)
    message = graphene.String()
    user = graphene.Field(UserType)
    token = graphene.Field(TokenType)

class RegisterUser(graphene.Mutation):
    """Register a new user"""
    
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        firstName = graphene.String(required=True)
        lastName = graphene.String(required=True)
    
    Output = RegisterUserResult
    
    @transaction.atomic
    def mutate(self, info, email, password, firstName, lastName):
        try:
            # Get User model inside the mutation to ensure proper database context
            User = get_user_model()
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return RegisterUserResult(
                    success=False,
                    message="User with this email already exists"
                )
            
            # Validate password strength
            if len(password) < 8:
                return RegisterUserResult(
                    success=False,
                    message="Password must be at least 8 characters long"
                )
            
            # Create user
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=firstName,
                last_name=lastName,
                is_active=True
            )
            
            # Generate JWT tokens
            serializer = EmailTokenObtainPairSerializer(data={
                "email": email,
                "password": password
            })
            
            if serializer.is_valid():
                tokens = serializer.validated_data
                token_data = TokenType(
                    access=tokens["access"],
                    refresh=tokens["refresh"]
                )
                
                # Create user type response
                user_data = UserType(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    firstName=user.first_name,
                    lastName=user.last_name,
                    name=f"{user.first_name} {user.last_name}",
                    isActive=user.is_active,
                    dateJoined=user.date_joined
                )
                
                return RegisterUserResult(
                    success=True,
                    message="User registered successfully",
                    user=user_data,
                    token=token_data
                )
            else:
                return RegisterUserResult(
                    success=False,
                    message="Failed to generate authentication tokens"
                )
                
        except Exception as e:
            logger.error(f"User registration error: {str(e)}")
            return RegisterUserResult(
                success=False,
                message=f"Registration failed: {str(e)}"
            )

class LoginUser(graphene.Mutation):
    """Login an existing user"""
    
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    Output = LoginUserResult
    
    @transaction.atomic
    def mutate(self, info, email, password):
        try:
            # Get User model inside the mutation to ensure proper database context
            User = get_user_model()
            
            # Authenticate user
            user = authenticate(username=email, password=password)
            
            if not user:
                return LoginUserResult(
                    success=False,
                    message="Invalid email or password"
                )
            
            if not user.is_active:
                return LoginUserResult(
                    success=False,
                    message="Account is deactivated"
                )
            
            # Generate JWT tokens
            serializer = EmailTokenObtainPairSerializer(data={
                "email": email,
                "password": password
            })
            
            if serializer.is_valid():
                tokens = serializer.validated_data
                token_data = TokenType(
                    access=tokens["access"],
                    refresh=tokens["refresh"]
                )
                
                # Create user type response
                user_data = UserType(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    firstName=user.first_name,
                    lastName=user.last_name,
                    name=f"{user.first_name} {user.last_name}",
                    isActive=user.is_active,
                    dateJoined=user.date_joined
                )
                
                return LoginUserResult(
                    success=True,
                    message="Login successful",
                    user=user_data,
                    token=token_data
                )
            else:
                return LoginUserResult(
                    success=False,
                    message="Failed to generate authentication tokens"
                )
                
        except Exception as e:
            logger.error(f"User login error: {str(e)}")
            return LoginUserResult(
                success=False,
                message=f"Login failed: {str(e)}"
            )

class AuthMutation(graphene.ObjectType):
    """Authentication mutations"""
    registerUser = RegisterUser.Field()
    loginUser = LoginUser.Field()
