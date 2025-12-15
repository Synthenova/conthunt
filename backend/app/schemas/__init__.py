"""Schemas package initialization."""
from .search import (
    SearchRequest,
    SearchResponse,
    PlatformResult,
    ContentItemResponse,
    AssetResponse,
    ResultItem,
)
from .history import (
    SearchHistoryItem,
    SearchHistoryResponse,
    PlatformCallInfo,
    AssetDetail,
    ContentItemDetail,
    SearchResultDetail,
    SearchDetailResponse,
)
from .media import SignedUrlResponse
from .roles import UserRole, UserRoleUpdate, UserInfo

__all__ = [
    # Search
    "SearchRequest",
    "SearchResponse",
    "PlatformResult",
    "ContentItemResponse",
    "AssetResponse",
    "ResultItem",
    # History
    "SearchHistoryItem",
    "SearchHistoryResponse",
    "PlatformCallInfo",
    "AssetDetail",
    "ContentItemDetail",
    "SearchResultDetail",
    "SearchDetailResponse",
    # Media
    "SignedUrlResponse",
    # Roles
    "UserRole",
    "UserRoleUpdate",
    "UserInfo",
]

