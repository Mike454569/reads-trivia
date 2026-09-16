"""Existing-Data Wiring pass (5/5): CFB Betting Lines -- first new capability
built on `cfb_betting_lines` (37,015 rows) beyond the existing
CFB_UPSET/BETTING_UPSET (outright-win) capability.

tools/quiz_export/cfb_betting_facts.py already had a correct, tested
`spread_result()`/`total_result()` computation but was wired into nothing
beyond its own test. tools/quiz_export/adapters/cfb_betting_cover.py reuses
that same real cover-margin math to build a real "who covered the spread"
guess capability (CFB_BETTING/COVERED_SPREAD), walked through the FULL real
capability_catalog lifecycle (DISCOVERED -> ... -> PUBLIC_ENABLED, with a
genuine passing Tier-2 100-round probe, not a shortcut), and made public.

Real finding this pass: a brand-new domain also needs adding to
tools/director_v02/schema.py's ALLOWED_DOMAINS/ALLOWED_PREDICATES (a
separate, hardcoded validator allowlist, regenerated via
generate_schema_and_prompt.py from the real capability_catalog -- NOT
auto-derived from registry.py alone) or the public route 503s with
BLOCKED_INVALID_SPEC despite every other gate (registry, capability_catalog,
PUBLIC_MODES, PUBLIC_MODE_ALLOWLIST, fly.toml) being correctly wired --
caught by actually calling the real public route, not assumed safe from the
adapter-level test alone.
"""
import pytest

from tools import game_director_v01 as v01
from tools.quiz_export.adapters import cfb_betting_cover as adapter
from tools.director_v02.providers.mock import MockDeterministicTranslator
from tools.director_v02 import registry, schema


def _generate(provider=None, target_count=10, seed="test-betting-cover"):
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_betting_line",
        "relationship_predicate": "COVERED_SPREAD", "object_type": "school", "answer_type": "school",
        "group_size": 2, "filters": {"provider": provider} if provider else {},
    }
    return v01.generate_package_from_spec(
        spec, adapter, request_text="test:betting_cover", director_request_id="test",
        seed=seed, target_count=target_count, id_start=1, freeze_timestamp=None, difficulty_filter=None,
    )


def test_generates_real_questions_with_default_consensus_provider():
    pkg = _generate()
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 10
    q = pkg["questions"][0]
    assert "consensus" in q["question"]
    assert len(set(q["options"])) == 2
    assert q["answer"] in q["options"]


def test_pushes_are_excluded_never_guessed_at():
    pkg = _generate(target_count=200)
    for q in pkg["questions"]:
        # A push has no real cover winner -- PUSH_NO_COVER_WINNER rejects
        # it in evaluate(), so it must never reach an exported question.
        assert "push" not in q["notes"].lower()


def test_grading_logic_is_self_consistent_across_a_real_sample():
    pkg = _generate(target_count=100)
    for q in pkg["questions"]:
        favorite, underdog = q["options"][0], q["options"][1]
        assert q["answer"] in (favorite, underdog)


@pytest.mark.parametrize("provider", ["Bovada", "DraftKings", "ESPN Bet"])
def test_explicit_provider_filter_scopes_to_that_provider_only(provider):
    pkg = _generate(provider=provider, target_count=20)
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    for q in pkg["questions"]:
        assert provider in q["question"]


# --- NL routing (Phase 6) ----------------------------------------------------

def test_nl_translator_routes_cover_the_spread_phrasing():
    r = MockDeterministicTranslator().translate("Give me a game about teams covering the spread.")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "CFB_BETTING"
    assert r["spec"]["relationship_predicate"] == "COVERED_SPREAD"


def test_nl_translator_still_routes_outright_upset_phrasing_unchanged():
    # Regression guard: adding COVERED_SPREAD must never shadow the
    # existing, separate BETTING_UPSET ("won outright") capability.
    r = MockDeterministicTranslator().translate("Make a game about underdogs that won outright.")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "CFB_UPSET"
    assert r["spec"]["relationship_predicate"] == "BETTING_UPSET"


# --- registry / catalog / schema consistency ---------------------------------

def test_registered_in_capability_registry():
    cap = registry.lookup("guess", "CFB_BETTING", "COVERED_SPREAD")
    assert cap is not None
    assert cap["adapter"] is adapter


def test_domain_and_predicate_in_schema_allowlists():
    # The real gap this pass found: a brand-new domain must be added to
    # schema.py's ALLOWED_DOMAINS/ALLOWED_PREDICATES (regenerated from the
    # capability_catalog) or the public route 503s with BLOCKED_INVALID_SPEC
    # even though every other gate is correctly wired.
    assert "CFB_BETTING" in schema.ALLOWED_DOMAINS
    assert "COVERED_SPREAD" in schema.ALLOWED_PREDICATES


def test_capability_catalog_row_is_public_enabled():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        row = c.execute(
            "SELECT verification_status, public_availability FROM capability_catalog "
            "WHERE capability_id = 'CFB_BETTING__COVERED_SPREAD'"
        ).fetchone()
    finally:
        c.close()
    assert row is not None
    assert row["verification_status"] == "PUBLIC_ENABLED"
    assert row["public_availability"] == "PUBLIC_ENABLED"


# --- real public route end-to-end --------------------------------------------

def test_public_route_real_fetch_and_answer_roundtrip(client):
    r = client.get("/v1/public/game", params={"mode": "cfb_betting_cover_guess", "seed": "pytest-betting-cover-1"})
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == "cfb_betting_cover_guess"
    assert len(body["payload"]["options"]) == 2

    r2 = client.post("/v1/public/game/answer", json={"game_id": body["game_id"], "answer": "Definitely Not A Real Team"})
    assert r2.status_code == 200
    assert r2.json()["correct"] is False
    canonical = r2.json()["canonical_answer"]
    assert canonical in body["payload"]["options"]

    r3 = client.post("/v1/public/game/answer", json={"game_id": body["game_id"], "answer": canonical})
    assert r3.json()["correct"] is True


def test_public_mode_on_the_allowlist():
    from gateway import config
    assert "cfb_betting_cover_guess" in config.PUBLIC_MODE_ALLOWLIST


def test_provider_in_the_global_schema_filter_allowlist():
    # Same real bug class as CFB_RANKING's "poll" filter (see
    # test_cfb_ranking_poll_expansion.py's own test for the full
    # writeup) -- schema.py's ALLOWED_FILTER_KEYS is a separate,
    # hand-maintained global gate a capability's own supported_filter_keys
    # does not substitute for. Added preemptively (no current NL phrase
    # triggers an explicit-provider request yet) so an explicit-provider
    # request never hits BLOCKED_UNSUPPORTED_FILTER the first time one is
    # actually made.
    from tools.director_v02 import schema
    assert "provider" in schema.ALLOWED_FILTER_KEYS
