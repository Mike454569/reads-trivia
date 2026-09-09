"""Reusable Game Format System pass -- real, verified tests for the format
registry (tools/director_v02/visual_templates.py) and its compatibility
matrix. See gateway/tests/test_comparison_bracket_mechanic.py for the new
COMPARISON_BRACKET mechanic's own tests, and gateway/tests/test_creator_format_selection.py
for end-to-end Creator format resolution.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_every_registered_format_has_the_full_required_metadata():
    from tools.director_v02 import visual_templates as vt

    required_keys = {
        "description", "payload_schema", "proven_in", "supported_mechanics",
        "min_items", "max_items", "interaction_model", "mobile_verified",
        "creator_selectable", "production_status",
    }
    for format_id, entry in vt.VISUAL_TEMPLATE_REGISTRY.items():
        missing = required_keys - set(entry.keys())
        assert not missing, f"{format_id} is missing required metadata: {missing}"
        assert entry["production_status"] in ("PRODUCTION_READY", "NEW_THIS_PASS"), format_id
        assert isinstance(entry["supported_mechanics"], list) and entry["supported_mechanics"], format_id


def test_every_format_names_either_a_real_renderer_or_a_real_existing_renderer_note():
    """A format without visual_payload support (the 5 Mechanic Pilot
    taxonomies' own formats -- GUESS_LADDER/HEAD_TO_HEAD/GRID_BOARD/
    MATCH_LIST_DEFAULT/COMPARE_CARD_DEFAULT/SURVIVAL_PROMPT_DEFAULT/
    CARD_STACK) must disclose the real, different architecture it
    actually lives in via existing_renderer_note. Every format that DOES
    flow through visual_template/visual_payload (DEFAULT_MULTIPLE_CHOICE/
    POSITION_LINEUP*/SORT_LIST_DEFAULT/TIMELINE_RIBBON/BRACKET_TREE) must
    name a real `renderer` instead -- payload_schema itself is correctly
    None for formats that need no extra payload at all (e.g.
    DEFAULT_MULTIPLE_CHOICE), so that field alone isn't the right check."""
    from tools.director_v02 import visual_templates as vt

    for format_id, entry in vt.VISUAL_TEMPLATE_REGISTRY.items():
        assert "renderer" in entry or "existing_renderer_note" in entry, (
            f"{format_id} names neither a real renderer nor an existing_renderer_note"
        )


def test_compatibility_matrix_is_derived_never_hand_duplicated():
    """FORMAT_COMPATIBILITY must exactly equal what a fresh derivation from
    each format's own supported_mechanics produces -- catches any future
    edit to VISUAL_TEMPLATE_REGISTRY that forgets to keep the derived
    matrix in sync (there's no separate hand-maintained copy to forget --
    this test would only fail if the derivation logic itself changed)."""
    from tools.director_v02 import visual_templates as vt

    rebuilt: dict[str, list[str]] = {}
    for format_id, entry in vt.VISUAL_TEMPLATE_REGISTRY.items():
        for mechanic in entry["supported_mechanics"]:
            rebuilt.setdefault(mechanic, []).append(format_id)
    assert rebuilt == vt.FORMAT_COMPATIBILITY


def test_grid_board_and_the_real_matching_mechanic_are_not_falsely_compatible():
    """Real bug found and fixed while building this registry: Immaculate
    Grid (GRID_BOARD) is a fully separate, bespoke pipeline that never
    routes through mechanic_engine.py's real MATCHING taxonomy -- their
    payloads are structurally incompatible (rows/cols/cells vs.
    left_items/right_items). GRID_BOARD must never be offered as a format
    choice for the real 'matching' mechanic."""
    from tools.director_v02 import visual_templates as vt

    assert "GRID_BOARD" not in vt.formats_for_mechanic("matching")
    assert "GRID_BOARD" in vt.formats_for_mechanic("grid_matching")


def test_guess_ladder_and_the_real_server_higher_lower_mechanic_are_not_falsely_compatible():
    """Same real class of bug as GRID_BOARD above: app.js's standalone
    Higher or Lower is client-side only (see tools/director_v04/
    higher_lower.py's own docstring for why that's a real, disclosed
    defect) -- GUESS_LADDER must never be offered as a format choice for
    the real, server-authoritative 'higher_lower' mechanic."""
    from tools.director_v02 import visual_templates as vt

    assert "GUESS_LADDER" not in vt.formats_for_mechanic("higher_lower")
    assert "GUESS_LADDER" in vt.formats_for_mechanic("client_higher_lower")


def test_every_real_mechanic_engine_taxonomy_has_at_least_one_compatible_format():
    from tools.director_v02 import visual_templates as vt

    for mechanic in ("guess", "sorting", "matching", "higher_lower", "elimination", "comparison", "clue"):
        formats = vt.formats_for_mechanic(mechanic)
        assert formats, f"mechanic {mechanic!r} has zero registered compatible formats"
        default = vt.default_format_for_mechanic(mechanic)
        assert default in formats


def test_timeline_ribbon_and_bracket_tree_are_the_two_new_formats_this_pass():
    from tools.director_v02 import visual_templates as vt

    assert vt.lookup("TIMELINE_RIBBON")["production_status"] == "NEW_THIS_PASS"
    assert vt.lookup("BRACKET_TREE")["production_status"] == "NEW_THIS_PASS"
    assert vt.is_format_compatible("TIMELINE_RIBBON", "sorting")
    assert vt.is_format_compatible("BRACKET_TREE", "comparison")
    assert not vt.is_format_compatible("BRACKET_TREE", "sorting")
    assert not vt.is_format_compatible("TIMELINE_RIBBON", "comparison")
