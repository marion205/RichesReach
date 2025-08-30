# core/schema.py
import graphene
import graphql_jwt
from .types import UserType, PostType
from .models import User, Post
from .mutations import CreateUser, CreatePost, SendMessage   # <-- add SendMessage

class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int(), email=graphene.String())
    wall_posts = graphene.List(PostType)

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_user(self, info, id=None, email=None):
        if id:
            return User.objects.filter(id=id).first()
        if email:
            return User.objects.filter(email=email).first()
        return None

    def resolve_wall_posts(self, info):
        return Post.objects.select_related('user').order_by('-created_at')

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_post = CreatePost.Field()
    send_message = SendMessage.Field()                 # <-- expose chatbot mutation
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)