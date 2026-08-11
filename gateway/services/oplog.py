"""Reads Engine Gateway -- structured operational logging (Director v0.7, Part M).

Distinct from `gateway/services/audit.py` (which records generation-specific
Director detail: spec, capability, translation status) and from
`tools/director_v02/audit_log.py` (which that module already wrote before
this milestone). This module is the per-HTTP-request operational log line
every request gets, regardless of route: timestamp, request ID, route,
status, latency -- the fields an operator watching the service actually
needs, kept separate from the deeper generation-specific record so neither
log gets cluttered with fields it doesn't need.

Never logs: admin tokens, Authorization headers, provider API keys, raw
database contents. Request text is hashed, never logged raw, per Part M's
explicit "be conservative with raw user request text" instruction --
stricter than gateway/services/audit.py's v0.6 behavior (which does log raw
text, disclosed as a deliberate dev-only choice there); this operational
log has no such carve-out.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

from .. import config

_write_lock = threading.Lock()


def record(*, request_id: str, route: str, method: str, status_code: int, latency_ms: float,
           capability: dict | None = None, generation_status: str | None = None,
           package_id: str | None = None, error_code: str | None = None) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "route": route,
        "method": method,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 3),
        "capability": capability,
        "generation_status": generation_status,
        "package_id": package_id,
        "error_code": error_code,
    }
    config.GATEWAY_AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
    with _write_lock:
        with open(config.OPERATIONAL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)


def record_event(event: str, **fields) -> None:
    """v1.4, Part 17/18: a second, domain-semantic structured log line,
    distinct from `record()`'s generic per-HTTP-request line above --
    `event` names a real gameplay occurrence (`public_game_served`,
    `public_game_no_eligible`, `public_answer_submitted`,
    `public_game_mode_disabled`) with whatever fields are meaningful for
    that event (mode, difficulty, latency_ms, generation_attempts, correct).
    Deliberately a plain function call from gateway/services/public_game.py
    itself, not threaded through FastAPI's Request/response objects --
    keeps the existing "thin route handlers, real logic in services"
    boundary intact (Part C), and this module already owns the one JSONL
    sink every operational log line in this Gateway writes to.

    Same 'never log this' rules `record()` already documents: no admin
    tokens, no raw free-text answers (only `correct: bool` is ever passed
    for an answer-submission event), no database contents beyond the
    small structured fields explicitly passed in."""
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    config.GATEWAY_AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
    with _write_lock:
        with open(config.OPERATIONAL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
