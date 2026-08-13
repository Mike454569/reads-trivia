"""Director v0.8 -- Feasibility Engine (v1.8, Part C).

The Game Creator's own layer on top of the already-real translate -> validate
pipeline (translator.py / validator.py / registry.py), NOT a second parser
and NOT a reimplementation of any of that logic. `assess()` calls the exact
same `pipeline.translate_and_validate()` every other caller (Gateway
preview, Gateway generate) already uses, then maps its GateResult onto a
richer, Creator-facing status vocabulary that GateResult alone doesn't
express: whether a "supported" capability has real, disclosed limitations,
and whether a request signals a real football concept this database is
simply missing data for (found by this milestone's own database audits, not
guessed).

--- THE SIX STATUSES (exactly what v1.8, Part C asked for) ---
  SUPPORTED                  -- a registered capability, no known caveats.
  SUPPORTED_WITH_LIMITATIONS -- a registered capability that IS real and
                                 will really generate real puzzles, but has
                                 disclosed, real caveats (registry.py's
                                 `known_limitations`) -- e.g. the lineup
                                 capability's "names not colleges" framing.
  UNDERSTOOD_BUT_UNSUPPORTED -- a real, schema-expressible football concept
                                 (validator recognizes mechanic+domain+
                                 predicate) with no registered adapter yet.
  MISSING_DATA                -- a real football concept this codebase has
                                 directly, empirically audited as absent from
                                 the database (see KNOWN_MISSING_DATA_SIGNALS
                                 below) -- distinct from UNDERSTOOD_BUT_
                                 UNSUPPORTED, which just means "no adapter
                                 written yet," not "the data doesn't exist."
  UNSAFE                      -- reserved for a capability explicitly flagged
                                 `unsafe=True` in the registry. Not reachable
                                 today (no registered capability is flagged
                                 unsafe, and the mock translator never
                                 authors code/SQL/paths -- see providers/
                                 mock.py's module docstring) -- kept as a
                                 real, mechanical status with a real
                                 enforcement point for Part L/M's security
                                 requirement, not a decorative label.
  UNKNOWN                      -- everything else: no recognized football
                                 intent at all (NO_MATCH), or genuine
                                 ambiguity needing clarification
                                 (NEEDS_CLARIFICATION -- `clarifying_question`
                                 is still passed through for the Creator UI
                                 to show, this status just doesn't invent a
                                 7th vocabulary value for it), or a malformed
                                 structured spec (only reachable via a
                                 directly-supplied spec, never real NL text).

This module never generates a package and never mutates anything. It also
never touched the Engine database at all until the feasibility-logic
correction pass described below -- that remains true for every status
except the one narrow, real-time-measured exception documented there.

--- FEASIBILITY-LOGIC CORRECTION: "POSITION + COLLEGE, NAMES HIDDEN" ---
A real bug, not a hypothetical: this module's original `KNOWN_MISSING_DATA_
SIGNALS` entry for "college" treated the NFL-local NULL columns
(`canonical_roster_seasons.school_id`, `canonical_players.primary_school_id`)
as proof college data was absent -- true for those two columns, but NOT
the same claim as "no college data exists anywhere in this database," and
it went stale the moment a later "CFB identity bridge hardened" operation
built `cfb_nfl_identity_bridge_certified` (2,542 real, HIGH_CONFIDENCE_
MULTI_SEASON_POSITION_CORROBORATED rows, confidence 0.994-0.999, zero
ambiguous/duplicate mappings -- confirmed directly). A hardcoded English
sentence can only ever describe the database as it was audited, not as it
is now -- the fix is to measure live instead of asserting from memory.

`_position_lineup_college_hidden_names_reason()` below does exactly that:
it calls `tools.quiz_export.adapters.lineup.lineup_college_coverage()`
(a real, parameterized query against the certified bridge, run fresh every
call) and reports the ACTUAL current coverage. As measured at the time this
correction pass was written: 0 of 415 real team-seasons had all 10 shown
positions bridged to a certified college, and only 6 had all 5 SKILL
positions bridged (ignoring the grouped OL entirely) -- both far below the
20-team-season floor (`MIN_FULL_LINEUP_COLLEGE_COVERAGE`) a real, repeatable
public mode needs.

UPDATE (position+college proof-game fix): exactly the "it will correctly
report SUPPORTED on its own, automatically" promise above came true. A real
identity-bridge expansion (`tools/data_refresh/nfl_college_identity_bridge.py`,
using only already-present Engine data) grew the certified bridge from 2,542
to 7,745+ rows; skill-position-only coverage is now 68 of 412 real,
actually-generatable team-seasons -- past the floor. A real capability
(`NFL_OFFENSE_LINEUP_COLLEGE` / `TEAM_OF_STARTING_LINEUP_BY_COLLEGE`, see
`tools/quiz_export/adapters/lineup_college.py`) is now registered for
exactly this 5-skill-position shape, and `providers/mock.py` /
`providers/anthropic_provider.py` both translate a names-hidden
position+college request to it directly -- so a real such request now
reaches `assess()`'s `gate_status == "READY"` branch above and returns
`SUPPORTED_WITH_LIMITATIONS` (known_limitations disclosing the excluded OL
row) WITHOUT ever reaching `_is_position_lineup_college_hidden_names_
request()`/`_position_lineup_college_hidden_names_reason()` below at all.
Full 10-position coverage remains permanently 0 (a real, measured,
structural ceiling -- OL college coverage is ~10% per player even after the
expansion, so all 5 OL simultaneously covered essentially never happens);
the two functions below remain as a genuine, correct MISSING_DATA fallback
for the (now much narrower) case where translation fails to produce a valid
spec for this exact request pattern for some other reason.

Critically: this is a SEPARATE, explicitly-requested variant (the creator
must ask for colleges with names hidden) from the existing, already-real,
already-shipped `TEAM_OF_STARTING_LINEUP` capability, which uses real
player NAMES and is unaffected by any of this -- see `providers/mock.py`'s
own "hidden names" carve-out for why a names-hidden college request can
never silently fall back to that names-based capability.
"""
from __future__ import annotations

