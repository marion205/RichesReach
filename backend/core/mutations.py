# core/mutations.py
import graphene
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from datetime import datetime, timezone
from .types import UserType, PostType, ChatMessageType, SourceType
from .models import Post

User = get_user_model()

class CreateUser(graphene.Mutation):
    user = graphene.Field(lambda: UserType)

    class Arguments:
        email = graphene.String(required=True)
        name = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, name, password):
        if User.objects.filter(email=email).exists():
            raise GraphQLError("A user with that email already exists.")
        user = User(email=email.strip().lower(), name=name)
        user.set_password(password)
        user.save()
        return CreateUser(user=user)

class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        content = graphene.String(required=True)

    def mutate(self, info, content):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Login required to post.")
        post = Post.objects.create(user=user, content=content)
        return CreatePost(post=post)

# --- NEW: chatbot mutation ---
class SendMessage(graphene.Mutation):
    class Arguments:
        session_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    Output = ChatMessageType

    def mutate(self, info, session_id, content):
        # TODO: replace with real bot call; this is a safe placeholder
        now = datetime.now(timezone.utc)
        answer = "\n".join([
            "Educational only — not financial advice.",
            f"You asked: {content}",
            "General pointers:",
            "• Define time horizon & risk tolerance.",
            "• Diversify and watch fees (broad index funds are common).",
            "• investor.gov has unbiased explainers."
        ])
        return ChatMessageType(
            id=str(int(now.timestamp())),
            role="assistant",
            content=answer,
            created_at=now,
            confidence=0.6,
            sources=[SourceType(
                title="Investor.gov: Introduction to Investing",
                url="https://www.investor.gov/introduction-investing",
                snippet="Official SEC resource on investing basics."
            )],
        )

# Root mutation
class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_post = CreatePost.Field()
    send_message = SendMessage.Field()   # <-- added