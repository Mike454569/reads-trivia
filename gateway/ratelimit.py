"""Reads Engine Gateway -- rate limiting (Director v0.7, Part G).

A simple in-process sliding-window counter, deliberately not backed by
Redis or any external store. Documented, disclosed limitation: this does
NOT survive a process restart (a fresh window starts empty) and does NOT
coordinate across multiple instances -- both are fine for this milestone's
single-instance, admin-only staging target (Part H's single-generation-job
design already assumes one process), and both are exactly the kind of
"blindly implement public-scale infrastructure private staging does not
yet require" the milestone's Part A explicitly warns against. A future
public-production milestone would need a shared store (Redis, or the
platform's own rate-limiting layer) precisely because multi-instance
coordination matters at that scale and doesn't here.

This is server-side and mandatory -- Part G is explicit that frontend
throttling alone is not acceptable, and nothing here depends on any client
behaving honestly.
"""
from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, float]:
        """Returns (allowed, retry_after_seconds). retry_after_seconds is
        0 when allowed=True. Bounded memory: each key's deque never holds
        more than max_requests timestamps, and only keys seen recently
        exist at all -- no unbounded growth from a churn of distinct keys
        (each key's queue self-trims on every call)."""
        now = time.monotonic()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] > self.window_seconds:
                q.popleft()
            if len(q) >= self.max_requests:
                retry_after = self.window_seconds - (now - q[0])
                return False, max(retry_after, 0.1)
            q.append(now)
            return True, 0.0

    def reset(self) -> None:
        """Test-only helper -- production code never needs to reset limiter state."""
        with self._lock:
            self._hits.clear()
