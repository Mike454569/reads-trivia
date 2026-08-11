"""Local/admin-only translation audit logging (Director v0.3, Part E).

Appends one JSON line per Director request to `tools/director_v02/logs/
audit_log.jsonl`. This directory is NOT referenced by `index.html`, `app.js`,
or the service worker -- it is a local development artifact only, never
served, never shipped.

What is logged, matching Part E's list exactly: request ID, provider used,
request-text hash, validated Director spec, capability selected, translation
status, generation status, package ID (if generated), provider latency,
Engine generation latency, rejection reason (if any).

What is NEVER logged, under any circumstance: API keys, authorization
headers, or any other secret value. Nothing in this module ever reads an
environment variable, a header, or a credential -- it only receives the
already-public-shaped TranslationResult/GateResult/package dicts the rest of
the pipeline already produced.

Raw request text: logged in full for THIS DEVELOPMENT MILESTONE ONLY,
alongside its SHA-256 hash. This is a deliberate, disclosed choice, not an
oversight -- see the module-level `RAW_TEXT_LOGGING` flag below. A
production design should flip this to hash-only (`RAW_TEXT_LOGGING = False`)
once real user request text may contain anything a developer shouldn't need
to read to debug the pipeline.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

# v1.4, Part 19: overridable via READS_DIRECTOR_AUDIT_LOG_DIR (same pattern
# gateway/config.py already uses for READS_ENGINE_LOG_DIR) -- fixes a real,
# repeatedly-observed problem, not a hypothetical one: every prior phase's
# test run (and every manual verification call made while developing this
# project) appended to this SAME committed file, since it used to have no
# way to redirect at all, dirtying the working tree every time and
# requiring a manual `git restore` before every checkpoint commit.
# gateway/tests/conftest.py sets this before the app is ever exercised, the
# same way it already redirects gateway.config.PACKAGES_DIR /
# GATEWAY_AUDIT_LOG_DIR for the exact same reason. Unset (every real/local
# non-test run) -- byte-for-byte the same default as every prior phase.
LOG_DIR = Path(os.environ.get("READS_DIRECTOR_AUDIT_LOG_DIR") or (Path(__file__).resolve().parent / "logs"))
LOG_PATH = LOG_DIR / "audit_log.jsonl"

# Documented, disclosed, dev-only. Flip to False and this stops writing
# `request_text_raw` (the hash is always written either way).
RAW_TEXT_LOGGING = True

_write_lock = threading.Lock()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record(*, request_text: str, director_request_id: str, provider: str,
           translation_status: str | None, validated_spec: dict | None,
           capability_key: tuple | None, generation_status: str,
           package_id: str | None, provider_latency_ms: float,
           engine_generation_latency_ms: float | None,
           rejection_reason: str | None) -> dict:
    """Writes one audit entry and returns it (useful for tests/reports --
    callers don't need to re-read the log file to see what was recorded)."""
    entry = {
        "request_id": director_request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "request_text_hash": _hash_text(request_text),
        "request_text_raw": request_text if RAW_TEXT_LOGGING else None,
        "translation_status": translation_status,
        "validated_spec": validated_spec,
        "capability_selected": list(capability_key) if capability_key else None,
        "generation_status": generation_status,
        "package_id": package_id,
        "provider_latency_ms": round(provider_latency_ms, 3),
        "engine_generation_latency_ms": (
            round(engine_generation_latency_ms, 3) if engine_generation_latency_ms is not None else None
        ),
        "rejection_reason": rejection_reason,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
    with _write_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    return entry


def read_all(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
