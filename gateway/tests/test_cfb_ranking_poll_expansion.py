"""Existing-Data Wiring pass (2/5): CFB Rankings/Polls poll-type expansion.

cfb_rankings (31,801 real rows) already had 2 registered capabilities
(RANKED_IN_POLL, RANKED_HIGHER) -- but both were hardcoded to poll='AP Top
25' only (9,080 of 31,801 real regular-season rows, ~30%), despite the
table genuinely carrying real Coaches Poll (9,131 rows) and Playoff
Committee Rankings (1,750 rows) snapshots at the same real 1-25 rank
range. Both adapters (tools/quiz_export/adapters/cfb_ranking.py,
cfb_ranking_comparison.py) now accept an explicit `poll` filter (default
unchanged: AP Top 25), and the mock NL translator now extracts it from
real phrasing ("Coaches Poll", "CFP", "Playoff Committee"). Every question
is still built from exactly one poll's own snapshot -- polls are never
combined into one implied ranking.
"""
import pytest

from tools import game_director_v01 as v01
from tools.quiz_export.adapters import cfb_ranking as ranking_adapter
from tools.quiz_export.adapters import cfb_ranking_comparison as cmp_adapter
from tools.director_v02.providers.mock import MockDeterministicTranslator

SUPPORTED_POLLS = ["AP Top 25", "Coaches Poll", "Playoff Committee Rankings"]


def _generate(adapter, predicate, entity_type, object_type, answer_type, group_size, poll, target_count=10):
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": entity_type,
        "relationship_predicate": predicate, "object_type": object_type, "answer_type": answer_type,
        "group_size": group_size, "filters": {"poll": poll},
    }
    return v01.generate_package_from_spec(
        spec, adapter, request_text=f"test:{predicate}:{poll}", director_request_id="test",
        seed=f"test-{predicate}-{poll}", target_count=target_count, id_start=1,
        freeze_timestamp=None, difficulty_filter=None,
    )


@pytest.mark.parametrize("poll", SUPPORTED_POLLS)
def test_ranked_in_poll_generates_real_questions_for_each_poll(poll):
    pkg = _generate(ranking_adapter, "RANKED_IN_POLL", "cfb_ranking", "school", "school", 4, poll)
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    q = pkg["questions"][0]
    assert poll in q["question"]
    assert len(set(q["options"])) == 4


@pytest.mark.parametrize("poll", SUPPORTED_POLLS)
def test_ranked_higher_generates_real_questions_for_each_poll(poll):
    pkg = _generate(cmp_adapter, "RANKED_HIGHER", "cfb_ranking_pair", "school", "school", 2, poll)
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    q = pkg["questions"][0]
    assert poll in q["question"]
    assert len(set(q["options"])) == 2


def test_unrecognized_poll_falls_back_to_ap_top_25_default():
    pkg = _generate(ranking_adapter, "RANKED_IN_POLL", "cfb_ranking", "school", "school", 4, "Not A Real Poll")
    assert pkg["qa_status"] == "PASSED"
    assert "AP Top 25" in pkg["questions"][0]["question"]


def test_no_poll_never_leaks_across_a_single_question():
    # Every individual generated question must be built from exactly one
    # poll's snapshot -- the poll name that appears in the question text
    # must match the poll actually requested, never a blend.
    pkg = _generate(ranking_adapter, "RANKED_IN_POLL", "cfb_ranking", "school", "school", 4, "Coaches Poll", target_count=25)
    for q in pkg["questions"]:
        assert "Coaches Poll" in q["question"]
        assert "AP Top 25" not in q["question"]
        assert "Playoff Committee Rankings" not in q["question"]


# --- NL routing (Phase 6) ----------------------------------------------------

@pytest.mark.parametrize("phrase,expected_poll", [
    ("Make a game about the Coaches Poll.", "Coaches Poll"),
    ("Make a game about CFP rankings.", "Playoff Committee Rankings"),
    ("Give me a Playoff Committee rankings game.", "Playoff Committee Rankings"),
])
def test_nl_translator_extracts_explicit_poll(phrase, expected_poll):
    r = MockDeterministicTranslator().translate(phrase)
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "CFB_RANKING"
    assert r["spec"]["filters"].get("poll") == expected_poll


def test_nl_translator_default_ranking_request_has_no_explicit_poll_filter():
    # No poll named -> no explicit filter, adapter's own AP Top 25 default
    # applies -- unchanged behavior from before this pass.
    r = MockDeterministicTranslator().translate("Make me a game about college football rankings.")
    assert r["translation_status"] == "TRANSLATED"
    assert "poll" not in r["spec"]["filters"]


def test_nl_translator_rank_range_and_poll_combine():
    r = MockDeterministicTranslator().translate("Give me a game about teams ranked in the top 10 in the Coaches Poll.")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["filters"] == {"rank_min": 1, "rank_max": 10, "poll": "Coaches Poll"}


# --- registry shape -----------------------------------------------------------

def test_registry_declares_poll_filter_key():
    from tools.director_v02 import registry
    ranked_in_poll = registry.CAPABILITY_REGISTRY[("guess", "CFB_RANKING", "RANKED_IN_POLL")]
    ranked_higher = registry.CAPABILITY_REGISTRY[("guess", "CFB_RANKING", "RANKED_HIGHER")]
    assert "poll" in ranked_in_poll["supported_filter_keys"]
    assert "poll" in ranked_higher["supported_filter_keys"]


def test_poll_in_the_global_schema_filter_allowlist():
    # Real production bug found after deploy: schema.py's ALLOWED_FILTER_KEYS
    # is a SEPARATE, hand-maintained global gate checked BEFORE a
    # capability's own supported_filter_keys (validator.py checks both) --
    # unlike ALLOWED_DOMAINS/ALLOWED_PREDICATES it is NOT part of
    # generate_schema_and_prompt.py's auto-generated block, so adding
    # "poll" to the capability's registry entry alone was not enough.
    # Every "Coaches Poll"/"CFP" NL request 500'd with
    # BLOCKED_UNSUPPORTED_FILTER in production until this was fixed --
    # caught by actually calling the real end-to-end /v1/creator/generate
    # route (not just the translator's output spec and the adapter
    # separately, which is what let this slip through the first time).
    from tools.director_v02 import schema
    assert "poll" in schema.ALLOWED_FILTER_KEYS


def test_full_http_route_real_generation_for_coaches_poll_request(client, auth_headers):
    r = client.post("/v1/creator/generate", json={"request_text": "Make a game about the Coaches Poll."}, headers=auth_headers)
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["qa_status"] == "PASSED"
    assert body["question_count"] > 0
    assert "Coaches Poll" in body["questions"][0]["question"]
