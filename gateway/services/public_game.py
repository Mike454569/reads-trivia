"""Reads Engine Gateway -- public gameplay (v1.2 pilot).

The production-safe boundary between the real Reads frontend (browser,
zero credentials) and the Engine. Everything in this module is a THIN
consumer of already-certified truth -- no game logic is reimplemented here
(same rule gateway/services/generation.py and graph.py already document):
question generation still goes through `tools.director_v02.pipeline` (the
same translate -> validate -> generate -> QA path `/v1/games/generate`
already uses), and persistence reuses the existing content-addressed
`gateway/services/packages.py` store. Part 9's explicit instruction --
"Public Gateway delivery is a consumer of certified engine truth, not a
competing generation system" -- is enforced by construction: this file has
no SQL, no graph traversal, no Director/Game Factory logic of its own.

--- WHY REUSING packages.py's package_id IS ENOUGH FOR A "GAME SESSION" ---
Part 7 asks for a game identifier that prevents obvious tampering "without
unnecessary cryptographic complexity". `package_id` already is exactly
that: a `GGP:<24 hex>` content hash of (spec, seed, ...), validated by
`packages._safe_filename_for_id()`'s strict allowlist regex before any
filesystem use, effectively unguessable (a client would have to find a
real sha256 preimage to forge one), and already has atomic, idempotent
storage. Reusing it here means a public `game_id` and an admin
`package_id` are literally the same identifier space -- no new storage
layer, no new ID scheme, nothing to keep in sync.

--- ANSWER LEAKAGE BOUNDARY ---
`_public_view()` is the ONLY function in this file allowed to shape what a
browser receives for a fresh game, and it is deliberately an allow-list
(only the named fields are copied out), not a deny-list of "strip these
fields" -- a future field added to the internal package shape is excluded
by default, not accidentally leaked. `correctIndex`, `answer`,
`source_ids`, `provenance`, `funnel`, `qa_checks_performed`, and `notes`
are never present in a fresh-game response. `notes` is deliberately only
ever returned from `validate_public_answer()` (after a real guess), never
from `get_public_game()` -- matching the one existing Reads Quiz
convention this pilot borrows (`renderQuizQuestion()` in app.js only shows
`q.notes` once a question has been answered).

--- WHY draft_guess AND NOT EVERY REGISTERED CAPABILITY ---
`config.PUBLIC_MODE_ALLOWLIST` has exactly one entry as of v1.2 (Part 3:
explicit allow-list; Part 34/35: Grid and Six Degrees are NOT migrated in
this phase). `championship_guess`/`player_from_clues` are real, registered
internal capabilities (see generation.list_capabilities()) that are
DELIBERATELY not yet public -- requesting them returns MODE_UNAVAILABLE
(a real, recognized capability, just not vetted for direct public
delivery yet), distinct from INVALID_MODE (not a real capability at all).
"""
from __future__ import annotations

import secrets
from typing import Any, Dict, List, Optional

from .. import config
from ..errors import GatewayError
from . import generation, packages

