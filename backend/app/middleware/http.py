"""HTTP middleware: request correlation ID and optional API key."""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

request_id_cv: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign X-Request-ID (reuse inbound header if present)."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
        rid = incoming.strip() if incoming else str(uuid.uuid4())
        request.state.request_id = rid
        token = request_id_cv.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_cv.reset(token)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """When AFE_API_KEY is set, require matching X-API-Key on all routes except health & OPTIONS."""

    async def dispatch(self, request: Request, call_next):
        if not settings.afe_api_key:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"
        if path == "/health":
            return await call_next(request)

        key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        rid = getattr(request.state, "request_id", None)
        if key != settings.afe_api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or missing API key",
                    "request_id": rid,
                },
                headers={"X-Request-ID": rid} if rid else {},
            )

        return await call_next(request)
