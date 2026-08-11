"""Reads Engine Gateway -- generation orchestration (Parts D, H; v1.6 Part A).

Thin wrapper around `tools.director_v02.pipeline` -- no Director/Game
Factory logic is reimplemented here (Part C: "Do NOT copy Game Factory or
Director logic into HTTP route handlers"). This module's real
responsibilities are per-path concurrency control and a hard wall-clock
timeout around the call into the pipeline.

v1.6, Part A1/A2/A4 -- root-caused, not assumed: TWO independent
concurrency policies now exist here, not one, because ADMIN and PUBLIC
generation have different real requirements:

  ADMIN (`generate()`, unchanged from v0.6/Part H): exactly one job at a
  time, across the whole process. This is deliberately still maximally
  conservative -- `request_text`/`spec` here can be arbitrary admin input,
  and `tools/director_v02/registry.py` is an extensible registry, not a
  closed set this module can fully audit for future write-behavior. Part H
  ("safest architecture... this milestone explicitly says is acceptable")
  never had a throughput requirement, so there is no reason to loosen it.

  PUBLIC (`generate_public()`, new): a bounded worker pool
  (`PUBLIC_GENERATION_MAX_CONCURRENCY` concurrent slots, default 4 -- see
  gateway/config.py's own comment for why 4 specifically, not a larger
  number), because the public path is a closed, already-audited set of exactly two
  capabilities (draft_guess, championship_guess -- gateway/config.py's
  PUBLIC_MODE_ALLOWLIST) whose ENTIRE generation path is proven read-only
  against the Engine SQLite file:
    - `tools/director_v02/pipeline.py` (line ~21): "This module never
      touches the Engine database directly."
    - `tools/game_director_v01.py`'s `generate_package_from_spec()` (the
      one function every guess-mechanic capability's `generate_fn` funnels
      through, per registry.py) opens exactly one connection
      (`engine.connect()`), issues only SELECT-shaped reads via
      `adapter.safety_check()` / `_engine_version_fingerprint()` /
      `adapter.fetch_ordered_candidates()`, and closes it -- confirmed by
      reading every line of that function; there is no `.execute()` of
      anything but a read query, and no `.commit()`, anywhere in it.
    - `tools/quiz_export/adapters/draft.py` and `championship.py` (the only
      two adapters reachable from the public allow-list): grepped for
      `.commit()`/`INSERT`/`UPDATE`/`DELETE` -- zero matches in either file.
    - This exact read-only property was ALREADY independently proven and
      documented in `tools/quiz_export/engine.py`'s `connect()` docstring
      (Director v0.7, Part E): "empirically verified this milestone that
      the ENTIRE Gateway generation path... performs ZERO writes to the
      Engine database" -- this phase re-derived the same conclusion by
      tracing the code fresh, then found that prior proof already sitting
      in the codebase confirming it independently.
  `game_factory.py`'s own `preview()`/`publish()`/`create_spec()` DO write
  (INSERT/UPDATE + `.commit()` against `game_factory_specs`,
  `game_factory_candidates`, `game_factory_qa`, `puzzle_catalog`,
  `game_factory_publications`) -- but neither public mode's generate_fn
  path ever calls them; only the Game Factory CLI (`game_factory.py main()`,
  a separate, unrelated entrypoint this Gateway never invokes) does.

  Because every public-path connection is independently opened, used for
  reads only, and closed within one call (no shared mutable state, no
  global RNG -- `engine.seeded()` returns a fresh per-call `random.Random`
  instance, not a module-level one), SQLite's own concurrent-reader support
  is sufficient: multiple public generation calls running in parallel
  threads is exactly the access pattern SQLite is built to allow. The
  existing per-connection `busy_timeout` PRAGMA (`tools/quiz_export/
  engine.py`'s `connect()`, Part E) remains in effect as a second layer of
  safety against the rare case of contention with an external writer.

Part A6 (backpressure): the public pool is bounded and NON-blocking, same
shape as the admin lock -- if all slots are busy, a caller gets a clean
`GENERATION_BUSY` immediately, never an unbounded queue or unbounded
threads.
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

# --- Admin generation: unchanged from v0.6/Part H ---------------------------
# Exactly one generation job at a time, across the whole process -- the
# safest architecture per Part H, and the one this milestone explicitly
# says is acceptable. A single dedicated worker thread also means every
# ADMIN generation call reaches the Engine DB serialized through one
# thread. Deliberately NOT loosened in v1.6 -- see module docstring: admin
# input is not a closed, pre-audited set the way the public allow-list is.
_generation_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gateway-generation")

# --- Public generation: v1.6, Part A -----------------------------------------
# A bounded, non-blocking semaphore (not the admin lock) sized well above 1
# -- see module docstring for the read-only proof this relies on. Backed by
# its own worker pool, entirely separate from the admin executor above, so
# admin and public generation can never contend with or starve each other.
_public_generation_semaphore = threading.Semaphore(config.PUBLIC_GENERATION_MAX_CONCURRENCY)
_public_executor = ThreadPoolExecutor(
    max_workers=config.PUBLIC_GENERATION_MAX_CONCURRENCY, thread_name_prefix="gateway-public-generation"
)


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
            # v1.8, Part D/E: which visual template this capability renders with --
            # defaults to the pre-v1.8 implicit rendering for every capability that
            # never declared one (Draft, Championship, Player From Clues).
            "visual_template": cap.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
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


def _run_pipeline_bounded(*, request_text: str | None, spec: dict | None, provider: str,
                           puzzle_count: int | None, difficulty: str | None, seed: str | None,
                           gate, executor: ThreadPoolExecutor, busy_message: str) -> dict:
    """Shared submit/await/timeout core for both `generate()` and
    `generate_public()` -- `gate` is whichever of `_generation_lock` (admin)
    or `_public_generation_semaphore` (public) applies; both expose the same
    `acquire(blocking=False)`/`release()` shape (a `threading.Lock` and a
    `threading.Semaphore` are interchangeable here), so one function can
    serve both call sites instead of two near-identical copies of this
    submit/timeout/release logic."""
    if provider == "anthropic":
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return {
                "package_id": None,
                "status": "REAL_PROVIDER_NOT_CONFIGURED",
                "reason": "ANTHROPIC_API_KEY is not set on this server.",
            }

    acquired = gate.acquire(blocking=False)
    if not acquired:
        raise GatewayError("GENERATION_BUSY", busy_message)
    try:
        future = executor.submit(
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
        gate.release()


def generate(*, request_text: str | None, spec: dict | None, provider: str,
             puzzle_count: int | None, difficulty: str | None, seed: str | None) -> dict:
    """ADMIN generation path (POST /v1/games/generate, and anything else
    passing arbitrary request_text/spec) -- runs the real Director pipeline
    under the single-slot concurrency guard and a hard timeout, unchanged
    from v0.6/Part H. See module docstring for why this stays maximally
    conservative while `generate_public()` below does not."""
    return _run_pipeline_bounded(
        request_text=request_text, spec=spec, provider=provider,
        puzzle_count=puzzle_count, difficulty=difficulty, seed=seed,
        gate=_generation_lock, executor=_executor,
        busy_message=(
            "Another generation job is already running. This Gateway allows only one "
            "generation job at a time (Director v0.6, Part H) -- retry shortly."
        ),
    )


def generate_public(*, spec: dict, difficulty: str | None, seed: str | None) -> dict:
    """PUBLIC generation path (gateway/services/public_game.py only) -- v1.6,
    Part A. Same pipeline, same timeout, but a bounded worker pool sized for
    real concurrent throughput instead of the admin path's single slot. Only
    ever called with a `spec` already built from `PUBLIC_MODES`' own
    certified templates (gateway/services/public_game.py), never arbitrary
    caller input -- see module docstring for the read-only proof this relies
    on. `provider` is always "mock" here (public gameplay never calls a real
    LLM) and `puzzle_count` is always 1 (one question per fetch) -- both
    fixed rather than parameters, since a public caller never has a reason
    to vary either."""
    return _run_pipeline_bounded(
        request_text=None, spec=spec, provider="mock",
        puzzle_count=1, difficulty=difficulty, seed=seed,
        gate=_public_generation_semaphore, executor=_public_executor,
        busy_message="This game is popular right now -- try again in a moment.",
    )
