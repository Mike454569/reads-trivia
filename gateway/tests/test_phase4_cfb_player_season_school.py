"""Reliability-design Phase 4 -- CFB Player + Season -> School vertical
slice acceptance tests. Mirrors Phase 3's required test list, against the
real, live Engine DB -- no mocking of the compiler/adapter/generation path.
This is also the second proof of tools/director_v02/compiler.py's
generalization claim.
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

TRIPLE = ("guess", "CFB_PLAYER_SEASON", "SCHOOL_OF_SEASON")


def _generate(target_count: int, seed: str):
    from tools.director_v02 import registry

    cap = registry.CAPABILITY_REGISTRY[TRIPLE]
    validated_spec = {
        "mechanic": "guess", "domain": "CFB_PLAYER_SEASON", "relationship_predicate": "SCHOOL_OF_SEASON",
        "question_count": target_count, "difficulty": "any", "filters": {}, "exclusions": [],
    }
    return registry._generate_guess_package(
        validated_spec, cap, request_text="phase 4 acceptance test", director_request_id="phase4-test",
        seed=seed, target_count=target_count, id_start=1, freeze_timestamp=None,
    )


def _fetch_row_directly(c, player_name: str, season: int) -> dict:
    """Real, targeted lookup bypassing fetch_ordered_candidates()'s
    max_fetched_candidates cap (a real, measured performance bound over
    this capability's ~270K-row pool -- see compiler.py's own docstring --
    that makes fetch_ordered_candidates() a random SAMPLE, not guaranteed
    to include any one specific real row for an arbitrary seed). evaluate()
    only needs a real row shaped the same way fetch_ordered_candidates()'s
    rows are -- this queries the exact same real tables directly for one
    specific, real, already-known-single-school player-season."""
    row = c.execute(
        """
        SELECT r.season AS season, r.school_id AS team_code, r.cfb_player_id AS entity_id,
               cp.display_name AS entity_name, r.verification_status AS verification_status,
               r.source_id AS source_id
        FROM cfb_roster_seasons_real r
        JOIN canonical_cfb_players cp ON cp.cfb_player_id = r.cfb_player_id
        WHERE cp.display_name = ? AND r.season = ?
        """,
        (player_name, season),
    ).fetchone()
    assert row is not None, f"no real row for {player_name!r} season {season}"
    return row


# --- Primary example: Tim Tebow, 2007 -> Florida ----------------------------

def test_tim_tebow_2007_resolves_to_florida():
    from tools.quiz_export import duplicates
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        match = _fetch_row_directly(c, "Tim Tebow", 2007)
        guard = duplicates.DuplicateGuard(track_entity=True)
        rng = engine_bootstrap.seeded("tebow-2007-test:distractors")
        result = pst.evaluate(c, match, rng, guard)
        assert result["options"][result["correctIndex"]] == "Florida"
        assert result["_audit"]["correct_answer_text"] == "Florida"
        assert result["question"] == "Which CFB school was Tim Tebow on during the 2007 season?"
        assert "played for" not in result["question"].lower()
        assert result["_audit"]["evidence_type"] == "ROSTER_MEMBERSHIP"
        assert result["_audit"]["season_status"] == "COMPLETE"
    finally:
        c.close()


# --- Historical and recent seasons work --------------------------------------

@pytest.mark.parametrize("season,player_name,expected_school", [
    (2007, "Tim Tebow", "Florida"),          # historical
    (2010, "Cam Newton", "Auburn"),           # historical
    (2020, "Trevor Lawrence", "Clemson"),      # recent
])
def test_historical_and_recent_seasons_both_work(season, player_name, expected_school):
    from tools.quiz_export import duplicates
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        match = _fetch_row_directly(c, player_name, season)
        guard = duplicates.DuplicateGuard(track_entity=True)
        rng = engine_bootstrap.seeded(f"cfb-season-test-{season}:distractors")
        result = pst.evaluate(c, match, rng, guard)
        assert result["options"][result["correctIndex"]] == expected_school
    finally:
        c.close()


# --- Multi-school seasons excluded with an explicit, counted reason --------

def test_multi_school_seasons_are_excluded_with_an_explicit_reason():
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        # Ahmari Huggins-Bruce, 2024: real, verified multi-school season.
        raw = c.execute(
            "SELECT DISTINCT school_id FROM cfb_roster_seasons_real WHERE cfb_player_id='ESPN_CFB:4431338' AND season=2024"
        ).fetchall()
        assert {r["school_id"] for r in raw} == {"CFB_SCHOOL_LOUISVILLE", "CFB_SCHOOL_SOUTH_CAROLINA"}

        rows = pst.fetch_ordered_candidates(c, "cfb-multischool-test")
        assert not any(r["entity_id"] == "ESPN_CFB:4431338" and r["season"] == 2024 for r in rows)
        assert pst.multi_team_exclusions() > 0
    finally:
        c.close()


# --- Same-name collisions cannot produce a silent incorrect match ----------

def test_caleb_williams_2023_five_way_collision_is_excluded():
    """A real, dramatic case: 5 distinct real players named 'Caleb Williams'
    were active in CFB in 2023 (Furman, Lamar, Pittsburgh, Tennessee, USC --
    including the real 2022 Heisman Trophy winner at USC; Jayden Daniels,
    not Caleb Williams, won the 2023 Heisman). None may appear as a
    generated candidate."""
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        ids = {
            r["cfb_player_id"] for r in c.execute(
                "SELECT DISTINCT cfb_player_id FROM canonical_cfb_players WHERE display_name='Caleb Williams'"
            ).fetchall()
        }
        real_collision_ids = {
            r["cfb_player_id"] for r in c.execute(
                "SELECT DISTINCT cfb_player_id FROM cfb_roster_seasons_real WHERE season=2023 AND cfb_player_id IN ({})".format(
                    ",".join("?" for _ in ids)
                ),
                tuple(ids),
            ).fetchall()
        }
        assert len(real_collision_ids) >= 5  # confirms this really is a live, 5-way collision

        rows = pst.fetch_ordered_candidates(c, "cfb-collision-test")
        matches = [r for r in rows if r["entity_name"] == "Caleb Williams" and r["season"] == 2023]
        assert matches == []
        assert pst.name_collision_exclusions() > 0
    finally:
        c.close()


# --- Unknown player-seasons fail cleanly ------------------------------------

def test_unknown_player_season_fails_cleanly():
    c = engine_bootstrap.connect()
    try:
        row = c.execute(
            "SELECT * FROM cfb_roster_seasons_real WHERE cfb_player_id='NOT_A_REAL_CFB_PLAYER_ID_XYZ' AND season=2020"
        ).fetchone()
        assert row is None
    finally:
        c.close()


# --- 100 real generation executions; uniqueness/pool reported independently

def test_100_generation_executions_succeed_with_independent_pool_reporting():
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[TRIPLE]
    try:
        result = health_probe.run_tier2_certification(
            c, "TEST_PHASE4_TIER2", "guess", "CFB_PLAYER_SEASON", "SCHOOL_OF_SEASON", cap,
        )
        checks = result["checks"]
        assert result["passed"] is True, result
        assert checks["generation_attempts"] == 100
        assert checks["successful_generations"] == 100
        assert checks["eligible_pool_size"] > 200_000
        assert checks["unique_questions_exercised"] == 100
        assert checks["test_sample_rate"] < 0.01
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id='TEST_PHASE4_TIER2'")
        c.commit()
        c.close()


def test_eligibility_report_matches_real_verified_figures():
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        pst.fetch_ordered_candidates(c, "cfb-eligibility-report-test")
        report = pst.eligibility_report()
        assert report["raw_candidate_count"] == 281_838
        assert report["eligible_candidate_count"] == 269_882
        assert report["excluded_candidate_count"] == 11_956
        assert report["excluded_breakdown"]["multi_team_exclusions"] == 284
        assert report["excluded_breakdown"]["name_collision_exclusions"] == 11_672
        assert report["excluded_breakdown"]["future_season_exclusions"] == 0
        assert report["eligible_candidate_count"] + report["excluded_candidate_count"] == report["raw_candidate_count"]
    finally:
        c.close()


# --- Season completeness: aggregate_presence strategy -----------------------

def test_season_status_uses_aggregate_presence_not_a_fixed_week_floor():
    """Real, checked design choice (avoiding the exact flaw flagged for the
    NFL capability): CFB completeness is real presence in cfb_school_seasons
    (an aggregate-outcomes table), not a fixed week-count floor -- CFB has
    no single real per-season week count across divisions/formats."""
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        for season in (2004, 2010, 2020, 2025):  # 2020: the real COVID-shortened season
            assert pst.season_status(c, season) == "COMPLETE"
        assert c.execute("SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season=2026").fetchone()[0] == 0
        assert pst.season_status(c, 2026) == "FUTURE"
    finally:
        c.close()


def test_future_season_2026_is_excluded_from_the_pool():
    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        rows = pst.fetch_ordered_candidates(c, "cfb-future-season-test")
        assert not any(r["season"] == 2026 for r in rows)
    finally:
        c.close()


# --- Multiple complete games/rounds -----------------------------------------

def test_multiple_consecutive_games_generate_successfully():
    for i in range(3):
        pkg = _generate(10, seed=f"cfb-consecutive-game-{i}")
        assert pkg["qa_status"] == "PASSED"
        assert pkg["question_count"] == 10
        assert len(pkg["questions"]) == 10


def test_multiple_consecutive_rounds_within_one_game():
    pkg = _generate(20, seed="cfb-consecutive-rounds")
    assert pkg["qa_status"] == "PASSED"
    questions = pkg["questions"]
    assert len(questions) == 20
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3


# --- Correct and incorrect submissions score properly ------------------------

def _normalize(s: str) -> str:
    return s.strip().lower()


def test_correct_and_incorrect_submissions_score_properly():
    pkg = _generate(10, seed="cfb-answer-scoring-test")
    for q in pkg["questions"]:
        correct_label = q["options"][q["correctIndex"]]
        wrong_label = next(o for o in q["options"] if o != correct_label)
        assert _normalize(correct_label) == _normalize(q["answer"])
        assert _normalize(wrong_label) != _normalize(q["answer"])
        assert _normalize(f"  {correct_label.upper()}  ") == _normalize(q["answer"])


# --- No answer/answer-derived data appears in client payloads --------------

def test_no_answer_data_leaks_into_a_client_safe_payload():
    from tools.director_v02 import round_serialization

    pkg = _generate(10, seed="cfb-leakage-test")
    for q in pkg["questions"]:
        client_payload = {
            "prompt": q["question"],
            "options": list(q["options"]),
            "visual_template": q.get("visual_template"),
            "visual_payload": q.get("visual_payload"),
        }
        round_serialization.assert_no_leaked_fields(client_payload)
        assert "correctIndex" not in client_payload
        assert "answer" not in client_payload


def test_no_generated_question_ever_says_played_for():
    pkg = _generate(50, seed="cfb-no-played-for-check")
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        assert "played for" not in q["question"].lower()
        assert q["provenance"]["evidence_type"] == "ROSTER_MEMBERSHIP"


# --- Registry/catalog consistency + Creator interpretation -----------------

def test_registry_consistency_passes_for_the_new_capability():
    from tools.director_v02 import catalog

    result = catalog.verify_registry_consistency("CFB_PLAYER_SEASON__SCHOOL_OF_SEASON")
    assert result["ok"] is True, result


def test_creator_interpretation_routes_a_real_cfb_request():
    from tools.director_v02 import feasibility

    result = feasibility.assess(
        "Make a guessing game where I see a CFB college football player and season and "
        "have to guess which school he was on that season."
    )
    assert result["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert result["capability"]["domain"] == "CFB_PLAYER_SEASON"
    assert result["capability"]["relationship_predicate"] == "SCHOOL_OF_SEASON"
    assert result["catalog_status"] == "GENERATION_VERIFIED"


def test_translator_does_not_hijack_existing_nfl_or_cfb_transfer_requests():
    from tools.director_v02 import translator

    nfl = translator.translate(
        "Make a guessing game where I see an NFL player and season and have to guess which "
        "team he played for that season."
    )
    assert nfl["spec"]["domain"] == "NFL_PLAYER_SEASON"

    draft = translator.translate(
        "Make a guessing game where I see an NFL player and have to guess which team drafted him."
    )
    assert draft["spec"]["domain"] == "NFL_DRAFT"

    transfer = translator.translate("Guess which school this transfer player played for.")
    assert transfer["spec"]["domain"] == "CFB_TRANSFER"


# --- Private preview through the real Gateway HTTP routes (admin-only) -----

CFB_PLAYER_SEASON_REQUEST = (
    "Make a guessing game where I see a CFB college football player and season and have to "
    "guess which school he was on that season."
)


def test_private_preview_full_lifecycle_through_real_gateway_routes(client, auth_headers):
    feas = client.post("/v1/creator/feasibility", json={"request_text": CFB_PLAYER_SEASON_REQUEST}, headers=auth_headers)
    assert feas.status_code == 200
    assert feas.json()["support_status"] == "SUPPORTED_WITH_LIMITATIONS"

    gen = client.post(
        "/v1/creator/generate",
        json={"request_text": CFB_PLAYER_SEASON_REQUEST, "puzzle_count": 5, "seed": "pytest-phase4-preview-1"},
        headers=auth_headers,
    )
    assert gen.status_code == 200
    body = gen.json()
    assert body["qa_status"] == "PASSED"
    assert body["review_status"] == "GENERATED"
    pid = body["package_id"]

    loaded = client.get(f"/v1/games/{pid}", headers=auth_headers)
    assert loaded.status_code == 200
    assert len(loaded.json()["questions"]) == 5

    approve = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "APPROVED"}, headers=auth_headers)
    assert approve.status_code == 200
    assert approve.json()["review_status"] == "APPROVED"


def test_capability_appears_in_creator_capabilities_listing(client, auth_headers):
    r = client.get("/v1/creator/capabilities", headers=auth_headers)
    assert r.status_code == 200
    caps = {c["relationship_predicate"]: c for c in r.json()["capabilities"]}
    assert "SCHOOL_OF_SEASON" in caps
    assert caps["SCHOOL_OF_SEASON"]["domain"] == "CFB_PLAYER_SEASON"
    assert caps["SCHOOL_OF_SEASON"]["support_status"] == "SUPPORTED_WITH_LIMITATIONS"


def test_private_preview_routes_still_require_admin(client):
    r = client.post("/v1/creator/generate", json={"request_text": CFB_PLAYER_SEASON_REQUEST})
    assert r.status_code == 401


def test_max_fetched_candidates_bounds_performance_without_lying_about_eligibility():
    """Real, measured fix: this capability's real eligible pool (269,882)
    made a single target_count=5 generation call take 116s before this cap
    (confirmed by direct timing) -- RelationshipSpec.max_fetched_candidates
    bounds the per-call evaluate() workload to a real, still-huge random
    sample, but eligibility_report() and health_probe's eligible_pool_size
    must keep reporting the TRUE, uncapped eligible count, never the
    smaller sample size."""
    import time

    from tools.quiz_export.adapters import cfb_player_season_school as pst

    c = engine_bootstrap.connect()
    try:
        assert pst.SPEC.max_fetched_candidates == 5000

        t0 = time.time()
        rows = pst.fetch_ordered_candidates(c, "cap-mechanism-test")
        elapsed = time.time() - t0
        assert len(rows) == 5000  # the cap, not the true eligible count
        assert elapsed < 15  # was 116s+ before the cap

        report = pst.eligibility_report()
        assert report["eligible_candidate_count"] == 269_882  # true count, unaffected by the cap
    finally:
        c.close()


def test_health_probe_reports_true_eligible_pool_not_the_capped_sample():
    from tools.director_v02 import health_probe, registry

    c = engine_bootstrap.connect()
    cap = registry.CAPABILITY_REGISTRY[TRIPLE]
    try:
        result = health_probe.run_tier2_certification(
            c, "TEST_CAP_MECHANISM", "guess", "CFB_PLAYER_SEASON", "SCHOOL_OF_SEASON", cap,
        )
        assert result["passed"] is True, result
        assert result["checks"]["eligible_pool_size"] == 269_882  # true count
        assert result["checks"]["exported_count"] == 5000  # the per-call capped sample
    finally:
        c.execute("DELETE FROM capability_health_probes WHERE capability_id='TEST_CAP_MECHANISM'")
        c.commit()
        c.close()


def test_compiler_generalization_proof_same_module_different_spec():
    """Direct proof the compiler generalizes: the NFL and CFB adapters both
    instantiate compiler.compile_adapter() from the same module, with
    different RelationshipSpecs, and both produce real, working, distinctly-
    behaving adapters."""
    from tools.director_v02 import compiler
    from tools.quiz_export.adapters import player_season_team as nfl_pst
    from tools.quiz_export.adapters import cfb_player_season_school as cfb_pst

    assert isinstance(nfl_pst._adapter, compiler.CompiledAdapter)
    assert isinstance(cfb_pst._adapter, compiler.CompiledAdapter)
    assert nfl_pst.SPEC.identity_resolution_strategy == "team_aliases"
    assert cfb_pst.SPEC.identity_resolution_strategy == "stable_identity_table"
    assert nfl_pst.SPEC.season_completeness_strategy == "weekly_evidence"
    assert cfb_pst.SPEC.season_completeness_strategy == "aggregate_presence"
    assert nfl_pst.SPEC.object_label == "team"
    assert cfb_pst.SPEC.object_label == "school"
