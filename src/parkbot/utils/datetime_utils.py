"""Utility functions for datetime operations."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime.

    Replaces deprecated datetime.utcnow() which returns naive datetime.
    All datetime objects should be timezone-aware for consistency.

    Returns:
        datetime: Current UTC time with timezone info

    Example:
        >>> from parkbot.utils.datetime_utils import utcnow
        >>> created_at = utcnow()
        >>> print(created_at)
        2026-05-27 12:34:56.789012+00:00
    """
    return datetime.now(timezone.utc)
