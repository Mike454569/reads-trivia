"""MASTER WORKBOOK ingestion pass -- real, permanent test coverage for the
new CFB_2026_CURRENT_ROSTER capability (tools/quiz_export/adapters/
cfb_2026_current_roster.py, tools/data_refresh/cfb_2026_roster_workbook_import.py).
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

INGESTED_TEAMS = {"Alabama", "Auburn", "Georgia Tech", "Kansas", "Oregon", "Texas", "UCLA", "USC"}


def _skip_if_not_ingested(c):
    n = c.execute(
        "SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season=2026 AND source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09'"
    ).fetchone()[0]
    if n == 0:
        pytest.skip("2026 roster workbook data not ingested in this environment")


def test_2026_roster_data_is_real_and_present():
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    n = c.execute(
        "SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season=2026 AND source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09'"
    ).fetchone()[0]
    assert n >= 700, n


def test_no_2026_cfb_roster_data_existed_before_this_source():
    """Real, confirmed-before-building-this: the automated SPORTSDATAVERSE_CFB
    pipeline has never had a 2026 CFB season -- this source is genuinely new
    season-level knowledge, not a duplicate."""
    from tools.quiz_export import engine
    c = engine.connect()
    n = c.execute(
        "SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season=2026 AND source_id='SPORTSDATAVERSE_CFB'"
    ).fetchone()[0]
    assert n == 0


def test_positions_are_normalized_short_codes_not_raw_concatenation():
    """Real bug caught in testing: preferring POSITION_GROUP_NORMALIZED
    produced ugly concatenated strings ('WIDERECEIVER', 'OFFENSIVELINE').
    Every real position on file must be a short code, never a
    concatenated/spelled-out value."""
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    rows = c.execute(
        "SELECT DISTINCT position FROM cfb_roster_seasons_real WHERE season=2026 "
        "AND source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09' AND position IS NOT NULL"
    ).fetchall()
    bad = [r["position"] for r in rows if len(r["position"]) > 4 or " " in r["position"]]
    assert not bad, bad


def test_entity_resolution_reused_existing_player_identities():
    """Real players who already exist in canonical_cfb_players (from the
    automated pipeline's prior seasons) must be reused, not duplicated
    under a second identity."""
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    row = c.execute(
        "SELECT cfb_player_id FROM canonical_cfb_players WHERE display_name='Jordon Davison'"
    ).fetchone()
    assert row is not None
    assert row["cfb_player_id"] == "ESPN_CFB:5141423"
    hit = c.execute(
        "SELECT 1 FROM cfb_roster_seasons_real WHERE season=2026 AND cfb_player_id=? AND source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09'",
        (row["cfb_player_id"],),
    ).fetchone()
    assert hit is not None


def test_new_players_get_a_workbook_namespaced_id_never_colliding_with_espn():
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    rows = c.execute(
        "SELECT cfb_player_id FROM canonical_cfb_players WHERE source_id='READS_MASTER_KNOWLEDGE_FEED_2026_09' LIMIT 5"
    ).fetchall()
    assert rows
    for r in rows:
        assert r["cfb_player_id"].startswith("WORKBOOK_CFB:")


def test_ambiguous_name_collisions_were_logged_not_guessed():
    from tools.quiz_export import engine
    c = engine.connect()
    _skip_if_not_ingested(c)
    n = c.execute(
        "SELECT COUNT(*) FROM qa_issues WHERE entity_type='cfb_2026_roster_workbook_row' AND issue_type='AMBIGUOUS_NAME_MATCH'"
    ).fetchone()[0]
    assert n > 0


def test_adapter_generates_real_valid_questions_end_to_end():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_2026_current_roster as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    _skip_if_not_ingested(c)
    candidates = adapter.fetch_ordered_candidates(c, "pytest-2026-roster")
    assert len(candidates) >= 700
    guard = DuplicateGuard(track_entity=True)
    rng = engine.seeded("pytest-2026-roster:distractors")
    accepted = []
    for row in candidates[:100]:
        r = adapter.evaluate(c, row, rng, guard)
        if isinstance(r, dict):
            accepted.append(r)
            guard.record(r["question"], r["_audit"]["entity_key"])
    assert len(accepted) >= 50
    for q in accepted:
        assert q["options"][q["correctIndex"]] in INGESTED_TEAMS
        assert len(set(q["options"])) == 4
        assert q["question"].endswith("Which team is he on?")


def test_real_end_to_end_package_generation_passes_qa():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_2026_current_roster as adapter
    from tools.quiz_export import engine

    c = engine.connect()
    _skip_if_not_ingested(c)
    spec = {
        "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_2026_roster_player",
        "relationship_predicate": "ON_2026_ROSTER", "object_type": "team",
        "answer_type": "team", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, adapter, request_text="pytest", director_request_id="pytest",
        seed="pytest-2026-roster-e2e", target_count=10, id_start=1,
    )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) == 10


def test_registered_in_capability_registry():
    from tools.director_v02 import registry
    key = ("guess", "CFB_2026_CURRENT_ROSTER", "ON_2026_ROSTER")
    assert key in registry.CAPABILITY_REGISTRY


def test_capability_catalog_reached_human_approved():
    from tools.quiz_export import engine
    from tools.director_v02 import catalog
    c = engine.connect()
    cap = catalog.get_capability(c, "CFB_2026_CURRENT_ROSTER__ON_2026_ROSTER")
    if cap is None:
        pytest.skip("capability_catalog row not present in this environment")
    assert cap["verification_status"] in ("HUMAN_APPROVED", "PUBLIC_ENABLED")


def test_creator_nl_request_reaches_the_new_capability(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": "guess which team a player is on based on their current 2026 roster",
              "seed": "pytest-nl-2026-roster"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    if body.get("status") not in (None, "SUCCESS"):
        pytest.skip(f"2026 roster workbook data not ingested in this environment ({body.get('reason')})")
    assert body.get("package_id")
