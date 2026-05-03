"""Consistent JSON errors and sanitization of server-side failures."""
from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    rid = _rid(request)
    headers = {}
    if rid:
        headers["X-Request-ID"] = rid

    if exc.status_code >= 500:
        logger.error(
            "HTTP %s (sanitized for client): %s",
            exc.status_code,
            exc.detail,
            extra={"request_id": rid},
        )
        body = {"detail": "Internal server error", "request_id": rid}
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": rid},
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = _rid(request)
    headers = {}
    if rid:
        headers["X-Request-ID"] = rid

    logger.exception(
        "Unhandled exception",
        extra={"request_id": rid},
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": rid,
        },
        headers=headers,
    )
