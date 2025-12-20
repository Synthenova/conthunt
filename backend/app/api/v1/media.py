"""Media API endpoint - GET /v1/media/{asset_id}/signed-url."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import get_current_user
from app.core import logger
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.services.cdn_signer import generate_signed_url
from app.schemas import SignedUrlResponse

router = APIRouter()


@router.get("/media/{asset_id}/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    asset_id: UUID,
    user: dict = Depends(get_current_user),
):
    """
    Generate a signed URL for a media asset.
    
    Verifies the user has access to the asset through RLS-protected tables
    (asset -> content_item -> search_result -> search).
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        # Get or create user
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        
        # Set RLS context
        await set_rls_user(conn, user_uuid)
        
        # Get asset with access check (joins through RLS-protected tables)
        asset = await queries.get_media_asset_with_access_check(conn, asset_id)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset["status"] != "stored" or not asset["gcs_uri"]:
        raise HTTPException(
            status_code=404,
            detail=f"Asset not available. Status: {asset['status']}"
        )
    
    try:
        # generate_signed_url is synchronous, so no await
        expiration = 3600  # 1 hour
        signed_url = generate_signed_url(
            gcs_filename=asset["gcs_uri"],
            expiration_seconds=expiration,
        )
        
        return SignedUrlResponse(
            url=signed_url,
            expires_in=expiration,
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate signed URL")


@router.get("/media/{asset_id}/content")
async def get_media_content(
    asset_id: UUID,
    user: dict = Depends(get_current_user),
):
    """
    Redirect to the GCS signed URL for a media asset.
    Used for persistent access to media (e.g., in history/boards).
    """
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    async with get_db_connection() as conn:
        user_uuid, _ = await get_or_create_user(conn, firebase_uid)
        await set_rls_user(conn, user_uuid)
        asset = await queries.get_media_asset_with_access_check(conn, asset_id)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check if we have the file
    if asset["status"] not in ("stored", "downloaded") or not asset["gcs_uri"]:
         # If not stored, we can't redirect to GCS.
         # For now, 404. Ideally we might redirect to source_url but that expires.
        raise HTTPException(status_code=404, detail="Media content not available in storage")
    
    try:
        # Generate short-lived signed URL
        signed_url = generate_signed_url(
            gcs_filename=asset["gcs_uri"],
            expiration_seconds=3600, # 1 hour
        )
        return RedirectResponse(url=signed_url, status_code=307)
    except Exception as e:
        logger.error(f"Failed to generate redirect for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve media content")


