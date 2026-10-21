"""Multi-format date normalizer to ISO-8601 format.
Parses ISO, US, European, and relative date expressions cleanly.
"""
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Optional


class DateNormalizer:
    """Normalizes heterogeneous date strings into standard ISO-8601 'YYYY-MM-DD' dates."""

    KNOWN_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    @classmethod
    def parse_relative_date(cls, text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
        """Convert relative expressions like '3 days ago' or 'yesterday' to ISO date."""
        ref = reference_date or datetime.now(timezone.utc)
        clean = text.lower().strip()

        if clean in ("today", "just posted", "just now", "0 days ago"):
            return ref.strftime("%Y-%m-%d")
        if clean in ("yesterday", "1 day ago"):
            return (ref - timedelta(days=1)).strftime("%Y-%m-%d")

        # Match 'X days ago'
        m_days = re.search(r"(\d+)\s+days?\s+ago", clean)
        if m_days:
            days = int(m_days.group(1))
            return (ref - timedelta(days=days)).strftime("%Y-%m-%d")

        # Match 'X weeks ago'
        m_weeks = re.search(r"(\d+)\s+weeks?\s+ago", clean)
        if m_weeks:
            weeks = int(m_weeks.group(1))
            return (ref - timedelta(days=weeks * 7)).strftime("%Y-%m-%d")

        # Match 'X hours ago'
        m_hours = re.search(r"(\d+)\s+hours?\s+ago", clean)
        if m_hours:
            hours = int(m_hours.group(1))
            return (ref - timedelta(hours=hours)).strftime("%Y-%m-%d")

        return None

    @classmethod
    def normalize_date(cls, raw_date: Any, reference_date: Optional[datetime] = None) -> Optional[str]:
        """Normalize arbitrary date representation into 'YYYY-MM-DD'.
        
        Returns:
            Normalized date string 'YYYY-MM-DD' if parsed, or None if missing or unparseable.
        """
        if raw_date is None:
            return None
        text = str(raw_date).strip()
        if not text or text.lower() in ("null", "none", "nan", "n/a", ""):
            return None

        # Check relative dates first
        rel = cls.parse_relative_date(text, reference_date=reference_date)
        if rel:
            return rel

        # Try standard known datetime format strings
        for fmt in cls.KNOWN_FORMATS:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Try dateutil parser if available as fallback
        try:
            from dateutil import parser as dateutil_parser
            dt = dateutil_parser.parse(text)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

        return None
