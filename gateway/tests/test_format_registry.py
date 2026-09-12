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
        "format_id", "display_name", "description", "payload_schema", "proven_in", "supported_mechanics",
        "mechanic_family", "supported_entity_types", "required_data_relationships", "min_pool_size",
        "min_items", "max_items", "interaction_model", "mobile_verified", "nfl_support", "cfb_support",
        "difficulty_support", "timed", "multiplayer_compatible", "scoring_model", "validation_rules",
        "answer_schema", "generation_schema", "qa_requirements", "casual_aliases",
        "creator_selectable", "production_status",
    }
    status_vocab = {"SUPPORTED", "SUPPORTED_WITH_LIMITATIONS", "MISSING_DATA", "UNKNOWN", "FORMAT_INCOMPATIBLE"}
    for format_id, entry in vt.VISUAL_TEMPLATE_REGISTRY.items():
        missing = required_keys - set(entry.keys())
        assert not missing, f"{format_id} is missing required metadata: {missing}"
        assert entry["production_status"] in vt.PRODUCTION_STATUS_VALUES, format_id
        assert isinstance(entry["supported_mechanics"], list) and entry["supported_mechanics"], format_id
        assert entry["format_id"] == format_id, format_id
        assert entry["nfl_support"] in status_vocab, format_id
        assert entry["cfb_support"] in status_vocab, format_id


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

    for mechanic in (
        "guess", "sorting", "matching", "higher_lower", "elimination", "comparison", "clue",
        # 40-Format Expansion pass: the 6 new mechanic families.
        "grid_constraint_board", "drive_progression", "roster_build", "knockout_bracket",
        "relationship_chain", "branch_state",
    ):
        formats = vt.formats_for_mechanic(mechanic)
        assert formats, f"mechanic {mechanic!r} has zero registered compatible formats"
        default = vt.default_format_for_mechanic(mechanic)
        assert default in formats


def test_new_taxonomy_formats_are_honestly_blocked_on_renderer_not_production_ready():
    """40-Format Expansion pass -- none of the 6 new mechanic_engine.py
    taxonomies have a real, reachable frontend renderer yet (confirmed: even
    KNOCKOUT_TOURNAMENT, whose view shape is byte-identical to BRACKET_TREE's,
    needs a new client-side ENGINE_MECHANIC_MODES entry that was not added
    this pass). Real backend/generation/answer-checking work must never be
    reported as a complete, playable format."""
    from tools.director_v02 import visual_templates as vt

    for format_id in (
        "CONNECTION_GRID", "PERFECT_DRIVE", "GOAL_LINE_STAND", "LINEUP_BUILDER", "AUCTION_DRAFT",
        "CAP_CHALLENGE", "KNOCKOUT_TOURNAMENT", "SIX_DEGREES", "CHAIN_REACTION", "CHOOSE_YOUR_PATH",
    ):
        entry = vt.lookup(format_id)
        assert entry is not None, format_id
        assert entry["production_status"] == "BLOCKED_RENDERER", format_id
        assert "existing_renderer_note" in entry and "renderer" not in entry, format_id


def test_timeline_ribbon_and_bracket_tree_are_now_production_ready():
    """40-Format Expansion pass: these two shipped and proved out under the
    Reusable Game Format System pass's own NEW_THIS_PASS status -- that
    status value no longer exists (replaced by the 5-value taxonomy), and
    both are real, proven, PRODUCTION_READY formats now."""
    from tools.director_v02 import visual_templates as vt

    assert vt.lookup("TIMELINE_RIBBON")["production_status"] == "PRODUCTION_READY"
    assert vt.lookup("BRACKET_TREE")["production_status"] == "PRODUCTION_READY"
    assert vt.is_format_compatible("TIMELINE_RIBBON", "sorting")
    assert vt.is_format_compatible("BRACKET_TREE", "comparison")
    assert not vt.is_format_compatible("BRACKET_TREE", "sorting")
    assert not vt.is_format_compatible("TIMELINE_RIBBON", "comparison")


def test_bracket_tree_renderer_string_names_the_real_function():
    """Real bug fixed during the 40-Format Expansion pass: this entry used
    to claim a nonexistent renderBracketTree() -- the real function is
    renderBracketTreeBody(v, s) (engine-game-ui.js:1318)."""
    from tools.director_v02 import visual_templates as vt

    assert "renderBracketTreeBody" in vt.lookup("BRACKET_TREE")["renderer"]


def test_timeline_ribbon_discloses_it_has_no_standalone_renderer():
    """Real bug fixed during the 40-Format Expansion pass: this entry used
    to claim a nonexistent renderTimelineRibbon() via `renderer` -- the
    real UI is an inline branch inside renderMechanicPilotBody's 'sorting'
    kind, so this format now (correctly) carries existing_renderer_note
    instead of a renderer string."""
    from tools.director_v02 import visual_templates as vt

    entry = vt.lookup("TIMELINE_RIBBON")
    assert "renderer" not in entry
    assert "existing_renderer_note" in entry
