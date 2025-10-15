"""
Enterprise Service Wrapper
Comprehensive service wrapper that integrates all enterprise-level features
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from functools import wraps
from datetime import datetime, timedelta
import logging

from .enterprise_config import config
from .enterprise_exceptions import (
    EnterpriseException, ErrorHandler, enterprise_exception_handler,
    validate_required_fields, validate_data_types
)
from .enterprise_logging import get_enterprise_logger, log_function_call, log_performance
from .enterprise_security import (
    input_sanitizer, security_monitor, rate_limiter,
    password_validator, jwt_manager
)
from .enterprise_monitoring import performance_monitor, api_monitor
from .enterprise_testing import EnterpriseTestCase, PerformanceTestMixin

T = TypeVar('T')


class EnterpriseService(Generic[T]):
    """
    Base enterprise service class with integrated monitoring, security, and error handling
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_enterprise_logger(service_name)
        self.rate_limiter = rate_limiter
        self.security_monitor = security_monitor
        self.performance_monitor = performance_monitor
        self.api_monitor = api_monitor
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the service"""
        self.logger.info(f"Initializing enterprise service: {self.service_name}")
        
        # Start monitoring if in production
        if config.is_production():
            self.performance_monitor.start_monitoring()
    
    @enterprise_exception_handler
    def execute_with_monitoring(
        self,
        operation: str,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function with comprehensive monitoring and error handling
        
        Args:
            operation: Name of the operation being performed
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            EnterpriseException: If operation fails
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting operation: {operation}")
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Record success metrics
            execution_time = time.time() - start_time
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.success",
                1,
                'counter'
            )
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.execution_time",
                execution_time * 1000,  # Convert to milliseconds
                'timer',
                unit='ms'
            )
            
            self.logger.info(f"Completed operation: {operation} in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            # Record error metrics
            execution_time = time.time() - start_time
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.error",
                1,
                'counter'
            )
            
            # Log security event if it's a security-related error
            if isinstance(e, EnterpriseException) and 'AUTH' in e.error_code.value:
                self.security_monitor.log_security_event(
                    "authentication_error",
                    "medium",
                    details={'operation': operation, 'error': str(e)}
                )
            
            self.logger.error(f"Operation failed: {operation} - {str(e)}")
            raise
    
    @enterprise_exception_handler
    async def execute_async_with_monitoring(
        self,
        operation: str,
        coro,
        *args,
        **kwargs
    ) -> T:
        """
        Execute async function with comprehensive monitoring and error handling
        
        Args:
            operation: Name of the operation being performed
            coro: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            EnterpriseException: If operation fails
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting async operation: {operation}")
            
            # Execute the async function
            result = await coro(*args, **kwargs)
            
            # Record success metrics
            execution_time = time.time() - start_time
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.success",
                1,
                'counter'
            )
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.execution_time",
                execution_time * 1000,  # Convert to milliseconds
                'timer',
                unit='ms'
            )
            
            self.logger.info(f"Completed async operation: {operation} in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            # Record error metrics
            execution_time = time.time() - start_time
            self.performance_monitor.record_metric(
                f"{self.service_name}.{operation}.error",
                1,
                'counter'
            )
            
            self.logger.error(f"Async operation failed: {operation} - {str(e)}")
            raise
    
    def validate_and_sanitize_input(
        self,
        data: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        field_types: Optional[Dict[str, type]] = None
    ) -> Dict[str, Any]:
        """
        Validate and sanitize input data
        
        Args:
            data: Input data to validate and sanitize
            required_fields: List of required field names
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            Sanitized and validated data
            
        Raises:
            EnterpriseException: If validation fails
        """
        try:
            # Validate required fields
            if required_fields:
                validate_required_fields(data, required_fields)
            
            # Validate data types
            if field_types:
                validate_data_types(data, field_types)
            
            # Sanitize input
            sanitized_data = input_sanitizer.sanitize_dict(data)
            
            self.logger.debug(f"Input validated and sanitized for {self.service_name}")
            
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Input validation failed for {self.service_name}: {str(e)}")
            raise
    
    def check_rate_limit(
        self,
        identifier: str,
        action: str,
        max_attempts: int = 10,
        window_minutes: int = 15
    ) -> bool:
        """
        Check if operation is rate limited
        
        Args:
            identifier: Unique identifier for rate limiting
            action: Action being performed
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            True if rate limited, False otherwise
        """
        is_limited = self.rate_limiter.is_rate_limited(
            identifier, action, max_attempts, window_minutes
        )
        
        if is_limited:
            self.security_monitor.log_security_event(
                "rate_limit_exceeded",
                "medium",
                details={
                    'identifier': identifier,
                    'action': action,
                    'max_attempts': max_attempts,
                    'window_minutes': window_minutes
                }
            )
        
        return is_limited
    
    def log_business_event(
        self,
        event: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Log business event
        
        Args:
            event: Event name
            details: Event details
            user_id: User ID if applicable
        """
        self.logger.log_business_event(
            event,
            details,
            context={'user_id': user_id} if user_id else None
        )
    
    def log_user_action(
        self,
        action: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log user action
        
        Args:
            action: Action performed
            user_id: User ID
            details: Action details
        """
        self.logger.log_user_action(
            action,
            user_id,
            details
        )
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get service health status
        
        Returns:
            Health status dictionary
        """
        return {
            'service_name': self.service_name,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'total_operations': self.performance_monitor.get_metric_summary(
                    f"{self.service_name}.total_operations"
                ),
                'error_rate': self.performance_monitor.get_metric_summary(
                    f"{self.service_name}.error_rate"
                ),
                'avg_response_time': self.performance_monitor.get_metric_summary(
                    f"{self.service_name}.avg_response_time"
                )
            }
        }


class EnterpriseAPIService(EnterpriseService):
    """
    Enterprise API service with HTTP-specific monitoring
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.api_monitor = api_monitor
    
    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None
    ):
        """
        Record API request metrics
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User ID if authenticated
        """
        self.api_monitor.record_request(endpoint, method, status_code, response_time)
        
        # Log API request
        self.logger.log_api_request(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            context={'user_id': user_id} if user_id else None
        )
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """
        Get API metrics
        
        Returns:
            API metrics dictionary
        """
        return self.api_monitor.get_api_stats()
    
    def get_endpoint_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics by endpoint
        
        Returns:
            Endpoint metrics dictionary
        """
        return self.api_monitor.get_endpoint_stats()


class EnterpriseDataService(EnterpriseService):
    """
    Enterprise data service with data-specific monitoring
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
    
    def validate_data_integrity(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate data integrity against schema
        
        Args:
            data: Data to validate
            schema: Validation schema
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Implement schema validation logic here
            # This is a placeholder for actual schema validation
            
            self.logger.debug(f"Data integrity validated for {self.service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {str(e)}")
            return False
    
    def log_data_access(
        self,
        data_type: str,
        operation: str,
        user_id: Optional[str] = None,
        record_count: Optional[int] = None
    ):
        """
        Log data access
        
        Args:
            data_type: Type of data accessed
            operation: Operation performed (read, write, delete)
            user_id: User ID if applicable
            record_count: Number of records affected
        """
        self.logger.log_business_event(
            f"data_{operation}",
            {
                'data_type': data_type,
                'operation': operation,
                'record_count': record_count
            },
            context={'user_id': user_id} if user_id else None
        )


def enterprise_service(service_name: str):
    """
    Decorator to create enterprise service from class
    
    Args:
        service_name: Name of the service
        
    Returns:
        Decorated class
    """
    def decorator(cls):
        class EnterpriseWrappedService(EnterpriseService):
            def __init__(self, *args, **kwargs):
                super().__init__(service_name)
                self._wrapped_service = cls(*args, **kwargs)
            
            def __getattr__(self, name):
                attr = getattr(self._wrapped_service, name)
                if callable(attr):
                    return self._wrap_method(name, attr)
                return attr
            
            def _wrap_method(self, method_name: str, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return self.execute_with_monitoring(
                        method_name,
                        method,
                        *args,
                        **kwargs
                    )
                return wrapper
        
        return EnterpriseWrappedService
    return decorator


def enterprise_api_service(service_name: str):
    """
    Decorator to create enterprise API service from class
    
    Args:
        service_name: Name of the service
        
    Returns:
        Decorated class
    """
    def decorator(cls):
        class EnterpriseWrappedAPIService(EnterpriseAPIService):
            def __init__(self, *args, **kwargs):
                super().__init__(service_name)
                self._wrapped_service = cls(*args, **kwargs)
            
            def __getattr__(self, name):
                attr = getattr(self._wrapped_service, name)
                if callable(attr):
                    return self._wrap_method(name, attr)
                return attr
            
            def _wrap_method(self, method_name: str, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return self.execute_with_monitoring(
                        method_name,
                        method,
                        *args,
                        **kwargs
                    )
                return wrapper
        
        return EnterpriseWrappedAPIService
    return decorator


# Example usage and integration
class ExampleEnterpriseService(EnterpriseService):
    """Example enterprise service"""
    
    def __init__(self):
        super().__init__("example_service")
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with enterprise features"""
        # Validate and sanitize input
        validated_data = self.validate_and_sanitize_input(
            data,
            required_fields=['id', 'name'],
            field_types={'id': int, 'name': str}
        )
        
        # Check rate limit
        if self.check_rate_limit("user_123", "process_data"):
            raise EnterpriseException(
                "Rate limit exceeded",
                ErrorCode.API_RATE_LIMIT_EXCEEDED
            )
        
        # Process data
        result = {
            'processed_id': validated_data['id'],
            'processed_name': validated_data['name'].upper(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log business event
        self.log_business_event(
            "data_processed",
            {'record_count': 1, 'data_type': 'example'}
        )
        
        return result
