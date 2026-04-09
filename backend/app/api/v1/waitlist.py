"""Waitlist endpoints."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from upstash_ratelimit.asyncio import Ratelimit
from upstash_ratelimit.limiter import SlidingWindow

from app.core import logger
from app.core.redis_client import get_global_redis
from app.db.session import get_db_connection

router = APIRouter()

MAX_REQUESTS_PER_MINUTE = 5
waitlist_ratelimit = Ratelimit(
    redis=get_global_redis(),
    limiter=SlidingWindow(max_requests=MAX_REQUESTS_PER_MINUTE, window=60, unit="s"),
    prefix="rl:waitlist",
)


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

    if ip_address:
        response = await waitlist_ratelimit.limit(ip_address)
        if not response.allowed:
            logger.warning("Waitlist rate limit hit for ip=%s", ip_address)
            raise HTTPException(status_code=429, detail="Too many requests")

    async with get_db_connection() as conn:
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
