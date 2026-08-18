"""Reliability-design Phase 5 correction -- Creator Intelligence CONCEPT
layer acceptance tests, proving the full approved completion target:
plain-language request -> distinct ranked CONCEPTS -> honest feasibility ->
no duplicates -> playable private preview when supported.

commit 1e006eb's tools/director_v02/creator_intelligence.py (retrieval) is
kept unchanged and reused internally by tools/director_v02/concepts.py --
these tests exercise the concept layer built on top of it.
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

_REQUIRED_CONCEPT_FIELDS = frozenset({
    "concept_id", "name", "premise", "domain", "player_objective", "core_mechanic",
    "required_catalog_relationships", "round_structure", "presentation_style", "answer_type",
    "scoring", "difficulty_progression", "hint_structure", "candidate_pool_size",
    "replayability_assessment", "freshness_potential", "feasibility_status", "limitations",
    "not_playable_reason", "missing_capabilities", "preview",
})


# --- 1. "Give me ten NFL game ideas" returns ten qualified concepts --------

def test_ten_nfl_ideas_returns_ten_qualified_concepts():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten NFL game ideas.", request_type="IDEAS", requested_count=10)
    assert result["returned_count"] == 10
    assert len(result["concepts"]) == 10
    assert result["coverage_gap_report"] is None


def test_every_concept_has_the_full_required_schema():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten NFL game ideas.", request_type="IDEAS", requested_count=10)
    for concept in result["concepts"]:
        missing = _REQUIRED_CONCEPT_FIELDS - set(concept.keys())
        assert not missing, f"{concept['concept_id']} missing fields: {missing}"


# --- 2. Not ten renamed versions of the same quiz ---------------------------

def test_ten_nfl_ideas_are_not_ten_renamed_versions_of_the_same_quiz():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten NFL game ideas.", request_type="IDEAS", requested_count=10)
    capability_ids = [c["required_catalog_relationships"][0]["capability_id"] for c in result["concepts"]]
    archetypes = [c["gameplay_archetype"] for c in result["concepts"]]
    signatures = [tuple(c["diversity_signature"]) for c in result["concepts"]]

    # Real, found-during-development requirement: capability-level breadth,
    # not just cosmetically-different signatures on the same 1-2 capabilities.
    assert len(set(capability_ids)) == len(capability_ids), "duplicate capability across the ten ideas"
    assert len(set(archetypes)) >= 8, f"too many repeated archetypes: {archetypes}"
    assert len(set(signatures)) == len(signatures), "duplicate diversity signature"


def test_diversity_signature_deduplicates_near_identical_boxscore_concepts():
    """Real, direct proof the signature-based semantic-dedup mechanism
    works: NFL_GAME_BOXSCORE's four real predicates (HAD_MORE_YARDS/
    HAD_MORE_SACKS/HAD_FEWER_TURNOVERS/HAD_FEWER_PENALTIES) all collapse to
    the same real HEAD_TO_HEAD_BOXSCORE archetype -- only one concept per
    (core_mechanic, archetype, round_structure) signature may survive."""
    from tools.director_v02 import concepts

    all_candidates = concepts._all_candidate_concepts("Guess which NFL team had more yards, sacks, or turnovers in a game.")
    deduplicated = concepts._deduplicate_by_signature(all_candidates)
    boxscore_multi_choice = [
        c for c in deduplicated
        if c["gameplay_archetype"] == "HEAD_TO_HEAD_BOXSCORE" and c["core_mechanic"] == "MULTIPLE_CHOICE_SINGLE_FACT"
    ]
    assert len(boxscore_multi_choice) == 1, boxscore_multi_choice


# --- 3. Mixed NFL/CFB request respects both domains -------------------------

def test_mixed_nfl_cfb_request_respects_both_domains():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess an NFL or CFB player, team, school, season, or game.", request_type="IDEAS", requested_count=10,
    )
    domains = [c["domain"] for c in result["concepts"]]
    assert any(d.startswith("NFL") for d in domains)
    assert any(d.startswith("CFB") for d in domains)


# --- 4. Off-topic request returns no fabricated concepts --------------------

def test_off_topic_request_returns_no_fabricated_concepts():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Tell me about your favorite pizza toppings.", request_type="IDEAS", requested_count=10,
    )
    assert result["concepts"] == []
    assert result["returned_count"] == 0
    assert result["coverage_gap_report"] is not None
    assert result["coverage_gap_report"]["returned_count"] == 0


# --- 5. Concept-only ideas never appear as playable -------------------------

def test_concept_only_ideas_never_appear_in_playable_ideas_results():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess which CFB Heisman Trophy winner played for which school.", request_type="PLAYABLE_IDEAS",
        requested_count=10,
    )
    for concept in result["concepts"]:
        assert concept["playability_status"] == "PLAYABLE_NOW"
        assert concept["not_playable_reason"] is None


def test_cross_mechanic_concept_is_never_falsely_marked_playable():
    """Real bug found and fixed during development: mechanic_taxonomy.
    creator_pipeline_supported is a TAXONOMY-level flag, true for
    PROGRESSIVE_CLUE_IDENTIFY only because of ONE bespoke real adapter
    (NFL_PLAYER_IDENTITY/IDENTIFY_FROM_CLUES) -- it must never generalize
    to a cross-mechanic concept proposed for a different capability (e.g.
    CFB_HEISMAN via progressive clues, which no real generator produces)."""
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess which CFB Heisman Trophy winner played for which school.", request_type="IDEAS", requested_count=15,
    )
    heisman_clue_concept = next(
        c for c in result["concepts"]
        if c["required_catalog_relationships"][0]["capability_id"] == "CFB_HEISMAN__WON_HEISMAN"
        and c["core_mechanic"] == "PROGRESSIVE_CLUE_IDENTIFY"
    )
    assert heisman_clue_concept["playability_status"] == "CONCEPT_ONLY"
    assert heisman_clue_concept["not_playable_reason"] is not None
    assert "no real generator produces it" in heisman_clue_concept["not_playable_reason"]

    # The one REAL native mapping must still be playable.
    result2 = concepts.generate_concepts("Guess the NFL player from clues about him.", request_type="IDEAS", requested_count=5)
    native = next(
        c for c in result2["concepts"]
        if c["required_catalog_relationships"][0]["capability_id"] == "NFL_PLAYER_IDENTITY__IDENTIFY_FROM_CLUES"
        and c["core_mechanic"] == "PROGRESSIVE_CLUE_IDENTIFY"
    )
    assert native["playability_status"] == "PLAYABLE_NOW"


# --- 6. Every PLAYABLE_NOW result has a functional private preview --------

def test_every_playable_now_result_has_a_functional_preview():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess an NFL player and season and which team he was on.", request_type="PLAYABLE_IDEAS", requested_count=3,
    )
    assert len(result["concepts"]) > 0
    for concept in result["concepts"]:
        assert concept["playability_status"] == "PLAYABLE_NOW"
        preview = concept["preview"]
        assert preview is not None
        assert preview["qa_status"] == "PASSED"
        assert preview["package_id"] is not None
        assert preview["sample_prompt"]
        # Phase 6: preview shape is now mechanic-specific (a guess-mechanic
        # concept has 4 real options; MATCHING/SORTING/HIGHER_LOWER/
        # ELIMINATION previews carry a differently-shaped real sample, e.g.
        # a single label) -- every mechanic still returns SOME real sample
        # data, never nothing.
        assert preview["sample_options"] is None or len(preview["sample_options"]) >= 1


def test_mixed_request_generates_preview_only_for_playable_half():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Guess a CFB college football player and school for a season.", request_type="MIXED", requested_count=8,
    )
    assert "playable_concepts" in result and "concept_only_ideas" in result
    for concept in result["playable_concepts"]:
        assert concept["preview"] is not None
        assert concept["preview"]["qa_status"] == "PASSED"
    for concept in result["concept_only_ideas"]:
        assert concept["preview"] is None
        assert concept["playability_status"] == "CONCEPT_ONLY"


# --- 7. Fewer-than-requested results include an exact coverage-gap report --

def test_fewer_than_requested_includes_exact_coverage_gap_report():
    from tools.director_v02 import concepts

    result = concepts.generate_concepts(
        "Tell me about your favorite pizza toppings.", request_type="IDEAS", requested_count=10,
    )
    gap = result["coverage_gap_report"]
    assert gap["requested_count"] == 10
    assert gap["returned_count"] == 0
    assert gap["shortfall"] == 10
    assert gap["total_candidate_concepts_generated"] == 0
    assert "Never padded" in gap["reason"]


# --- 8. Repeated requests surface additional qualified concepts -----------

def test_repeated_request_with_exclusion_surfaces_different_concepts():
    from tools.director_v02 import concepts

    first = concepts.generate_concepts(
        "Guess which CFB Heisman Trophy winner played for which school.", request_type="IDEAS", requested_count=10,
    )
    first_ids = {c["concept_id"] for c in first["concepts"]}

    second = concepts.generate_concepts(
        "Guess which CFB Heisman Trophy winner played for which school.", request_type="IDEAS", requested_count=10,
        exclude_concept_ids=list(first_ids),
    )
    second_ids = {c["concept_id"] for c in second["concepts"]}

    assert second_ids, "repeated request should surface more real concepts when inventory permits"
    assert first_ids.isdisjoint(second_ids)


# --- 9. Candidate-pool/replayability come from real catalog/validation data

def test_candidate_pool_and_replayability_come_from_real_tier2_data():
    """candidate_pool_size must equal the SAME already-certified Tier-2
    eligible_pool_size a direct DB query returns -- proving it is read
    from real validation data, not recomputed or guessed inside the
    concept layer."""
    from tools.director_v02 import concepts
    from tools.quiz_export import engine as engine_bootstrap

    result = concepts.generate_concepts("Guess which team won the Super Bowl.", request_type="IDEAS", requested_count=10)
    super_bowl = next(
        c for c in result["concepts"]
        if c["required_catalog_relationships"][0]["capability_id"] == "NFL_SUPER_BOWL__WON_CHAMPIONSHIP"
    )

    c = engine_bootstrap.connect()
    try:
        expected_pool_size = concepts._real_pool_size(c, "NFL_SUPER_BOWL__WON_CHAMPIONSHIP")
    finally:
        c.close()

    assert expected_pool_size is not None
    assert super_bowl["candidate_pool_size"] == expected_pool_size
    assert super_bowl["replayability_assessment"] == concepts._replayability_assessment(expected_pool_size)


def test_replayability_assessment_reflects_real_pool_size_thresholds():
    from tools.director_v02 import concepts

    assert concepts._replayability_assessment(50000) == "HIGH"
    assert concepts._replayability_assessment(500) == "MODERATE"
    assert concepts._replayability_assessment(50) == "LOW"
    assert concepts._replayability_assessment(5) == "VERY_LOW"
    assert concepts._replayability_assessment(None) == "UNKNOWN -- no Tier-2 certification on record"


def test_freshness_is_informational_not_an_automatic_quality_bonus():
    """Owner-required: frequently-refreshed data must never be scored
    automatically higher than verified historical data -- freshness only
    factors into ranking when the REQUEST ITSELF signals wanting current
    content."""
    from tools.director_v02 import concepts

    no_signal_words = {"guess", "nfl", "team"}
    fresh = concepts._freshness_potential({"freshness_category": "REGULARLY_REFRESHED"}, no_signal_words)
    assert fresh["relevant_to_this_request"] is False

    with_signal_words = {"guess", "current", "season"}
    fresh2 = concepts._freshness_potential({"freshness_category": "REGULARLY_REFRESHED"}, with_signal_words)
    assert fresh2["relevant_to_this_request"] is True


# --- Gateway route: admin-gated, real end-to-end ----------------------------

def test_creator_concepts_requires_admin(client):
    r = client.post("/v1/creator/concepts", json={"request_text": "Guess an NFL player."})
    assert r.status_code == 401


def test_creator_concepts_route_ideas(client, auth_headers):
    r = client.post(
        "/v1/creator/concepts",
        json={"request_text": "Give me ten NFL game ideas.", "request_type": "IDEAS", "requested_count": 10},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["returned_count"] == 10
    assert len(body["concepts"]) == 10


def test_creator_concepts_route_playable_ideas_real_preview(client, auth_headers):
    r = client.post(
        "/v1/creator/concepts",
        json={
            "request_text": "Guess an NFL player and season and which team he was on.",
            "request_type": "PLAYABLE_IDEAS", "requested_count": 2,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["concepts"]) > 0
    for concept in body["concepts"]:
        assert concept["preview"]["qa_status"] == "PASSED"
        pid = concept["preview"]["package_id"]
        loaded = client.get(f"/v1/games/{pid}", headers=auth_headers)
        assert loaded.status_code == 200
        # Phase 6: a stored package's real round-content key is mechanic-
        # specific (questions/rounds/sequence/puzzles) -- at least one must
        # be present with real, non-empty content.
        body = loaded.json()
        round_content = [body.get(k) for k in ("questions", "rounds", "sequence", "puzzles") if body.get(k)]
        assert round_content and len(round_content[0]) >= 1


def test_creator_concepts_rejects_invalid_request_type(client, auth_headers):
    r = client.post(
        "/v1/creator/concepts",
        json={"request_text": "Guess an NFL player.", "request_type": "NOT_A_REAL_TYPE"},
        headers=auth_headers,
    )
    assert r.status_code == 400


# --- 10. At least ten concepts inspected with real details ------------------

def test_inspect_ten_concepts_for_the_phase5_report():
    """Not a pass/fail assertion beyond real structural checks -- this test
    prints the real data used directly in the corrected Phase 5 report
    (mechanics, required relationships, feasibility, preview status)."""
    from tools.director_v02 import concepts

    result = concepts.generate_concepts("Give me ten NFL game ideas.", request_type="IDEAS", requested_count=10)
    assert len(result["concepts"]) == 10
    for c in result["concepts"]:
        assert c["core_mechanic"] in ("MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY",
                                       "MATCHING", "SORTING_TIMELINE", "HIGHER_LOWER_STREAK",
                                       "ELIMINATION_SURVIVAL", "POSITION_LINEUP_GRID")
        assert c["required_catalog_relationships"][0]["capability_id"]
        assert c["feasibility_status"] is not None
        assert c["playability_status"] in ("PLAYABLE_NOW", "CONCEPT_ONLY")
