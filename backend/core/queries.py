import graphene
from django.contrib.auth import get_user_model
from .types import UserType, PostType
from .models import Post

User = get_user_model()

class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    me = graphene.Field(UserType)
    wall_posts = graphene.List(PostType)

    def resolve_all_users(root, info):
        return User.objects.all()

    def resolve_me(root, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_wall_posts(self, info):
        return Post.objects.select_related("user").order_by("-created_at")