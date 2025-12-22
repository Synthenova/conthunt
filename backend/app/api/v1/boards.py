from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.db.queries.content import get_video_media_asset_for_content_item
from app.schemas.boards import (
    BoardCreate, BoardResponse,
    BoardItemCreate, BoardItemBatchCreate, BoardItemResponse
)
from app.api.v1.analysis import run_gemini_analysis
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset
from app.services.cdn_signer import generate_signed_url
from app.services.cloud_tasks import cloud_tasks
from app.core import get_settings

settings = get_settings()

router = APIRouter()

@router.get("", response_model=List[BoardResponse])
@router.get("/", response_model=List[BoardResponse])
async def list_boards(
    check_item_id: Optional[UUID] = Query(None),
    user: dict = Depends(get_current_user),
):
    """List all boards for the current user."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        return await queries.get_user_boards(conn, user_uuid, check_content_item_id=check_item_id)


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_in: BoardCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new board."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")

    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        return await queries.search_user_boards(conn, user_uuid, q)


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get board details."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    print(f"[BOARD_SUMMARY] Request for board_id={board_id}")
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        
        # Verify board exists
        board = await queries.get_board_by_id(conn, board_id)
        print(f"[BOARD_SUMMARY] Board found: {board is not None}")
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        result = await queries.get_board_items_summary(conn, board_id)
        print(f"[BOARD_SUMMARY] Returning {len(result) if result else 0} items")
        return result


@router.post("/{board_id}/items", status_code=status.HTTP_201_CREATED)
async def add_item_to_board(
    board_id: UUID,
    item_in: BoardItemCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Add a content item to a board. Triggers Gemini analysis in background."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    await run_gemini_analysis(media_asset_id, background_tasks=None, use_cloud_tasks=True)

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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    media_asset_ids = []
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
        await run_gemini_analysis(media_asset_id, background_tasks=None, use_cloud_tasks=True)
        
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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
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
