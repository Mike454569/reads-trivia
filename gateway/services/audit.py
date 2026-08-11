"""Reads Engine Gateway -- request-level audit trail (Part J).

Deliberately thin: `tools.director_v02.pipeline.run()` ALREADY calls
`tools.director_v02.audit_log.record()` internally for every generation
attempt (request-text hash, validated spec, capability, translation status,
generation status, package ID, provider/engine latency, rejection reason --
the exact fields Part J lists) -- that existing infrastructure is reused
as-is, not reimplemented, satisfying "reuse the existing Director audit
infrastructure where practical."

This module adds only the fields that are genuinely Gateway-specific and
that the Director-level log has no way to know about: the Gateway's own
per-HTTP-request ID (`request_id`, distinct from Director's own `GDR2:...`
request ID), which endpoint was hit, and the caller-supplied generation
parameters before any Director validation touched them. Cross-referenced to
the Director-level entry via `director_request_id`.

Never logs: admin token, Authorization header, or any other secret --
confirmed by inspection, no field below reads from `request.headers` or
`config.admin_token()`.
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone

from .. import config

_write_lock = threading.Lock()


def _hash_text(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(entry: dict) -> None:
    config.GATEWAY_AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
    with _write_lock:
        with open(config.GATEWAY_AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)


def record_preview(*, request_id: str, body, result: dict) -> None:
    _write({
        "request_id": request_id,
        "endpoint": "/v1/games/preview",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": body.provider,
        "request_text_hash": _hash_text(body.request_text),
        "spec_provided": body.spec is not None,
        "gate_status": result.get("gate_status") or result.get("status"),
        "capability": result.get("capability"),
    })


def record_generate(*, request_id: str, body, result: dict, latency_ms: float,
                     endpoint: str = "/v1/games/generate") -> None:
    # v1.8, Part B: `endpoint` defaults to the original literal so both
    # existing call sites (games_generate) are byte-for-byte unaffected;
    # the new Creator route (creator_generate) passes its own real path.
    director_spec = result.get("director_spec") or {}
    _write({
        "request_id": request_id,
        "endpoint": endpoint,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": body.provider,
        "request_text_hash": _hash_text(body.request_text),
        "spec_provided": body.spec is not None,
        "puzzle_count_requested": body.puzzle_count,
        "difficulty_requested": body.difficulty,
        "seed": body.seed,
        "director_request_id": result.get("director_request_id"),
        "capability_selected": {
            "mechanic": director_spec.get("mechanic"),
            "domain": director_spec.get("domain"),
            "relationship_predicate": director_spec.get("relationship_predicate"),
        } if director_spec else None,
        "package_id": result.get("package_id"),
        "qa_status": result.get("qa_status"),
        "status": result.get("status") or ("GENERATED" if result.get("package_id") else "BLOCKED"),
        "total_latency_ms": round(latency_ms, 3),
    })
