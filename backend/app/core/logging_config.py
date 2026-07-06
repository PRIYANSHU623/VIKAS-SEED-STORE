"""
Structured Logging Configuration for KrishiSathi
Handles JSON logging with separate log files for different concerns
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
import os
from typing import Any, Dict

from app.core.config import LOG_LEVEL, ENVIRONMENT


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": ENVIRONMENT,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration
        
        return json.dumps(log_data, default=str)


def setup_logging(log_dir: str = "logs") -> None:
    """
    Configure structured logging for all modules
    
    Logs are separated into:
    - app.log: Application logs
    - error.log: Error logs only
    - access.log: API access logs
    - ai.log: AI/ML service logs
    - scanner.log: Scanner service logs
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (for development)
    if ENVIRONMENT == "development":
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Application log file
    app_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=10
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(JSONFormatter())
    
    # Error log file
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # API Access log file
    access_handler = logging.handlers.RotatingFileHandler(
        log_path / "access.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=10
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(JSONFormatter())
    
    # AI service log file
    ai_handler = logging.handlers.RotatingFileHandler(
        log_path / "ai.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=10
    )
    ai_handler.setLevel(log_level)
    ai_handler.setFormatter(JSONFormatter())
    
    # Scanner service log file
    scanner_handler = logging.handlers.RotatingFileHandler(
        log_path / "scanner.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=10
    )
    scanner_handler.setLevel(log_level)
    scanner_handler.setFormatter(JSONFormatter())
    
    # Add handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").addHandler(access_handler)
    logging.getLogger("app.services.agent").addHandler(ai_handler)
    logging.getLogger("app.routers.scanner").addHandler(scanner_handler)
    
    # Suppress noisy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
