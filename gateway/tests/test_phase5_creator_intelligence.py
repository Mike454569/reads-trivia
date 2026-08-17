"""Reliability-design Phase 5 -- Creator Intelligence, tightly scoped to the
owner's completion target: plain-language request -> distinct ranked ideas
-> honest feasibility -> no duplicates -> playable private preview when
supported. Reuses the catalog, feasibility vocabulary, and existing
private-preview Gateway routes unchanged -- no new generation code.
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


# --- Distinct, ranked, no duplicates -----------------------------------------

def test_ideas_are_distinct_no_duplicate_triples():
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Guess an NFL player and team, maybe from the draft or a season roster.")
    assert len(ideas) > 1  # a broad request should surface multiple real ideas
    triples = [(i["mechanic"], i["domain"], i["relationship_predicate"]) for i in ideas]
    assert len(triples) == len(set(triples))  # structurally impossible to duplicate, verified anyway


def test_ideas_are_ranked_by_match_strength_then_feasibility():
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Guess which team won the Super Bowl.")
    assert ideas[0]["domain"] == "NFL_SUPER_BOWL"
    assert ideas[0]["relationship_predicate"] == "WON_CHAMPIONSHIP"
    scores = [i["match_score"] for i in ideas]
    assert scores == sorted(scores, reverse=True)  # non-increasing match_score order


def test_narrow_request_never_padded_with_irrelevant_ideas():
    """'never pad below the real qualified count' -- a request with no real
    overlap against any registered capability returns an empty list, never
    invented filler."""
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Tell me about your favorite pizza toppings.")
    assert ideas == []


def test_generic_stopwords_do_not_dominate_ranking():
    """Real, found issue during development: 'guess' appears in ~96% of
    registered capabilities' own signatures and carries no discriminative
    signal -- must not inflate every idea's score roughly equally."""
    from tools.director_v02 import creator_intelligence as ci

    assert "guess" in ci._STOPWORDS
    ideas = ci.generate_ideas("Guess which team won the Super Bowl.")
    assert "guess" not in ideas[0]["matched_words"]


def test_max_ideas_is_honored():
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Guess an NFL or CFB player, team, school, season, or game.", max_ideas=3)
    assert len(ideas) <= 3


# --- Honest feasibility -------------------------------------------------------

def test_ideas_report_real_catalog_backed_feasibility_not_registry_presence():
    """The exact real bug this whole reliability effort exists to prevent:
    an idea must never claim a stronger feasibility tier than its real
    catalog state proves. NFL_PLAYER_SEASON/TEAM_OF_SEASON is HUMAN_APPROVED
    (not PUBLIC_ENABLED) -- must report VERIFIED_NOT_RELEASED, never
    SUPPORTED, and legacy public capabilities must report SUPPORTED."""
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Guess an NFL player and season and which team he was on.")
    by_predicate = {i["relationship_predicate"]: i for i in ideas}

    nfl_season = by_predicate["TEAM_OF_SEASON"]
    assert nfl_season["catalog_vocabulary_status"] == "VERIFIED_NOT_RELEASED"
    assert nfl_season["catalog_status"] == "HUMAN_APPROVED"
    assert nfl_season["can_preview"] is True  # real, proven to generate -- just not public yet

    draft = by_predicate["DRAFTED_BY"]
    assert draft["catalog_vocabulary_status"] == "SUPPORTED"
    assert draft["can_preview"] is True


def test_cfb_idea_reports_generation_verified_honestly():
    from tools.director_v02 import creator_intelligence as ci

    ideas = ci.generate_ideas("Guess a CFB college football player and school for a season.")
    by_predicate = {i["relationship_predicate"]: i for i in ideas}
    cfb_season = by_predicate["SCHOOL_OF_SEASON"]
    assert cfb_season["catalog_vocabulary_status"] == "VERIFIED_NOT_RELEASED"
    assert cfb_season["catalog_status"] == "GENERATION_VERIFIED"
    assert cfb_season["can_preview"] is True


def test_ideas_never_invent_a_capability_not_in_the_real_registry():
    from tools.director_v02 import creator_intelligence as ci, registry

    ideas = ci.generate_ideas("Guess an NFL or CFB player, team, school, season, coach, or game.", max_ideas=25)
    real_triples = set(registry.CAPABILITY_REGISTRY.keys())
    for idea in ideas:
        triple = (idea["mechanic"], idea["domain"], idea["relationship_predicate"])
        assert triple in real_triples


# --- Gateway route: admin-gated, real end-to-end preview --------------------

def test_creator_ideas_requires_admin(client):
    r = client.post("/v1/creator/ideas", json={"request_text": "Guess an NFL player and team."})
    assert r.status_code == 401


def test_creator_ideas_rejects_extra_fields(client, auth_headers):
    r = client.post(
        "/v1/creator/ideas",
        json={"request_text": "Guess an NFL player.", "spec": {"mechanic": "guess"}},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_creator_ideas_route_returns_distinct_ranked_ideas(client, auth_headers):
    r = client.post(
        "/v1/creator/ideas",
        json={"request_text": "Guess an NFL player and team, maybe from the draft or a season roster."},
        headers=auth_headers,
    )
    assert r.status_code == 200
    ideas = r.json()["ideas"]
    assert len(ideas) > 1
    triples = [(i["domain"], i["relationship_predicate"]) for i in ideas]
    assert len(triples) == len(set(triples))


def test_idea_to_playable_private_preview_full_lifecycle(client, auth_headers):
    """The full owner-specified target, end to end: plain-language request
    -> ranked ideas -> pick a can_preview idea -> generate a REAL preview
    via the EXISTING, unchanged /v1/games/generate + /v1/games/{id} +
    /v1/creator/review routes -- zero new generation code exercised here
    beyond the ideas endpoint itself."""
    ideas_resp = client.post(
        "/v1/creator/ideas",
        json={"request_text": "Guess an NFL player and season and which team he was on."},
        headers=auth_headers,
    )
    assert ideas_resp.status_code == 200
    ideas = ideas_resp.json()["ideas"]
    idea = next(i for i in ideas if i["can_preview"])

    spec = {
        "mechanic": idea["mechanic"], "domain": idea["domain"],
        "relationship_predicate": idea["relationship_predicate"],
        "question_count": 5, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    gen = client.post("/v1/games/generate", json={"spec": spec, "provider": "mock"}, headers=auth_headers)
    assert gen.status_code == 200
    body = gen.json()
    assert body["qa_status"] == "PASSED"
    pid = body["package_id"]

    loaded = client.get(f"/v1/games/{pid}", headers=auth_headers)
    assert loaded.status_code == 200
    assert len(loaded.json()["questions"]) == 5

    review = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "APPROVED"}, headers=auth_headers)
    assert review.status_code == 200
    assert review.json()["review_status"] == "APPROVED"


def test_idea_marked_not_previewable_is_never_falsely_claimed_playable():
    """No registered capability is currently below GENERATION_VERIFIED, so
    this test documents the real invariant directly against the mapping
    function rather than needing a synthetic not-yet-verified capability."""
    from tools.director_v02 import creator_intelligence as ci

    assert isinstance(ci._PREVIEWABLE_VOCAB, frozenset)
    assert "UNDERSTOOD_NOT_IMPLEMENTED" not in ci._PREVIEWABLE_VOCAB
    assert "DATA_EXISTS_UNVERIFIED" not in ci._PREVIEWABLE_VOCAB
    assert "IMPLEMENTED_NOT_VERIFIED" not in ci._PREVIEWABLE_VOCAB
    assert None not in ci._PREVIEWABLE_VOCAB
