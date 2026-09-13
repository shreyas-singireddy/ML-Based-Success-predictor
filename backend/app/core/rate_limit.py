"""
Lightweight in-memory sliding-window rate limiting.

Used to guard the authentication and GenAI assistant endpoints. This is a
per-process limiter appropriate for a single-worker deployment (the default
production target). For multi-worker deployments the same policy must be moved
to a shared store (Redis) — documented in docs/production-deployment.md.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

logger = logging.getLogger("student_predictor.rate_limit")


@dataclass
class _Window:
    timestamps: List[float] = field(default_factory=list)


class RateLimiter:
    """Sliding-window limiter keyed by an arbitrary string (IP, user id, ...).

    `max_calls` may be a static integer or a zero-argument callable that is
    re-evaluated on every call (used to honor runtime configuration changes).
    """

    def __init__(
        self,
        max_calls: Union[int, Callable[[], int]],
        window_seconds: int = 60,
    ) -> None:
        self._max_calls = max_calls
        self.window_seconds = window_seconds
        self._buckets: Dict[str, _Window] = {}
        self._lock = threading.Lock()

    @property
    def max_calls(self) -> int:
        if callable(self._max_calls):
            return max(int(self._max_calls()), 1)
        return max(int(self._max_calls), 1)

    def check(self, key: str, *, cost: int = 1) -> bool:
        """Register `cost` calls for `key`. Returns True when the call is
        allowed, False when the limit would be exceeded."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets.setdefault(key, _Window())
            bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]
            if len(bucket.timestamps) + cost > self.max_calls:
                return False
            bucket.timestamps.extend([now] * cost)
            return True

    def remaining(self, key: str) -> int:
        """Remaining allowance for `key` in the current window."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                return self.max_calls
            active = [t for t in bucket.timestamps if t > cutoff]
            return max(0, self.max_calls - len(active))

    def reset(self, key: Optional[str] = None) -> None:
        """Clear limits for `key`, or all keys when `key` is None (tests/admin)."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)


def client_ip_key(request) -> str:
    """Build a rate-limit key from the caller's IP via observable headers."""
    from backend.app.core.observability import _client_host

    return f"ip:{_client_host(request)}"