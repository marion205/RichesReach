"""
GraphQL Mutations for Social Poll Features
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from django.utils import timezone
from datetime import timedelta
from .models import Post
from .types import PostType

logger = logging.getLogger(__name__)


class VotePoll(graphene.Mutation):
    """Vote on a poll option"""
    
    class Arguments:
        post_id = graphene.ID(required=True)
        option_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    post = graphene.Field(PostType)
    error = graphene.String()
    
    @login_required
    def mutate(self, info, post_id, option_id):
        user = info.context.user
        
        try:
            post = Post.objects.get(id=post_id, kind='POLL')
        except Post.DoesNotExist:
            return VotePoll(
                success=False,
                error="Poll not found"
            )
        
        # Check if poll is still open
        if post.poll and post.poll.get('closesAt'):
            closes_at = post.poll.get('closesAt')
            if isinstance(closes_at, str):
                from dateutil.parser import parse
                closes_at = parse(closes_at)
            if timezone.now() > closes_at:
                return VotePoll(
                    success=False,
                    error="Poll has closed"
                )
        
        # Get poll options
        poll = post.poll or {}
        options = poll.get('options', [])
        
        # Find the option
        option_found = False
        updated_options = []
        for opt in options:
            opt_id = opt.get('id') or str(options.index(opt))
            if str(opt_id) == str(option_id):
                # Increment vote count
                votes = opt.get('votes', 0)
                updated_options.append({
                    **opt,
                    'votes': votes + 1
                })
                option_found = True
            else:
                updated_options.append(opt)
        
        if not option_found:
            return VotePoll(
                success=False,
                error="Poll option not found"
            )
        
        # Update poll with new vote counts
        poll['options'] = updated_options
        post.poll = poll
        post.save()
        
        # Refresh from DB
        post.refresh_from_db()
        
        return VotePoll(
            success=True,
            post=post
        )


class SocialPollMutations(graphene.ObjectType):
    """Social poll mutations"""
    vote_poll = VotePoll.Field()
    # CamelCase alias for GraphQL schema
    votePoll = VotePoll.Field()

