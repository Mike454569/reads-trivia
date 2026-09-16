"""Existing-Data Wiring pass (4/5): public-route wiring for the new
CROSS_LEAGUE_HONORS/ALL_AMERICAN_TO_NFL_DRAFT_TEAM capability -- mirrors
test_cfb_betting_cover.py's real end-to-end pattern (mode id
cfb_all_america_draft_team_guess).
"""
from gateway import config


def test_public_mode_on_the_allowlist():
    assert "cfb_all_america_draft_team_guess" in config.PUBLIC_MODE_ALLOWLIST


def test_public_route_real_fetch_and_answer_roundtrip(client):
    r = client.get("/v1/public/game", params={"mode": "cfb_all_america_draft_team_guess", "seed": "pytest-aa-draft-1"})
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == "cfb_all_america_draft_team_guess"
    assert len(body["payload"]["options"]) == 4
    assert len(set(body["payload"]["options"])) == 4

    r2 = client.post("/v1/public/game/answer", json={"game_id": body["game_id"], "answer": "Definitely Not A Real Team"})
    assert r2.status_code == 200
    assert r2.json()["correct"] is False
    canonical = r2.json()["canonical_answer"]
    assert canonical in body["payload"]["options"]

    r3 = client.post("/v1/public/game/answer", json={"game_id": body["game_id"], "answer": canonical})
    assert r3.json()["correct"] is True


def test_capability_catalog_row_is_public_enabled():
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        row = c.execute(
            "SELECT verification_status, public_availability FROM capability_catalog "
            "WHERE capability_id = 'CROSS_LEAGUE_HONORS__ALL_AMERICAN_TO_NFL_DRAFT_TEAM'"
        ).fetchone()
    finally:
        c.close()
    assert row is not None
    assert row["verification_status"] == "PUBLIC_ENABLED"
    assert row["public_availability"] == "PUBLIC_ENABLED"
