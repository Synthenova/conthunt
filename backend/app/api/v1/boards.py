from typing import List, Optional
from uuid import UUID
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.db import get_db_connection, set_rls_user, queries
from app.db.queries.content import get_video_media_asset_for_content_item
from app.schemas.boards import (
    BoardCreate, BoardResponse,
    BoardItemCreate, BoardItemBatchCreate, BoardItemResponse
)
from app.schemas.insights import BoardInsightsResponse, BoardInsightsResult, BoardInsightsProgress
from app.api.v1.analysis import run_gemini_analysis
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.services.cdn_signer import generate_signed_url
from app.services.cloud_tasks import cloud_tasks

from app.core import get_settings, logger

settings = get_settings()

router = APIRouter()

@router.get("", response_model=List[BoardResponse])
@router.get("/", response_model=List[BoardResponse])
async def list_boards(
    check_item_id: Optional[UUID] = Query(None),
    user: dict = Depends(get_current_user),
):
    """List all boards for the current user."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        boards = await queries.get_user_boards(conn, user_uuid, check_content_item_id=check_item_id)
        for board in boards:
            preview_urls = board.get("preview_urls") or []
            signed_urls = []
            for url in preview_urls:
                if url and url.startswith("gs://"):
                    signed_urls.append(generate_signed_url(url))
                else:
                    signed_urls.append(url)
            board["preview_urls"] = signed_urls
        return boards


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_in: BoardCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new board."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        board_id = await queries.create_board(conn, user_uuid, board_in.name)
        
        board = await queries.get_board_by_id(conn, board_id)
        await conn.commit()
        
        return board


@router.get("/search", response_model=List[BoardResponse])
async def search_boards(
    q: str,
    user: dict = Depends(get_current_user),
):
    """Search global boards (by name or content)."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        return await queries.search_user_boards(conn, user_uuid, q)


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get board details."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a board."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        success = await queries.delete_board(conn, board_id)
        if not success:
            raise HTTPException(status_code=404, detail="Board not found")
        await conn.commit()


