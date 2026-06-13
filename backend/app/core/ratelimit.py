"""A dependency-free, in-process token-bucket rate limiter middleware.

Good enough to blunt accidental floods on a single instance (the MVP runs small).
It is intentionally per-process — for multi-instance limiting use a shared store.
Health checks are never limited so probes always succeed.
"""
from __future__ import annotations

import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

__all__ = ["RateLimitMiddleware"]


class _Bucket:
    __slots__ = ("tokens", "updated")

    def __init__(self, tokens: float, updated: float) -> None:
        self.tokens = tokens
        self.updated = updated


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate: float = 10.0, burst: int = 20, clock=time.monotonic) -> None:
        super().__init__(app)
        self._rate = rate          # tokens refilled per second
        self._burst = float(burst)  # bucket capacity
        self._clock = clock
        self._lock = threading.Lock()
        self._buckets: dict[str, _Bucket] = {}

    def _client(self, request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                self._buckets[key] = _Bucket(self._burst - 1, now)
                return True
            b.tokens = min(self._burst, b.tokens + (now - b.updated) * self._rate)
            b.updated = now
            if b.tokens >= 1:
                b.tokens -= 1
                return True
            return False

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path.startswith("/api/health"):
            return await call_next(request)
        if not self._allow(self._client(request)):
            return JSONResponse({"detail": "Too many requests"}, status_code=429,
                                headers={"Retry-After": "1"})
        response: Response = await call_next(request)
        return response
