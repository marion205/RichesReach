"""
Attach DataLoaders to GraphQL context so resolvers can use the same
per-request loaders (batch + cache) and avoid N+1.
"""
from typing import Any, Optional

from core.dataloaders import (
    get_user_loader,
    get_stock_loader,
    get_income_profile_loader,
    get_bank_account_loader,
)


class GraphQLLoaders:
    """
    Container for per-request DataLoaders. Attach to info.context.loaders
    so resolvers use the same batch/cache for the duration of the request.
    """

    __slots__ = ("user_loader", "stock_loader", "income_profile_loader", "bank_account_loader")

    def __init__(
        self,
        user_loader=None,
        stock_loader=None,
        income_profile_loader=None,
        bank_account_loader=None,
    ):
        self.user_loader = user_loader or get_user_loader()
        self.stock_loader = stock_loader or get_stock_loader()
        self.income_profile_loader = income_profile_loader or get_income_profile_loader()
        self.bank_account_loader = bank_account_loader or get_bank_account_loader()


def get_loaders_for_context(context: Any) -> Optional[GraphQLLoaders]:
    """
    Return the loaders instance attached to this request's GraphQL context, if any.
    Resolvers can use: loaders = get_loaders_for_context(info.context); loaders.user_loader.load(id)
    """
    if not context:
        return None
    return getattr(context, "loaders", None)


def create_loaders_for_request() -> GraphQLLoaders:
    """
    Create a GraphQLLoaders instance for a request (uses shared get_*_loader singletons).
    Attach to context so resolvers use context.loaders.user_loader.load(id) etc.
    """
    return GraphQLLoaders(
        user_loader=get_user_loader(),
        stock_loader=get_stock_loader(),
        income_profile_loader=get_income_profile_loader(),
        bank_account_loader=get_bank_account_loader(),
    )
