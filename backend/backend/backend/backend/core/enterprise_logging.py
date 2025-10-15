"""
Enterprise Logging System
Comprehensive logging for enterprise-level monitoring and debugging
"""
import logging
import json
import time
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from django.conf import settings
from django.core.cache import cache
import traceback


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories"""
    AUTHENTICATION = "AUTH"
    API_REQUEST = "API"
    DATABASE = "DB"
    BUSINESS_LOGIC = "BIZ"
    MACHINE_LEARNING = "ML"
    PERFORMANCE = "PERF"
    SECURITY = "SEC"
    SYSTEM = "SYS"
    USER_ACTION = "USER"


@dataclass
class LogContext:
    """Log context information"""
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class EnterpriseLogger:
    """Enterprise logging system"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        self._setup_formatters()
    
    def _setup_formatters(self):
        """Setup log formatters"""
        # JSON formatter for structured logging
        self.json_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console formatter for development
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _create_log_entry(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.value,
            'category': category.value,
            'logger': self.name,
            'message': message,
            'context': asdict(context) if context else None,
            'extra_data': extra_data or {}
        }
        
        return log_entry
    
    def _log(self, level: LogLevel, message: str, category: LogCategory, **kwargs):
        """Internal logging method"""
        context = kwargs.get('context')
        extra_data = kwargs.get('extra_data', {})
        
        log_entry = self._create_log_entry(level, message, category, context, extra_data)
        
        # Log to standard logger
        log_message = json.dumps(log_entry)
        getattr(self.logger, level.value.lower())(log_message)
        
        # Store in cache for real-time monitoring
        self._store_log_entry(log_entry)
    
    def _store_log_entry(self, log_entry: Dict[str, Any]):
        """Store log entry in cache for monitoring"""
        try:
            # Store recent logs in cache
            cache_key = f"recent_logs:{log_entry['category']}"
            recent_logs = cache.get(cache_key, [])
            recent_logs.append(log_entry)
            
            # Keep only last 100 entries
            if len(recent_logs) > 100:
                recent_logs = recent_logs[-100:]
            
            cache.set(cache_key, recent_logs, timeout=3600)  # 1 hour
        except Exception as e:
            # Don't let logging errors break the application
            pass
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, category, **kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, message, category, **kwargs)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, category, **kwargs)
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        response_time: float,
        context: Optional[LogContext] = None
    ):
        """Log API request"""
        message = f"{method} {endpoint} - {status_code} - {response_time:.3f}s"
        self.info(
            message,
            category=LogCategory.API_REQUEST,
            context=context,
            extra_data={
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'response_time': response_time
            }
        )
    
    def log_user_action(
        self,
        action: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None
    ):
        """Log user action"""
        message = f"User {user_id} performed action: {action}"
        self.info(
            message,
            category=LogCategory.USER_ACTION,
            context=context,
            extra_data={
                'action': action,
                'user_id': user_id,
                'details': details or {}
            }
        )
    
    def log_business_event(
        self,
        event: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None
    ):
        """Log business event"""
        message = f"Business event: {event}"
        self.info(
            message,
            category=LogCategory.BUSINESS_LOGIC,
            context=context,
            extra_data={
                'event': event,
                'details': details or {}
            }
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[LogContext] = None
    ):
        """Log performance metric"""
        message = f"Performance metric: {metric_name} = {value} {unit}"
        self.info(
            message,
            category=LogCategory.PERFORMANCE,
            context=context,
            extra_data={
                'metric_name': metric_name,
                'value': value,
                'unit': unit
            }
        )
    
    def log_security_event(
        self,
        event: str,
        severity: str = "medium",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None
    ):
        """Log security event"""
        message = f"Security event: {event} (severity: {severity})"
        level = LogLevel.WARNING if severity == "high" else LogLevel.INFO
        self._log(
            level,
            message,
            LogCategory.SECURITY,
            context=context,
            extra_data={
                'event': event,
                'severity': severity,
                'details': details or {}
            }
        )


def get_enterprise_logger(name: str) -> EnterpriseLogger:
    """Get enterprise logger instance"""
    return EnterpriseLogger(name)


def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_enterprise_logger(func.__module__)
        
        # Log function entry
        logger.debug(
            f"Entering function: {func.__name__}",
            category=LogCategory.SYSTEM,
            extra_data={
                'function_name': func.__name__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }
        )
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log function exit
            logger.debug(
                f"Exiting function: {func.__name__}",
                category=LogCategory.SYSTEM,
                extra_data={
                    'function_name': func.__name__,
                    'execution_time': execution_time,
                    'success': True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log function error
            logger.error(
                f"Error in function: {func.__name__}",
                category=LogCategory.SYSTEM,
                extra_data={
                    'function_name': func.__name__,
                    'execution_time': execution_time,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            
            raise
    
    return wrapper


def log_performance(metric_name: str, unit: str = "ms"):
    """Decorator to log performance metrics"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_enterprise_logger(func.__module__)
            
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.log_performance_metric(metric_name, execution_time, unit)
            
            return result
        
        return wrapper
    return decorator


def log_api_endpoint(endpoint_name: str):
    """Decorator to log API endpoint calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_enterprise_logger(func.__module__)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                logger.log_api_request(
                    method="POST",  # Default, should be overridden
                    endpoint=endpoint_name,
                    status_code=200,
                    response_time=response_time
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                logger.log_api_request(
                    method="POST",
                    endpoint=endpoint_name,
                    status_code=500,
                    response_time=response_time
                )
                
                raise
        
        return wrapper
    return decorator


class LoggingMiddleware:
    """Django middleware for request logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_enterprise_logger('middleware')
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        context = LogContext(
            request_id=request.META.get('HTTP_X_REQUEST_ID'),
            endpoint=request.path,
            method=request.method,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        self.logger.info(
            f"Request: {request.method} {request.path}",
            category=LogCategory.API_REQUEST,
            context=context
        )
        
        response = self.get_response(request)
        
        # Log response
        response_time = time.time() - start_time
        
        self.logger.log_api_request(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
            response_time=response_time,
            context=context
        )
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
