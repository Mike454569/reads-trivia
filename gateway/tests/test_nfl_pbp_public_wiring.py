"""Existing-Data Wiring pass: 7 real backend capabilities (nfl_plays/
nfl_plays_defense_ext/nfl_drives_real -- NFL_SCORING_PLAY/FIRST_TOUCHDOWN_
SCORER, NFL_DEFENSIVE_EVENT/{RECORDED_SACK,RECORDED_INTERCEPTION,
FORCED_FUMBLE,RECOVERED_FUMBLE}, NFL_DRIVE/DRIVE_RESULT, NFL_GAME_BOXSCORE/
HAD_MORE_SACKS) that were already built, registered in tools/director_v02/
registry.py, and GENERATION_VERIFIED, but sat unreachable at
public_availability=PRIVATE -- confirmed by direct capability_catalog audit
before this pass (all 7 correctly PRIVATE, since none had a
gateway/services/public_game.py PUBLIC_MODES entry). Real candidate surveys
(target_count=999999 against the real generate_package_from_spec()
pipeline -- the exact function real gameplay uses, not a re-derivation)
found thousands of genuinely well-represented Easy/Medium/Hard candidates
for every one of the 7 -- see public_game.py's own comment block for exact
numbers. Runs against the real Engine database via the real public route,
not mocked.
"""
import pytest

from gateway import config

NEW_MODES = [
    "nfl_first_touchdown_guess", "nfl_sack_guess", "nfl_interception_guess",
    "nfl_forced_fumble_guess", "nfl_fumble_recovery_guess", "nfl_drive_result_guess",
    "nfl_game_boxscore_sacks_guess",
]


def _get(client, mode, **params):
    params["mode"] = mode
    return client.get("/v1/public/game", params=params)


def _answer(client, game_id, answer):
    return client.post("/v1/public/game/answer", json={"game_id": game_id, "answer": answer})


def test_seven_new_nfl_pbp_modes_on_the_allowlist():
    assert set(NEW_MODES) <= config.PUBLIC_MODE_ALLOWLIST


@pytest.mark.parametrize("mode", NEW_MODES)
def test_new_mode_real_fetch_and_answer_roundtrip(client, mode):
    r = _get(client, mode, seed=f"pytest-{mode}-1")
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == mode
    assert len(body["payload"]["options"]) == 4
    assert len(set(body["payload"]["options"])) == 4  # no duplicate options (no multi-valid-answer trap)
    assert body["payload"]["prompt"]  # a real, non-empty question

    r2 = _answer(client, body["game_id"], "Definitely Not A Real Answer")
    assert r2.status_code == 200
    assert r2.json()["correct"] is False
    canonical = r2.json()["canonical_answer"]
    assert canonical in body["payload"]["options"]

    r3 = _answer(client, body["game_id"], canonical)
    assert r3.json()["correct"] is True


@pytest.mark.parametrize("mode", NEW_MODES)
def test_new_mode_certifies_all_three_difficulty_bands(client, mode):
    # Real candidate survey found thousands of accepted candidates in every
    # band for all 7 -- confirm the mode actually SERVES all 3, not just
    # that the survey found them once.
    for difficulty in ("easy", "medium", "hard"):
        r = _get(client, mode, seed=f"pytest-{mode}-{difficulty}", difficulty=difficulty)
        assert r.status_code == 200, (mode, difficulty, r.json())
        assert r.json()["difficulty"].lower() == difficulty


def test_capability_catalog_rows_reflect_public_enabled():
    # recompute_public_availability() must have actually been run against
    # this DB, not just the code-level allowlist updated -- a stale
    # capability_catalog row would make test_public_availability_truth.py
    # fail and would mean this pass's DB-side step was skipped.
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        rows = c.execute(
            "SELECT capability_id, public_availability FROM capability_catalog "
            "WHERE domain IN ('NFL_SCORING_PLAY','NFL_DEFENSIVE_EVENT','NFL_DRIVE','NFL_GAME_BOXSCORE') "
            "AND relationship_predicate IN ('FIRST_TOUCHDOWN_SCORER','RECORDED_SACK','RECORDED_INTERCEPTION',"
            "'FORCED_FUMBLE','RECOVERED_FUMBLE','DRIVE_RESULT','HAD_MORE_SACKS')"
        ).fetchall()
    finally:
        c.close()
    assert len(rows) == 7
    for row in rows:
        assert row["public_availability"] == "PUBLIC_ENABLED", row["capability_id"]
