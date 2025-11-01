"""Logging configuration and utilities."""

import sys
from typing import Any, Dict

import orjson
from loguru import logger

from ..config import config


def serialize_json(record: Dict[str, Any]) -> str:
    """Serialize log record to JSON."""
    # Extract necessary fields
    log_data = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add extra fields
    if record.get("extra"):
        log_data.update(record["extra"])
    
    # Add exception info if present
    if record.get("exception"):
        log_data["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback
        }
    
    return orjson.dumps(log_data).decode()


def redact_sensitive(message: str) -> str:
    """Redact sensitive information from log messages."""
    if not config.telemetry.redact_secrets:
        return message
    
    # Simple redaction patterns
    import re
    
    # Redact email addresses
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', message)
    
    # Redact API keys
    message = re.sub(r'(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?[\w-]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
    
    # Redact passwords
    message = re.sub(r'(password|pwd)["\']?\s*[:=]\s*["\']?[^"\'\s]+', r'\1=[REDACTED]', message, flags=re.IGNORECASE)
    
    return message


def setup_logging():
    """Configure logging based on settings."""
    # Remove default handler
    logger.remove()
    
    # Configure format based on json_logging setting
    if config.telemetry.json_logging:
        # JSON format
        logger.add(
            sys.stdout,
            format=lambda record: serialize_json(record) + "\n",
            level=config.settings.log_level,
            filter=lambda record: redact_sensitive(record["message"]) or True
        )
    else:
        # Human-readable format
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=config.settings.log_level,
            filter=lambda record: redact_sensitive(record["message"]) or True
        )
    
    # Add file output if configured
    if config.telemetry.sink in ("file", "both"):
        logger.add(
            "logs/mini-atlas.log",
            rotation="10 MB",
            retention="7 days",
            format=lambda record: serialize_json(record) + "\n" if config.telemetry.json_logging else "{time} | {level} | {message}",
            level=config.settings.log_level
        )


def get_logger(name: str) -> logger:
    """Get a contextualized logger."""
    return logger.bind(module=name)


# Setup logging on import
setup_logging()
