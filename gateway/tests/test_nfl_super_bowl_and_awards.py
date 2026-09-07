"""Tests for the two capabilities built on the NFL Wikipedia history import
(tools/data_refresh/nfl_wikipedia_history_import.py) -- NFL_SUPER_BOWL/
WON_CHAMPIONSHIP and NFL_AWARDS/WON_AWARD. Real DB, real pipeline, no
mocking of generation/QA -- same convention as test_lineup_college.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.director_v02 import pipeline, translator as translator_mod  # noqa: E402
from tools.quiz_export import engine  # noqa: E402


def test_super_bowl_phrasing_resolves_to_won_championship_not_old_postseason_capability():
    result = translator_mod.translate(
        "Make a game where I guess which team won the Super Bowl.", provider="mock",
    )
    assert result["translation_status"] == "TRANSLATED"
    assert result["spec"]["domain"] == "NFL_SUPER_BOWL"
    assert result["spec"]["relationship_predicate"] == "WON_CHAMPIONSHIP"


def test_old_team_postseason_phrasing_still_resolves_unchanged():
    result = translator_mod.translate(
        "Guess how a team finished in the playoffs.", provider="mock",
    )
    assert result["translation_status"] == "TRANSLATED"
    assert result["spec"]["domain"] == "NFL_CHAMPIONSHIP"
    assert result["spec"]["relationship_predicate"] == "TEAM_POSTSEASON_RESULT"


def test_mvp_phrasing_resolves_to_awards_capability():
    for text in (
        "Quiz me on who won the NFL MVP award each year.",
        "Guess the Offensive Player of the Year.",
        "Guess the Defensive Rookie of the Year.",
        "Who won Super Bowl MVP?",
    ):
        result = translator_mod.translate(text, provider="mock")
        assert result["translation_status"] == "TRANSLATED", text
        assert result["spec"]["domain"] == "NFL_AWARDS", text
        assert result["spec"]["relationship_predicate"] == "WON_AWARD", text


def test_super_bowl_mvp_phrasing_does_not_get_swallowed_by_championship_pattern():
    # "Super Bowl" + "won" + an award word must route to NFL_AWARDS, not
    # NFL_SUPER_BOWL -- see the WON_CHAMPIONSHIP block's own has_award_word
    # exclusion in mock.py.
    result = translator_mod.translate("Guess who won Super Bowl MVP each year.", provider="mock")
    assert result["spec"]["domain"] == "NFL_AWARDS"


def test_super_bowl_history_end_to_end_real_pipeline():
    # Absolute Final Closeout fix: real candidate pool is now 60 (all 60
    # real Super Bowls, up from 24 -- see nfl_super_bowl.py's own module
    # docstring), so an explicit in-text count is no longer required to
    # clear validator.py's spec-bounds check before question_count_override
    # is applied.
    pkg = pipeline.run(
        "Make a game where I guess which team won the Super Bowl. Give me 20 questions.",
        provider="mock", seed="test-nfl-super-bowl-e2e", question_count_override=20,
    )
    assert pkg.get("qa_status") == "PASSED"
    questions = pkg.get("questions") or []
    assert 1 <= len(questions) <= 20  # real pool is 60 -- may be capped by dedupe, never padded/fabricated
    seen_questions = set()
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3
        assert "Super Bowl" in q["question"]
        assert q["question"] not in seen_questions
        seen_questions.add(q["question"])


def test_super_bowl_history_all_sixty_real_games_are_now_playable():
    """The core regression: 36 of 60 real Super Bowls (1966-2001) used to
    be rejected outright as TEAM_UNRESOLVED because the import script left
    winner/loser_team_code NULL for every pre-2002 game -- even though it
    preserved the real raw team name text. Resolving by name instead of a
    missing code recovers all 60."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import nfl_super_bowl as sb

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_championship_event",
        "relationship_predicate": "WON_CHAMPIONSHIP", "object_type": "team",
        "answer_type": "team", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, sb, request_text="pytest", director_request_id="pytest",
        seed="pytest-sb-all-60", target_count=100, id_start=1,
    )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 60
    assert pkg["funnel"]["rejected_counts"] == {}


def test_super_bowl_one_resolves_by_real_historical_name():
    """Super Bowl I (1966 season, Packers over Chiefs) has NULL team codes
    in the source table but real preserved name text -- the exact case
    this fix exists for."""
    from tools.quiz_export.adapters import nfl_super_bowl as sb

    c = engine.connect()
    try:
        row = c.execute(
            "SELECT winner_name_raw, loser_name_raw FROM nfl_championship_events WHERE sb_number='I'"
        ).fetchone()
        assert row["winner_name_raw"] == "Green Bay Packers"
        winner, err = sb.resolve_franchise_by_name(c, row["winner_name_raw"])
        assert err is None
        assert "Green Bay" in winner["full_name"]
    finally:
        c.close()


def test_super_bowl_history_has_real_easy_content_now():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import nfl_super_bowl as sb

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_championship_event",
        "relationship_predicate": "WON_CHAMPIONSHIP", "object_type": "team",
        "answer_type": "team", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, sb, request_text="pytest", director_request_id="pytest",
        seed="pytest-sb-easy", target_count=100, id_start=1,
    )
    difficulties = {q["difficulty"] for q in pkg["questions"]}
    assert "Easy" in difficulties
    assert "Medium" in difficulties
    assert "Hard" in difficulties


def test_season_awards_end_to_end_real_pipeline():
    pkg = pipeline.run(
        "Quiz me on who won NFL season awards -- MVP, Offensive Player of the Year, "
        "Defensive Player of the Year, Rookie of the Year.",
        provider="mock", seed="test-nfl-awards-e2e", question_count_override=25,
    )
    assert pkg.get("qa_status") == "PASSED"
    questions = pkg.get("questions") or []
    assert 1 <= len(questions) <= 25  # real resolved pool is 238
    seen_questions = set()
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3
        assert q["question"] not in seen_questions
        seen_questions.add(q["question"])


def test_awards_distractors_are_always_real_award_winners_not_random_players():
    """Real regression guard for the exact failure mode cfb_heisman.py's own
    module docstring documents (a wide random-player pool producing
    obviously-implausible distractors) -- every option shown, correct or
    not, must be a real winner of one of these six award types."""
    from tools.quiz_export.adapters import nfl_season_awards as adapter

    c = engine.connect()
    try:
        winners = adapter._all_resolved_award_winners(c)
        winner_names = set(winners.values())
        rows = adapter.fetch_ordered_candidates(c, seed="test-awards-distractor-guard")
        import random
        rng = engine.seeded("test-awards-distractor-guard:distractors")
        from tools.quiz_export import duplicates
        guard = duplicates.DuplicateGuard(track_entity=adapter.TRACK_ENTITY)
        checked = 0
        for row in rows:
            result = adapter.evaluate(c, row, rng, guard)
            if isinstance(result, str):
                continue
            for opt in result["options"]:
                assert opt in winner_names, f"non-award-winner distractor leaked: {opt!r}"
            checked += 1
            if checked >= 30:
                break
        assert checked > 0
    finally:
        c.close()
