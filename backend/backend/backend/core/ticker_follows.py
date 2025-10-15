# Simple in-memory storage for ticker follows
# This is a temporary solution until migration issues are resolved

from typing import Set, Dict
from django.contrib.auth.models import User

# In-memory storage for ticker follows
_ticker_follows: Dict[int, Set[str]] = {}

def follow_ticker(user_id: int, symbol: str) -> bool:
    """Follow a ticker symbol for a user"""
    if user_id not in _ticker_follows:
        _ticker_follows[user_id] = set()
    _ticker_follows[user_id].add(symbol.upper())
    return True

def unfollow_ticker(user_id: int, symbol: str) -> bool:
    """Unfollow a ticker symbol for a user"""
    if user_id in _ticker_follows:
        _ticker_follows[user_id].discard(symbol.upper())
    return True

def get_followed_tickers(user_id: int) -> Set[str]:
    """Get all ticker symbols followed by a user"""
    return _ticker_follows.get(user_id, set())

def is_following(user_id: int, symbol: str) -> bool:
    """Check if a user is following a ticker symbol"""
    return symbol.upper() in _ticker_follows.get(user_id, set())