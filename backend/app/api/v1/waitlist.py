"""Waitlist endpoints."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from app.core import logger
from app.db.session import get_db_connection

router = APIRouter()

MAX_REQUESTS_PER_MINUTE = 5


class WaitlistRequest(BaseModel):
    email: EmailStr


class WaitlistResponse(BaseModel):
    status: str
    already_joined: bool


@router.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(payload: WaitlistRequest, request: Request) -> WaitlistResponse:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    email = payload.email.lower()

    async with get_db_connection() as conn:
        if ip_address:
            rate_limit = await conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM waitlist_requests
                    WHERE ip_address = :ip
                      AND created_at > now() - interval '1 minute'
                    """
                ),
                {"ip": ip_address},
            )
            if rate_limit.scalar_one() >= MAX_REQUESTS_PER_MINUTE:
                logger.warning("Waitlist rate limit hit for ip=%s", ip_address)
                raise HTTPException(status_code=429, detail="Too many requests")

        await conn.execute(
            text(
                """
                INSERT INTO waitlist_requests (ip_address)
                VALUES (:ip)
                """
            ),
            {"ip": ip_address},
        )

        result = await conn.execute(
            text(
                """
                INSERT INTO waitlist (email, ip_address, user_agent)
                VALUES (:email, :ip, :ua)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
                """
            ),
            {"email": email, "ip": ip_address, "ua": user_agent},
        )
        inserted = result.fetchone() is not None

    return WaitlistResponse(status="ok", already_joined=not inserted)
