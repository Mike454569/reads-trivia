"""40-Format Expansion pass -- real tests for the new optional `format` spec
key (tools/director_v02/schema.py's OPTIONAL_SPEC_KEYS/ALLOWED_FORMATS,
validator.py's compatibility check + new FORMAT_INCOMPATIBLE gate status,
format_resolution.py's resolve_format_for_capability()). See
gateway/tests/test_capability_registry_format_membership.py for the
underlying resolver's own dedicated tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _draft_spec(**overrides):
    spec = {
        "mechanic": "guess", "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY",
        "question_count": 5, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    spec.update(overrides)
    return spec


def test_format_omitted_is_unchanged_backward_compatible_behavior():
    from tools.director_v02 import validator

    gate = validator.validate_translation({"translation_status": "TRANSLATED", "spec": _draft_spec()})
    assert gate["gate_status"] == "READY"
    assert gate["validated_spec"]["format"] == "DEFAULT_MULTIPLE_CHOICE"


def test_explicit_compatible_format_is_honored():
    from tools.director_v02 import validator

    gate = validator.validate_translation({
        "translation_status": "TRANSLATED", "spec": _draft_spec(format="HEAD_TO_HEAD"),
    })
    assert gate["gate_status"] == "READY"
    assert gate["validated_spec"]["format"] == "HEAD_TO_HEAD"


def test_unknown_format_value_is_rejected_at_schema_level():
    from tools.director_v02 import validator

    gate = validator.validate_translation({
        "translation_status": "TRANSLATED", "spec": _draft_spec(format="NOT_A_REAL_FORMAT"),
    })
    assert gate["gate_status"] == "BLOCKED_INVALID_SPEC"


def test_payload_incompatible_format_is_rejected_format_incompatible():
    """POSITION_LINEUP needs adapter-specific position/season data the Draft
    adapter never produces -- real, disclosed shape safety, not just a
    mechanic-family check."""
    from tools.director_v02 import validator

    gate = validator.validate_translation({
        "translation_status": "TRANSLATED", "spec": _draft_spec(format="POSITION_LINEUP"),
    })
    assert gate["gate_status"] == "FORMAT_INCOMPATIBLE"
    assert gate["suggested_formats"] == ["DEFAULT_MULTIPLE_CHOICE"]


def test_mechanic_incompatible_format_is_rejected_format_incompatible():
    from tools.director_v02 import validator

    gate = validator.validate_translation({
        "translation_status": "TRANSLATED", "spec": _draft_spec(format="MATCH_LIST_DEFAULT"),
    })
    assert gate["gate_status"] == "FORMAT_INCOMPATIBLE"
    # MATCH_LIST_DEFAULT itself must never appear as a suggestion for the
    # 'guess' mechanic -- it's a "matching"-only format.
    assert "MATCH_LIST_DEFAULT" not in gate["suggested_formats"]
    assert "DEFAULT_MULTIPLE_CHOICE" in gate["suggested_formats"]


def test_lineup_capability_own_default_still_wins_when_format_unspecified():
    """Real backward-compatibility guarantee central to this pass: adding
    the `format` key must never change a single existing capability's
    current rendering when the caller doesn't ask for anything."""
    from tools.director_v02 import validator

    spec = {
        "mechanic": "guess", "domain": "NFL_OFFENSE_LINEUP", "relationship_predicate": "TEAM_OF_STARTING_LINEUP",
        "question_count": 5, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    gate = validator.validate_translation({"translation_status": "TRANSLATED", "spec": spec})
    assert gate["gate_status"] == "READY"
    assert gate["validated_spec"]["format"] == "POSITION_LINEUP"


def test_lineup_capability_requesting_its_own_existing_format_is_a_harmless_confirmation():
    from tools.director_v02 import validator

    spec = {
        "mechanic": "guess", "domain": "NFL_OFFENSE_LINEUP", "relationship_predicate": "TEAM_OF_STARTING_LINEUP",
        "question_count": 5, "difficulty": "any", "filters": {}, "exclusions": [], "format": "POSITION_LINEUP",
    }
    gate = validator.validate_translation({"translation_status": "TRANSLATED", "spec": spec})
    assert gate["gate_status"] == "READY"
    assert gate["validated_spec"]["format"] == "POSITION_LINEUP"


def test_format_key_alone_does_not_satisfy_the_required_key_set():
    """Regression guard: `format` is optional, never required -- omitting
    every required key must still fail exactly as it always has."""
    from tools.director_v02 import validator

    gate = validator.validate_translation({
        "translation_status": "TRANSLATED", "spec": {"format": "DEFAULT_MULTIPLE_CHOICE"},
    })
    assert gate["gate_status"] == "BLOCKED_INVALID_SPEC"


def test_allowed_formats_is_derived_from_the_real_format_registry():
    from tools.director_v02 import schema, visual_templates as vt

    assert schema.ALLOWED_FORMATS == frozenset(vt.all_template_ids())
