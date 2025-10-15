# marketdata/schema.py
import graphene
from graphene_django import DjangoObjectType
from .models import Quote, OptionContract, Equity, ProviderHealth
from .service import MarketDataService

class QuoteType(graphene.ObjectType):
    """Real-time quote data"""
    symbol = graphene.String()
    price = graphene.Float()
    change = graphene.Float()
    change_percent = graphene.Float()
    volume = graphene.Int()
    high = graphene.Float()
    low = graphene.Float()
    open = graphene.Float()
    bid = graphene.Float()
    ask = graphene.Float()
    timestamp = graphene.Float()
    provider = graphene.String()
    cached_at = graphene.Float()

class OptionContractType(graphene.ObjectType):
    """Options contract data"""
    symbol = graphene.String()
    type = graphene.String()
    strike = graphene.Float()
    expiration = graphene.String()
    bid = graphene.Float()
    ask = graphene.Float()
    last_price = graphene.Float()
    volume = graphene.Int()
    open_interest = graphene.Int()
    implied_volatility = graphene.Float()
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()

class OptionsChainType(graphene.ObjectType):
    """Options chain data"""
    symbol = graphene.String()
    contracts = graphene.List(OptionContractType)
    provider = graphene.String()
    cached_at = graphene.Float()

class EquityType(graphene.ObjectType):
    """Company equity information"""
    symbol = graphene.String()
    name = graphene.String()
    exchange = graphene.String()
    sector = graphene.String()
    industry = graphene.String()
    market_cap = graphene.BigInt()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    provider = graphene.String()
    cached_at = graphene.Float()

class ProviderStatusType(graphene.ObjectType):
    """Provider health status"""
    provider = graphene.String()
    available = graphene.Boolean()
    failures = graphene.Int()
    circuit_open = graphene.Boolean()

class MarketDataQuery(graphene.ObjectType):
    """Market data GraphQL queries"""
    
    # Real-time quotes
    quote = graphene.Field(QuoteType, symbol=graphene.String(required=True))
    quotes = graphene.List(QuoteType, symbols=graphene.List(graphene.String, required=True))
    
    # Company profiles
    profile = graphene.Field(EquityType, symbol=graphene.String(required=True))
    profiles = graphene.List(EquityType, symbols=graphene.List(graphene.String, required=True))
    
    # Options data
    options_chain = graphene.Field(
        OptionsChainType, 
        symbol=graphene.String(required=True), 
        limit=graphene.Int()
    )
    
    # Provider status
    provider_status = graphene.List(ProviderStatusType)
    
    def resolve_quote(self, info, symbol):
        """Get real-time quote for a symbol"""
        try:
            service = MarketDataService()
            data = service.get_quote(symbol)
            return QuoteType(**data)
        except Exception as e:
            # Return None for failed requests (GraphQL handles this gracefully)
            return None
    
    def resolve_quotes(self, info, symbols):
        """Get real-time quotes for multiple symbols"""
        service = MarketDataService()
        quotes = []
        
        for symbol in symbols:
            try:
                data = service.get_quote(symbol)
                quotes.append(QuoteType(**data))
            except Exception as e:
                # Skip failed symbols
                continue
        
        return quotes
    
    def resolve_profile(self, info, symbol):
        """Get company profile for a symbol"""
        try:
            service = MarketDataService()
            data = service.get_profile(symbol)
            return EquityType(**data)
        except Exception as e:
            return None
    
    def resolve_profiles(self, info, symbols):
        """Get company profiles for multiple symbols"""
        service = MarketDataService()
        profiles = []
        
        for symbol in symbols:
            try:
                data = service.get_profile(symbol)
                profiles.append(EquityType(**data))
            except Exception as e:
                continue
        
        return profiles
    
    def resolve_options_chain(self, info, symbol, limit=50):
        """Get options chain for a symbol"""
        try:
            service = MarketDataService()
            data = service.get_options_chain(symbol, limit)
            
            # Convert contracts to GraphQL objects
            contracts = []
            for contract_data in data.get("contracts", []):
                contracts.append(OptionContractType(**contract_data))
            
            return OptionsChainType(
                symbol=data.get("symbol"),
                contracts=contracts,
                provider=data.get("provider"),
                cached_at=data.get("cached_at")
            )
        except Exception as e:
            return None
    
    def resolve_provider_status(self, info):
        """Get status of all providers"""
        try:
            service = MarketDataService()
            status_data = service.get_provider_status()
            
            status_list = []
            for provider, status in status_data.items():
                status_list.append(ProviderStatusType(
                    provider=provider,
                    available=status["available"],
                    failures=status["failures"],
                    circuit_open=status["circuit_open"]
                ))
            
            return status_list
        except Exception as e:
            return []

# Mutations for cache management
class ClearCache(graphene.Mutation):
    """Clear market data cache"""
    
    class Arguments:
        pattern = graphene.String()
    
    success = graphene.Boolean()
    cleared = graphene.Int()
    message = graphene.String()
    
    def mutate(self, info, pattern="md:*"):
        try:
            service = MarketDataService()
            result = service.clear_cache(pattern)
            
            if "error" in result:
                return ClearCache(
                    success=False,
                    cleared=0,
                    message=result["error"]
                )
            
            return ClearCache(
                success=True,
                cleared=result["cleared"],
                message=f"Cleared {result['cleared']} cache entries"
            )
        except Exception as e:
            return ClearCache(
                success=False,
                cleared=0,
                message=str(e)
            )

class MarketDataMutation(graphene.ObjectType):
    """Market data mutations"""
    clear_cache = ClearCache.Field()
