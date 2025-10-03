"""
Logging utilities for RichesReach.
"""
import os
import re
import logging


class RedactSecretsFilter(logging.Filter):
    """
    Filter to redact sensitive information from log messages.
    """
    
    def __init__(self):
        super().__init__()
        # List of environment variable names that contain secrets
        self.secret_keys = [
            'ALPHA_VANTAGE_API_KEY',
            'FINNHUB_API_KEY', 
            'NEWS_API_KEY',
            'POLYGON_API_KEY',
            'OPENAI_API_KEY',
            'SECRET_KEY',
            'DB_PASSWORD',
            'REDIS_PASSWORD',
            'EMAIL_HOST_PASSWORD',
            'SENTRY_DSN',
        ]
        
        # Get actual secret values to redact
        self.secrets_to_redact = []
        for key in self.secret_keys:
            value = os.getenv(key)
            if value:
                self.secrets_to_redact.append(value)
        
        # Common patterns to redact
        self.patterns = [
            r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        ]
    
    def filter(self, record):
        """Filter and redact sensitive information from log records."""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            
            # Redact known secret values
            for secret in self.secrets_to_redact:
                if secret in msg:
                    msg = msg.replace(secret, '***REDACTED***')
            
            # Redact patterns
            for pattern in self.patterns:
                msg = re.sub(pattern, r'\1=***REDACTED***', msg, flags=re.IGNORECASE)
            
            record.msg = msg
        
        return True


class ProductionLogFormatter(logging.Formatter):
    """
    Custom formatter for production logs with structured output.
    """
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return str(log_entry)
