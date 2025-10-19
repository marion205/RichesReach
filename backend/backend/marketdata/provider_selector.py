# marketdata/provider_selector.py
import time
import logging
from typing import Callable, List, Dict, Any
from django.utils import timezone
from .providers.polygon import PolygonProvider
from .providers.finnhub import FinnhubProvider
from .models import ProviderHealth

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker pattern for provider health management"""
    
    def __init__(self, max_failures: int = 3, failure_window: int = 60):
        self.max_failures = max_failures
        self.failure_window = failure_window
        self.failures = 0
        self.opened_at = 0
        self.last_failure_time = 0
    
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.max_failures:
            self.opened_at = time.time()
            logger.warning(f"Circuit breaker opened after {self.failures} failures")
    
    def record_success(self):
        """Record a success and reset the circuit"""
        if self.failures > 0:
            logger.info(f"Circuit breaker reset after {self.failures} failures")
        self.failures = 0
        self.opened_at = 0
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.failures < self.max_failures:
            return False
        
        # Check if we're still in the failure window
        if time.time() - self.last_failure_time > self.failure_window:
            # Reset if we're past the failure window
            self.failures = 0
            self.opened_at = 0
            return False
        
        return True
    
    def allow_request(self) -> bool:
        """Check if requests are allowed through the circuit"""
        return not self.is_open()

class ProviderSelector:
    """Selects and manages market data providers with fallback and circuit breaking"""
    
    def __init__(self):
        self.providers = []
        self.circuit_breakers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        try:
            # Try to initialize Polygon first (preferred for options and real-time)
            polygon = PolygonProvider()
            self.providers.append(polygon)
            self.circuit_breakers[polygon.name] = CircuitBreaker()
            logger.info("Polygon provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Polygon provider: {e}")
        
        try:
            # Add Finnhub as fallback
            finnhub = FinnhubProvider()
            self.providers.append(finnhub)
            self.circuit_breakers[finnhub.name] = CircuitBreaker()
            logger.info("Finnhub provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Finnhub provider: {e}")
        
        if not self.providers:
            raise Exception("No market data providers available")
        
        logger.info(f"Initialized {len(self.providers)} providers: {[p.name for p in self.providers]}")
    
    def _update_provider_health(self, provider_name: str, success: bool, error: str = None):
        """Update provider health in database"""
        try:
            health, created = ProviderHealth.objects.get_or_create(
                provider=provider_name,
                defaults={'is_healthy': True}
            )
            
            if success:
                health.is_healthy = True
                health.last_success = timezone.now()
                health.failure_count = 0
            else:
                health.is_healthy = False
                health.last_failure = timezone.now()
                health.failure_count += 1
            
            health.save()
            
        except Exception as e:
            logger.error(f"Failed to update provider health: {e}")
    
    def try_call(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Try calling a method on providers with fallback and circuit breaking"""
        errors = {}
        
        for provider in self.providers:
            circuit = self.circuit_breakers.get(provider.name)
            
            # Check circuit breaker
            if circuit and not circuit.allow_request():
                logger.warning(f"Circuit breaker open for {provider.name}, skipping")
                continue
            
            try:
                # Call the method on the provider
                method = getattr(provider, method_name)
                result = method(*args, **kwargs)
                
                # Record success
                if circuit:
                    circuit.record_success()
                self._update_provider_health(provider.name, True)
                
                logger.info(f"Successfully called {method_name} on {provider.name}")
                return {
                    "provider": provider.name,
                    "data": result,
                    "success": True
                }
                
            except Exception as e:
                error_msg = str(e)
                errors[provider.name] = error_msg
                
                # Record failure
                if circuit:
                    circuit.record_failure()
                self._update_provider_health(provider.name, False, error_msg)
                
                logger.warning(f"{method_name} failed on {provider.name}: {error_msg}")
                continue
        
        # All providers failed
        error_summary = "; ".join([f"{name}: {error}" for name, error in errors.items()])
        raise Exception(f"All providers failed for {method_name}: {error_summary}")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get quote with provider fallback"""
        return self.try_call("get_quote", symbol)
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get profile with provider fallback"""
        return self.try_call("get_profile", symbol)
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain with provider fallback"""
        return self.try_call("get_options_chain", symbol, limit)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for provider in self.providers:
            circuit = self.circuit_breakers.get(provider.name)
            status[provider.name] = {
                "available": not circuit.is_open() if circuit else True,
                "failures": circuit.failures if circuit else 0,
                "circuit_open": circuit.is_open() if circuit else False
            }
        return status
