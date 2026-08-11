"""Reads Engine Gateway -- public gameplay (v1.2 draft pilot, v1.3
generalized to a multi-mode public mode registry).

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
layer, no new ID scheme, nothing to keep in sync. Re-audited in v1.3 with
multiple modes live (Part 7): `validate_public_answer()` never takes a
client-declared `mode` at all -- the mode is derived entirely from the
loaded package itself, so there is no "declared mode" field for a client
to lie about, and a Draft `game_id` cannot be used to somehow validate a
Championship answer or vice versa (the package loaded IS the puzzle;
there's nothing else to target). See `test_public_game.py`'s
`test_cross_mode_game_id_stays_scoped_to_its_own_mode` for the real check.

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

--- WHY draft_guess + championship_guess AND NOT EVERY REGISTERED CAPABILITY ---
`config.PUBLIC_MODE_ALLOWLIST` has exactly two entries as of v1.3 (Part 3/33:
explicit, hand-certified allow-list; Part 16/17: Grid and Six Degrees are
NOT migrated in this phase). `player_from_clues` is a real, registered
internal capability (see generation.list_capabilities()) that is
DELIBERATELY not yet public -- requesting it returns MODE_UNAVAILABLE (a
real, recognized capability, just not vetted for direct public delivery
yet), distinct from INVALID_MODE (not a real capability at all).

--- WHY THIS ISN'T A "DraftGuessHandler / ChampionshipGuessHandler" CLASS HIERARCHY ---
Part 30 sketches per-mode handler classes. Both certified modes here are
the SAME internal mechanic shape (`guess` -> Game Factory/adapter ->
4-option multiple choice, `options[correctIndex]`) -- introducing separate
handler classes for two modes with byte-identical fetch/validate logic
would be ceremony with no behavioral difference (Part 30's own "do not
overengineer... for hypothetical future modes" caveat). What actually WAS
Draft-specific coupling in v1.2, and is fixed here: (1) only one registry
entry existed at all, (2) there was no per-mode certified-difficulty check
(a mode's metadata could silently advertise a difficulty band that has
zero real candidates), (3) `/v1/public/modes` returned only
`{mode, competition, title}`, too thin for a client to make a real choice
between modes. `PUBLIC_MODES` entries now carry a `kind` field
(`"multiple_choice"` for both today) specifically so a future mode with a
genuinely different mechanic (e.g. free-text) has a real place to branch
from, without speculative branching code that has no mode to exercise it
yet.
"""
from __future__ import annotations

import secrets
import time
from typing import Any, Dict, List, Optional

from .. import config
from ..errors import GatewayError
from . import generation, oplog, packages

# The public game contract's own version (Part 31) -- distinct from
# `package_version` (metadata.version below), which is the internal
# Director package SCHEMA version. contract_version only needs to move if
# the shape of THIS response (the fields a client parses) changes in a
# breaking way; nothing has needed that yet, so it starts at 1.
CONTRACT_VERSION = 1

