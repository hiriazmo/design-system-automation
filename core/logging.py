"""
Structured Logging for Design System Extractor
================================================

Provides consistent logging across the application using loguru.
Falls back to standard logging if loguru is not available.
"""

import sys
from typing import Optional

try:
    from loguru import logger as _loguru_logger

    # Remove default handler
    _loguru_logger.remove()

    # Add structured console handler
    _loguru_logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[module]}</cyan> | {message}",
        level="INFO",
        colorize=True,
    )

    # Add file handler for debugging (rotated)
    _loguru_logger.add(
        "logs/extractor_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        catch=True,  # Don't crash on log errors
    )

    HAS_LOGURU = True

except ImportError:
    import logging

    HAS_LOGURU = False
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def get_logger(module_name: str = "app"):
    """
    Get a logger instance for a specific module.

    Args:
        module_name: Name of the module (e.g., 'rule_engine', 'aurora', 'app')

    Returns:
        Logger instance with module context
    """
    if HAS_LOGURU:
        return _loguru_logger.bind(module=module_name)
    else:
        return logging.getLogger(module_name)


# Pre-configured loggers for common modules
app_logger = get_logger("app")
rule_engine_logger = get_logger("rule_engine")
agent_logger = get_logger("agents")
extraction_logger = get_logger("extraction")
