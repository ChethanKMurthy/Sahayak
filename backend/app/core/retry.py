"""A tiny synchronous retry-with-backoff helper.

Used to wrap flaky outbound calls (e.g. LLM / provider HTTP) so a transient
failure doesn't surface to the user. Backoff is deterministic (no randomness),
which keeps tests reproducible — see the project's no-`random` constraint.
"""
from __future__ import annotations

import functools
import time
from typing import Callable, Tuple, Type, TypeVar

T = TypeVar("T")

__all__ = ["retry", "with_retry"]


def retry(
    attempts: int = 3,
    base_delay: float = 0.2,
    factor: float = 2.0,
    max_delay: float = 5.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: retry the wrapped call up to `attempts` times on `exceptions`.

    Delay before attempt *n* (1-indexed) is min(base_delay * factor**(n-1), max_delay).
    Re-raises the last exception once attempts are exhausted.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last: BaseException | None = None
            for n in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203
                    last = exc
                    if n == attempts - 1:
                        break
                    sleep(min(base_delay * (factor ** n), max_delay))
            assert last is not None
            raise last

        return wrapper

    return decorator


def with_retry(fn: Callable[..., T], *args, **kwargs) -> T:
    """Call `fn(*args, **kwargs)` with the default retry policy. Convenience wrapper."""
    return retry()(fn)(*args, **kwargs)
