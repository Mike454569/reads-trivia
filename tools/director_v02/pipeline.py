"""Director v0.2+ pipeline entrypoint:

    user text -> translator.translate() -> validator.validate_translation()
    -> [READY] -> capability["generate_fn"](...) -> GeneratedGamePackage

As of Director v0.4, this module is mechanic-agnostic: it never builds a
Game-Factory-shaped spec itself and never assumes every capability shares
one generation path. Each registry entry declares its own `generate_fn`
(see `registry.py`) -- `guess`-mechanic capabilities (Draft, Championship)
dispatch to a wrapper around `game_director_v01.generate_package_from_spec()`;
`identify_player_from_clues` dispatches to its own dedicated builder in
`tools/director_v04/player_from_clues.py`. This module attaches the two
fields every package gets regardless of mechanic (`director_spec`,
`translator`) generically, after the mechanic-specific generator returns,
rather than baking them into any one generator.

The old regex parser (`game_director.interpret()` via
`game_director_v01.interpret_and_gate()`) is untouched and still works
standalone -- it is simply not consulted here.

This module never touches the Engine database directly.
"""
from __future__ import annotations

import hashlib
import time

from . import audit_log  # noqa: E402
from . import translator as translator_mod  # noqa: E402
from . import validator as validator_mod  # noqa: E402

ID_START = 610000  # default fallback only -- each capability's own
                    # `pipeline_id_start` (registry.py) takes precedence.


def _director_request_id(request_text: str, translator_id: str) -> str:
    return "GDR2:" + hashlib.sha256(f"{request_text}|{translator_id}".encode()).hexdigest()[:24]


def _synthetic_translation_result(spec: dict, request_text: str) -> dict:
    """Wraps a caller-supplied structured spec (Director v0.6 Gateway: 'accept
    a natural-language request OR a validated structured spec') in the exact
    TranslationResult shape a real translator would produce, so it flows
    through validator.validate_translation() with NO special-casing -- a
    directly-supplied spec is exactly as untrusted as translator output and
    faces the exact same allowlist/bounds checks, never a bypass."""
    return {
        "raw_request_text": request_text or "(structured spec supplied directly, no natural-language translation)",
        "translator_id": "direct-spec",
        "translation_status": "TRANSLATED",
        "spec": spec,
        "translator_notes": "Spec supplied directly by the caller, not produced by any translator.",
    }


def translate_and_validate(request_text: str | None = None, *, spec: dict | None = None,
                            provider: str = "mock") -> tuple[dict, dict]:
    """The translate+validate half of run(), factored out so a preview-only
    caller (Director v0.6 Gateway's POST /v1/games/preview) can get the same
    translation/validation result WITHOUT triggering generation -- shared
    code, not a second implementation. Exactly one of request_text/spec must
    be meaningfully provided; if spec is given, request_text is used only as
    an optional human-readable label (see _synthetic_translation_result)."""
    if spec is not None:
        translation = _synthetic_translation_result(spec, request_text or "")
    else:
        translation = translator_mod.translate(request_text or "", provider=provider)
    gate = validator_mod.validate_translation(translation)
    return translation, gate


