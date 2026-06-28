"""Built-in ETL transformation functions."""
import re
from datetime import datetime
from typing import Any


def coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def parse_date(value: Any, fmt: str = "%Y-%m-%d") -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            return None
    return None


def normalize_currency(value: Any) -> float:
    """Remove currency symbols and parse as float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove common currency symbols and thousands separators
        cleaned = re.sub(r"[$€£¥,\s]", "", value)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def strip_whitespace(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def map_values(value: Any, mapping: dict[Any, Any]) -> Any:
    """Map a value through a dictionary lookup."""
    return mapping.get(value, value)


def default_if_none(value: Any, default: Any) -> Any:
    """Return default if value is None, else value."""
    return default if value is None else value