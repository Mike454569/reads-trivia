"""Existing-Data Wiring pass (4/5, All-America): CFB_ALL_AMERICAN -> NFL_
DRAFT_TEAM, the exact relationship the wiring spec's Phase 2/4 named.

Deliberately does NOT reuse _cross_league_honors_common.py's join (which
uses the full, un-tiered cfb_nfl_identity_bridge_certified) -- scoped to
the bridge's HIGH_CONFIDENCE_MULTI_SEASON_POSITION_CORROBORATED tier only
(463 real rows measured directly), per this pass's "accuracy over raw
count" policy. Team resolution reuses draft.py's own resolve_franchise().
"""
import pytest

from tools import game_director_v01 as v01
from tools.quiz_export.adapters import cfb_all_america_draft_team as adapter
from tools.director_v02 import registry


def _generate(target_count=10, seed="test-aa-draft-team"):
    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "cross_league_player",
        "relationship_predicate": "ALL_AMERICAN_TO_NFL_DRAFT_TEAM", "object_type": "team", "answer_type": "team",
        "group_size": 4, "filters": {},
    }
    return v01.generate_package_from_spec(
        spec, adapter, request_text="test:aa_draft_team", director_request_id="test",
        seed=seed, target_count=target_count, id_start=1, freeze_timestamp=None, difficulty_filter=None,
    )


def test_safety_check_does_not_query_the_raw_cfb_all_america_table():
    # Real production bug caught after deploy: safety_check() originally
    # copied cfb_odd_college_out.py's pattern and queried the RAW
    # cfb_all_america table for verification_status/source_id -- a table
    # this adapter never actually reads from (it only reads
    # cfb_all_america_certified) and which, it turned out, doesn't even
    # exist in the real production database (confirmed directly via
    # `flyctl ssh console` -- local dev has it, production doesn't; a
    # real, pre-existing environment gap, not something this pass
    # introduced). cfb_all_america_certified has no verification_status/
    # source_id columns of its own, so the correct safety_check is a
    # plain descriptive note, matching every other capability already
    # built on this same table (see cfb_all_american_to_all_pro.py).
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        result = adapter.safety_check(c)
    finally:
        c.close()
    assert "note" in result
    assert result == {"note": "composed via cfb_all_america_certified (HIGH_CONFIDENCE bridge tier) + team_aliases"}


def test_generates_real_questions():
    pkg = _generate(target_count=20)
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 20
    for q in pkg["questions"]:
        assert len(set(q["options"])) == 4
        assert q["answer"] in q["options"]
        assert "College Football All-American" in q["question"]
        # Grammar regression guard: never "an College..."
        assert "an College" not in q["question"]


def test_real_full_pool_is_healthy():
    pkg = _generate(target_count=999999)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["funnel"]["accepted_total"] >= 300  # measured directly at 397


def test_no_leakage_of_correct_answer_before_grading():
    pkg = _generate(target_count=10)
    for q in pkg["questions"]:
        # The question text must never name the correct team directly.
        assert q["answer"] not in q["question"]


def test_registered_in_capability_registry():
    cap = registry.lookup("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_NFL_DRAFT_TEAM")
    assert cap is not None
    assert cap["adapter"] is adapter


@pytest.mark.parametrize("difficulty", ["any", "medium"])
def test_supported_difficulties_generate(difficulty):
    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "cross_league_player",
        "relationship_predicate": "ALL_AMERICAN_TO_NFL_DRAFT_TEAM", "object_type": "team", "answer_type": "team",
        "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, adapter, request_text="test", director_request_id="test",
        seed=f"test-diff-{difficulty}", target_count=5, id_start=1, freeze_timestamp=None,
        difficulty_filter=difficulty,
    )
    assert pkg["qa_status"] == "PASSED"
