import logging
import graphene
from graphene import Dynamic

logger = logging.getLogger("graphql")

class Query(graphene.ObjectType):
    ping = graphene.String()
    def resolve_ping(root, info): 
        return "ok"

def _lazy_add_to_watchlist():
    try:
        from gql.mutations.watchlist import AddToWatchlist
        return AddToWatchlist.Field()
    except Exception as e:
        logger.exception("Lazy import of AddToWatchlist failed: %s", e)
        return None

class Mutation(graphene.ObjectType):
    add_to_watchlist = Dynamic(_lazy_add_to_watchlist)

schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=True)
