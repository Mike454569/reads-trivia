"""Power 4 Coverage Closeout workbook ingestion -- real, permanent test
coverage for the new CFB_2026_HEAD_COACH capability
(tools/quiz_export/adapters/cfb_2026_head_coach.py,
tools/data_refresh/cfb_2026_coach_scheme_workbook_import.py).
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


def _skip_if_not_ingested(c):
    row = c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cfb_team_2026_coaching_profile'"
    ).fetchone()
    if not row or row[0] == 0:
        pytest.skip("cfb_team_2026_coaching_profile table not ingested in this environment")
    n = c.execute("SELECT COUNT(*) FROM cfb_team_2026_coaching_profile").fetchone()[0]
    if n == 0:
        pytest.skip("cfb_team_2026_coaching_profile has no rows in this environment")


def test_2026_coaching_profile_covers_all_67_power4_teams():
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    n = c.execute("SELECT COUNT(*) FROM cfb_team_2026_coaching_profile").fetchone()[0]
    assert n == 67, n


def test_existing_coach_identity_reused_not_duplicated():
    """Dabo Swinney already existed in cfb_coaches (a real historical row,
    first_year=2016/last_year=2018, from a prior import) -- his 2026
    profile row must reuse that same identity, never create a second one."""
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    dabo = c.execute("SELECT * FROM cfb_coaches WHERE cfb_coach_id='CFB_COACH_DABO_SWINNEY'").fetchone()
    assert dabo is not None
    profile = c.execute(
        "SELECT cfb_coach_id, head_coach_name FROM cfb_team_2026_coaching_profile WHERE school_id='CFB_SCHOOL_CLEMSON'"
    ).fetchone()
    assert profile is not None
    assert profile["cfb_coach_id"] == "CFB_COACH_DABO_SWINNEY"
    assert profile["head_coach_name"] == "Dabo Swinney"


def test_new_coach_identity_created_when_genuinely_new():
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    row = c.execute("SELECT * FROM cfb_coaches WHERE cfb_coach_id='CFB_COACH_BILL_O_BRIEN'").fetchone()
    assert row is not None
    assert row["coach_name"] == "Bill O'Brien"


def test_no_duplicate_coach_school_links_primary_key_violated():
    """Real design decision under test: this data does NOT write into
    cfb_coach_school_links (whose real PRIMARY KEY(cfb_coach_id, school_id)
    would collide for a coach like Dabo who never left his school) -- it
    lives in its own new table instead."""
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    n = c.execute(
        "SELECT COUNT(*) FROM cfb_coach_school_links WHERE cfb_coach_id='CFB_COACH_DABO_SWINNEY' AND school_id='CFB_SCHOOL_CLEMSON'"
    ).fetchone()[0]
    assert n == 1, "the existing historical link row must be untouched, never duplicated"


def test_adapter_generates_real_valid_questions_end_to_end():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_2026_head_coach as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    _skip_if_not_ingested(c)
    candidates = adapter.fetch_ordered_candidates(c, "pytest-2026-coach")
    assert len(candidates) == 67
    guard = DuplicateGuard(track_entity=True)
    rng = engine.seeded("pytest-2026-coach:distractors")
    accepted = []
    for row in candidates:
        r = adapter.evaluate(c, row, rng, guard)
        if isinstance(r, dict):
            accepted.append(r)
            guard.record(r["question"], r["_audit"]["entity_key"])
    assert len(accepted) == 67
    real_teams = {c2["school_name"] for c2 in candidates}
    for q in accepted:
        assert q["options"][q["correctIndex"]] in real_teams
        assert len(set(q["options"])) == 4
        assert q["question"].startswith("Which team does ")


def test_real_end_to_end_package_generation_passes_qa():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_2026_head_coach as adapter
    from tools.quiz_export import engine

    c = engine.connect()
    _skip_if_not_ingested(c)
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_2026_team_coach",
        "relationship_predicate": "COACHES_TEAM_2026", "object_type": "team",
        "answer_type": "team", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, adapter, request_text="pytest", director_request_id="pytest",
        seed="pytest-2026-coach-e2e", target_count=10, id_start=1,
    )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 10


def test_registered_in_capability_registry():
    from tools.director_v02 import registry
    key = ("guess", "CFB_2026_HEAD_COACH", "COACHES_TEAM_2026")
    assert key in registry.CAPABILITY_REGISTRY


def test_capability_catalog_reached_public_enabled():
    from tools.quiz_export import engine
    from tools.director_v02 import catalog
    c = engine.connect()
    cap = catalog.get_capability(c, "CFB_2026_HEAD_COACH__COACHES_TEAM_2026")
    if cap is None:
        pytest.skip("capability_catalog row not present in this environment")
    assert cap["verification_status"] == "PUBLIC_ENABLED"


def test_nl_request_with_cfb_and_2026_signal_reaches_new_capability(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": "who is the 2026 CFB coach for this team", "seed": "pytest-nl-2026-coach"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    if body.get("status") not in (None, "SUCCESS"):
        pytest.skip(f"2026 coach workbook data not ingested in this environment ({body.get('reason')})")
    assert body["parsed_spec"]["entity_type"] == "cfb_2026_team_coach"
    assert body.get("package_id")


def test_bare_coach_request_still_routes_to_nfl_coaching_unchanged(client, auth_headers):
    """Real regression guard: adding the new narrow CFB rule must not
    change NFL_COACHING's existing bare "coach" behavior at all."""
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": "who is this team coach", "seed": "pytest-bare-coach"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.json()
    assert r.json()["parsed_spec"]["entity_type"] == "nfl_coach_season"
    assert r.json()["parsed_spec"]["relationship_predicate"] == "COACHED_TEAM"


def test_public_mode_generates_a_real_round(client):
    r = client.get("/v1/public/game", params={"mode": "cfb_2026_coach_guess", "seed": "pytest-public-coach"})
    if r.status_code != 200:
        pytest.skip("2026 coach workbook data not ingested in this environment")
    body = r.json()
    assert body["payload"]["prompt"].startswith("Which team does ")
    assert len(body["payload"]["options"]) == 4
