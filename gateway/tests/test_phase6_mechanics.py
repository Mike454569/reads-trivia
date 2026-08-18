"""Reliability Design Phase 6 -- Mechanic Execution Framework.

Real, private, playable rounds for the six new/formalized mechanic
templates (MULTIPLE_CHOICE_SINGLE_FACT and PROGRESSIVE_CLUE_IDENTIFY were
formalized under the common execution contract, not rebuilt; MATCHING,
SORTING_TIMELINE, HIGHER_LOWER_STREAK, ELIMINATION_SURVIVAL, and
POSITION_LINEUP_GRID are genuinely new/newly-wired this phase). Covers:
generator-level correctness with real NFL+CFB data, the client-safe view /
server-authoritative evaluate contract (no leakage before an answer is
submitted), the admin-gated Gateway routes end to end, consecutive rounds,
and Creator Intelligence's updated PLAYABLE_NOW gating + mechanic-diversity
selection.
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

_LEAK_MARKERS = ("_private", "correctIndex", "_audit", "_mechanic_variant")


def _assert_no_leakage(obj) -> None:
    import json
    s = json.dumps(obj)
    for marker in _LEAK_MARKERS:
        assert marker not in s, f"leakage suspect: {marker!r} found in {obj!r}"


# --- Generator-level: real NFL + CFB data, both variants per mechanic -----

def test_matching_generates_real_nfl_and_cfb_rounds():
    from tools.director_v04 import matching

    nfl = matching.build_package("t-nfl", "NFL_DRAFT_CLASS_MATCH", round_count=2, pair_count=4)
    assert nfl["qa_status"] == "PASSED"
    assert nfl["round_count"] >= 1
    r = nfl["rounds"][0]
    assert len(r["left_items"]) == len(r["right_items"]) == 4
    assert len(set(p["item_id"] for p in r["left_items"])) == 4
    # Structural no-duplicate-solution guarantee: right-side labels distinct.
    assert len({it["label"] for it in r["right_items"]}) == 4

    cfb = matching.build_package("t-cfb", "CFB_HEISMAN_SCHOOL_MATCH", round_count=2, pair_count=4)
    assert cfb["qa_status"] == "PASSED"
    assert cfb["round_count"] >= 1


def test_sorting_generates_real_nfl_and_cfb_rounds_tie_free():
    from tools.director_v04 import sorting

    nfl = sorting.build_package("t-nfl", "NFL_DRAFT_PICK_ORDER", round_count=2, item_count=4)
    assert nfl["qa_status"] == "PASSED"
    r = nfl["rounds"][0]
    assert len(r["items_shuffled"]) == 4
    assert len(set(r["_private_correct_order"])) == 4  # tie-free -- no repeated position

    cfb = sorting.build_package("t-cfb", "CFB_HEISMAN_YEAR_ORDER", round_count=2, item_count=4)
    assert cfb["qa_status"] == "PASSED"


def test_higher_lower_generates_real_nfl_and_cfb_sequences_tie_free():
    from tools.director_v04 import higher_lower

    nfl = higher_lower.build_package("t-nfl", "NFL_TEAM_SEASON_WINS", sequence_length=10)
    assert nfl["qa_status"] == "PASSED"
    values = [it["_private_value"] for it in nfl["sequence"]]
    assert len(set(values)) == len(values)  # tie-exclusion, every item distinct

    cfb = higher_lower.build_package("t-cfb", "CFB_TEAM_SEASON_WINS", sequence_length=10)
    assert cfb["qa_status"] == "PASSED"


def test_elimination_generates_real_nfl_and_cfb_sequences_with_true_and_false():
    from tools.director_v04 import elimination

    nfl = elimination.build_package("t-nfl", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    assert nfl["qa_status"] == "PASSED"
    memberships = {it["_private_membership"] for it in nfl["sequence"]}
    assert memberships == {True, False}  # real qualified true AND false examples

    cfb = elimination.build_package("t-cfb", "CFB_NATIONAL_CHAMPION_SURVIVAL", sequence_length=10)
    assert cfb["qa_status"] == "PASSED"
    cfb_memberships = {it["_private_membership"] for it in cfb["sequence"]}
    assert cfb_memberships == {True, False}


# --- mechanic_engine: client-safe view never leaks, evaluation is real ----

@pytest.mark.parametrize("taxonomy_id,variant,gen_kwargs", [
    ("MATCHING", "NFL_DRAFT_CLASS_MATCH", {"round_count": 2, "pair_count": 4}),
    ("SORTING_TIMELINE", "CFB_HEISMAN_YEAR_ORDER", {"round_count": 2, "item_count": 4}),
    ("HIGHER_LOWER_STREAK", "NFL_TEAM_SEASON_WINS", {"sequence_length": 10}),
    ("ELIMINATION_SURVIVAL", "CFB_NATIONAL_CHAMPION_SURVIVAL", {"sequence_length": 10}),
])
def test_client_safe_view_never_leaks_the_private_answer(taxonomy_id, variant, gen_kwargs):
    from tools.director_v02 import mechanic_engine

    if taxonomy_id == "MATCHING":
        package = mechanic_engine.generate_matching_round(variant=variant, seed="leak-test", **gen_kwargs)
    elif taxonomy_id == "SORTING_TIMELINE":
        package = mechanic_engine.generate_sorting_round(variant=variant, seed="leak-test", **gen_kwargs)
    elif taxonomy_id == "HIGHER_LOWER_STREAK":
        package = mechanic_engine.generate_higher_lower_round(variant=variant, seed="leak-test", **gen_kwargs)
    else:
        package = mechanic_engine.generate_elimination_round(variant=variant, seed="leak-test", **gen_kwargs)

    progress = mechanic_engine.initial_progress(taxonomy_id)
    view = mechanic_engine.client_safe_view(taxonomy_id, package, progress)
    _assert_no_leakage(view)


def test_progressive_clue_view_never_leaks_the_answer_but_reveals_clues():
    from tools.director_v02 import mechanic_engine

    package = mechanic_engine.generate_clue_round(target_count=2, seed="leak-test-clues")
    progress = mechanic_engine.initial_progress("PROGRESSIVE_CLUE_IDENTIFY")
    view = mechanic_engine.client_safe_view("PROGRESSIVE_CLUE_IDENTIFY", package, progress)
    assert "answer" not in str(view).lower().replace("can_reveal", "").replace("clues_revealed", "")
    assert view["clues_revealed_count"] == 1
    assert len(view["clues"]) == 1


def test_matching_evaluate_is_server_authoritative_partial_credit():
    from tools.director_v02 import mechanic_engine

    package = mechanic_engine.generate_matching_round(
        variant="NFL_DRAFT_CLASS_MATCH", round_count=1, pair_count=4, seed="eval-test")
    progress = mechanic_engine.initial_progress("MATCHING")
    correct_key = package["rounds"][0]["_private_answer_key"]
    # Half right, half wrong -- proves partial credit is computed from the
    # REAL stored key, not trusted from the submission.
    items = list(correct_key.items())
    submission = {"mapping": {items[0][0]: items[0][1], items[1][0]: "WRONG"}}
    result, new_progress = mechanic_engine.evaluate_submission("MATCHING", package, progress, submission)
    assert result["correct_count"] == 1
    assert result["total_pairs"] == 4
    assert result["all_correct"] is False
    assert new_progress["current_index"] == 1


def test_higher_lower_evaluate_ends_streak_on_wrong_guess():
    from tools.director_v04 import higher_lower
    from tools.director_v02 import mechanic_engine

    package = higher_lower.build_package("streak-end-test", "NFL_TEAM_SEASON_WINS", sequence_length=10)
    progress = mechanic_engine.initial_progress("HIGHER_LOWER_STREAK")
    cur_v = package["sequence"][0]["_private_value"]
    next_v = package["sequence"][1]["_private_value"]
    wrong_guess = "lower" if next_v > cur_v else "higher"
    result, new_progress = mechanic_engine.evaluate_submission(
        "HIGHER_LOWER_STREAK", package, progress, {"guess": wrong_guess})
    assert result["correct"] is False
    assert new_progress["ended"] is True
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission("HIGHER_LOWER_STREAK", package, new_progress, {"guess": "higher"})


def test_elimination_evaluate_ends_run_on_wrong_guess():
    from tools.director_v04 import elimination
    from tools.director_v02 import mechanic_engine

    package = elimination.build_package("survival-end-test", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    progress = mechanic_engine.initial_progress("ELIMINATION_SURVIVAL")
    actual = package["sequence"][0]["_private_membership"]
    result, new_progress = mechanic_engine.evaluate_submission(
        "ELIMINATION_SURVIVAL", package, progress, {"guess": not actual})
    assert result["correct"] is False
    assert new_progress["ended"] is True


# --- Gateway routes: admin-gated, real end-to-end, consecutive rounds -----

def test_mechanics_round_requires_admin(client):
    r = client.post("/v1/creator/mechanics/round", json={"taxonomy_id": "MATCHING", "variant": "NFL_DRAFT_CLASS_MATCH"})
    assert r.status_code == 401


@pytest.mark.parametrize("body", [
    {"taxonomy_id": "MULTIPLE_CHOICE_SINGLE_FACT", "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY", "question_count": 2},
    {"taxonomy_id": "POSITION_LINEUP_GRID", "variant": "NFL_OFFENSE_LINEUP_COLLEGE_TEAM_ONLY", "question_count": 2},
    {"taxonomy_id": "PROGRESSIVE_CLUE_IDENTIFY", "round_count": 2},
    {"taxonomy_id": "MATCHING", "variant": "NFL_DRAFT_CLASS_MATCH", "round_count": 2, "pair_count": 4},
    {"taxonomy_id": "SORTING_TIMELINE", "variant": "CFB_HEISMAN_YEAR_ORDER", "round_count": 2, "item_count": 4},
    {"taxonomy_id": "HIGHER_LOWER_STREAK", "variant": "NFL_TEAM_SEASON_WINS", "sequence_length": 10},
    {"taxonomy_id": "ELIMINATION_SURVIVAL", "variant": "CFB_NATIONAL_CHAMPION_SURVIVAL", "sequence_length": 10},
])
def test_mechanics_round_start_returns_client_safe_view_for_every_mechanic(body, client, auth_headers):
    r = client.post("/v1/creator/mechanics/round", json=body, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["round_id"]
    assert data["taxonomy_id"] == body["taxonomy_id"]
    _assert_no_leakage(data["view"])


def test_multiple_choice_consecutive_rounds_without_load_failed(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round", json={
        "taxonomy_id": "MULTIPLE_CHOICE_SINGLE_FACT", "domain": "NFL_GAME_RESULT",
        "relationship_predicate": "WON_GAME", "question_count": 4,
    }, headers=auth_headers)
    assert r.status_code == 200
    round_id = r.json()["round_id"]
    for _ in range(4):
        sub = client.post(f"/v1/creator/mechanics/round/{round_id}/submit",
                           json={"submission": {"answer": "x"}}, headers=auth_headers)
        assert sub.status_code == 200
        assert "correct" in sub.json()["result"]


def test_matching_round_resume_after_submit(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round", json={
        "taxonomy_id": "MATCHING", "variant": "NFL_DRAFT_CLASS_MATCH", "round_count": 2, "pair_count": 4,
    }, headers=auth_headers)
    round_id = r.json()["round_id"]
    left_id = r.json()["view"]["left_items"][0]["item_id"]
    right_id = r.json()["view"]["right_items"][0]["item_id"]
    sub = client.post(f"/v1/creator/mechanics/round/{round_id}/submit",
                       json={"submission": {"mapping": {left_id: right_id}}}, headers=auth_headers)
    assert sub.status_code == 200
    assert sub.json()["result"]["total_pairs"] == 4

    resumed = client.get(f"/v1/creator/mechanics/round/{round_id}", headers=auth_headers)
    assert resumed.status_code == 200
    assert resumed.json()["view"]["round_index"] == 1
    _assert_no_leakage(resumed.json()["view"])


def test_mechanics_round_not_found_is_clean_error(client, auth_headers):
    r = client.get("/v1/creator/mechanics/round/GGP5:0000000000000000000000ab", headers=auth_headers)
    assert r.status_code == 404


def test_mechanics_round_rejects_unknown_variant(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "MATCHING", "variant": "NOT_A_REAL_VARIANT"}, headers=auth_headers)
    assert r.status_code == 400


# --- Creator Intelligence integration: gating + diversity ------------------

def test_position_lineup_grid_is_playable_now_not_matching():
    """Real bug found and fixed during Phase 6: a LINEUP domain used to be
    proposed as MATCHING-compatible (wrong mechanic entirely) and was never
    reachable as its own real taxonomy. Now it must appear as its own
    PLAYABLE_NOW POSITION_LINEUP_GRID concept."""
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess the NFL team from its starting offense lineup.", request_type="IDEAS", requested_count=15)
    lineup_concepts = [c for c in result["concepts"] if "LINEUP" in c["domain"]]
    assert lineup_concepts, "expected at least one LINEUP concept"
    # A LINEUP domain may legitimately be PROPOSED under more than one
    # taxonomy (e.g. a CONCEPT_ONLY SORTING_TIMELINE idea) -- what matters is
    # that its own real, native mechanic (POSITION_LINEUP_GRID) is present
    # and PLAYABLE_NOW, and that no OTHER taxonomy for this domain is ever
    # falsely marked playable.
    playable = [c for c in lineup_concepts if c["playability_status"] == "PLAYABLE_NOW"]
    assert playable, "no playable LINEUP concept found"
    for c in playable:
        assert c["core_mechanic"] == "POSITION_LINEUP_GRID"
    for c in lineup_concepts:
        if c["core_mechanic"] != "POSITION_LINEUP_GRID":
            assert c["playability_status"] == "CONCEPT_ONLY"


def test_ten_playable_nfl_ideas_represent_at_least_six_mechanics():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten playable NFL game ideas.", request_type="PLAYABLE_IDEAS", requested_count=10)
    assert result["returned_count"] == 10
    for c in result["concepts"]:
        assert c["playability_status"] == "PLAYABLE_NOW"
        assert c["preview"]["qa_status"] == "PASSED"
    mechanics = {c["core_mechanic"] for c in result["concepts"]}
    assert len(mechanics) >= 6, f"only {len(mechanics)} distinct mechanics: {mechanics}"


def test_ten_playable_cfb_ideas_stay_in_domain_and_never_pad():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten playable CFB game ideas.", request_type="PLAYABLE_IDEAS", requested_count=10)
    for c in result["concepts"]:
        assert c["domain"].startswith("CFB_"), f"non-CFB concept leaked into a CFB-only request: {c['concept_id']}"
        assert c["playability_status"] == "PLAYABLE_NOW"
        assert c["preview"]["qa_status"] == "PASSED"
    # Real, disclosed ceiling: CFB has no PROGRESSIVE_CLUE_IDENTIFY or
    # POSITION_LINEUP_GRID capability at all (no CFB player-clues capability,
    # no CFB lineup-board capability), so 5 distinct mechanics -- not 6 -- is
    # CFB's genuine current maximum. Asserting the real number, not padding
    # the requirement to a number the real data can't honestly support.
    mechanics = {c["core_mechanic"] for c in result["concepts"]}
    assert mechanics == {"MULTIPLE_CHOICE_SINGLE_FACT", "MATCHING", "SORTING_TIMELINE",
                          "HIGHER_LOWER_STREAK", "ELIMINATION_SURVIVAL"}


def test_general_ideas_request_never_repeats_a_capability():
    """Real bug found and fixed during Phase 6: allowing mechanic-diversity
    selection to reuse a capability across mechanics too freely let one
    capability (compatible with 3+ mechanics) fill several of the ten
    slots by itself for a general IDEAS request -- the exact "renamed
    duplicate" failure this design exists to prevent. Capability reuse is
    now restricted to PLAYABLE_NOW concepts filling an otherwise-unfillable
    mechanic slot, never a general free-for-all."""
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten NFL game ideas.", request_type="IDEAS", requested_count=10)
    capability_ids = [c["required_catalog_relationships"][0]["capability_id"] for c in result["concepts"]]
    assert len(set(capability_ids)) == len(capability_ids)


def test_off_topic_request_never_surfaces_new_mechanic_concepts():
    """Real bug found and fixed during Phase 6: the four HIGHER_LOWER_STREAK/
    ELIMINATION_SURVIVAL concepts were appended unconditionally regardless
    of request relevance, breaking the off-topic/no-fabrication contract."""
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Tell me about your favorite pizza toppings.", request_type="IDEAS", requested_count=10)
    assert result["returned_count"] == 0
    assert result["concepts"] == []
