"""Custom transformation function registry."""
from typing import Callable, Any

# Global registry of custom transform functions
_TRANSFORM_REGISTRY: dict[str, Callable[[Any], Any]] = {}


def register_transform(name: str, fn: Callable[[Any], Any]) -> None:
    """Register a custom transformation function."""
    _TRANSFORM_REGISTRY[name] = fn


def get_transform(name: str) -> Callable[[Any], Any] | None:
    """Retrieve a registered transform function by name."""
    return _TRANSFORM_REGISTRY.get(name)


def list_transforms() -> list[str]:
    """List all registered transform names."""
    return list(_TRANSFORM_REGISTRY.keys())


def clear_transforms() -> None:
    """Clear all registered transforms (useful for testing)."""
    _TRANSFORM_REGISTRY.clear()
