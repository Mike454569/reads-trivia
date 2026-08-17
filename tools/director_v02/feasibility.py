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

--- STALE-COLLEGE-FEASIBILITY FIX (general "college of an NFL player") ---
A second, separate real bug, found by literally testing the live Creator
against "Make me a game where I guess the college of an NFL player.": the
generic `KNOWN_MISSING_DATA_SIGNALS["college"]` entry (below) was a
HARDCODED English sentence citing `cfb_nfl_identity_bridge_certified`'s
2,542-row count -- the SAME staleness bug the position+college fix above
already found and fixed once, recurring in a second, more general place
this module makes the same kind of claim. That 2,542 number was stale on
two independent counts by the time this was caught: (1) the bridge itself
had already grown past 2,542 (see UPDATE above), and (2) a completely
DIFFERENT, larger, more directly relevant table -- `draft_facts.college` /
`nfl_players_draft.college`, backfilled from the `draft_picks.csv` source's
long-unmapped `college` column, 12,914 of 12,927 real draft rows (1980-2026)
-- makes a GENERAL player<->college capability genuinely supportable now,
completely independent of the narrower, season-lineup-specific bridge this
sentence was originally (and still, for its own narrow case) describing.

Fix, same discipline as the position+college fix: (1) two new real,
registered capabilities now exist --
`ATTENDED_COLLEGE`/`NFL_DRAFT` (guess a specific drafted player's college,
`tools/quiz_export/adapters/draft_college.py`) and an extended
`IDENTIFY_FROM_CLUES`/`NFL_PLAYER_IDENTITY` routing (guess the player from
college+other clues -- that capability already supported "college" and
"draft_round" as clue types; it just weren't reachable from this exact
phrasing before) -- so most real "college" requests now resolve via
`gate_status == "READY"` and never reach this fallback at all. (2) For the
narrower remainder that still doesn't match either pattern (e.g. a request
mentioning "college" with no player/school framing the translator
recognizes), `_general_college_missing_data_reason()` below replaces the
hardcoded sentence with a live query against `draft_facts` every call, the
same "measure live, never assert from memory" fix the position+college
correction pass already established.
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

# Reliability-design Phase 1: the corrected, catalog-backed vocabulary
# (approved design). Added here, additively, alongside the six statuses
# above -- NOT a replacement. The six above describe what the EXISTING
# registry-driven translate/validate/lookup pipeline can distinguish today;
# these seven describe a capability's real position in
# capability_catalog.verification_status's lifecycle, and become load-
# bearing once a later phase (1) starts registering genuinely NEW,
# not-yet-public capabilities in the catalog and (2) adds the liveness
# probe that gates SUPPORTED on more than registry presence (Phase 2 -- not
# built yet). In Phase 1 every real catalog row is either PUBLIC_ENABLED-
# equivalent (LEGACY_PUBLIC_PENDING_REVALIDATION) or doesn't exist at all,
# so these seven terms are reachable in code and covered by tests, but
# never actually returned by a real end-user request yet -- see
# `catalog_status_for()` below and its own docstring.
CATALOG_SUPPORT_STATUSES = frozenset({
    "SUPPORTED",
    "VERIFIED_NOT_RELEASED",
    "IMPLEMENTED_NOT_VERIFIED",
    "DATA_EXISTS_UNVERIFIED",
    "UNDERSTOOD_NOT_IMPLEMENTED",
    "INSUFFICIENT_COVERAGE",
    "TEMPORARILY_UNAVAILABLE",
})

# capability_catalog.verification_status -> the corrected vocabulary term.
# An implemented-but-unreleased capability is never called an "unsupported
# mechanic" -- it gets its own real, distinct term (VERIFIED_NOT_RELEASED).
_CATALOG_STATE_TO_VOCAB = {
    "PUBLIC_ENABLED": "SUPPORTED",
    "LEGACY_PUBLIC_PENDING_REVALIDATION": "SUPPORTED",
    "HUMAN_APPROVED": "VERIFIED_NOT_RELEASED",
    "GENERATION_VERIFIED": "VERIFIED_NOT_RELEASED",
    "IMPLEMENTED": "IMPLEMENTED_NOT_VERIFIED",
    "DATA_PRESENT": "DATA_EXISTS_UNVERIFIED",
    "STRUCTURALLY_VALIDATED": "DATA_EXISTS_UNVERIFIED",
    "DISCOVERED": "UNDERSTOOD_NOT_IMPLEMENTED",
    "BLOCKED": "TEMPORARILY_UNAVAILABLE",
}


