"""P0 Accuracy + Reliability Hardening pass: the single shared "is this
package actually a real, playable game" contract, enforced at the real
choke points every capability's package must pass through (gateway/services/
packages.py's save_package(), plus reusable by any audit/QA script) instead
of trusting each generator's own self-reported qa_status field.

Why this exists: every generate_fn (game_director_v01.py's guess-mechanic
path, the two player_from_clues variants, and the director_v04 mechanic
pilots) already computes its own qa_status ("PASSED" only when its own
content list is non-empty) -- real, existing guards, not invented here. But
those are 8+ separate, independently-written checks; a bug in any ONE of
them (a future capability that sets qa_status="PASSED" unconditionally, or
miscounts an empty list as non-empty) would silently defeat its own guard
with nothing else catching it. This module is the second, INDEPENDENT check
that doesn't trust any generator's self-report -- it inspects the actual
package content and decides for itself whether the package is real.

`validate_package_contract()` returns a list of violation strings (empty
list == passes the contract). Never raises on a malformed package -- a
package that fails validation is exactly the case this function exists to
report, not crash on.
"""
from __future__ import annotations

from typing import Any

# Every known "list of playable content" key across every mechanic shape in
# this codebase (game_director_v01.py's "questions", the two player_from_clues
# variants' "puzzles", the director_v04 mechanic pilots' "rounds"/"items"/
# "games", public_six_degrees.py's "steps"). Real, found gap this pass:
# tools/director_v02/mechanic_engine.py -- the separate taxonomy-based
# wrapper POST /v1/creator/mechanics/round uses -- independently re-wraps
# the same underlying HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL generation
# under a DIFFERENT key, "sequence" (not "items", which is what the raw
# director_v04/{higher_lower,elimination}.py modules' own build_package()
# uses for the separate public_mechanics.py path) -- and
# LIVE_WEEKLY_FANTASY_DRAFT's package is a player POOL to draft from
# ("players"), not a list of rounds. A package must have exactly one of
# these present as a real, non-empty list -- checked in this priority order
# only to pick a single unambiguous key to validate contents of when more
# than one happens to be present (never expected in practice; each mechanic
# only ever sets one).
_CONTENT_LIST_KEYS = ("questions", "puzzles", "rounds", "items", "games", "steps", "sequence", "players")

# Coach Connections (public_coach_connections.py) is structurally different
# from every mechanic above: the "content" isn't a list of rounds/questions
# at all -- one package IS one graph-traversal puzzle, described by a
# start/end pair and the real, engine-verified path between them. Detected
# by its own `mode` field (the same field the codebase already checks this
# way elsewhere, e.g. public_coach_connections.py's own exclude-pairs logic)
# rather than forced into the generic list-key shape above.
_GRAPH_PUZZLE_MODES = frozenset({"coach_connections"})


def _validate_graph_puzzle(package: dict) -> list[str]:
    violations = []
    start, end = package.get("start"), package.get("end")
    if not isinstance(start, dict) or not start.get("id"):
        violations.append("graph puzzle: start entity is missing or blank")
    if not isinstance(end, dict) or not end.get("id"):
        violations.append("graph puzzle: end entity is missing or blank")
    path = package.get("canonical_path")
    if not isinstance(path, list) or not path:
        violations.append("graph puzzle: canonical_path is empty -- no real connection was found")
    return violations


def _find_content_list(package: dict) -> tuple[str | None, list]:
    for key in _CONTENT_LIST_KEYS:
        value = package.get(key)
        if isinstance(value, list):
            return key, value
    return None, []


