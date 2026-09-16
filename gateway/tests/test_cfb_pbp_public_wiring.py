"""Existing-Data Wiring pass (Phase 3, CFB play-by-play): public-route
wiring for CFB_GAME_BOXSCORE/HAD_MORE_SACKS (mode id
cfb_game_boxscore_sacks_guess) -- mirrors test_cfb_betting_cover.py's real
end-to-end pattern.
"""
from gateway import config


def test_public_mode_on_the_allowlist():
    assert "cfb_game_boxscore_sacks_guess" in config.PUBLIC_MODE_ALLOWLIST


def test_public_route_real_fetch_and_answer_roundtrip(client):
    r = client.get("/v1/public/game", params={"mode": "cfb_game_boxscore_sacks_guess", "seed": "pytest-cfb-pbp-1"})
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == "cfb_game_boxscore_sacks_guess"
    assert len(body["payload"]["options"]) == 2
    assert len(set(body["payload"]["options"])) == 2

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
            "WHERE capability_id = 'CFB_GAME_BOXSCORE__HAD_MORE_SACKS'"
        ).fetchone()
    finally:
        c.close()
    assert row is not None
    assert row["verification_status"] == "PUBLIC_ENABLED"
    assert row["public_availability"] == "PUBLIC_ENABLED"
