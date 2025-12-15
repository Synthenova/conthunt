"""Media API endpoint - GET /v1/media/{asset_id}/signed-url."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.core import logger
from app.db import get_db_connection, get_or_create_user, set_rls_user, queries
from app.storage import gcs_client
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
        expiration = 3600  # 1 hour
        signed_url = gcs_client.generate_signed_url(
            gcs_uri=asset["gcs_uri"],
            expiration_seconds=expiration,
        )
        
        return SignedUrlResponse(
            url=signed_url,
            expires_in=expiration,
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate signed URL")
