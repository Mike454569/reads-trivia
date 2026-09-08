"""User-reported gap (verbatim): "For One School Missing, and Odd College
out could we please for the love of gosh quit only using rosters that is
lame and will get the users tired of my games." Investigated directly:
even after adding CFB_ALL_AMERICA as a 6th real source, every source in
_group_board_common.py's pool (including it) is still fundamentally "a
roster of real people, each with a college" -- the underlying game always
felt the same regardless of which roster fed it.

Fixed by adding a 7th real source, CFB_CONFERENCE_SEASON, built from real
FBS conference realignment membership (`cfb_standings`, 2002-2025) -- a
group of real SCHOOLS directly (e.g. "these are 2024 SEC members"), not
an attribute of some other roster entity. Zero adapter-level changes were
needed for Odd College Out / Spot the Fake Lineup / One School Missing to
pick this up -- all three already call `fetch_all_boards(c)` with no
pool_kinds restriction, so a new entry in _group_board_common.ALL_POOL_KINDS
flows through automatically; the only per-adapter change needed was the
`_GROUP_PHRASE` display-text lookup and a matching safety_check entry.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_cfb_conference_season_boards_are_real_and_school_heterogeneous():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    boards = gbc.cfb_conference_season_boards(c)
    assert len(boards) >= 100, f"expected a real, substantial pool, got {len(boards)}"
    for b in boards:
        assert b["pool_kind"] == "CFB_CONFERENCE_SEASON"
        assert 2002 <= b["season"] <= 2025
        schools = list(b["positions"].values())
        assert len(set(schools)) == len(schools), f"duplicate real school in one conference-season board: {b}"
        assert len(schools) >= 4


def test_fbs_independents_is_never_treated_as_a_real_conference():
    """FBS Independents is a real classification for "has no conference" --
    grouping by it would be a fabricated shared trait, not a genuine one."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    boards = gbc.cfb_conference_season_boards(c)
    assert not any("Independents" in b["team_display_name"] for b in boards)


def test_cfb_conference_season_is_part_of_the_default_shared_pool():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    assert "CFB_CONFERENCE_SEASON" in gbc.ALL_POOL_KINDS
    boards = gbc.fetch_all_boards(c)
    kinds_present = {b["pool_kind"] for b in boards}
    assert "CFB_CONFERENCE_SEASON" in kinds_present


def test_cfb_conference_season_is_excluded_from_the_team_season_only_pool():
    """A real conference-season group has no single coherent team-season
    answer -- must stay out of Three Clues / Franchise Marathon's narrower
    pool exactly like CFB_ALL_AMERICA/DRAFT_CLASS/HONOR_GROUP already do."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as three_clues

    c = engine.connect()
    boards = gbc.fetch_all_boards(c, pool_kinds=three_clues._TEAM_SEASON_POOL_KINDS)
    kinds_present = {b["pool_kind"] for b in boards}
    assert "CFB_CONFERENCE_SEASON" not in kinds_present


def test_odd_college_out_now_surfaces_real_conference_membership_questions():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_odd_college_out as adapter

    factory_spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "odd_college_out_board",
        "relationship_predicate": "IMPOSTOR_COLLEGE", "object_type": "college",
        "answer_type": "college", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        factory_spec, adapter, request_text="pytest", director_request_id="pytest",
        seed="pytest-conference-season", target_count=300, id_start=1,
    )
    assert pkg["qa_status"] == "PASSED"
    conf_questions = [q for q in pkg["questions"] if q["entity_key"].startswith("board:CFB_CONFERENCE_SEASON:")]
    assert conf_questions, "expected at least one real conference-membership question in a 300-target sample"
    for q in conf_questions:
        assert len(set(q["options"])) == 4


def test_one_school_missing_and_spot_the_fake_lineup_also_pick_up_conference_season():
    """The exact same fix must flow to Odd College Out's two siblings, which
    share the identical unrestricted fetch_all_boards(c) call."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_one_school_missing, cfb_spot_the_fake_lineup

    for adapter, predicate, object_type in (
        (cfb_one_school_missing, "MISSING_COLLEGE", "college"),
        (cfb_spot_the_fake_lineup, "ALTERED_POSITION", "position"),
    ):
        factory_spec = {
            "competition_id": "CFB", "mechanic": "guess", "entity_type": "odd_college_out_board",
            "relationship_predicate": predicate, "object_type": object_type,
            "answer_type": object_type, "group_size": 4, "filters": {},
        }
        pkg = v01.generate_package_from_spec(
            factory_spec, adapter, request_text="pytest", director_request_id="pytest",
            seed=f"pytest-conference-sibling-{adapter.CATEGORY}", target_count=300, id_start=1,
        )
        assert pkg["qa_status"] == "PASSED"
        conf_questions = [q for q in pkg["questions"] if q["entity_key"].startswith("board:CFB_CONFERENCE_SEASON:")]
        assert conf_questions, f"{adapter.CATEGORY}: expected at least one real conference-membership question"


def test_missing_cfb_standings_table_degrades_gracefully_instead_of_crashing():
    """Same real production-safety discipline as CFB_ALL_AMERICA's own
    missing-table regression test: simulates the table being absent on a
    real connection (restored in a finally, never touching the on-disk
    file) and asserts generation still completes."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc
    from tools.quiz_export.adapters import cfb_odd_college_out
    from tools import game_director_v01 as v01

    c = engine.connect()
    c.execute("ALTER TABLE cfb_standings RENAME TO cfb_standings_hidden_for_test")
    c.commit()
    try:
        assert gbc.cfb_conference_season_table_exists(c) is False
        assert gbc.cfb_conference_season_boards(c) == []

        safety_result = cfb_odd_college_out.safety_check(c)
        assert safety_result["cfb_conference_season"] == {"status": "TABLE_NOT_YET_AVAILABLE_IN_THIS_ENGINE_DEPLOYMENT"}

        factory_spec = {
            "competition_id": "CFB", "mechanic": "guess", "entity_type": "odd_college_out_board",
            "relationship_predicate": "IMPOSTOR_COLLEGE", "object_type": "college",
            "answer_type": "college", "group_size": 4, "filters": {},
        }
        pkg = v01.generate_package_from_spec(
            factory_spec, cfb_odd_college_out, request_text="pytest", director_request_id="pytest",
            seed="pytest-missing-standings", target_count=50, id_start=1,
        )
        assert pkg["qa_status"] == "PASSED"
        assert len(pkg["questions"]) > 0
    finally:
        c.execute("ALTER TABLE cfb_standings_hidden_for_test RENAME TO cfb_standings")
        c.commit()
        c.close()