from . import pipeline as director_pipeline
from . import registry

SUPPORT_STATUSES = frozenset({
    "SUPPORTED",
    "SUPPORTED_WITH_LIMITATIONS",
    "UNDERSTOOD_BUT_UNSUPPORTED",
    "MISSING_DATA",
    "UNSAFE",
    "UNKNOWN",
})

# Real, audited signals for concepts this database genuinely does not have
# data for -- each backed by a real query result recorded here, not a guess.
# Checked ONLY when the request does NOT already resolve to a registered
# capability (a request that matches the lineup capability's own keyword
# pattern already gets an honest SUPPORTED_WITH_LIMITATIONS instead -- this
# table is for concepts with no substitute at all).
KNOWN_MISSING_DATA_SIGNALS = {
    # NOTE: this generic entry is the fallback for a BARE "college" mention
    # with no lineup/position framing (e.g. "make a game about where players
    # went to college") -- it is intentionally NOT the check used for the
    # specific "position + college, names hidden" lineup request, which gets
    # its own live-measured, real-numbers reason instead (see
    # `_position_lineup_college_hidden_names_reason()` and `assess()` below).
    # Updated during the feasibility-logic correction pass to stop claiming
    # college data is absent outright -- it no longer is (see module
    # docstring) -- while still being honest that no registered capability
    # uses it for anything other than the narrow lineup case.
    frozenset({"college", "colleges"}): (
        "A certified NFL<->CFB college identity bridge does exist "
        "(cfb_nfl_identity_bridge_certified, 2,542 real high-confidence rows), but no registered "
        "capability is built on it for a general college-guessing request. See the "
        "position+college 'names hidden' lineup variant for the one place this bridge IS measured "
        "and used, and tools/quiz_export/adapters/lineup.lineup_college_coverage() for real, current "
        "coverage numbers -- which today are not enough to support even that narrower case."
    ),
    frozenset({"salary", "salaries", "contract", "contracts", "cap"}): (
        "No salary/contract/cap table exists in this database at all -- this is not a partial-coverage "
        "gap, there is no relevant table to query."
    ),
    frozenset({"injury", "injuries", "injured"}): (
        "No injury table exists in this database."
    ),
}


def _words(text: str) -> set[str]:
    import re
    return set(re.findall(r"[a-z]+", text.lower()))


def _missing_data_reason(request_text: str) -> str | None:
    words = _words(request_text)
    for signal_words, reason in KNOWN_MISSING_DATA_SIGNALS.items():
        if words & signal_words:
            return reason
    return None


_POSITION_LINEUP_WORDS = {"lineup", "lineups", "starters", "starting", "offense", "offensive", "position", "positions"}
_HIDDEN_NAMES_WORDS = {"hidden", "hide", "anonymous"}


def _is_position_lineup_college_hidden_names_request(request_text: str) -> bool:
    """Mirrors providers/mock.py's own carve-out check (same word sets, same
    intent) -- kept as an independent check here rather than imported from
    mock.py, because feasibility.py must recognize this request even when a
    real (non-mock) translator provider is configured someday and would
    never route through mock.py's pattern matching at all. Deliberately
    narrow: requires an explicit hidden/hide/anonymous/"no names" signal,
    not just any college mention, so an ordinary college-phrased lineup
    request (no names-hidden ask) is untouched and keeps falling through to
    the real, already-shipped names-based capability."""
    words = _words(request_text)
    has_college = bool(words & {"college", "colleges"})
    has_hidden_names = (
        bool(words & _HIDDEN_NAMES_WORDS)
        or "no names" in request_text.lower()
        or "without names" in request_text.lower()
        or "names hidden" in request_text.lower()
    )
    has_lineup_signal = bool(words & _POSITION_LINEUP_WORDS)
    return has_college and has_hidden_names and has_lineup_signal


