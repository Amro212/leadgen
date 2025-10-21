"""
Logging utilities using Loguru.
Provides a logger factory with console and rotating file handlers.
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import SETTINGS


def setup_logger():
    """
    Configure the loguru logger with console and file handlers.
    
    Returns:
        logger: Configured loguru logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=SETTINGS.LOG_LEVEL
    )
    
    # Add rotating file handler
    log_file = SETTINGS.LOG_DIR / "app.log"
    logger.add(
        log_file,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress rotated logs
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=SETTINGS.LOG_LEVEL
    )
    
    return logger


def get_logger(name: str):
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name for the logger (usually __name__)
    
    Returns:
        logger: Logger instance bound to the given name
    """
    return logger.bind(name=name)


# Initialize logger on import
setup_logger()