# Public mode id -> (internal Director capability spec, public-facing copy,
# real certified difficulty support). The public mode id is a stable,
# independent vocabulary -- NOT the internal (mechanic, domain,
# relationship_predicate) tuple -- so the public contract never has to
# change shape if internal registry naming changes.
#
# `certified_difficulties`: hand-verified against REAL candidate surveys
# (Part 20/3), never copied from the internal capability registry's
# `supported_difficulties` (which is technically-supported-by-the-adapter-
# code, not empirically-has-real-candidates -- a real, different thing).
# "any" is not listed per-mode because it isn't a difficulty band claim at
# all -- it means "no difficulty filter", which trivially always has
# candidates if the mode has any candidates. Both modes below were
# surveyed directly this phase: 0 "Easy" candidates for either (Draft:
# 0/232 accepted; Championship: 0/296 accepted) -- so "easy" is
# deliberately absent from both, not an oversight.
PUBLIC_MODES: Dict[str, Dict[str, Any]] = {
    "draft_guess": {
        "competition": "NFL",
        "title": "NFL Draft History: Guess the Team",
        "instructions": "You'll be shown a real NFL player. Pick the team that actually drafted him.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_DRAFT",
            "relationship_predicate": "DRAFTED_BY",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "championship_guess": {
        "competition": "NFL",
        "title": "NFL Playoffs: Guess the Result",
        "instructions": "You'll be shown a real NFL team and season. Pick how their postseason actually ended.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_CHAMPIONSHIP",
            "relationship_predicate": "TEAM_POSTSEASON_RESULT",
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
KNOWN_NOT_YET_PUBLIC_MODES = frozenset({"player_from_clues"})

assert set(PUBLIC_MODES) == config.PUBLIC_MODE_ALLOWLIST, (
    "PUBLIC_MODES and config.PUBLIC_MODE_ALLOWLIST have drifted apart -- these must name the same modes."
)

MAX_GAME_FETCH_ATTEMPTS = 5  # bounded retry for the exclude-recent-repeats loop (Part 27) -- never unbounded

# relationship_predicate -> public mode id -- built once from PUBLIC_MODES
# so validate_public_answer() can report `mode` in its telemetry event
# (Part 17) without needing a `mode` parameter from the client (Part 7:
# there deliberately isn't one). Keyed by relationship_predicate ALONE,
# not the (domain, predicate) pair the request spec uses -- a real
# mismatch found by actually inspecting a generated package, not assumed:
# the VALIDATED/stored `parsed_spec` (game_director_v01's output) never
# contains a `domain` key at all -- the validator normalizes it away into
# `entity_type`/`competition_id`/`object_type` instead. `relationship_
# predicate` is the one field that survives unchanged and is already
# unique per certified mode (DRAFTED_BY vs. TEAM_POSTSEASON_RESULT), so it
# alone is a safe, real lookup key -- re-verified directly against a real
# generated package's actual `parsed_spec` shape.
_MODE_BY_PREDICATE = {
    entry["spec"]["relationship_predicate"]: mode_id
    for mode_id, entry in PUBLIC_MODES.items()
}


def _mode_for_package(stored: dict) -> Optional[str]:
    spec = stored.get("parsed_spec") or {}
    return _MODE_BY_PREDICATE.get(spec.get("relationship_predicate"))


def list_public_modes() -> List[dict]:
    """Part 19: client-safe mode discovery. Only ever the fields a client
    needs to make a real choice (which mode, what difficulties actually
    work, what kind of gameplay to render) -- never internal source
    tables, answer truth, or QA/admin detail (Part 13). `available` reflects
    BOTH production rollout controls (Part 10/11: the master
    PUBLIC_GAME_ENABLED switch and the per-mode READS_PUBLIC_MODES
    narrowing) -- a client can build an honest "currently unavailable" UI
    from this alone, without needing to first attempt a fetch and parse an
    error."""
    modes_currently_allowed = config.public_modes_allowed()
    return [
        {
            "mode": mode_id,
            "competition": entry["competition"],
            "title": entry["title"],
            "kind": entry["kind"],
            "difficulties": sorted(entry["certified_difficulties"]) + ["any"],
            "available": config.PUBLIC_GAME_ENABLED and mode_id in modes_currently_allowed,
        }
        for mode_id, entry in PUBLIC_MODES.items()
    ]


def _ensure_public_gameplay_enabled() -> None:
    """Part 10: the master operator kill switch, checked before anything
    else -- one env var (READS_PUBLIC_GAME_ENABLED=false) takes every
    public mode down with a clean, structured response, no redeploy."""
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_game_mode_disabled", mode=None, reason="master_switch_off")
        raise GatewayError(
            "SERVICE_UNAVAILABLE",
            "Public gameplay is currently disabled.",
        )


def _ensure_mode_public(mode: str) -> dict:
    _ensure_public_gameplay_enabled()
    if mode in PUBLIC_MODES:
        if mode not in config.public_modes_allowed():
            # Part 11: code-certified but currently rolled back via
            # READS_PUBLIC_MODES -- the client-facing meaning is identical
            # to MODE_UNAVAILABLE ("not offered right now"), regardless of
            # whether that's a permanent code decision or a temporary ops
            # one, so it reuses the same code rather than inventing a
            # distinction no client actually needs to act on differently.
            oplog.record_event("public_game_mode_disabled", mode=mode, reason="mode_narrowed")
            raise GatewayError(
                "MODE_UNAVAILABLE",
                f"mode={mode!r} is temporarily unavailable.",
            )
        return PUBLIC_MODES[mode]
    if mode in KNOWN_NOT_YET_PUBLIC_MODES:
        raise GatewayError(
            "MODE_UNAVAILABLE",
            f"mode={mode!r} is a real Reads Engine capability but is not yet available through the "
            f"public API.",
        )
    raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized mode.")


def _ensure_difficulty_certified(mode: str, entry: dict, difficulty: Optional[str]) -> None:
    """Part 20/21: reject an uncertified difficulty request BEFORE burning
    real generation attempts on it. Real bug this fixes (found empirically,
    not assumed): requesting difficulty="easy" for draft_guess in v1.2
    silently spent all 5 retry attempts (each a real Engine DB round-trip)
    only to land on NO_ELIGIBLE_GAME every time, because "easy" has zero
    real candidates for this mode -- a fact known in advance, not something
    that needs re-discovering per request. "any" always passes: it isn't a
    difficulty-band claim, it's "no filter", which trivially works if the
    mode has any real candidates at all."""
    if difficulty is None or difficulty == "any":
        return
    if difficulty in entry["certified_difficulties"]:
        return
    raise GatewayError(
        "INVALID_REQUEST",
        f"mode={mode!r} does not have certified {difficulty!r}-difficulty candidates. "
        f"Certified difficulties: {sorted(entry['certified_difficulties'])} (plus 'any').",
    )


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
            "contract_version": CONTRACT_VERSION,
        },
    }


def get_public_game(*, mode: str, difficulty: Optional[str], seed: Optional[str],
                     exclude_game_ids: Optional[List[str]]) -> dict:
    t0 = time.perf_counter()
    entry = _ensure_mode_public(mode)
    _ensure_difficulty_certified(mode, entry, difficulty)
    exclude = set(exclude_game_ids or [])
    attempts_used = 0

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
        attempts_used = attempt + 1
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
            oplog.record_event(
                "public_game_no_eligible", mode=mode, difficulty=difficulty or "any",
                generation_attempts=attempts_used, latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            )
            raise GatewayError(
                "NO_ELIGIBLE_GAME",
                f"No QA-passed question could be generated for mode={mode!r} right now.",
            )
        # Every eligible attempt landed on an excluded game_id -- real,
        # honest outcome for a very small eligible pool, not an
        # infrastructure failure.
        stored = last_eligible

    saved = packages.save_package(stored)
    view = _public_view(mode, entry, saved)
    oplog.record_event(
        "public_game_served", mode=mode, difficulty=view["difficulty"],
        generation_attempts=attempts_used, latency_ms=round((time.perf_counter() - t0) * 1000, 3),
    )
    return view


def validate_public_answer(*, game_id: str, answer: str) -> dict:
    """Part 6/32: one shared validator for every public mode -- there is no
    per-mode branch here because every certified mode today shares the same
    `options[correctIndex]` label shape (Part 30's docstring explains why
    that means no handler classes are needed yet). Normalization
    (strip + case-fold exact match) is mode-agnostic by construction: it
    compares whatever label string the mode's own generator put in
    `options`, never a hand-maintained alias table in this file or in the
    browser. No `mode` parameter is accepted from the client at all -- the
    mode is implied entirely by which package `game_id` resolves to, which
    is also why cross-mode tampering has no surface here (Part 7).

    Part 10: also honors the master kill switch -- a real emergency
    shutdown should stop answer submission too, not just leave already-
    in-flight games playable while new ones can't be fetched."""
    _ensure_public_gameplay_enabled()
    try:
        stored = packages.load_package(game_id)
    except packages.PackageIdInvalid:
        stored = None
    if not stored:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    t0 = time.perf_counter()
    q = stored["questions"][0]
    norm = answer.strip().lower()
    correct_label = q["options"][q["correctIndex"]]
    is_correct = norm == correct_label.strip().lower() or norm == str(q.get("answer", "")).strip().lower()
    oplog.record_event(
        "public_answer_submitted", mode=_mode_for_package(stored), correct=is_correct,
        latency_ms=round((time.perf_counter() - t0) * 1000, 3),
        # Never the raw `answer` string itself (Part 17: "avoid logging raw
        # free-text answers") -- only whether it was right.
    )
    return {
        "correct": is_correct,
        "canonical_answer": correct_label,
        # Matches existing Quiz semantics (app.js renderQuizQuestion): the
        # correct answer -- and any notes -- are only ever revealed AFTER a
        # real guess, never in the initial game payload.
        "notes": q.get("notes") or None,
    }
