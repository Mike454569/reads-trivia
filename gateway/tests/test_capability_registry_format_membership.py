"""40-Format Expansion pass -- closes the two-track format-compatibility gap
documented in tools/director_v02/visual_templates.py's own module docstring
and tools/director_v02/format_resolution.py's: every CAPABILITY_REGISTRY
("guess"/"identify_player_from_clues") entry hardcodes its own
`visual_template` string, but never imported visual_templates.py to prove
that string is even a real, registered, mechanic-compatible format. This
test makes that a hard CI failure going forward -- without touching any of
the 60+ entries' own working code.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

_SCHEMA_MECHANIC_TO_FORMAT_MECHANIC = {"guess": "guess", "identify_player_from_clues": "clue"}

# Real finding from building this test: "identify_player_from_clues"
# capabilities never set a "visual_template" key at all (confirmed live --
# neither _generate_player_from_clues_package nor
# _generate_cfb_player_from_clues_package ever reads/writes that field; the
# frontend's Player From Clues screen is its own dedicated UI, not driven by
# a per-question visual_template). "DEFAULT_MULTIPLE_CHOICE" is only the
# right fallback for the "guess" mechanic; CARD_STACK is the real,
# already-registered format for this one.
_DEFAULT_VISUAL_TEMPLATE_BY_MECHANIC = {
    "guess": "DEFAULT_MULTIPLE_CHOICE",
    "identify_player_from_clues": "CARD_STACK",
}


def test_every_capability_registry_visual_template_is_real_and_mechanic_compatible():
    from tools.director_v02 import registry, visual_templates as vt

    checked = 0
    for (mechanic, domain, predicate), capability in registry.CAPABILITY_REGISTRY.items():
        visual_template = capability.get("visual_template", _DEFAULT_VISUAL_TEMPLATE_BY_MECHANIC.get(mechanic, "DEFAULT_MULTIPLE_CHOICE"))
        entry = vt.lookup(visual_template)
        assert entry is not None, (
            f"({mechanic}, {domain}, {predicate})'s visual_template={visual_template!r} "
            f"is not a real key in VISUAL_TEMPLATE_REGISTRY"
        )
        format_mechanic = _SCHEMA_MECHANIC_TO_FORMAT_MECHANIC.get(mechanic)
        assert format_mechanic is not None, f"unrecognized DirectorSpec mechanic {mechanic!r} on {domain}/{predicate}"
        assert format_mechanic in entry["supported_mechanics"], (
            f"({mechanic}, {domain}, {predicate})'s visual_template={visual_template!r} does not declare "
            f"{format_mechanic!r} in its own supported_mechanics"
        )
        checked += 1
    assert checked == len(registry.CAPABILITY_REGISTRY)


def test_resolve_format_for_capability_is_a_true_noop_when_unspecified():
    """Real backward-compatibility guarantee: an absent `format` must return
    exactly the capability's own existing default, never a different,
    auto-selected one -- this is what protects lineup.py/lineup_college.py's
    real POSITION_LINEUP*/rendering from being silently overridden."""
    from tools.director_v02 import format_resolution as fr
    from tools.director_v02 import registry

    draft_cap = registry.lookup("guess", "NFL_DRAFT", "DRAFTED_BY")
    lineup_cap = registry.lookup("guess", "NFL_OFFENSE_LINEUP", "TEAM_OF_STARTING_LINEUP")
    assert fr.resolve_format_for_capability(draft_cap, "guess", None) == "DEFAULT_MULTIPLE_CHOICE"
    assert fr.resolve_format_for_capability(lineup_cap, "guess", None) == "POSITION_LINEUP"


def test_resolve_format_for_capability_accepts_a_compatible_payload_free_format():
    from tools.director_v02 import format_resolution as fr
    from tools.director_v02 import registry

    draft_cap = registry.lookup("guess", "NFL_DRAFT", "DRAFTED_BY")
    assert fr.resolve_format_for_capability(draft_cap, "guess", "HEAD_TO_HEAD") == "HEAD_TO_HEAD"


def test_resolve_format_for_capability_rejects_a_payload_requiring_format_on_the_wrong_capability():
    """Real, disclosed shape safety: POSITION_LINEUP requires a `positions`
    payload the Draft adapter never produces -- must be rejected, not
    silently substituted or half-rendered."""
    from tools.director_v02 import format_resolution as fr
    from tools.director_v02 import registry

    draft_cap = registry.lookup("guess", "NFL_DRAFT", "DRAFTED_BY")
    try:
        fr.resolve_format_for_capability(draft_cap, "guess", "POSITION_LINEUP")
        assert False, "expected FormatIncompatibleError"
    except fr.FormatIncompatibleError as e:
        assert "positions" in str(e) or "season" in str(e)


def test_resolve_format_for_capability_rejects_a_mechanic_incompatible_format():
    from tools.director_v02 import format_resolution as fr
    from tools.director_v02 import registry

    draft_cap = registry.lookup("guess", "NFL_DRAFT", "DRAFTED_BY")
    try:
        fr.resolve_format_for_capability(draft_cap, "guess", "MATCH_LIST_DEFAULT")
        assert False, "expected FormatIncompatibleError"
    except fr.FormatIncompatibleError as e:
        assert "MATCH_LIST_DEFAULT" in str(e)
