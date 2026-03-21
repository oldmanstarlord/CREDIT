"""
Logging configuration: structured JSON logging for production
"""

import logging
import json
import sys
from datetime import datetime
from importlib import import_module
from app.core.config import settings


jsonlogger = None
try:
    jsonlogger = import_module("pythonjsonlogger.jsonlogger")
except Exception:
    jsonlogger = None


def setup_logging():
    """
    Configure structured JSON logging for production monitoring.
    Logs are sent to stdout/stderr where they can be collected by CloudWatch.
    """
    
    # Remove default handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    
    # JSON formatter with custom fields
    if jsonlogger is not None:
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s %(status_code)s %(user_id)s',
            timestamp=True
        )
        console_handler.setFormatter(json_formatter)
    else:
        plain_formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        console_handler.setFormatter(plain_formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(
        logging.DEBUG if settings.DEBUG else logging.INFO
    )
    
    return root_logger


# Initialize logger
logger = setup_logging()


class StructuredLogger:
    """
    Wrapper for structured logging with standard fields.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, extra={**kwargs, 'status_code': None, 'user_id': None})
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, extra={**kwargs, 'status_code': None, 'user_id': None})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, extra={**kwargs, 'status_code': None, 'user_id': None})
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, extra={**kwargs, 'status_code': None, 'user_id': None})
    
    def audit(self, event_type: str, user_id: str, **kwargs):
        """
        Log audit event (critical action with user context).
        
        Args:
            event_type: Type of event (application_submitted, decision_approved, etc.)
            user_id: ID of user who triggered the event
            **kwargs: Additional context fields
        """
        self.logger.info(
            f"AUDIT: {event_type}",
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