def _validate_guess_question(q: dict, index: int) -> list[str]:
    violations = []
    options = q.get("options")
    if not isinstance(options, list) or len(options) < 2:
        violations.append(f"questions[{index}]: options must be a list of at least 2 -- got {options!r}")
        return violations  # nothing else here is checkable without real options
    correct_index = q.get("correctIndex")
    if not isinstance(correct_index, int) or not (0 <= correct_index < len(options)):
        violations.append(f"questions[{index}]: correctIndex {correct_index!r} not a valid index into options")
        return violations
    answer = q.get("answer")
    if not answer or not str(answer).strip():
        violations.append(f"questions[{index}]: answer is blank")
    elif answer != options[correct_index]:
        # Real, dangerous failure mode: a package whose declared "answer" field
        # doesn't match the option actually marked correct -- a player could be
        # shown the right option but scored wrong (or vice versa) depending on
        # which field a given renderer trusts.
        violations.append(
            f"questions[{index}]: answer {answer!r} does not match options[correctIndex] {options[correct_index]!r}"
        )
    # No multiple-correct-answer accident: every option must be distinct
    # (case/whitespace-insensitive -- "Dallas Cowboys" and "dallas cowboys "
    # are the same real answer duplicated, not two valid distractors).
    normalized = [str(o).strip().lower() for o in options]
    if len(set(normalized)) != len(normalized):
        violations.append(f"questions[{index}]: duplicate options make the correct answer ambiguous -- {options!r}")
    if not str(q.get("question") or "").strip():
        violations.append(f"questions[{index}]: question text is blank")
    return violations


def _validate_puzzle(p: dict, index: int) -> list[str]:
    violations = []
    answer = p.get("answer")
    if not isinstance(answer, dict) or not str(answer.get("displayName") or answer.get("display_name") or "").strip():
        violations.append(f"puzzles[{index}]: answer entity is missing or blank")
    clues = p.get("clues")
    if not isinstance(clues, list) or not clues:
        violations.append(f"puzzles[{index}]: clues list is empty")
    return violations


def validate_package_contract(package: dict) -> list[str]:
    """Independently verifies a generated package is a real, non-empty,
    structurally sound playable game. Returns a list of human-readable
    violation strings; an empty list means the package satisfies the global
    supported-game contract. This is deliberately stricter than, and
    independent of, whatever qa_status the generator itself already set --
    a caller enforcing "no empty/broken SUPPORTED package" should trust this
    function's verdict, not the package's own self-report."""
    violations: list[str] = []
    if not isinstance(package, dict):
        return [f"package is not a dict: {type(package)!r}"]

    if not str(package.get("package_id") or "").strip():
        violations.append("package_id is missing or blank")

    qa_status = package.get("qa_status")
    if qa_status not in ("PASSED", "FAILED"):
        violations.append(f"qa_status is missing/blank/unrecognized: {qa_status!r}")

    review_status = package.get("review_status")
    if not str(review_status or "").strip():
        violations.append("review_status is missing or blank")

    if package.get("mode") in _GRAPH_PUZZLE_MODES:
        violations.extend(_validate_graph_puzzle(package))
        return violations

    content_key, content_list = _find_content_list(package)
    if content_key is None:
        violations.append(
            f"package has no recognized non-empty content list (checked {_CONTENT_LIST_KEYS}) -- "
            f"an empty candidate pool produced a package with nothing to play"
        )
        return violations  # nothing further to check without real content
    if not content_list:
        violations.append(f"{content_key} is present but empty -- 0-question/0-puzzle package")
        return violations

    if content_key == "questions":
        for i, q in enumerate(content_list):
            violations.extend(_validate_guess_question(q, i))
    elif content_key == "puzzles":
        for i, p in enumerate(content_list):
            violations.extend(_validate_puzzle(p, i))
    # rounds/items/games (the director_v04 mechanic pilots): each mechanic's
    # own internal shape varies enough (and each already has its own
    # dedicated safety-check module) that this shared contract only enforces
    # the universal invariant -- non-empty -- for those, already done above.

    return violations


def is_valid_package(package: dict) -> bool:
    """Convenience boolean wrapper -- see validate_package_contract()."""
    return not validate_package_contract(package)
