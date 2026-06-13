"""A small thread-safe TTL cache and a decorator.

Handy for caching the scheme/form knowledge-base load or eligibility explanations
for a short window without pulling in an external cache dependency. Time is taken
from a monotonic clock so it is immune to wall-clock changes.
"""
from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable, Hashable, TypeVar

T = TypeVar("T")

__all__ = ["TTLCache", "ttl_cached"]


class TTLCache:
    """A minimal key→value cache where entries expire after `ttl` seconds."""

    def __init__(self, ttl: float = 60.0, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl
        self._clock = clock
        self._lock = threading.Lock()
        self._store: dict[Hashable, tuple[float, Any]] = {}

    def get(self, key: Hashable, default: Any = None) -> Any:
        with self._lock:
            hit = self._store.get(key)
            if hit is None:
                return default
            expires_at, value = hit
            if self._clock() >= expires_at:
                self._store.pop(key, None)
                return default
            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._store[key] = (self._clock() + self._ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


def ttl_cached(ttl: float = 60.0) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Memoize a function's results for `ttl` seconds, keyed by its arguments."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        cache = TTLCache(ttl)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))
            sentinel = object()
            cached = cache.get(key, sentinel)
            if cached is not sentinel:
                return cached  # type: ignore[return-value]
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator
