# Domain query mixins; schema composes these into ExtendedQuery.
from .trading import TradingQuery
from .banking import BudgetSpendingQuery
from .social import SocialQuery
from .market_data import MarketDataQuery
from .analytics import AnalyticsQuery
from .security import SecurityQuery
from .signals import SignalsQuery
from .options_rust import OptionsRustQuery
from .discussions import DiscussionsQuery

__all__ = [
    "TradingQuery",
    "BudgetSpendingQuery",
    "SocialQuery",
    "MarketDataQuery",
    "AnalyticsQuery",
    "SecurityQuery",
    "SignalsQuery",
    "OptionsRustQuery",
    "DiscussionsQuery",
]
