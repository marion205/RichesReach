import graphene

class WatchlistItemType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()

class AddToWatchlist(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)

    ok = graphene.Boolean()
    item = graphene.Field(WatchlistItemType)

    @classmethod
    def mutate(cls, root, info, symbol):
        # Lazy import keeps GraphQL <-> models decoupled at import time
        from core.models import WatchlistItem
        user = getattr(info.context, "user", None)
        if not user or not user.is_authenticated:
            raise Exception("Authentication required")
        item, _ = WatchlistItem.objects.get_or_create(
            user=user, symbol=symbol.upper().strip()
        )
        return AddToWatchlist(ok=True, item=WatchlistItemType(id=item.id, symbol=item.symbol))
