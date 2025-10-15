"""
Enterprise Exception Handling System
Centralized exception handling for enterprise-level error management
"""
import logging
import traceback
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json


class ErrorCode(Enum):
    """Standardized error codes"""
    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTH_001"
    AUTHORIZATION_DENIED = "AUTH_002"
    INVALID_TOKEN = "AUTH_003"
    TOKEN_EXPIRED = "AUTH_004"
    INSUFFICIENT_PERMISSIONS = "AUTH_005"
    
    # API & External Services
    API_RATE_LIMIT_EXCEEDED = "API_001"
    API_SERVICE_UNAVAILABLE = "API_002"
    API_INVALID_RESPONSE = "API_003"
    API_TIMEOUT = "API_004"
    API_QUOTA_EXCEEDED = "API_005"
    
    # Data & Validation
    INVALID_INPUT_DATA = "DATA_001"
    MISSING_REQUIRED_FIELD = "DATA_002"
    DATA_VALIDATION_FAILED = "DATA_003"
    INVALID_DATA_FORMAT = "DATA_004"
    DATA_NOT_FOUND = "DATA_005"
    
    # Business Logic
    INSUFFICIENT_FUNDS = "BIZ_001"
    INVALID_OPERATION = "BIZ_002"
    BUSINESS_RULE_VIOLATION = "BIZ_003"
    PORTFOLIO_LIMIT_EXCEEDED = "BIZ_004"
    TRADING_HOURS_CLOSED = "BIZ_005"
    
    # System & Infrastructure
    DATABASE_CONNECTION_ERROR = "SYS_001"
    CACHE_ERROR = "SYS_002"
    FILE_SYSTEM_ERROR = "SYS_003"
    NETWORK_ERROR = "SYS_004"
    INTERNAL_SERVER_ERROR = "SYS_005"
    
    # Machine Learning
    ML_MODEL_ERROR = "ML_001"
    ML_PREDICTION_FAILED = "ML_002"
    ML_TRAINING_FAILED = "ML_003"
    ML_DATA_INSUFFICIENT = "ML_004"
    ML_MODEL_NOT_LOADED = "ML_005"


@dataclass
class ErrorContext:
    """Error context information"""
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    timestamp: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class EnterpriseException(Exception):
    """Base enterprise exception class"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.context = context or ErrorContext()
        self.original_exception = original_exception
        self.timestamp = self.context.timestamp or self._get_timestamp()
        
        # Log the exception
        self._log_exception()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _log_exception(self):
        """Log the exception"""
        logger = logging.getLogger(__name__)
        
        log_data = {
            'error_code': self.error_code.value,
            'message': self.message,
            'status_code': self.status_code,
            'context': self.context.__dict__,
            'timestamp': self.timestamp
        }
        
        if self.original_exception:
            log_data['original_exception'] = str(self.original_exception)
            log_data['traceback'] = traceback.format_exc()
        
        if self.status_code >= 500:
            logger.error(f"Enterprise Exception: {json.dumps(log_data)}")
        else:
            logger.warning(f"Enterprise Exception: {json.dumps(log_data)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            'error_code': self.error_code.value,
            'message': self.message,
            'status_code': self.status_code,
            'timestamp': self.timestamp,
            'context': self.context.__dict__ if self.context else None
        }


class AuthenticationException(EnterpriseException):
    """Authentication related exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AUTHENTICATION_FAILED, **kwargs):
        super().__init__(message, error_code, status_code=401, **kwargs)


class AuthorizationException(EnterpriseException):
    """Authorization related exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AUTHORIZATION_DENIED, **kwargs):
        super().__init__(message, error_code, status_code=403, **kwargs)


class ValidationException(EnterpriseException):
    """Data validation exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INVALID_INPUT_DATA, **kwargs):
        super().__init__(message, error_code, status_code=400, **kwargs)


class APIException(EnterpriseException):
    """API related exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.API_SERVICE_UNAVAILABLE, **kwargs):
        super().__init__(message, error_code, status_code=502, **kwargs)


class BusinessLogicException(EnterpriseException):
    """Business logic exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INVALID_OPERATION, **kwargs):
        super().__init__(message, error_code, status_code=422, **kwargs)


class SystemException(EnterpriseException):
    """System related exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR, **kwargs):
        super().__init__(message, error_code, status_code=500, **kwargs)


class MLException(EnterpriseException):
    """Machine learning related exceptions"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.ML_MODEL_ERROR, **kwargs):
        super().__init__(message, error_code, status_code=500, **kwargs)


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_exception(exception: Exception, context: Optional[ErrorContext] = None) -> EnterpriseException:
        """Convert any exception to EnterpriseException"""
        
        if isinstance(exception, EnterpriseException):
            return exception
        
        # Map common exceptions to enterprise exceptions
        if isinstance(exception, ValidationError):
            return ValidationException(
                message=str(exception),
                error_code=ErrorCode.DATA_VALIDATION_FAILED,
                context=context,
                original_exception=exception
            )
        
        if isinstance(exception, ConnectionError):
            return SystemException(
                message="Database connection failed",
                error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
                context=context,
                original_exception=exception
            )
        
        if isinstance(exception, TimeoutError):
            return APIException(
                message="Request timeout",
                error_code=ErrorCode.API_TIMEOUT,
                context=context,
                original_exception=exception
            )
        
        # Default to system exception
        return SystemException(
            message=str(exception),
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            context=context,
            original_exception=exception
        )
    
    @staticmethod
    def create_error_response(exception: EnterpriseException) -> JsonResponse:
        """Create standardized error response"""
        return JsonResponse(
            {
                'success': False,
                'error': exception.to_dict()
            },
            status=exception.status_code
        )
    
    @staticmethod
    def log_error(exception: Exception, context: Optional[ErrorContext] = None):
        """Log error with context"""
        logger = logging.getLogger(__name__)
        
        error_data = {
            'exception_type': type(exception).__name__,
            'message': str(exception),
            'context': context.__dict__ if context else None,
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"Error occurred: {json.dumps(error_data)}")


def enterprise_exception_handler(func):
    """Decorator for enterprise exception handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(args[0], 'user_id', None) if args else None,
                endpoint=getattr(args[0], 'endpoint', None) if args else None,
                method=getattr(args[0], 'method', None) if args else None
            )
            
            enterprise_exception = ErrorHandler.handle_exception(e, context)
            raise enterprise_exception
    
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate required fields in data"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationException(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            error_code=ErrorCode.MISSING_REQUIRED_FIELD
        )


def validate_data_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """Validate data types"""
    for field, expected_type in field_types.items():
        if field in data and not isinstance(data[field], expected_type):
            raise ValidationException(
                message=f"Field '{field}' must be of type {expected_type.__name__}",
                error_code=ErrorCode.INVALID_DATA_FORMAT
            )