def _position_lineup_college_hidden_names_reason() -> str:
    """The ONE place this module touches the Engine database (module
    docstring) -- a real, live, parameterized-query measurement, run fresh
    every call, never a cached or hardcoded claim. See
    tools.quiz_export.adapters.lineup.lineup_college_coverage()."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import lineup as lineup_adapter

    c = engine.connect()
    try:
        coverage = lineup_adapter.lineup_college_coverage(c)
    finally:
        c.close()

    return (
        f"Measured live against the certified NFL<->CFB identity bridge "
        f"({coverage['bridge_table']}, {coverage['bridge_entries']} real entries): "
        f"only {coverage['full_lineup_college_coverage']} of {coverage['total_candidate_team_seasons']} real "
        f"team-seasons have every shown position's college verified, and only "
        f"{coverage['skill_positions_only_college_coverage']} even if the offensive line is dropped entirely. "
        f"Both are far below the {coverage['min_required_for_support']}-team-season floor a real, repeatable "
        f"public mode needs (for comparison, every other registered capability has dozens to hundreds of real "
        f"candidates). Per-position bridge coverage: "
        + ", ".join(f"{slot} {coverage['per_slot_hit_counts'][slot]}/{coverage['per_slot_totals'][slot]}"
                     for slot in ("QB", "RB", "WR", "TE", "OL"))
        + ". Not supported -- and never silently substituted with player names, since names were explicitly "
          "asked to be hidden."
    )


def assess(request_text: str | None = None, *, spec: dict | None = None, provider: str = "mock") -> dict:
    """The Creator's single entrypoint: given a natural-language request (or
    a structured spec), returns a Creator-facing feasibility assessment.
    Never raises -- always a structured dict with a `support_status` in
    SUPPORT_STATUSES."""
    translation, gate = director_pipeline.translate_and_validate(request_text, spec=spec, provider=provider)
    gate_status = gate["gate_status"]

    result = {
        "support_status": "UNKNOWN",
        "reason": gate.get("gate_reason"),
        "capability": None,
        "known_limitations": [],
        "visual_template": None,
        "clarifying_question": None,
        "closest_supported_capability": None,
        "translator_notes": translation.get("translator_notes"),
        "translation_status": translation.get("translation_status"),
    }

    if gate_status == "READY":
        capability = gate["capability"]
        limitations = list(capability.get("known_limitations", []))
        if capability.get("unsafe"):
            result["support_status"] = "UNSAFE"
            result["reason"] = "This capability is flagged unsafe in the registry and cannot be generated."
            return result
        result["support_status"] = "SUPPORTED_WITH_LIMITATIONS" if limitations else "SUPPORTED"
        result["known_limitations"] = limitations
        validated_spec = gate["validated_spec"]
        result["capability"] = {
            "mechanic": validated_spec["mechanic"],
            "domain": validated_spec["domain"],
            "relationship_predicate": validated_spec["relationship_predicate"],
            "category": capability.get("category"),
        }
        result["visual_template"] = capability.get("visual_template", "DEFAULT_MULTIPLE_CHOICE")
        return result

    if gate_status == "UNDERSTOOD_BUT_UNSUPPORTED":
        result["support_status"] = "UNDERSTOOD_BUT_UNSUPPORTED"
        result["closest_supported_capability"] = gate.get("closest_supported_capability")
        return result

    if gate_status == "NEEDS_CLARIFICATION":
        result["support_status"] = "UNKNOWN"
        result["clarifying_question"] = gate.get("clarifying_question")
        return result

    # BLOCKED_NO_TRANSLATION (NO_MATCH or malformed translator output),
    # BLOCKED_INVALID_SPEC, BLOCKED_OUT_OF_BOUNDS, BLOCKED_UNSUPPORTED_FILTER.
    if request_text:
        # Checked BEFORE the generic KNOWN_MISSING_DATA_SIGNALS fallback --
        # this specific request gets a real, live-measured, numbers-backed
        # reason instead of the generic static one (which would also match,
        # since it's still a "college" mention, but would be far less
        # precise and wouldn't reflect today's actual bridge coverage).
        if _is_position_lineup_college_hidden_names_request(request_text):
            result["support_status"] = "MISSING_DATA"
            result["reason"] = _position_lineup_college_hidden_names_reason()
            return result
        missing_reason = _missing_data_reason(request_text)
        if missing_reason:
            result["support_status"] = "MISSING_DATA"
            result["reason"] = missing_reason
            return result

    result["support_status"] = "UNKNOWN"
    return result


def list_capability_support_summary() -> list[dict]:
    """Every registered capability's own support status, for the Creator's
    'what's already possible' reference view -- always SUPPORTED or
    SUPPORTED_WITH_LIMITATIONS by construction (only registered capabilities
    reach this list), never generates anything."""
    out = []
    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        limitations = list(cap.get("known_limitations", []))
        out.append({
            "mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
            "category": cap.get("category"),
            "support_status": "SUPPORTED_WITH_LIMITATIONS" if limitations else "SUPPORTED",
            "known_limitations": limitations,
            "visual_template": cap.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
        })
    return out
