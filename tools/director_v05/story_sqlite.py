"""Shared SQLite write helpers for Story Factory production paths."""
from __future__ import annotations

import sqlite3
import time

WRITE_BUSY_TIMEOUT_MS = 120_000
WRITE_COMMIT_ATTEMPTS = 8
WRITE_COMMIT_BACKOFF_SECONDS = 1.5


def prepare_write_connection(c):
    c.execute(f"PRAGMA busy_timeout={WRITE_BUSY_TIMEOUT_MS}")
    return c


def commit_with_retry(c, *, attempts=WRITE_COMMIT_ATTEMPTS):
    """Retry only transient SQLite busy/locked commits.

    All non-lock OperationalError values still fail immediately.
    """
    last = None
    for attempt in range(1, int(attempts) + 1):
        try:
            c.commit()
            return
        except sqlite3.OperationalError as exc:
            msg = str(exc).casefold()
            if "locked" not in msg and "busy" not in msg:
                raise
            last = exc
            if attempt >= int(attempts):
                raise
            time.sleep(WRITE_COMMIT_BACKOFF_SECONDS * attempt)
    if last:
        raise last
