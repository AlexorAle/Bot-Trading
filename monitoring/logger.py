"""Logging helper for monitoring subpackage."""

import logging
from typing import Optional


def get_monitoring_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger configured for monitoring components."""
    logger = logging.getLogger(name or "monitoring")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger




