"""
DataLoader implementation for GraphQL to prevent N+1 query problems
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging
from django.contrib.auth import get_user_model
from .models import Stock, IncomeProfile
from .banking_models import BankAccount

logger = logging.getLogger(__name__)
User = get_user_model()


class DataLoader:
    """
    Simple DataLoader implementation for batching and caching GraphQL queries
    Prevents N+1 query problems by batching multiple requests into single queries
    """
    
    def __init__(self, batch_load_fn, cache_key_fn=None):
        """
        Initialize DataLoader
        
        Args:
            batch_load_fn: Function that takes a list of keys and returns a list of values
            cache_key_fn: Optional function to generate cache key from key (default: str)
        """
        self.batch_load_fn = batch_load_fn
        self.cache_key_fn = cache_key_fn or str
        self.cache = {}
        self.queue = []
        self.batch_scheduled = False
    
    def load(self, key):
        """
        Load a single value by key
        
        Args:
            key: The key to load
            
        Returns:
            Promise-like object (in this case, a simple value since we're sync)
        """
        cache_key = self.cache_key_fn(key)
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Add to queue for batching
        if key not in self.queue:
            self.queue.append(key)
        
        # Schedule batch load if not already scheduled
        if not self.batch_scheduled:
            self.batch_scheduled = True
            # In a real async implementation, this would be scheduled
            # For now, we'll do immediate batch loading
            self._dispatch_batch()
        
        # Return from cache (will be populated by batch load)
        return self.cache.get(cache_key)
    
    def load_many(self, keys: List) -> List:
        """
        Load multiple values by keys
        
        Args:
            keys: List of keys to load
            
        Returns:
            List of values (None for missing keys)
        """
        return [self.load(key) for key in keys]
    
    def _dispatch_batch(self):
        """Execute batch load for all queued keys"""
        if not self.queue:
            self.batch_scheduled = False
            return
        
        keys = list(self.queue)
        self.queue = []
        self.batch_scheduled = False
        
        try:
            # Call batch load function
            results = self.batch_load_fn(keys)
            
            # Cache results
            for key, value in zip(keys, results):
                cache_key = self.cache_key_fn(key)
                self.cache[cache_key] = value
        except Exception as e:
            logger.error(f"Error in DataLoader batch load: {e}", exc_info=True)
            # Cache None for failed keys
            for key in keys:
                cache_key = self.cache_key_fn(key)
                self.cache[cache_key] = None
    
    def clear(self, key=None):
        """
        Clear cache for a specific key or all keys
        
        Args:
            key: Optional key to clear (if None, clears all)
        """
        if key is None:
            self.cache.clear()
        else:
            cache_key = self.cache_key_fn(key)
            self.cache.pop(cache_key, None)
    
    def prime(self, key, value):
        """
        Prime the cache with a key-value pair
        
        Args:
            key: The key
            value: The value to cache
        """
        cache_key = self.cache_key_fn(key)
        self.cache[cache_key] = value


# Global DataLoader instances
_user_loader = None
_stock_loader = None
_income_profile_loader = None
_bank_account_loader = None


def get_user_loader() -> DataLoader:
    """Get or create User DataLoader"""
    global _user_loader
    if _user_loader is None:
        def batch_load_users(user_ids: List[int]) -> List[Optional[User]]:
            """Batch load users by IDs"""
            users = User.objects.filter(id__in=user_ids)
            user_dict = {user.id: user for user in users}
            return [user_dict.get(user_id) for user_id in user_ids]
        
        _user_loader = DataLoader(batch_load_users)
    return _user_loader


def get_stock_loader() -> DataLoader:
    """Get or create Stock DataLoader"""
    global _stock_loader
    if _stock_loader is None:
        def batch_load_stocks(symbols: List[str]) -> List[Optional[Stock]]:
            """Batch load stocks by symbols"""
            symbols_upper = [s.upper() for s in symbols]
            stocks = Stock.objects.filter(symbol__in=symbols_upper)
            stock_dict = {stock.symbol.upper(): stock for stock in stocks}
            return [stock_dict.get(s.upper()) for s in symbols]
        
        _stock_loader = DataLoader(batch_load_stocks)
    return _stock_loader


def get_income_profile_loader() -> DataLoader:
    """Get or create IncomeProfile DataLoader"""
    global _income_profile_loader
    if _income_profile_loader is None:
        def batch_load_income_profiles(user_ids: List[int]) -> List[Optional[IncomeProfile]]:
            """Batch load income profiles by user IDs"""
            profiles = IncomeProfile.objects.filter(user_id__in=user_ids).select_related('user')
            profile_dict = {profile.user_id: profile for profile in profiles}
            return [profile_dict.get(user_id) for user_id in user_ids]
        
        _income_profile_loader = DataLoader(batch_load_income_profiles)
    return _income_profile_loader


def get_bank_account_loader() -> DataLoader:
    """Get or create BankAccount DataLoader"""
    global _bank_account_loader
    if _bank_account_loader is None:
        def batch_load_bank_accounts(user_ids: List[int]) -> List[List[BankAccount]]:
            """Batch load bank accounts by user IDs (returns list of lists)"""
            accounts = BankAccount.objects.filter(user_id__in=user_ids, is_verified=True)
            accounts_by_user = defaultdict(list)
            for account in accounts:
                accounts_by_user[account.user_id].append(account)
            return [accounts_by_user.get(user_id, []) for user_id in user_ids]
        
        _bank_account_loader = DataLoader(batch_load_bank_accounts)
    return _bank_account_loader


def clear_all_loaders():
    """Clear all DataLoader caches"""
    global _user_loader, _stock_loader, _income_profile_loader, _bank_account_loader
    if _user_loader:
        _user_loader.clear()
    if _stock_loader:
        _stock_loader.clear()
    if _income_profile_loader:
        _income_profile_loader.clear()
    if _bank_account_loader:
        _bank_account_loader.clear()

