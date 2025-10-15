# marketdata/providers/base.py
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod

class Provider(Protocol):
    """Protocol defining the interface for market data providers"""
    name: str
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        ...
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile/fundamentals"""
        ...
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain for a symbol"""
        ...

class BaseProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, api_key: str, timeout: int = 5):
        self.api_key = api_key
        self.timeout = timeout
        self._client = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base API URL"""
        pass
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to uppercase"""
        return symbol.upper().strip()
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle API errors with logging"""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"{self.name} {operation} failed: {error}")
        raise error
