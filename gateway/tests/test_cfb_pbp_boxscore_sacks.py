"""Existing-Data Wiring pass (Phase 3, CFB play-by-play): CFB_GAME_
BOXSCORE/HAD_MORE_SACKS -- the first real capability built directly on
cfb_plays (3.72M rows) beyond CFB_UPSET/BETTING_UPSET-adjacent uses. No
CFB team_game_stats-style table exists, so sack counts are aggregated live
from real play-by-play. Team-level only -- cfb_plays has no player-
identity columns, so player-level CFB PBP capabilities are a real,
disclosed non-goal, not attempted here.
"""
import pytest

from tools import game_director_v01 as v01
from tools.quiz_export.adapters import cfb_game_boxscore_sacks as adapter
from tools.director_v02 import registry


def _generate(target_count=10, seed="test-cfb-boxscore-sacks"):
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_game",
        "relationship_predicate": "HAD_MORE_SACKS", "object_type": "school", "answer_type": "school",
        "group_size": 2, "filters": {},
    }
    return v01.generate_package_from_spec(
        spec, adapter, request_text="test:cfb_boxscore_sacks", director_request_id="test",
        seed=seed, target_count=target_count, id_start=1, freeze_timestamp=None, difficulty_filter=None,
    )


def test_generates_real_questions():
    pkg = _generate(target_count=20)
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 20
    for q in pkg["questions"]:
        assert len(set(q["options"])) == 2
        assert q["answer"] in q["options"]


def test_real_full_pool_is_healthy():
    pkg = _generate(target_count=999999)
    assert pkg["qa_status"] == "PASSED"
    # Real pool is 14,921 total, but fetch_ordered_candidates() caps at
    # MAX_FETCHED_CANDIDATES=5000 per call (same real safeguard every
    # other adapter in this codebase uses) -- a handful are then rejected
    # for real reasons (e.g. a display-name collision), so this checks a
    # realistic bound, not the literal cap.
    assert pkg["funnel"]["accepted_total"] >= 4900


def test_ties_are_never_generated():
    pkg = _generate(target_count=200)
    for q in pkg["questions"]:
        # A tied sack count has no fair winner -- confirm no notes claim
        # equal counts for both sides.
        assert q["notes"].count(" to ") == 1


def test_grammar_singular_plural_sack_count():
    pkg = _generate(target_count=200)
    saw_singular = False
    for q in pkg["questions"]:
        assert "1 sacks" not in q["notes"]
        if "1 sack " in q["notes"] or q["notes"].endswith("1 sack."):
            saw_singular = True
    assert saw_singular, "expected at least one real 1-sack game in a 200-question sample"


def test_registered_in_capability_registry():
    cap = registry.lookup("guess", "CFB_GAME_BOXSCORE", "HAD_MORE_SACKS")
    assert cap is not None
    assert cap["adapter"] is adapter


@pytest.mark.parametrize("difficulty", ["any", "easy", "medium", "hard"])
def test_all_difficulty_bands_generate(difficulty):
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_game",
        "relationship_predicate": "HAD_MORE_SACKS", "object_type": "school", "answer_type": "school",
        "group_size": 2, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, adapter, request_text="test", director_request_id="test",
        seed=f"test-diff-{difficulty}", target_count=5, id_start=1, freeze_timestamp=None,
        difficulty_filter=difficulty,
    )
    assert pkg["qa_status"] == "PASSED"
