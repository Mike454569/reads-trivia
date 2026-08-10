"""Reads Engine Gateway -- generation orchestration (Parts D, H).

Thin wrapper around `tools.director_v02.pipeline` -- no Director/Game
Factory logic is reimplemented here (Part C: "Do NOT copy Game Factory or
Director logic into HTTP route handlers"). This module's only real
responsibilities are the two things that are genuinely Gateway-specific:
(1) a single-generation-job-at-a-time concurrency guard, and (2) a hard
wall-clock timeout around the call into the pipeline -- both explicitly
required by Part H because generation ultimately touches the 1.65GB Engine
SQLite file, and this project's own audit (READS_ENGINE_GATEWAY_AUDIT.md)
found none of the eight pre-existing Engine servers protect that at all.
"""
from __future__ import annotations

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.director_v02 import pipeline as director_pipeline  # noqa: E402
from tools.director_v02 import registry as director_registry  # noqa: E402

from .. import config  # noqa: E402
from ..errors import GatewayError  # noqa: E402

# Exactly one generation job at a time, across the whole process -- the
# safest architecture per Part H, and the one this milestone explicitly
# says is acceptable. A single dedicated worker thread also means every
# generation call reaches the Engine DB serialized through one thread,
# never two SQLite connections opened concurrently by this process.
_generation_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gateway-generation")


def list_capabilities() -> list[dict]:
    """Read-only reflection of the capability registry -- GET /v1/capabilities.
    Deliberately re-shapes each entry rather than returning the raw registry
    dict: strips the `adapter`/`generate_fn` Python object references (never
    serializable, and exactly the kind of Engine-internals leak Part C's
    'the frontend must never know... Python module names, adapter names'
    rule forbids) down to plain, documented, JSON-safe fields."""
    out = []
    for (mechanic, domain, predicate), cap in director_registry.CAPABILITY_REGISTRY.items():
        out.append({
            "mechanic": mechanic,
            "domain": domain,
            "relationship_predicate": predicate,
            "category": cap.get("category"),
            "min_question_count": cap.get("min_question_count"),
            "max_question_count": cap.get("max_question_count"),
            "supported_difficulties": sorted(cap.get("supported_difficulties", [])),
        })
    return out


def preview(*, request_text: str | None, spec: dict | None, provider: str) -> dict:
    """No generation, no lock, no timeout needed -- translate+validate only
    is fast and touches the Engine DB not at all (validator.py never opens
    a connection). Mirrors POST /v1/games/preview exactly."""
    if provider == "anthropic":
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            # Matches Part K exactly: do not fake a real-provider result.
            return {
                "status": "REAL_PROVIDER_NOT_CONFIGURED",
                "reason": "ANTHROPIC_API_KEY is not set on this server.",
            }
    translation, gate = director_pipeline.translate_and_validate(request_text, spec=spec, provider=provider)
    result = {
        "translation_status": translation.get("translation_status"),
        "translator_id": translation.get("translator_id"),
        "translator_notes": translation.get("translator_notes"),
        "gate_status": gate["gate_status"],
        "gate_reason": gate.get("gate_reason"),
        "normalized_spec": gate.get("validated_spec"),
    }
    if gate["gate_status"] == "READY":
        cap = gate["capability"]
        result["capability"] = {"mechanic": gate["validated_spec"]["mechanic"],
                                 "domain": gate["validated_spec"]["domain"],
                                 "relationship_predicate": gate["validated_spec"]["relationship_predicate"],
                                 "category": cap.get("category")}
    if gate["gate_status"] == "NEEDS_CLARIFICATION":
        result["understood"] = gate.get("understood") or {}
        result["missing_fields"] = gate.get("missing_fields") or []
        result["question"] = gate.get("clarifying_question")
    if gate["gate_status"] == "UNDERSTOOD_BUT_UNSUPPORTED":
        result["closest_supported_capability"] = gate.get("closest_supported_capability")
    return result


def generate(*, request_text: str | None, spec: dict | None, provider: str,
             puzzle_count: int | None, difficulty: str | None, seed: str | None) -> dict:
    """Runs the real Director pipeline (translate -> validate -> generate ->
    QA) under the single-slot concurrency guard and a hard timeout. Returns
    exactly what `pipeline.run()` returns -- a full package dict on success,
    or a small structured non-package result (BLOCKED_*/NEEDS_CLARIFICATION/
    UNDERSTOOD_BUT_UNSUPPORTED) otherwise. Raises GatewayError only for
    genuine infrastructure failure (busy, timeout, real-provider-not-configured)
    -- never for an ordinary unsupported/ambiguous request, which is a normal
    structured return, not an exception."""
    if provider == "anthropic":
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return {
                "package_id": None,
                "status": "REAL_PROVIDER_NOT_CONFIGURED",
                "reason": "ANTHROPIC_API_KEY is not set on this server.",
            }

    acquired = _generation_lock.acquire(blocking=False)
    if not acquired:
        raise GatewayError(
            "GENERATION_BUSY",
            "Another generation job is already running. This Gateway allows only one "
            "generation job at a time (Director v0.6, Part H) -- retry shortly.",
        )
    try:
        future = _executor.submit(
            director_pipeline.run,
            request_text, spec=spec, provider=provider,
            seed=seed or f"gateway-{int(time.time() * 1000)}",
            question_count_override=puzzle_count, difficulty_override=difficulty,
        )
        try:
            return future.result(timeout=config.GENERATION_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            raise GatewayError(
                "GENERATION_FAILED",
                f"Generation exceeded the {config.GENERATION_TIMEOUT_SECONDS}s timeout.",
            )
    finally:
        _generation_lock.release()
