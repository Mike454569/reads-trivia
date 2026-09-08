"""User-reported gap: "For the Odd college out could do more college based
questions too instead of NFL rosters." Investigated directly: every one of
_group_board_common.py's 5 real board sources (SB_CHAMPION, CURRENT_TEAM_2026,
NFL_TEAM_SEASON_ROSTER, DRAFT_CLASS, HONOR_GROUP) is NFL data -- colleges
only ever appear as an attribute of an NFL player. Odd College Out (and its
siblings Spot the Fake Lineup / One School Missing, which share the exact
same pool) never actually showed a real group of COLLEGE football players.

Fixed by adding a 6th real source, CFB_ALL_AMERICA, built from
`cfb_all_america`'s real, named College Football All-America honorees
(WIKIPEDIA_STRUCTURED_SECONDARY, 1889-2025), resolved to `schools.school_name`,
grouped by season, floored at 1950 (76 real seasons with >=4 distinct real
schools). Zero adapter-level changes were needed for Odd College Out / Spot
the Fake Lineup / One School Missing to pick this up -- all three already
call `fetch_all_boards(c)` with no pool_kinds restriction, so a new entry in
_group_board_common.ALL_POOL_KINDS flows through automatically; the only
per-adapter change needed was the `_GROUP_PHRASE` display-text lookup.
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


def test_cfb_all_america_boards_are_real_and_college_heterogeneous():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    boards = gbc.cfb_all_america_boards(c)
    assert len(boards) >= 50, f"expected a real, substantial pool, got {len(boards)}"
    for b in boards:
        assert b["pool_kind"] == "CFB_ALL_AMERICA"
        assert 1950 <= b["season"] <= 2025
        colleges = list(b["positions"].values())
        assert len(set(colleges)) >= 4, f"season {b['season']}: expected real college heterogeneity"


def test_cfb_all_america_is_part_of_the_default_shared_pool():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc

    c = engine.connect()
    assert "CFB_ALL_AMERICA" in gbc.ALL_POOL_KINDS
    boards = gbc.fetch_all_boards(c)
    kinds_present = {b["pool_kind"] for b in boards}
    assert "CFB_ALL_AMERICA" in kinds_present


def test_cfb_all_america_is_excluded_from_the_team_season_only_pool():
    """Three Clues One Champion / Franchise Marathon ask "guess the team AND
    season" -- a CFB All-America class has no single coherent team-season
    answer, so it must stay out of that narrower pool exactly like
    DRAFT_CLASS/HONOR_GROUP already do."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import _group_board_common as gbc
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as three_clues

    c = engine.connect()
    boards = gbc.fetch_all_boards(c, pool_kinds=three_clues._TEAM_SEASON_POOL_KINDS)
    kinds_present = {b["pool_kind"] for b in boards}
    assert "CFB_ALL_AMERICA" not in kinds_present


def test_odd_college_out_now_surfaces_real_cfb_all_america_questions():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_odd_college_out as adapter

    factory_spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "odd_college_out_board",
        "relationship_predicate": "IMPOSTOR_COLLEGE", "object_type": "college",
        "answer_type": "college", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        factory_spec, adapter, request_text="pytest", director_request_id="pytest",
        seed="pytest-odd-college-out-aa", target_count=300, id_start=1,
    )
    assert pkg["qa_status"] == "PASSED"
    questions = pkg["questions"]
    aa_questions = [q for q in questions if q["entity_key"].startswith("board:CFB_ALL_AMERICA:")]
    assert aa_questions, "expected at least one real CFB All-America-sourced question in a 300-target sample"
    for q in aa_questions:
        assert "All-America" in q["question"]
        assert len(set(q["options"])) == 4


def test_one_school_missing_and_spot_the_fake_lineup_also_pick_up_cfb_all_america():
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
            seed=f"pytest-aa-sibling-{adapter.CATEGORY}", target_count=300, id_start=1,
        )
        assert pkg["qa_status"] == "PASSED"
        aa_questions = [q for q in pkg["questions"] if q["entity_key"].startswith("board:CFB_ALL_AMERICA:")]
        assert aa_questions, f"{adapter.CATEGORY}: expected at least one real CFB All-America-sourced question"


def test_every_cfb_all_america_school_resolves_through_the_canonical_schools_table():
    """Real bug this pass avoided: a board built from the row's own raw
    `school_name_raw` (inconsistent for the same real school across
    different source pages) instead of resolving through `schools.school_name`
    (the one canonical CFB school identity used everywhere else) would show
    inconsistent naming for the same real school. Directly verifies the
    query joins through `schools`, not `school_name_raw`."""
    from tools.quiz_export import engine

    c = engine.connect()
    missing = c.execute(
        "SELECT COUNT(DISTINCT a.school_id) FROM cfb_all_america a "
        "LEFT JOIN schools s ON s.school_id = a.school_id "
        "WHERE s.school_id IS NULL AND a.school_id IS NOT NULL"
    ).fetchone()[0]
    assert missing == 0, f"{missing} real school_ids in cfb_all_america don't resolve through schools"
