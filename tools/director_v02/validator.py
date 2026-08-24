"""Strict validation of translator output. Treats EVERY translator -- mock or
real LLM -- as untrusted input. Nothing here trusts that the translator
already enforced its own schema; every check is re-applied independently.

Security property this module provides, regardless of how well-behaved (or
compromised, or simply buggy) the translator is: every field that reaches
`generate_package_from_spec()` has passed an `in <hardcoded allowlist>`
check against a finite Python set of literal safe strings, or an integer
bounds check. There is no code path from a TranslationResult's string
content into a SQL string, a Python expression, a file path, a URL, or a
dynamically-resolved module/predicate/adapter name -- unrecognized values
are rejected outright, never coerced, sanitized-and-used, or logged into an
executable context.

Returns a GateResult:
    {
        "gate_status": one of GATE_STATUSES below,
        "gate_reason": str,
        "validated_spec": dict | None,      # only set when gate_status == "READY"
        "capability": dict | None,          # registry entry, only set when READY
        "missing_capability": tuple | None, # (mechanic, domain, predicate) when UNDERSTOOD_BUT_UNSUPPORTED
        "closest_supported_capability": tuple | None,
    }
"""
from __future__ import annotations

from . import registry, schema

GATE_STATUSES = frozenset({
    "READY",
    "BLOCKED_NO_TRANSLATION",       # translator produced NO_MATCH or malformed TranslationResult
    "BLOCKED_INVALID_SPEC",         # spec present but fails schema/allowlist/type checks
    "BLOCKED_OUT_OF_BOUNDS",        # question_count outside allowed range
    "BLOCKED_UNSUPPORTED_FILTER",   # filters/exclusions non-empty, not supported by any registered capability
    "UNDERSTOOD_BUT_UNSUPPORTED",   # schema-valid spec (or a recognized-but-unsupported mechanic),
                                     # but no registered capability covers it
    "NEEDS_CLARIFICATION",          # translator recognized partial signal but not enough to resolve --
                                     # see DIRECTOR_V03_CLARIFICATION_CONTRACT.md
})


def _blocked(status: str, reason: str, **extra) -> dict:
    out = {
        "gate_status": status,
        "gate_reason": reason,
        "validated_spec": None,
        "capability": None,
        "missing_capability": None,
        "closest_supported_capability": None,
        "understood": None,
        "missing_fields": None,
        "clarifying_question": None,
    }
    out.update(extra)
    return out