def run(request_text: str | None = None, *, spec: dict | None = None, provider: str = "mock", seed: str,
        id_start: int | None = None, freeze_timestamp: str | None = None,
        question_count_override: int | None = None, difficulty_override: str | None = None) -> dict:
    """Never raises for ordinary bad/unsupported/hostile input -- always
    returns a structured dict. Only genuine infrastructure failure inside a
    provider (e.g. a real network error) is caught inside that provider and
    turned into a NO_MATCH TranslationResult, per providers/base.py.

    `spec`: optional structured DirectorSpec, bypassing the translator
    entirely (Director v0.6 Gateway). Still fully re-validated by
    validator.validate_translation() -- see _synthetic_translation_result().
    Existing callers (v0.2-v0.5, always passing only request_text) are
    unaffected -- spec defaults to None, taking the exact prior code path.

    `question_count_override`/`difficulty_override`: optional Gateway-supplied
    overrides applied AFTER validation, checked against the SAME
    capability-specific bounds (registry.py) the translator-inferred values
    would have faced -- never a way to exceed what any other caller could
    already request. None (the default) preserves exact prior behavior for
    every existing caller."""
    t0 = time.perf_counter()
    translation, gate = translate_and_validate(request_text, spec=spec, provider=provider)
    provider_latency_ms = (time.perf_counter() - t0) * 1000

    # Normalize once: every existing (pre-v0.6) caller always passed a real
    # request_text string, so every downstream use (audit logging, package
    # construction) was written assuming a string. A spec-only Gateway call
    # has none -- translate_and_validate()/_synthetic_translation_result()
    # already computed a sensible fallback label into translation['raw_request_text'];
    # reuse it here rather than letting `None` reach any downstream string op.
    request_text = request_text if request_text is not None else translation["raw_request_text"]

    director_request_id = _director_request_id(request_text, translation.get("translator_id", "unknown"))

    if gate["gate_status"] == "READY" and (question_count_override is not None or difficulty_override is not None):
        capability = gate["capability"]
        validated_spec = dict(gate["validated_spec"])
        if question_count_override is not None:
            if not (capability["min_question_count"] <= question_count_override <= capability["max_question_count"]):
                gate = {
                    "gate_status": "BLOCKED_OUT_OF_BOUNDS",
                    "gate_reason": f"question_count override {question_count_override} outside this capability's "
                                   f"bounds [{capability['min_question_count']}, {capability['max_question_count']}]",
                    "validated_spec": None, "capability": None, "missing_capability": None,
                    "closest_supported_capability": None, "understood": None, "missing_fields": None,
                    "clarifying_question": None,
                }
            else:
                validated_spec["question_count"] = question_count_override
        if gate["gate_status"] == "READY" and difficulty_override is not None:
            if difficulty_override not in capability["supported_difficulties"]:
                gate = {
                    "gate_status": "UNDERSTOOD_BUT_UNSUPPORTED",
                    "gate_reason": f"difficulty override {difficulty_override!r} not supported by this capability "
                                   f"(supported: {sorted(capability['supported_difficulties'])})",
                    "validated_spec": None, "capability": None, "missing_capability": None,
                    "closest_supported_capability": None, "understood": None, "missing_fields": None,
                    "clarifying_question": None,
                }
            else:
                validated_spec["difficulty"] = difficulty_override
        if gate["gate_status"] == "READY":
            gate = dict(gate, validated_spec=validated_spec)

    if gate["gate_status"] != "READY":
        result = {
            "package_id": None,
            "status": gate["gate_status"],
            "reason": gate["gate_reason"],
            "director_request_id": director_request_id,
            "translator": translation,
            "missing_capability": gate.get("missing_capability"),
            "closest_supported_capability": gate.get("closest_supported_capability"),
        }
        if gate["gate_status"] == "NEEDS_CLARIFICATION":
            # Matches the Part D clarification contract shape exactly (see
            # DIRECTOR_V03_CLARIFICATION_CONTRACT.md): status/understood/
            # missing_fields/question. `understood` and `question` are
            # DISPLAY TEXT for a future human-facing clarification UI --
            # never re-parsed as intent by any code path.
            result["understood"] = gate.get("understood") or {}
            result["missing_fields"] = gate.get("missing_fields") or []
            result["question"] = gate.get("clarifying_question")
        audit_log.record(
            request_text=request_text, director_request_id=director_request_id, provider=provider,
            translation_status=translation.get("translation_status"), validated_spec=None,
            capability_key=None, generation_status="NOT_ATTEMPTED", package_id=None,
            provider_latency_ms=provider_latency_ms, engine_generation_latency_ms=None,
            rejection_reason=gate["gate_reason"],
        )
        return result

    validated_spec = gate["validated_spec"]
    capability = gate["capability"]
    resolved_id_start = id_start if id_start is not None else capability.get("pipeline_id_start", ID_START)

    t1 = time.perf_counter()
    package = capability["generate_fn"](
        validated_spec, capability,
        request_text=request_text, director_request_id=director_request_id,
        seed=seed, target_count=validated_spec["question_count"], id_start=resolved_id_start,
        freeze_timestamp=freeze_timestamp,
    )
    engine_generation_latency_ms = (time.perf_counter() - t1) * 1000

    # Attached generically here (not inside any one generate_fn) so every
    # package gets these two fields the same way regardless of mechanic.
    package["director_spec"] = validated_spec
    package["translator"] = translation

    capability_key = (validated_spec["mechanic"], validated_spec["domain"], validated_spec["relationship_predicate"])
    audit_log.record(
        request_text=request_text, director_request_id=director_request_id, provider=provider,
        translation_status=translation.get("translation_status"), validated_spec=validated_spec,
        capability_key=capability_key, generation_status="GENERATED" if package.get("package_id") else "FAILED",
        package_id=package.get("package_id"),
        provider_latency_ms=provider_latency_ms, engine_generation_latency_ms=engine_generation_latency_ms,
        rejection_reason=None,
    )
    return package
