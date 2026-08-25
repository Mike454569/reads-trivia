"""Tests for the Rivalry Data + Gold Standard Content Integration operation:
- CFB Rivalry Trivia (curated 1,272-question bank, 43 real rivalry packs)
- NFL Offense by College, curated (32 current teams, all 11 positions)
- Super Bowl Champion Offense by College (60 real champions, 1966-2025 seasons)
- 8 additional Gold Standard "10. New Game Modes" P0 concepts built on the
  same curated Super Bowl champion data (Odd College Out, Fill the Colleges,
  Spot the Fake Lineup, Who Changed?, Three Clues One Champion, Position
  Trap, Duplicate College Hunt, One School Missing) plus Franchise Marathon/
  Era Gauntlet as real filters on the base capability.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.director_v02 import pipeline, registry  # noqa: E402
from tools.quiz_export import engine  # noqa: E402

NEW_SB_CHAMPION_CAPABILITIES = [
    ("guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE"),
    ("guess", "CFB_ODD_COLLEGE_OUT", "IMPOSTOR_COLLEGE"),
    ("guess", "CFB_FILL_THE_COLLEGES", "COLLEGE_OF_POSITION"),
    ("guess", "CFB_SPOT_THE_FAKE_LINEUP", "ALTERED_POSITION"),
    ("guess", "CFB_WHO_CHANGED", "CHANGED_POSITION"),
    ("guess", "CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES"),
    ("guess", "CFB_POSITION_TRAP", "SWAPPED_POSITION_PAIR"),
    ("guess", "CFB_DUPLICATE_COLLEGE_HUNT", "REPEATED_COLLEGE"),
    ("guess", "CFB_ONE_SCHOOL_MISSING", "MISSING_COLLEGE"),
]


def _generate(mechanic, domain, predicate, *, seed, target_count=None, filters=None):
    cap = registry.CAPABILITY_REGISTRY[(mechanic, domain, predicate)]
    from tools import game_director_v01 as v01
    spec = {
        "competition_id": cap["competition_id"], "mechanic": mechanic, "entity_type": cap["entity_type"],
        "relationship_predicate": predicate, "object_type": cap["object_type"], "answer_type": cap["answer_type"],
        "group_size": cap["group_size"], "filters": filters or {},
    }
    return v01.generate_package_from_spec(
        spec, cap["adapter"], request_text="test", director_request_id="TEST_RGS",
        seed=seed, target_count=target_count or cap["max_question_count"], id_start=1,
        freeze_timestamp=None, package_version="0.2", qa_checks_performed=[],
    )


# --- Import data integrity -------------------------------------------------

def test_rivalry_bank_has_real_row_counts():
    c = engine.connect()
    total = c.execute("SELECT COUNT(*) FROM cfb_trivia_bank").fetchone()[0]
    rivalry = c.execute("SELECT COUNT(*) FROM cfb_trivia_bank WHERE is_rivalry=1").fetchone()[0]
    general = total - rivalry
    packs = c.execute("SELECT COUNT(*) FROM cfb_rivalry_pack_index").fetchone()[0]
    c.close()
    assert total == 1272
    assert rivalry == 860
    assert general == 412
    assert packs == 43


def test_every_rivalry_pack_has_exactly_20_questions():
    c = engine.connect()
    rows = c.execute(
        "SELECT rivalry_pack_number, COUNT(*) as n FROM cfb_trivia_bank WHERE is_rivalry=1 "
        "GROUP BY rivalry_pack_number"
    ).fetchall()
    c.close()
    assert len(rows) == 43
    for r in rows:
        assert r["n"] == 20, f"pack {r['rivalry_pack_number']} has {r['n']} questions, expected 20"


def test_rivalry_school_mapping_iron_bowl():
    c = engine.connect()
    row = c.execute(
        "SELECT school_a_id, school_b_id FROM cfb_rivalry_pack_index WHERE pack_number=1"
    ).fetchone()
    c.close()
    assert row["school_a_id"] == "CFB_SCHOOL_ALABAMA"
    assert row["school_b_id"] == "CFB_SCHOOL_AUBURN"


def test_curated_offense_board_counts():
    c = engine.connect()
    current = c.execute(
        "SELECT COUNT(*) FROM curated_nfl_offense_college_board WHERE board_type='CURRENT_TEAM_2026'"
    ).fetchone()[0]
    sb = c.execute(
        "SELECT COUNT(*) FROM curated_nfl_offense_college_board WHERE board_type='SB_CHAMPION'"
    ).fetchone()[0]
    positions = c.execute("SELECT COUNT(*) FROM curated_nfl_offense_college_position").fetchone()[0]
    c.close()
    assert current == 32
    assert sb == 60
    assert positions == (32 + 60) * 11


def test_sb_champion_seasons_span_1966_to_2025_with_no_gaps():
    # P0 Accuracy + Reliability Hardening pass: this range (and the test's
    # own former name) reflected a real, confirmed off-by-one-year bug in
    # the curated workbook's season labeling -- SB I capped the 1966
    # season (played Jan 1967), not "1967". Cross-verified against
    # nfl_championship_events (an independently Wikipedia-sourced table):
    # paired positionally in chronological order, all 60 rows now match
    # exactly (season AND winner name), 0 mismatches. See the fix in
    # curated_nfl_offense_college_board (season = season - 1 for every
    # SB_CHAMPION row).
    c = engine.connect()
    seasons = sorted(
        r["season"] for r in c.execute(
            "SELECT season FROM curated_nfl_offense_college_board WHERE board_type='SB_CHAMPION'"
        ).fetchall()
    )
    c.close()
    assert seasons == list(range(1966, 2026))


# --- No player names on any offense-by-college board ------------------------

_NAME_LEAK_PATTERN = re.compile(r"\b(Elway|Brady|Manning|Mahomes|Darnold)\b")


def test_current_team_offense_boards_have_no_player_names():
    pkg = _generate("guess", "NFL_OFFENSE_COLLEGE_CURATED", "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE", seed="qa-names-1")
    assert len(pkg["questions"]) > 0
    for q in pkg["questions"]:
        assert not _NAME_LEAK_PATTERN.search(q["question"])
        payload = q.get("visual_payload") or {}
        for p in payload.get("positions", []):
            assert not _NAME_LEAK_PATTERN.search(p["college"])


def test_sb_champion_offense_boards_have_no_player_names():
    pkg = _generate("guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE", seed="qa-names-2")
    assert len(pkg["questions"]) > 0
    for q in pkg["questions"]:
        assert not _NAME_LEAK_PATTERN.search(q["question"])


# --- No zero-question packages, correct answer preserved --------------------

def test_no_new_capability_produces_a_zero_question_package():
    caps = [
        ("guess", "CFB_RIVALRY_TRIVIA", "CORRECT_TRIVIA_ANSWER"),
        ("guess", "NFL_OFFENSE_COLLEGE_CURATED", "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE"),
        *NEW_SB_CHAMPION_CAPABILITIES,
    ]
    for mech, dom, pred in caps:
        pkg = _generate(mech, dom, pred, seed=f"qa-nonzero-{dom}")
        assert len(pkg["questions"]) > 0, f"{dom}/{pred} produced a zero-question package"


def test_correct_answer_index_always_points_at_the_real_answer():
    for mech, dom, pred in [
        ("guess", "CFB_RIVALRY_TRIVIA", "CORRECT_TRIVIA_ANSWER"),
        *NEW_SB_CHAMPION_CAPABILITIES,
    ]:
        pkg = _generate(mech, dom, pred, seed=f"qa-answer-{dom}")
        for q in pkg["questions"]:
            assert q["options"][q["correctIndex"]] == q["answer"]


def test_rivalry_pack_filter_scopes_to_exactly_that_pack():
    pkg = _generate(
        "guess", "CFB_RIVALRY_TRIVIA", "CORRECT_TRIVIA_ANSWER", seed="qa-filter-1",
        target_count=25, filters={"rivalry_pack_number": 1},
    )
    assert 1 <= len(pkg["questions"]) <= 20
    assert pkg["funnel"]["considered"] == 20


def test_duplicate_college_hunt_only_uses_boards_with_a_real_duplicate():
    pkg = _generate("guess", "CFB_DUPLICATE_COLLEGE_HUNT", "REPEATED_COLLEGE", seed="qa-dup-1")
    assert pkg["funnel"]["considered"] == 60
    assert pkg["funnel"]["accepted_total"] == 27


def test_franchise_marathon_filter_scopes_to_one_franchise_chronologically():
    pkg = _generate(
        "guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
        seed="qa-marathon-1", target_count=10, filters={"franchise_name": "Pittsburgh Steelers"},
    )
    seasons = [int(q["answer"].split()[0]) for q in pkg["questions"]]
    assert all("Pittsburgh Steelers" in q["answer"] for q in pkg["questions"])
    assert seasons == sorted(seasons)


def test_era_gauntlet_filter_returns_one_board_per_era():
    pkg = _generate(
        "guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
        seed="qa-era-1", target_count=10, filters={"era_gauntlet": True},
    )
    assert len(pkg["questions"]) == 7


# --- Creator natural-language routing ---------------------------------------

_RETEST_PROMPTS = [
    "Make me an Iron Bowl trivia game",
    "Give me rivalry trivia about Michigan and Ohio State",
    "Make me a College Offense game",
    "Give me a Super Bowl offense by colleges",
    "Make me play Odd College Out",
    "Give me Three Clues One Champion",
    "give me a game where you guess the NFL offense without names just college and position",
    "Give me a Super Bowl winning offense by colleges and make me guess the team and season",
    "Give me a game about college football rivalries",
    "Make me trivia about Alabama vs Auburn",
    "Give me a Red River Rivalry game",
    "Make me play Fill the Colleges",
    "Give me a Spot the Fake Lineup game",
    "Make me a Who Changed game",
    "Give me a Position Trap game",
    "Make me a Duplicate Hunt game",
    "Give me One School Missing",
    "Give me an Era Gauntlet game",
]


def test_creator_retest_prompts_all_generate_nonzero_passed_packages():
    for i, prompt in enumerate(_RETEST_PROMPTS):
        result = pipeline.run(prompt, provider="mock", seed=f"creator-retest-{i}")
        questions = result.get("questions")
        assert questions, f"{prompt!r} produced no questions: {result}"
        assert result.get("qa_status") == "PASSED", f"{prompt!r} failed QA: {result.get('_diagnostics')}"


def test_specific_historical_season_still_routes_to_bridge_based_capability():
    from tools.director_v02.providers.mock import MockDeterministicTranslator
    t = MockDeterministicTranslator()
    tr = t.translate("give me a game where you guess the 2012 NFL offense without names just college and position")
    assert tr["translation_status"] == "TRANSLATED"
    assert tr["spec"]["domain"] == "NFL_OFFENSE_LINEUP_COLLEGE"


def test_plain_single_school_rival_lookup_still_routes_to_old_capability():
    from tools.director_v02.providers.mock import MockDeterministicTranslator
    t = MockDeterministicTranslator()
    tr = t.translate("who is Alabama's rival")
    assert tr["translation_status"] == "TRANSLATED"
    assert tr["spec"]["domain"] == "CFB_RIVALRY"
    assert tr["spec"]["relationship_predicate"] == "RIVAL_OF"