def validate_translation(translation_result: dict) -> dict:
    if not isinstance(translation_result, dict):
        return _blocked("BLOCKED_NO_TRANSLATION", "Translator did not return a dict.")

    status = translation_result.get("translation_status")
    notes = translation_result.get("translator_notes", "")

    if status == "UNDERSTOOD_UNSUPPORTED_MECHANIC":
        return _blocked(
            "UNDERSTOOD_BUT_UNSUPPORTED",
            f"Translator recognized the request but no capability implements it yet: {notes}",
            closest_supported_capability=_suggest_closest(),
        )

    if status == "NEEDS_CLARIFICATION":
        # The Engine, not the translator, is the source of truth for WHICH
        # structured fields are still missing/required -- but at this stage
        # we have no candidate spec to check field-by-field, so we pass
        # through the translator's own missing_fields list (itself only
        # ever drawn from DirectorSpec's known field names in both the mock
        # and the real-provider system prompt) rather than re-deriving it.
        # `understood`/`clarifying_question` are DISPLAY TEXT ONLY -- never
        # used to construct a spec or select a capability.
        understood = translation_result.get("understood")
        missing_fields = translation_result.get("missing_fields")
        question = translation_result.get("clarifying_question")
        return _blocked(
            "NEEDS_CLARIFICATION",
            f"Translator recognized partial NFL/trivia intent but not enough to resolve "
            f"to a specific game: {notes}",
            understood=understood if isinstance(understood, dict) else {},
            missing_fields=[f for f in missing_fields if isinstance(f, str)] if isinstance(missing_fields, list) else [],
            clarifying_question=question if isinstance(question, str) else "What kind of NFL trivia game do you want?",
        )

    if status != "TRANSLATED":
        # Covers "NO_MATCH" and any unrecognized/missing status value.
        return _blocked(
            "BLOCKED_NO_TRANSLATION",
            f"Translator did not produce a usable spec (status={status!r}): {notes}",
        )

    spec = translation_result.get("spec")
    if not isinstance(spec, dict):
        return _blocked("BLOCKED_INVALID_SPEC", "translation_status was TRANSLATED but spec was not a dict.")

    # --- Exact key-set check first -- catches injected extra fields outright. ---
    keys = set(spec.keys())
    missing_required = schema.REQUIRED_SPEC_KEYS - keys
    if missing_required:
        return _blocked("BLOCKED_INVALID_SPEC", f"spec is missing required fields: {sorted(missing_required)}")
    unexpected = keys - schema.ALL_SPEC_KEYS
    if unexpected:
        return _blocked(
            "BLOCKED_INVALID_SPEC",
            f"spec contains fields outside the allowed schema (rejected, not ignored): {sorted(unexpected)}",
        )

    mechanic = spec.get("mechanic")
    domain = spec.get("domain")
    predicate = spec.get("relationship_predicate")
    question_count = spec.get("question_count")
    difficulty = spec.get("difficulty")
    filters = spec.get("filters", {})
    exclusions = spec.get("exclusions", [])

    if not isinstance(mechanic, str) or mechanic not in schema.ALLOWED_MECHANICS:
        return _blocked("BLOCKED_INVALID_SPEC", f"mechanic {mechanic!r} is not in the allowlist {sorted(schema.ALLOWED_MECHANICS)}")
    if not isinstance(domain, str) or domain not in schema.ALLOWED_DOMAINS:
        return _blocked("BLOCKED_INVALID_SPEC", f"domain {domain!r} is not in the allowlist {sorted(schema.ALLOWED_DOMAINS)}")
    if not isinstance(predicate, str) or predicate not in schema.ALLOWED_PREDICATES:
        return _blocked("BLOCKED_INVALID_SPEC", f"relationship_predicate {predicate!r} is not in the allowlist {sorted(schema.ALLOWED_PREDICATES)}")
    if not isinstance(difficulty, str) or difficulty not in schema.ALLOWED_DIFFICULTIES:
        return _blocked("BLOCKED_INVALID_SPEC", f"difficulty {difficulty!r} is not in the allowlist {sorted(schema.ALLOWED_DIFFICULTIES)}")
    if isinstance(question_count, bool) or not isinstance(question_count, int):
        return _blocked("BLOCKED_INVALID_SPEC", f"question_count must be an integer, got {question_count!r}")
    if not (schema.QUESTION_COUNT_MIN <= question_count <= schema.QUESTION_COUNT_MAX):
        return _blocked(
            "BLOCKED_OUT_OF_BOUNDS",
            f"question_count {question_count} outside allowed range "
            f"[{schema.QUESTION_COUNT_MIN}, {schema.QUESTION_COUNT_MAX}]",
        )
    if not isinstance(filters, dict) or set(filters.keys()) - schema.ALLOWED_FILTER_KEYS:
        return _blocked("BLOCKED_UNSUPPORTED_FILTER", f"filters {filters!r} contains keys no capability supports yet")
    if not isinstance(exclusions, list) or (exclusions and not schema.EXCLUSIONS_SUPPORTED):
        return _blocked("BLOCKED_UNSUPPORTED_FILTER", f"exclusions {exclusions!r} are not supported by any registered capability yet")

    capability = registry.lookup(mechanic, domain, predicate)
    if capability is None:
        return _blocked(
            "UNDERSTOOD_BUT_UNSUPPORTED",
            f"'{mechanic}+{domain}+{predicate}' is schema-valid but not a registered capability yet.",
            missing_capability=(mechanic, domain, predicate),
            closest_supported_capability=_suggest_closest(),
        )

    if not (capability["min_question_count"] <= question_count <= capability["max_question_count"]):
        return _blocked(
            "BLOCKED_OUT_OF_BOUNDS",
            f"question_count {question_count} outside this capability's bounds "
            f"[{capability['min_question_count']}, {capability['max_question_count']}]",
        )
    if difficulty not in capability["supported_difficulties"]:
        return _blocked("UNDERSTOOD_BUT_UNSUPPORTED", f"difficulty {difficulty!r} not supported by this capability")
    if set(filters.keys()) - capability["supported_filter_keys"]:
        return _blocked(
            "BLOCKED_UNSUPPORTED_FILTER",
            f"filters {filters!r} contains key(s) this specific capability does not support "
            f"(supports: {sorted(capability['supported_filter_keys'])})",
        )

    return {
        "gate_status": "READY",
        "gate_reason": "spec is schema-valid and matches a registered capability",
        "validated_spec": dict(spec),
        "capability": capability,
        "missing_capability": None,
        "closest_supported_capability": None,
    }


def _suggest_closest() -> tuple[str, str, str] | None:
    keys = registry.all_capability_keys()
    return keys[0] if keys else None
