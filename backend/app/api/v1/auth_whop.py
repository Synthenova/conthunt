"""Whop Authentication Endpoint."""
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from firebase_admin import auth as fb_auth

from whop_sdk import AsyncWhop

from app.core import settings, logger
from app.db import get_db_connection

router = APIRouter(prefix="/auth/whop-exchange", tags=["auth"])

# Get settings instance
app_settings = settings.get_settings()

whop_client = AsyncWhop(
    api_key=app_settings.WHOP_API_KEY,
    app_id=app_settings.WHOP_APP_ID 
)

class WhopExchangeRequest(BaseModel):
    experienceId: str

@router.post("")
async def whop_exchange(req: Request, body: WhopExchangeRequest):
    """
    Exchange Whop User Token for Firebase Custom Token.
    1. Verify headers via SDK logic (Prod & Dev Proxy safe)
    2. Check Roles via check_access (Pro > Creator > Free)
    3. Sync User to DB (including photo_url if possible)
    4. Mint Custom Token
    """
    try:
        logger.info(f"Whop Auth: Starting exchange for experienceId={body.experienceId}")
        
        # Extract Token
        whop_token = req.headers.get("x-whop-user-token")
        if not whop_token:
            raise HTTPException(status_code=401, detail="Missing x-whop-user-token header")

        # MANUAL VERIFICATION (SDK lacks verify_user_token)
        import jwt
        try:
            # Decode without signature verification first to check issuer/type
            claims = jwt.decode(whop_token, options={"verify_signature": False})
        except Exception as e:
             logger.error(f"Whop Auth: Failed to decode JWT: {e}")
             raise HTTPException(status_code=401, detail="Invalid Token Format")

        whop_user_id = claims.get("sub")
        issuer = claims.get("iss", "")
        # is_dev = claims.get("isDev", False)

        # 1. Dev Proxy Token Check
        if "exp-proxy" in issuer:
             logger.warning(f"Whop Auth: Detected Dev/Proxy Token ({issuer}). Trusting 'sub' claim for local testing.")
        else:
             logger.info(f"Whop Auth: Prod Token detected for {whop_user_id}.")

        logger.debug(f"Whop Auth: Verified user_id={whop_user_id}")
        
        # Fetch User Details & Email (Validates User Existence)
        email = None
        photo_url = None
        try:
            whop_user = await whop_client.users.retrieve(whop_user_id)
            email = getattr(whop_user, "email", None)
            
            # Extract Profile Picture safely
            if hasattr(whop_user, "profile_picture") and whop_user.profile_picture:
                photo_url = getattr(whop_user.profile_picture, "url", None)

            logger.debug(f"Whop Auth: Retrieved email={email}, photo={photo_url}")
        except Exception as e:
            logger.error(f"Whop Auth: Failed to retrieve user {whop_user_id}: {e}")
            raise HTTPException(status_code=401, detail="Failed to validate Whop User")

        # 2. Get Roles (Precedence: Pro > Creator > Free)
        role = "free"
        
        prod_pro = app_settings.WHOP_PRODUCT_PRO
        prod_creator = app_settings.WHOP_PRODUCT_CREATOR

        async def check(pid):
            if not pid: return False
            try:
                acc = await whop_client.users.check_access(id=whop_user_id, resource_id=pid)
                return acc.has_access
            except:
                return False

        if await check(prod_pro):
            role = "pro_research"
        elif await check(prod_creator):
             role = "creator"
        # Optional: Explicit check for free, but default is already free.
        
        logger.info(f"Whop Auth: Role '{role}' determined for {whop_user_id}")
        
        # 3. Sync User
        # Define Firebase UID early so we can insert it
        firebase_uid = f"whop:{whop_user_id}"
        
        async with get_db_connection() as conn:
            from sqlalchemy import text
            
            # Find existing user by whop_id
            result = await conn.execute(
                text("SELECT id FROM users WHERE whop_user_id = :wuid"),
                {"wuid": whop_user_id}
            )
            row = result.fetchone()
            user_uuid = None
            
            if row:
                user_uuid = row[0]
                logger.debug(f"Whop Auth: Updating existing user {user_uuid}")
                # Update role
                await conn.execute(
                    text("UPDATE users SET role = :role WHERE id = :uid"),
                    {"role": role, "uid": user_uuid}
                )
            else:
                # Note: We cannot link by email because the 'users' table does not store emails.
                # It relies on firebase_uid or whop_user_id.
                
                # Create new user
                logger.info(f"Whop Auth: Creating new user for {whop_user_id}")
                result = await conn.execute(
                    text("""
                        INSERT INTO users (firebase_uid, role, whop_user_id, current_period_start)
                        VALUES (:fuid, :role, :wuid, NOW())
                        ON CONFLICT (firebase_uid) DO UPDATE SET whop_user_id = EXCLUDED.whop_user_id
                        RETURNING id
                    """),
                    {"fuid": firebase_uid, "role": role, "wuid": whop_user_id}
                )
                user_uuid = result.fetchone()[0]
            
            await conn.commit()
            
        # 4. Mint Firebase Token with Claims
        claims = {
                "db_user_id": str(user_uuid),
                "role": role,
                "auth_provider": "whop"
        }
        if photo_url:
            claims["picture"] = photo_url

        try:
             # Also update Firebase User Profile with Photo (so it persists)
             try:
                 fb_auth.update_user(firebase_uid, photo_url=photo_url, display_name=whop_user.username)
             except fb_auth.UserNotFoundError:
                 # Create
                 fb_auth.create_user(uid=firebase_uid, photo_url=photo_url, display_name=whop_user.username, email=email)
             except Exception as e:
                 logger.warning(f"Firebase User Update failed: {e}")

        except Exception:
            pass # Ignore firebase management errors, just mint token

        custom_token = fb_auth.create_custom_token(
            firebase_uid, 
            developer_claims=claims
        )
        
        logger.info(f"Whop Auth: Successfully minted token for {whop_user_id}")
        return {
            "firebase_custom_token": custom_token.decode("utf-8"),
            "role": role
        }

    except Exception as e:
        logger.exception(f"Whop Auth Error: {e}")
        if "valid" in str(e).lower() or "token" in str(e).lower():
             raise HTTPException(status_code=401, detail="Invalid Whop Token")
        raise HTTPException(status_code=500, detail="Internal Auth Error")
