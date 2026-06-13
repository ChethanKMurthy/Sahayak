"""Request-ID + timing middleware.

Tags every request with an `X-Request-ID` (honouring an inbound one if present)
and logs method, path, status and duration. Keeps logs PII-free — only the path
template-ish string is logged, never query/body contents.
"""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sahayak.request")

__all__ = ["RequestLogMiddleware"]


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.monotonic()
        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            logger.exception("%s %s -> ERROR (%.1fms) [%s]",
                             request.method, request.url.path, elapsed, request_id)
            raise
        elapsed = (time.monotonic() - start) * 1000
        logger.info("%s %s -> %s (%.1fms) [%s]",
                    request.method, request.url.path, response.status_code, elapsed, request_id)
        response.headers["X-Request-ID"] = request_id
        return response
