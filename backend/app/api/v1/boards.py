from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.db.queries.content import get_video_media_asset_for_content_item
from app.schemas.boards import (
    BoardCreate, BoardResponse,
    BoardItemCreate, BoardItemResponse
)
from app.api.v1.analysis import run_gemini_analysis
from app.services.twelvelabs_processing import process_twelvelabs_indexing_by_media_asset

router = APIRouter()

@router.get("/", response_model=List[BoardResponse])
async def list_boards(
    user: dict = Depends(get_current_user),
):
    """List all boards for the current user."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user")
        
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        return await queries.get_user_boards(conn, user_uuid)


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
            
        return await queries.get_board_items(conn, board_id)


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
    
    # Trigger Gemini analysis (non-blocking)
    await run_gemini_analysis(media_asset_id, background_tasks)

    # Trigger TwelveLabs Indexing
    background_tasks.add_task(process_twelvelabs_indexing_by_media_asset, media_asset_id)
             
    return {"status": "added"}


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
            
        return await queries.search_in_board(conn, board_id, q)
