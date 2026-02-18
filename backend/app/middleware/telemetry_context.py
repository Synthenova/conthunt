from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.telemetry_context import (
    attach_request_telemetry,
    bind_telemetry,
    telemetry_from_headers,
)


class TelemetryContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ctx = telemetry_from_headers(request.headers)
        attach_request_telemetry(request, ctx)

        with bind_telemetry(ctx):
            response: Response = await call_next(request)

        # Echo action id to aid client/support correlation.
        if ctx.action_id:
            response.headers.setdefault("x-action-id", ctx.action_id)

        return response
