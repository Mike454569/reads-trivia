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

This module never touches the Engine database, never generates a package,
and never mutates anything -- pure read/reason over already-existing,
already-proven pipeline output.
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
    frozenset({"college", "colleges"}): (
        "Audited directly: canonical_roster_seasons.school_id is NULL for 100% of rows (0/60,246), "
        "canonical_players.primary_school_id is NULL for 100% of rows (0/17,113), and the only NFL<->CFB "
        "player bridge (nfl_cfb_player_links) has 124 total rows, only 39 with any recorded starts. "
        "College attendance is not reliably present in this database for NFL players."
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