@router.get("/{board_id}/items", response_model=List[BoardItemResponse])
async def get_board_items(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get items in a board."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        # Verify board exists
        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        items = await queries.get_board_items(conn, board_id)        
        
        # Sign URLs for stored assets        
        for item in items:
            for asset in item.get("assets", []):
                if asset.get("status") in ("stored", "downloaded") and asset.get("gcs_uri"):
                    asset["source_url"] = generate_signed_url(asset["gcs_uri"])        

        return items


@router.get("/{board_id}/items/summary")
async def get_board_items_summary(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get board items summary for agent - minimal text data + media_asset_id only."""
    logger.debug(f"[BOARD_SUMMARY] Request for board_id={board_id}")
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        # Verify board exists
        board = await queries.get_board_by_id(conn, board_id)
        logger.debug(f"[BOARD_SUMMARY] Board found: {board is not None}")
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        result = await queries.get_board_items_summary(conn, board_id)
        logger.debug(f"[BOARD_SUMMARY] Returning {len(result) if result else 0} items")
        return result


@router.get("/{board_id}/insights", response_model=BoardInsightsResponse)
async def get_board_insights(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get cached board insights with progress tracking."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)

        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")

        insights = await queries.get_board_insights(conn, board_id)
        progress_data = await queries.get_board_insights_progress(conn, board_id)
        progress = BoardInsightsProgress(
            total_videos=progress_data["total_videos"],
            analyzed_videos=progress_data["analyzed_videos"],
            failed_videos=progress_data["failed_videos"],
        )

        if not insights:
            return BoardInsightsResponse(
                board_id=board_id,
                status="empty",
                progress=progress,
            )

        insights_result = insights.get("insights_result") or {}
        parsed_insights = None
        if insights_result:
            parsed_insights = BoardInsightsResult(**insights_result)

        return BoardInsightsResponse(
            id=insights.get("id"),
            board_id=board_id,
            status=insights.get("status", "processing"),
            insights=parsed_insights,
            progress=progress,
            error=insights.get("error"),
            created_at=insights.get("created_at"),
            updated_at=insights.get("updated_at"),
            last_completed_at=insights.get("last_completed_at"),
        )


@router.post("/{board_id}/insights/refresh", response_model=BoardInsightsResponse)
async def refresh_board_insights(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Trigger background refresh for board insights."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)

        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")

        await queries.upsert_pending_board_insights(conn, board_id)
        insights = await queries.get_board_insights(conn, board_id)
        progress_data = await queries.get_board_insights_progress(conn, board_id)

    await cloud_tasks.create_http_task(
        queue_name=settings.QUEUE_GEMINI,
        relative_uri="/v1/tasks/boards/insights",
        payload={
            "board_id": str(board_id),
            "user_id": str(user_uuid),
            "user_role": user.get("role"),
        },
    )

    insights_result = insights.get("insights_result") if insights else {}
    parsed_insights = None
    if insights_result:
        parsed_insights = BoardInsightsResult(**insights_result)

    progress = BoardInsightsProgress(
        total_videos=progress_data["total_videos"],
        analyzed_videos=progress_data["analyzed_videos"],
        failed_videos=progress_data["failed_videos"],
    )

    return BoardInsightsResponse(
        id=insights.get("id") if insights else None,
        board_id=board_id,
        status="processing",
        insights=parsed_insights,
        progress=progress,
        created_at=insights.get("created_at") if insights else None,
        updated_at=insights.get("updated_at") if insights else None,
        last_completed_at=insights.get("last_completed_at") if insights else None,
    )


@router.post("/{board_id}/items", status_code=status.HTTP_201_CREATED)
async def add_item_to_board(
    board_id: UUID,
    item_in: BoardItemCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Add a content item to a board. Triggers Gemini analysis in background."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        try:
            await queries.add_item_to_board(conn, board_id, item_in.content_item_id)
            await conn.commit()
        except Exception:
             raise HTTPException(status_code=400, detail="Could not add item (check board/item id)")
        
        # Resolve content_item_id to media_asset_id for background tasks
        media_asset = await get_video_media_asset_for_content_item(conn, item_in.content_item_id)
        if not media_asset:
            # No video asset - skip analysis but still return success
            return {"status": "added"}
        
        media_asset_id = media_asset.get("id")
    
    # Trigger Gemini analysis (via Cloud Tasks)
    # NOTE: Gemini analysis disabled to reduce costs.
    # await run_gemini_analysis(media_asset_id, background_tasks=None, use_cloud_tasks=True)

    # Trigger TwelveLabs Indexing (via Cloud Tasks)
    await cloud_tasks.create_http_task(
        queue_name=settings.QUEUE_TWELVELABS,
        relative_uri="/v1/tasks/twelvelabs/index",
        payload={"media_asset_id": str(media_asset_id)}
    )
             
    return {"status": "added"}


@router.post("/{board_id}/items/batch", status_code=status.HTTP_201_CREATED)
async def batch_add_items_to_board(
    board_id: UUID,
    items_in: BoardItemBatchCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Add multiple content items to a board in a single request.
    
    More efficient than calling the single-item endpoint multiple times.
    Triggers Gemini analysis for each video in the background.
    """
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    media_asset_ids = []
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        # Verify board exists
        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        try:
            inserted_count = await queries.batch_add_items_to_board(
                conn, board_id, items_in.content_item_ids
            )
            await conn.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not add items: {str(e)}")
        
        # Collect media_asset_ids for background processing
        for content_item_id in items_in.content_item_ids:
            media_asset = await get_video_media_asset_for_content_item(conn, content_item_id)
            if media_asset:
                media_asset_ids.append(media_asset.get("id"))
    
    # Trigger background analysis for each video
    for media_asset_id in media_asset_ids:
        # Trigger Gemini via Cloud Tasks (passed flag)
        # NOTE: Gemini analysis disabled to reduce costs.
        # await run_gemini_analysis(media_asset_id, background_tasks=None, use_cloud_tasks=True)
        
        # Trigger TwelveLabs via Cloud Tasks directly
        await cloud_tasks.create_http_task(
           queue_name=settings.QUEUE_TWELVELABS,
           relative_uri="/v1/tasks/twelvelabs/index",
           payload={"media_asset_id": str(media_asset_id)}
        )
    
    return {
        "status": "added",
        "items_added": inserted_count,
        "total_requested": len(items_in.content_item_ids),
    }


@router.delete("/{board_id}/items/{content_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_board(
    board_id: UUID,
    content_item_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Remove item from board."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        success = await queries.remove_item_from_board(conn, board_id, content_item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item not found in board")
        await conn.commit()


@router.get("/{board_id}/search", response_model=List[BoardItemResponse])
async def search_in_board(
    board_id: UUID,
    q: str,
    user: dict = Depends(get_current_user),
):
    """Search within a specific board."""
    user_uuid = user["db_user_id"]
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        await set_rls_user(conn, user_uuid)
        
        board = await queries.get_board_by_id(conn, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
            
        items = await queries.search_in_board(conn, board_id, q)
        
        # Sign URLs for stored assets
        for item in items:
            for asset in item.get("assets", []):
                if asset.get("status") in ("stored", "downloaded") and asset.get("gcs_uri"):
                    asset["source_url"] = generate_signed_url(asset["gcs_uri"])
                    
        return items
