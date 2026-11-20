"""Logging configuration for A11yCoach."""

import logging

from a11ycoach.core.settings import settings


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
