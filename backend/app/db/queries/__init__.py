"""
Database query functions - modular organization.

All functions are re-exported here for backwards compatibility.
Import from specific modules for cleaner code:
    from app.db.queries.search import insert_search
    from app.db.queries.boards import create_board
    from app.db.queries.analysis import get_video_analysis_by_content_item
    from app.db.queries.content import get_content_item_by_id
    from app.db.queries.users import get_user_role
"""

# Search queries
from app.db.queries.search import (
    compute_search_hash,
    insert_search,
    insert_platform_call,
    upsert_content_item,
    insert_search_result,
    insert_media_asset,
    get_search_by_id,
    get_user_searches,
    get_platform_calls_for_search,
    get_search_results_with_content,
    get_media_asset_with_access_check,
)

# Board queries
from app.db.queries.boards import (
    create_board,
    get_user_boards,
    get_board_by_id,
    delete_board,
    add_item_to_board,
    remove_item_from_board,
    get_board_items,
    search_user_boards,
    search_in_board,
)

# TwelveLabs queries (indexing only)
from app.db.queries.twelvelabs import (
    get_twelvelabs_asset_by_content_item,
    upsert_twelvelabs_asset,
    update_twelvelabs_asset_status,
)

# Analysis queries (Gemini-based)
from app.db.queries.analysis import (
    get_video_analysis_by_content_item,
    insert_video_analysis,
    create_pending_analysis,
    update_analysis_status,
)

# Content queries (shared)
from app.db.queries.content import (
    get_content_item_by_id,
)

# User queries
from app.db.queries.users import (
    get_user_role,
    update_user_role,
    update_user_role,
    update_user_dodo_subscription,
)

# Chat queries
from app.db.queries.chats import (
    create_chat,
    get_user_chats,
    get_chat_thread_id,
    check_chat_exists,
    delete_chat,
)

__all__ = [
    # Search
    "compute_search_hash",
    "insert_search",
    "insert_platform_call",
    "upsert_content_item",
    "insert_search_result",
    "insert_media_asset",
    "get_search_by_id",
    "get_user_searches",
    "get_platform_calls_for_search",
    "get_search_results_with_content",
    "get_media_asset_with_access_check",
    # Boards
    "create_board",
    "get_user_boards",
    "get_board_by_id",
    "delete_board",
    "add_item_to_board",
    "remove_item_from_board",
    "get_board_items",
    "search_user_boards",
    "search_in_board",
    # TwelveLabs
    "get_twelvelabs_asset_by_content_item",
    "upsert_twelvelabs_asset",
    "update_twelvelabs_asset_status",
    "get_video_analysis_by_content_item",
    "insert_video_analysis",
    "create_pending_analysis",
    "update_analysis_status",
    # Content
    "get_content_item_by_id",
    # Users
    "get_user_role",
    "update_user_role",
    "update_user_dodo_subscription",
    # Chats
    "create_chat",
    "get_user_chats",
    "get_chat_thread_id",
    "check_chat_exists",
    "delete_chat",
]

