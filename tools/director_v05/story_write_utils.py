"""SQLite write helpers shared by Story Factory producers.

Kept dependency-neutral on purpose: harvesters and the trivia factory both
need lock-tolerant commits, and neither should import the other just to get
that behavior.
"""
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
    """Commit a Story Factory write without dying on transient readers."""
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


# Backward-compatible private aliases for existing call sites.
_prepare_write_connection = prepare_write_connection
_commit_with_retry = commit_with_retry