def catalog_status_for(mechanic: str, domain: str, predicate: str) -> str | None:
    """Maps a (mechanic, domain, predicate) triple's REAL, current
    capability_catalog row to the corrected vocabulary term. Returns None
    if no catalog row exists at all (Phase 1: this is true for every
    triple that isn't one of the 21 real, registered capabilities -- the
    catalog only contains real, backfilled rows, never a guessed one).

    Phase 1 scope note: `PUBLIC_ENABLED` here does NOT yet require a
    passing liveness probe (that infrastructure is Phase 2) -- it reflects
    the row's recorded state only. Once Phase 2 lands, this function (or
    its caller) additionally requires a fresh passing probe before
    returning "SUPPORTED", closing the exact gap this whole reliability
    design exists to close. Not wired into `assess()`'s actual return value
    yet -- see module note above `CATALOG_SUPPORT_STATUSES`; this is
    published, tested, real code that a later phase composes with, not
    dead code."""
    from tools.director_v02 import catalog
    from tools.quiz_export import engine

    c = engine.connect()
    try:
        row = catalog.get_capability_by_triple(c, mechanic, domain, predicate)
    finally:
        c.close()
    if row is None:
        return None
    return _CATALOG_STATE_TO_VOCAB.get(row["verification_status"], "UNDERSTOOD_NOT_IMPLEMENTED")


def raw_catalog_state_for(mechanic: str, domain: str, predicate: str) -> str | None:
    """Phase 2 correction: returns the ACTUAL internal capability_catalog
    lifecycle state (e.g. "LEGACY_PUBLIC_PENDING_REVALIDATION",
    "PUBLIC_ENABLED") -- never the mapped, user-facing vocabulary term
    (that's `catalog_status_for()` above). `assess()`'s `catalog_status`
    field now returns THIS, kept deliberately distinct from the user-facing
    `support_status` field: a caller who wants the corrected 7-term
    vocabulary instead should call `catalog_status_for()` directly, or use
    `assess()`'s `catalog_vocabulary_status` field."""
    from tools.director_v02 import catalog
    from tools.quiz_export import engine

    c = engine.connect()
    try:
        row = catalog.get_capability_by_triple(c, mechanic, domain, predicate)
    finally:
        c.close()
    return row["verification_status"] if row else None