# Public mode id -> (internal Director capability spec, public-facing copy).
# The public mode id is a stable, independent vocabulary -- NOT the internal
# (mechanic, domain, relationship_predicate) tuple -- so the public contract
# never has to change shape if internal registry naming changes.
PUBLIC_MODES: Dict[str, Dict[str, Any]] = {
    "draft_guess": {
        "competition": "NFL",
        "title": "NFL Draft History: Guess the Team",
        "instructions": "You'll be shown a real NFL player. Pick the team that actually drafted him.",
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_DRAFT",
            "relationship_predicate": "DRAFTED_BY",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
}

# Real, registered internal capabilities (generation.list_capabilities())
# that are NOT on the public allow-list -- used only to give an honest
# MODE_UNAVAILABLE instead of a misleading INVALID_MODE for a mode id a
# caller might reasonably expect to exist. Kept as literal, hand-verified
# strings (not derived from the registry) so this file never accidentally
# expands the public surface just because a new internal capability ships.
KNOWN_NOT_YET_PUBLIC_MODES = frozenset({"championship_guess", "player_from_clues"})

assert set(PUBLIC_MODES) == config.PUBLIC_MODE_ALLOWLIST, (
    "PUBLIC_MODES and config.PUBLIC_MODE_ALLOWLIST have drifted apart -- these must name the same modes."
)

MAX_GAME_FETCH_ATTEMPTS = 5  # bounded retry for the exclude-recent-repeats loop (Part 27) -- never unbounded


def list_public_modes() -> List[dict]:
    return [
        {"mode": mode_id, "competition": entry["competition"], "title": entry["title"]}
        for mode_id, entry in PUBLIC_MODES.items()
    ]


def _ensure_mode_public(mode: str) -> None:
    if mode in PUBLIC_MODES:
        return
    if mode in KNOWN_NOT_YET_PUBLIC_MODES:
        raise GatewayError(
            "MODE_UNAVAILABLE",
            f"mode={mode!r} is a real Reads Engine capability but is not yet available through the "
            f"public API -- the v1.2 pilot covers draft_guess only.",
        )
    raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized mode.")


def _public_view(mode: str, entry: dict, stored: dict) -> dict:
    """The ONE place allowed to decide what a browser sees for a fresh
    game. Allow-list, not a deny-list -- see module docstring."""
    q = stored["questions"][0]
    return {
        "game_id": stored["package_id"],
        "mode": mode,
        "competition": entry["competition"],
        "difficulty": q.get("difficulty"),
        "title": stored.get("game_title"),
        "instructions": stored.get("game_instructions"),
        "payload": {
            "prompt": q["question"],
            "options": list(q["options"]),
        },
        "metadata": {
            "seed": (stored.get("_diagnostics") or {}).get("seed"),
            "version": stored.get("package_version"),
        },
    }


def get_public_game(*, mode: str, difficulty: Optional[str], seed: Optional[str],
                     exclude_game_ids: Optional[List[str]]) -> dict:
    _ensure_mode_public(mode)
    entry = PUBLIC_MODES[mode]
    exclude = set(exclude_game_ids or [])

    # A real bug caught by actually calling this (not assumed from reading
    # the pipeline code): the Director validator requires `difficulty`
    # INSIDE the spec dict itself -- the separate `difficulty=` kwarg to
    # generation.generate() is applied too late to satisfy that check.
    # Confirmed directly: the same spec without this field fails validation
    # with "spec is missing required fields: ['difficulty']" before
    # generation ever runs.
    call_spec = dict(entry["spec"])
    call_spec["difficulty"] = difficulty or "any"

    stored = None
    last_eligible = None  # most recent QA-passed, non-empty result, even if it's in the exclude set
    for attempt in range(MAX_GAME_FETCH_ATTEMPTS):
        # A caller-pinned seed is honored exactly once, never silently
        # replaced -- Part 26 (determinism) outranks Part 27 (avoid
        # immediate repeats) when they conflict. Without a pinned seed,
        # each attempt gets a fresh random seed so a real exclude list can
        # actually find a different real question.
        real_seed = seed if (seed and attempt == 0) else secrets.token_hex(8)
        result = generation.generate(
            request_text=None, spec=call_spec, provider="mock",
            puzzle_count=1, difficulty=difficulty, seed=real_seed,
        )
        # Real bug caught by actually running Part 25's pilot-data
        # verification, not assumed from reading the code: game_director_v01
        # sets qa_status "PASSED" whenever contract_failures is empty --
        # which is also true when `questions` is EMPTY (nothing to fail
        # validation), e.g. a narrow difficulty filter matching zero
        # candidates for this particular seed's small deterministic sample.
        # Treating that as eligible caused an IndexError in _public_view's
        # `stored["questions"][0]`. One unlucky seed isn't a hard failure --
        # retry with another seed, same as any other ineligible attempt.
        eligible = bool(result.get("package_id")) and result.get("qa_status") == "PASSED" and result.get("questions")
        if not eligible:
            if seed and attempt == 0:
                # The caller's pinned seed genuinely isn't eligible --
                # don't silently swap in a different seed than the one
                # explicitly requested (Part 26 determinism).
                break
            continue
        last_eligible = result
        if result["package_id"] not in exclude:
            stored = result
            break
    if stored is None:
        if last_eligible is None:
            raise GatewayError(
                "NO_ELIGIBLE_GAME",
                f"No QA-passed question could be generated for mode={mode!r} right now.",
            )
        # Every eligible attempt landed on an excluded game_id -- real,
        # honest outcome for a very small eligible pool, not an
        # infrastructure failure.
        stored = last_eligible

    saved = packages.save_package(stored)
    return _public_view(mode, entry, saved)


def validate_public_answer(*, game_id: str, answer: str) -> dict:
    try:
        stored = packages.load_package(game_id)
    except packages.PackageIdInvalid:
        stored = None
    if not stored:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    q = stored["questions"][0]
    norm = answer.strip().lower()
    correct_label = q["options"][q["correctIndex"]]
    is_correct = norm == correct_label.strip().lower() or norm == str(q.get("answer", "")).strip().lower()
    return {
        "correct": is_correct,
        "canonical_answer": correct_label,
        # Matches existing Quiz semantics (app.js renderQuizQuestion): the
        # correct answer -- and any notes -- are only ever revealed AFTER a
        # real guess, never in the initial game payload.
        "notes": q.get("notes") or None,
    }
