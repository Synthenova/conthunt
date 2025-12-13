"""Platforms package initialization."""
from .base import (
    AssetType,
    MediaUrl,
    NormalizedItem,
    ParsedPlatformResponse,
    PlatformCallResult,
    PlatformAdapter,
)
from .registry import PLATFORM_ADAPTERS, get_adapter, get_available_platforms

__all__ = [
    "AssetType",
    "MediaUrl",
    "NormalizedItem",
    "ParsedPlatformResponse",
    "PlatformCallResult",
    "PlatformAdapter",
    "PLATFORM_ADAPTERS",
    "get_adapter",
    "get_available_platforms",
]
