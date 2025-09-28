"""
Centralized logging configuration for StoryOS v2
Provides comprehensive logging with different levels and formatters
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset color
    }
    
    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

class StoryOSLogger:
    """Centralized logger for StoryOS application"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls, log_level: str = "INFO", log_to_file: bool = True, 
                     max_file_size_mb: int = 10, backup_count: int = 5, 
                     rotation_type: str = "size"):
        """
        Setup logging configuration for the entire application
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to files
            max_file_size_mb: Maximum size of each log file in MB (for size-based rotation)
            backup_count: Number of backup files to keep
            rotation_type: 'size' for size-based rotation, 'time' for time-based (daily)
        """
        if cls._configured:
            return
            
        # Convert log level string to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if log_to_file and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if enabled) with rotation
        if log_to_file:
            log_file = os.path.join(log_dir, "storyos.log")
            
            # Choose rotation type
            if rotation_type.lower() == "time":
                # Time-based rotation (daily)
                file_handler = TimedRotatingFileHandler(
                    log_file, 
                    when='midnight', 
                    interval=1,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                # Add date suffix to rotated files
                file_handler.suffix = "%Y%m%d"
            else:
                # Size-based rotation (default)
                max_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            
            file_handler.setLevel(numeric_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Error file handler with rotation (always log errors to separate file)
        if log_to_file:
            error_log_file = os.path.join(log_dir, "storyos_errors.log")
            
            # Smaller files for errors, size-based rotation only
            error_max_bytes = 5 * 1024 * 1024  # 5MB max for error files
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=error_max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
                'Exception: %(exc_info)s\n'
                '---',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(error_formatter)
            root_logger.addHandler(error_handler)
        
        # Set third-party loggers to WARNING to reduce noise
        logging.getLogger('pymongo').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        
        cls._configured = True
        
        # Log the setup completion
        logger = cls.get_logger("logging_config")
        logger.info(f"Logging configured - Level: {log_level}, File logging: {log_to_file}")
        if log_to_file:
            logger.info(f"Log files location: {os.path.abspath(log_dir)}")
            logger.info(f"Rotation: {rotation_type}, Max size: {max_file_size_mb}MB, Backup count: {backup_count}")
        else:
            logger.info("Console only logging")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if name not in cls._loggers:
            if not cls._configured:
                cls.setup_logging()
            
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]
    
    @classmethod
    def log_user_action(cls, user_id: str, action: str, details: Optional[dict] = None):
        """Log user actions with consistent format"""
        logger = cls.get_logger("user_actions")
        details_str = f" | Details: {details}" if details else ""
        logger.info(f"User: {user_id} | Action: {action}{details_str}")
    
    @classmethod
    def log_error_with_context(cls, logger_name: str, error: Exception, context: Optional[dict] = None):
        """Log errors with additional context information"""
        logger = cls.get_logger(logger_name)
        context_str = f" | Context: {context}" if context else ""
        logger.error(f"Error: {str(error)}{context_str}", exc_info=True)
    
    @classmethod 
    def log_performance(cls, logger_name: str, operation: str, duration: float, details: Optional[dict] = None):
        """Log performance metrics"""
        logger = cls.get_logger(logger_name)
        details_str = f" | Details: {details}" if details else ""
        logger.info(f"Performance | Operation: {operation} | Duration: {duration:.3f}s{details_str}")
    
    @classmethod
    def log_api_call(cls, service: str, endpoint: str, status: str, duration: float, details: Optional[dict] = None):
        """Log API calls with consistent format"""
        logger = cls.get_logger("api_calls")
        details_str = f" | Details: {details}" if details else ""
        logger.info(f"API Call | Service: {service} | Endpoint: {endpoint} | Status: {status} | Duration: {duration:.3f}s{details_str}")

# Convenience function to get logger instances
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (convenience function)"""
    return StoryOSLogger.get_logger(name)

# Setup logging when module is imported
def initialize_logging():
    """Initialize logging based on environment variables or defaults"""
    log_level = os.getenv('STORYOS_LOG_LEVEL', 'INFO')
    log_to_file = os.getenv('STORYOS_LOG_TO_FILE', 'true').lower() == 'true'
    
    # File rotation configuration
    max_file_size_mb = int(os.getenv('STORYOS_LOG_MAX_SIZE_MB', '10'))
    backup_count = int(os.getenv('STORYOS_LOG_BACKUP_COUNT', '5'))
    rotation_type = os.getenv('STORYOS_LOG_ROTATION_TYPE', 'size')  # 'size' or 'time'
    
    StoryOSLogger.setup_logging(
        log_level=log_level, 
        log_to_file=log_to_file,
        max_file_size_mb=max_file_size_mb,
        backup_count=backup_count,
        rotation_type=rotation_type
    )

# Auto-initialize logging
initialize_logging()