# Real, audited signals for concepts this database genuinely does not have
# data for -- each backed by a real query result recorded here, not a guess.
# Checked ONLY when the request does NOT already resolve to a registered
# capability (a request that matches the lineup capability's own keyword
# pattern already gets an honest SUPPORTED_WITH_LIMITATIONS instead -- this
# table is for concepts with no substitute at all). "college"/"colleges" is
# deliberately NOT listed here -- see `_general_college_missing_data_reason()`
# below for why a bare college mention now needs a LIVE-measured reason,
# never a hardcoded one (that was exactly the stale-college-feasibility bug).
KNOWN_MISSING_DATA_SIGNALS = {
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


_GENERAL_COLLEGE_WORDS = frozenset({"college", "colleges", "school", "schools"})


def _general_college_missing_data_reason() -> str:
    """The bare-"college"-mention fallback, now LIVE-measured every call
    instead of a hardcoded sentence (the exact bug this whole correction
    pass exists to fix -- see module docstring's STALE-COLLEGE-FEASIBILITY
    FIX section). Reached only when a college-mentioning request matches
    NEITHER real registered capability (ATTENDED_COLLEGE's "guess the
    college" phrasing, or IDENTIFY_FROM_CLUES's "guess the player from his
    college" phrasing) -- i.e. genuine translator ambiguity, not a real data
    gap, so this reports what DOES exist rather than claiming absence."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import draft_college

    c = engine.connect()
    try:
        coverage = draft_college.live_college_coverage(c)
    finally:
        c.close()

    return (
        f"Measured live against {coverage['table']} ({coverage['source_id']}): "
        f"{coverage['rows_with_college']} of {coverage['total_draft_rows']} real NFL draft picks "
        f"({coverage['min_season']}-{coverage['max_season']}) have a known college on record, covering "
        f"{coverage['unique_players_with_college']} unique players across {coverage['unique_colleges']} real "
        f"colleges. Two real, registered capabilities already use this: ATTENDED_COLLEGE/NFL_DRAFT (\"guess "
        f"the college/school [a player] attended\") and IDENTIFY_FROM_CLUES/NFL_PLAYER_IDENTITY (\"guess the "
        f"player from his college [and other clues]\") -- this specific request just didn't match either "
        f"phrasing pattern. Try rephrasing as one of those two framings. (For the separate, narrower "
        f"season-specific 'starting lineup by college, names hidden' capability, see "
        f"tools.quiz_export.adapters.lineup.lineup_college_coverage() for its own live coverage numbers.)"
    )


def _missing_data_reason(request_text: str) -> str | None:
    words = _words(request_text)
    if words & _GENERAL_COLLEGE_WORDS:
        return _general_college_missing_data_reason()
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
        # Phase 2 correction: `catalog_status` is the RAW internal lifecycle
        # state (e.g. "LEGACY_PUBLIC_PENDING_REVALIDATION"), deliberately
        # kept separate from the user-facing `support_status` above --
        # never a second copy of it. `catalog_vocabulary_status` is the
        # mapped, corrected 7-term vocabulary value for callers that want
        # that instead. Both populated only on the READY path today (Phase
        # 1/2 scope: every real catalog row is currently one of the 21
        # already-registered capabilities).
        "catalog_status": None,
        "catalog_vocabulary_status": None,
    }

    if gate_status == "READY":
        capability = gate["capability"]
        limitations = list(capability.get("known_limitations", []))
        if capability.get("unsafe"):
            result["support_status"] = "UNSAFE"
            result["reason"] = "This capability is flagged unsafe in the registry and cannot be generated."
            return result
        validated_spec = gate["validated_spec"]
        result["capability"] = {
            "mechanic": validated_spec["mechanic"],
            "domain": validated_spec["domain"],
            "relationship_predicate": validated_spec["relationship_predicate"],
            "category": capability.get("category"),
        }
        result["visual_template"] = capability.get("visual_template", "DEFAULT_MULTIPLE_CHOICE")
        # Reliability-design Phase 1/2/3: catalog cross-check, computed
        # BEFORE support_status is decided (Phase 1/2 attached these as
        # diagnostic-only fields that never changed support_status --
        # Phase 3 closes that gap for real, now that a genuinely new,
        # not-yet-verified capability exists to prove it against).
        # Defensively wrapped: a catalog lookup failure (e.g. the table
        # doesn't exist in some other environment) must never break a real
        # feasibility response -- falls back to registry-presence-only
        # behavior rather than raising, same as before this correction.
        catalog_lookup_ok = True
        try:
            result["catalog_status"] = raw_catalog_state_for(
                validated_spec["mechanic"], validated_spec["domain"], validated_spec["relationship_predicate"],
            )
            result["catalog_vocabulary_status"] = catalog_status_for(
                validated_spec["mechanic"], validated_spec["domain"], validated_spec["relationship_predicate"],
            )
        except Exception:
            result["catalog_status"] = None
            result["catalog_vocabulary_status"] = None
            catalog_lookup_ok = False

        # Phase 3 correction: never report SUPPORTED/SUPPORTED_WITH_LIMITATIONS
        # from registry presence alone -- this is the EXACT real bug this
        # whole reliability effort exists to close ("PLAYER + SEASON -> TEAM
        # was labeled SUPPORTED, but generation returned Load failed"). Only
        # gates on a DEFINITE, successfully-retrieved not-yet-proven catalog
        # state -- a catalog LOOKUP FAILURE (infrastructure hiccup, caught
        # above) or no row found at all falls back to the old registry-
        # presence behavior rather than blocking every real capability over
        # a diagnostic side-channel problem; this matches the module's
        # existing "a catalog lookup failure must never break a real
        # feasibility response" guarantee. GENERATION_VERIFIED and
        # HUMAN_APPROVED (both map to VERIFIED_NOT_RELEASED) are real and
        # proven to generate -- good enough for admin-only private preview,
        # just not public release, so they are NOT gated here.
        _NOT_YET_PROVEN_VOCAB = {
            "UNDERSTOOD_NOT_IMPLEMENTED", "DATA_EXISTS_UNVERIFIED",
            "IMPLEMENTED_NOT_VERIFIED", "TEMPORARILY_UNAVAILABLE",
        }
        if catalog_lookup_ok and result["catalog_vocabulary_status"] in _NOT_YET_PROVEN_VOCAB:
            result["support_status"] = "UNDERSTOOD_BUT_UNSUPPORTED"
            result["reason"] = (
                f"This capability is recognized but has not yet been verified as actually working "
                f"(catalog lifecycle state: {result['catalog_status']}). Not reporting SUPPORTED from "
                f"registry presence alone."
            )
            result["known_limitations"] = []
            return result

        result["support_status"] = "SUPPORTED_WITH_LIMITATIONS" if limitations else "SUPPORTED"
        result["known_limitations"] = limitations
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
    """Every registry-registered capability that has ALSO been verified in
    the catalog (at least GENERATION_VERIFIED), for the Creator's 'what's
    already possible' reference view -- always SUPPORTED or
    SUPPORTED_WITH_LIMITATIONS by construction, never generates anything.

    Phase 3 correction: this used to include every registry entry
    unconditionally ("only registered capabilities reach this list" was
    true but not sufficient -- registry presence alone is exactly the
    claim this whole reliability effort exists to stop trusting). A
    capability whose catalog row hasn't reached a proven state yet
    (DISCOVERED/DATA_PRESENT/STRUCTURALLY_VALIDATED/IMPLEMENTED/BLOCKED) is
    real and registered but not yet verified to actually generate --
    excluded from this specific "what's already possible" list rather than
    claimed SUPPORTED, honest with itself the same way assess() now is. A
    capability the catalog lookup fails to resolve at all (should not
    happen for a real registered one, but never silently trusted) is
    conservatively excluded too."""
    _PROVEN_VOCAB = {"SUPPORTED", "VERIFIED_NOT_RELEASED"}
    out = []
    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        try:
            vocab_status = catalog_status_for(mechanic, domain, predicate)
        except Exception:
            vocab_status = None
        if vocab_status not in _PROVEN_VOCAB:
            continue
        limitations = list(cap.get("known_limitations", []))
        out.append({
            "mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
            "category": cap.get("category"),
            "support_status": "SUPPORTED_WITH_LIMITATIONS" if limitations else "SUPPORTED",
            "known_limitations": limitations,
            "visual_template": cap.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
        })
    return out
