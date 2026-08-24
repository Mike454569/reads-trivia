"""Tests for the public gameplay API (gateway/services/public_game.py,
gateway/app.py's /v1/public/* routes) -- v1.2 introduced draft_guess, v1.3
adds championship_guess through the same generalized mode registry.

Runs against the real, checksum-verified Reads_v4_Database.sqlite via the
same Director pipeline /v1/games/generate already uses -- not mocked. Every
route here is deliberately called WITHOUT auth_headers (the whole point:
these routes must work with no admin token, unlike every other route in
this Gateway)."""
import json
import time

from gateway import config
from gateway.errors import ERROR_CODES
from gateway.services import packages


def _get_game(client, **params):
    params.setdefault("mode", "draft_guess")
    return client.get("/v1/public/game", params=params)


def _get_champ_game(client, **params):
    params.setdefault("mode", "championship_guess")
    return client.get("/v1/public/game", params=params)


def _get_lineup_game(client, **params):
    params.setdefault("mode", "lineup_guess")
    return client.get("/v1/public/game", params=params)


def _get_heisman_game(client, **params):
    params.setdefault("mode", "cfb_heisman_guess")
    return client.get("/v1/public/game", params=params)


def _get_nfl_game_result_game(client, **params):
    params.setdefault("mode", "nfl_game_result_guess")
    return client.get("/v1/public/game", params=params)


def _get_cfb_game_result_game(client, **params):
    params.setdefault("mode", "cfb_game_result_guess")
    return client.get("/v1/public/game", params=params)


def _get_boxscore_game(client, **params):
    params.setdefault("mode", "nfl_game_boxscore_guess")
    return client.get("/v1/public/game", params=params)


# --- public auth (no admin token needed) -------------------------------------

def test_public_modes_no_auth_needed(client):
    r = client.get("/v1/public/modes")
    assert r.status_code == 200
    modes_by_id = {m["mode"]: m for m in r.json()["modes"]}
    # v1.7, Part C8: Six Degrees composed into the SAME unified list -- see
    # test_six_degrees_mode_registered_alongside_guess_modes below for its
    # own dedicated assertions. v1.8, Part F/O: lineup_guess is the third
    # Director-pipeline guess mode, certified alongside the other two. The
    # CFB data enrichment operation added the fourth (and first CFB) mode.
    # Coach Connections v2 rebuild: "coach_connections" (real graph-driven
    # generation, gateway/services/public_coach_connections.py) REPLACES the
    # old "six_degrees_guess" entry in this list -- same product slot, see
    # app.py's public_modes() docstring.
    # Public-readiness punch-list: lineup_college_guess is the ninth mode --
    # certified public only after the real generation-timeout starvation
    # defect for this domain was fixed and regression-tested (see
    # gateway/tests/test_lineup_starvation_fix.py).
    assert set(modes_by_id) == {
        "draft_guess", "championship_guess", "coach_connections", "lineup_guess", "cfb_heisman_guess",
        "nfl_game_result_guess", "cfb_game_result_guess", "nfl_game_boxscore_guess", "lineup_college_guess",
    }
    draft = modes_by_id["draft_guess"]
    assert draft["competition"] == "NFL"
    assert draft["title"] == "NFL Draft History: Guess the Team"
    assert draft["kind"] == "multiple_choice"
    assert draft["available"] is True
    # Part 20: only real, certified difficulties advertised -- "easy" was
    # surveyed this phase (0/232 real candidates) and must never appear.
    assert set(draft["difficulties"]) == {"medium", "hard", "any"}
    champ = modes_by_id["championship_guess"]
    assert champ["competition"] == "NFL"
    assert champ["kind"] == "multiple_choice"
    assert set(champ["difficulties"]) == {"medium", "hard", "any"}
    lineup = modes_by_id["lineup_guess"]
    assert lineup["competition"] == "NFL"
    assert lineup["kind"] == "multiple_choice"
    # v1.8, Part F: unlike Draft/Championship, this domain genuinely has real
    # "easy" candidates (more recent seasons) -- see public_game.py's own
    # comment for the real survey numbers.
    assert set(lineup["difficulties"]) == {"easy", "medium", "hard", "any"}
    heisman = modes_by_id["cfb_heisman_guess"]
    assert heisman["competition"] == "CFB"
    assert heisman["kind"] == "multiple_choice"
    # Real survey: 91/91 real Heisman winners accepted, zero rejections,
    # genuinely spanning all three bands (Hard 46, Easy 27, Medium 18).
    assert set(heisman["difficulties"]) == {"easy", "medium", "hard", "any"}


def test_public_game_no_auth_needed(client):
    r = _get_game(client)
    assert r.status_code == 200


def test_public_answer_no_auth_needed(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "anything"})
    assert r.status_code == 200


def test_admin_routes_still_require_admin_auth(client):
    # Regression: adding public routes must not have loosened any existing
    # admin route's auth requirement.
    assert client.get("/v1/graph/search", params={"query": "Mahomes"}).status_code == 401
    assert client.get("/v1/grid/criteria").status_code == 401
    assert client.post("/v1/games/generate", json={"request_text": "x"}).status_code == 401


# --- answer leakage -----------------------------------------------------------

def test_game_payload_never_contains_answer(client):
    r = _get_game(client)
    raw = r.text
    body = r.json()
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh /v1/public/game response"
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    # v1.8, Part D/E: visual_template/visual_payload are always present now
    # (defaulting to DEFAULT_MULTIPLE_CHOICE/None for this pre-v1.8 mode) --
    # additive fields, never containing the answer (see the loop above).
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert body["payload"]["visual_template"] == "DEFAULT_MULTIPLE_CHOICE"
    assert body["payload"]["visual_payload"] is None
    assert len(body["payload"]["options"]) == 4


def test_answer_response_reveals_canonical_answer_only_after_guessing(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "anything"})
    body = r.json()
    assert set(body.keys()) == {"correct", "canonical_answer", "notes"}
    assert body["canonical_answer"] in game["payload"]["options"]


# --- answer validation ---------------------------------------------------------

def test_correct_answer_accepted(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_incorrect_answer_rejected(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_answer_case_and_whitespace_insensitive(client):
    game = _get_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "  " + real_answer.upper() + "  "})
    assert r.json()["correct"] is True


# --- game identity / tampering -------------------------------------------------

def test_unknown_game_id_rejected(client):
    r = client.post("/v1/public/game/answer", json={"game_id": "GGP:0000000000000000000000", "answer": "x"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_malformed_game_id_rejected_same_as_unknown(client):
    # Never distinguish "malformed" from "genuinely missing" to the client
    # (same reasoning packages.load_package's own docstring already gives).
    r = client.post("/v1/public/game/answer", json={"game_id": "not-a-real-id-at-all", "answer": "x"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "INVALID_GAME_ID"


def test_answer_request_extra_field_rejected(client):
    game = _get_game(client).json()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x", "score": 100})
    assert r.status_code == 400


# --- mode allow-list -----------------------------------------------------------

def test_unknown_mode_is_invalid_mode(client):
    r = _get_game(client, mode="not_a_real_mode")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_MODE"


def test_known_internal_but_not_public_mode_is_mode_unavailable(client):
    # championship_guess graduated to public in v1.3 (see below) --
    # player_from_clues is the real, registered-but-not-yet-public
    # capability left to exercise this path now.
    r = _get_game(client, mode="player_from_clues")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"


def test_grid_and_six_degrees_are_not_public_modes(client):
    # Part 16/17: neither is migrated in v1.3 -- confirm they're not
    # accidentally reachable as a "mode" through this new surface. (Note:
    # "six_degrees" as a PUBLIC_MODE_ALLOWLIST entry specifically is still
    # correctly absent even though Six Degrees itself did get a real public
    # route in v1.7 -- it's served by a structurally separate system,
    # public_six_degrees.py, never folded into this Director-pipeline
    # registry -- see that module's own docstring.)
    assert "grid" not in config.PUBLIC_MODE_ALLOWLIST
    assert "six_degrees" not in config.PUBLIC_MODE_ALLOWLIST
    # Public-readiness punch-list: lineup_college_guess added, certified
    # only after its real starvation defect was fixed and regression-tested.
    assert config.PUBLIC_MODE_ALLOWLIST == frozenset({
        "draft_guess", "championship_guess", "lineup_guess", "cfb_heisman_guess",
        "nfl_game_result_guess", "cfb_game_result_guess", "nfl_game_boxscore_guess",
        "lineup_college_guess",
    })


# --- determinism ----------------------------------------------------------------

def test_same_seed_same_mode_returns_same_game(client):
    g1 = _get_game(client, seed="pytest-fixed-seed-1").json()
    g2 = _get_game(client, seed="pytest-fixed-seed-1").json()
    assert g1["game_id"] == g2["game_id"]
    assert g1["payload"]["prompt"] == g2["payload"]["prompt"]


def test_different_seeds_can_return_different_games(client):
    g1 = _get_game(client, seed="pytest-seed-aaa").json()
    g2 = _get_game(client, seed="pytest-seed-bbb").json()
    assert g1["game_id"] != g2["game_id"]


# --- validation -------------------------------------------------------------

def test_invalid_difficulty_rejected(client):
    r = _get_game(client, difficulty="nonsense")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_missing_mode_param_rejected(client):
    r = client.get("/v1/public/game")
    assert r.status_code == 400


# --- rate limiting ---------------------------------------------------------

def test_rate_limit_enforced_on_public_game(client, monkeypatch):
    from gateway.app import public_game_limiter
    monkeypatch.setattr(public_game_limiter, "max_requests", 3)
    public_game_limiter.reset()
    statuses = [_get_game(client, seed=f"ratelimit-{i}").status_code for i in range(5)]
    assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    public_game_limiter.reset()
    monkeypatch.setattr(public_game_limiter, "max_requests", config.PUBLIC_GAME_RATE_LIMIT_MAX)


def test_public_game_rate_limit_is_shared_across_modes(client, monkeypatch):
    # Part 22: a deliberate, simple design choice -- one bucket per client
    # PER ROUTE, not per (client, mode). /v1/public/game is a single route
    # that happens to take a `mode` query param; both certified modes
    # ultimately call the same single-slot-concurrency-guarded
    # generation.generate() pipeline, so bounding combined draft+
    # championship traffic together is what actually protects that shared
    # resource. A per-mode bucket would let a client double its real
    # generation load by alternating modes -- exactly what this test
    # guards against.
    from gateway.app import public_game_limiter
    monkeypatch.setattr(public_game_limiter, "max_requests", 4)
    public_game_limiter.reset()
    statuses = []
    for i in range(6):
        mode = "draft_guess" if i % 2 == 0 else "championship_guess"
        statuses.append(_get_game(client, mode=mode, seed=f"shared-limit-{i}").status_code)
    assert statuses.count(429) >= 2, f"expected the shared bucket to rate-limit across modes, got {statuses}"
    public_game_limiter.reset()
    monkeypatch.setattr(public_game_limiter, "max_requests", config.PUBLIC_GAME_RATE_LIMIT_MAX)


def test_rate_limit_enforced_on_public_answer(client):
    from gateway.app import public_answer_limiter
    game = _get_game(client).json()
    orig = public_answer_limiter.max_requests
    public_answer_limiter.max_requests = 3
    public_answer_limiter.reset()
    try:
        statuses = [client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"}).status_code for _ in range(5)]
        assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    finally:
        public_answer_limiter.reset()
        public_answer_limiter.max_requests = orig


# --- CORS ---------------------------------------------------------------------

def test_production_reads_origin_is_allowed_by_default(client):
    r = client.options("/v1/public/game", headers={
        "Origin": "https://reads.football",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") == "https://reads.football"


def test_untrusted_origin_not_reflected(client):
    r = client.options("/v1/public/game", headers={
        "Origin": "https://evil-scraper.example.com",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") != "https://evil-scraper.example.com"


# --- error contract never leaks internals --------------------------------------

def test_public_errors_never_contain_admin_secret(client, auth_headers):
    r = client.post("/v1/public/game/answer", json={"game_id": "GGP:0000000000000000000000", "answer": "x"})
    raw = r.text
    assert auth_headers["Authorization"].split(" ")[1] not in raw
    assert "sqlite" not in raw.lower()
    assert "/Users/" not in raw


def test_new_error_codes_registered():
    assert {"INVALID_MODE", "MODE_UNAVAILABLE", "NO_ELIGIBLE_GAME", "INVALID_GAME_ID", "GAME_EXPIRED"} <= ERROR_CODES


# --- capabilities discovery unaffected -----------------------------------------

def test_capabilities_route_unaffected_by_public_routes(client):
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    # v1.8 added a 4th registered capability, CFB data enrichment a 5th, the
    # App-Wide Engine Migration operation a 6th and 7th, the position+college
    # proof-game fix an 8th, the Historical Engine Enrichment operation a
    # 9th (NFL_GAME_BOXSCORE), the stale-college-feasibility fix a 10th
    # (ATTENDED_COLLEGE), the NFL Wikipedia history import an 11th and 12th
    # (WON_CHAMPIONSHIP/NFL_SUPER_BOWL, WON_AWARD/NFL_AWARDS), the
    # Creator-gap-audit operation nine more, 13th-21st -- see
    # test_gateway.py::test_capabilities_unauthenticated_and_exactly_twenty_one.
    # Rivalry Data + Gold Standard Content Integration operation added 11
    # more, 22nd-32nd, all walked to PUBLIC_ENABLED -- same real reason as
    # that test's sibling assertion.
    assert len(r.json()["capabilities"]) == 32


# --- performance (Part 23, cheap sanity check) ---------------------------------

def test_public_answer_is_fast_no_generation(client):
    game = _get_game(client).json()
    t0 = time.perf_counter()
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"})
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    assert elapsed < 1.0, f"answer validation took {elapsed:.2f}s -- should be a cheap package lookup, not generation"


# --- v1.3: championship_guess, migrated through the same generalized registry --

def test_championship_game_no_auth_needed(client):
    r = _get_champ_game(client)
    assert r.status_code == 200


def test_championship_payload_never_contains_answer(client):
    r = _get_champ_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh championship_guess response"
    body = r.json()
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert len(body["payload"]["options"]) == 4
    assert body["mode"] == "championship_guess"


def test_championship_correct_answer_accepted(client):
    game = _get_champ_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_championship_incorrect_answer_rejected(client):
    game = _get_champ_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


# --- lineup_guess (v1.8, Part F/O) ------------------------------------------

def test_lineup_payload_never_contains_answer_and_carries_a_real_visual_payload(client):
    r = _get_lineup_game(client)
    assert r.status_code == 200
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh lineup_guess response"
    body = r.json()
    assert body["mode"] == "lineup_guess"
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert body["payload"]["visual_template"] == "POSITION_LINEUP"
    positions = body["payload"]["visual_payload"]["positions"]
    assert [p["position"] for p in positions] == ["QB", "RB", "WR", "WR", "TE", "OL", "OL", "OL", "OL", "OL"]
    # The answer team must never appear as one of the player names shown.
    names = {p["name"] for p in positions}
    assert not (names & set(body["payload"]["options"]))


def test_lineup_correct_answer_accepted(client):
    game = _get_lineup_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_lineup_incorrect_answer_rejected(client):
    game = _get_lineup_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False


def test_lineup_easy_difficulty_is_certified_and_works(client):
    # Real difference from Draft/Championship (Part 20/21) -- this domain
    # genuinely has "easy" candidates, so this must NOT be rejected.
    r = _get_lineup_game(client, difficulty="easy")
    assert r.status_code == 200


# --- cfb_heisman_guess (CFB data enrichment operation) -----------------------
# The first CFB public mode -- proves the exact same public API/registry/
# answer-validation code that already serves 3 NFL modes also serves a
# genuinely new CFB domain with zero architectural change.

def test_heisman_game_no_auth_needed(client):
    r = _get_heisman_game(client)
    assert r.status_code == 200


def test_heisman_payload_never_contains_answer(client):
    r = _get_heisman_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh cfb_heisman_guess response"
    body = r.json()
    assert body["mode"] == "cfb_heisman_guess"
    assert body["competition"] == "CFB"
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert body["payload"]["visual_template"] == "DEFAULT_MULTIPLE_CHOICE"
    assert len(body["payload"]["options"]) == 4


def test_heisman_correct_answer_accepted(client):
    game = _get_heisman_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_heisman_incorrect_answer_rejected(client):
    game = _get_heisman_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_heisman_easy_difficulty_is_certified_and_works(client):
    # Real survey: 27/91 real winners graded Easy -- must NOT be rejected.
    r = _get_heisman_game(client, difficulty="easy")
    assert r.status_code == 200


def test_heisman_question_is_a_real_verifiable_fact(client):
    # Spot-check the actual generated prompt shape, and confirm the option
    # set is drawn from real school names -- confirms the real adapter (not
    # a stub) is wired in. A player's own real prompt/answer varies by seed
    # (this seed is not separately hand-verified to a specific winner the
    # way the manual e2e check was) -- the structural checks here are what's
    # actually asserted.
    game = _get_heisman_game(client, seed="test-heisman-real-fact").json()
    assert game["payload"]["prompt"].startswith("Which school did ")
    assert "Heisman Trophy winner" in game["payload"]["prompt"]
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    assert real_answer in game["payload"]["options"]


def test_championship_question_is_a_real_postseason_fact(client):
    # Spot-check the actual generated prompt shape, not just that SOMETHING
    # came back -- confirms the real adapter (not a stub) is wired in.
    game = _get_champ_game(client, seed="test-champ-real-fact").json()
    assert game["payload"]["prompt"].startswith("How did the ")
    assert "NFL season" in game["payload"]["prompt"]
    real_outcomes = {
        "Won the Super Bowl", "Lost the Super Bowl", "Lost in the Conference Championship",
        "Lost in the Divisional Round", "Lost in the Wild Card Round",
    }
    assert set(game["payload"]["options"]) <= real_outcomes


# --- v1.3: public mode registry ------------------------------------------------

def test_all_eight_certified_guess_modes_registered(client):
    # Scoped to public_game's own Director-pipeline guess-mechanic registry
    # specifically (not the combined /v1/public/modes response, which as of
    # v1.7 also includes coach_connections -- a structurally different
    # system, see gateway/services/public_coach_connections.py's own module
    # docstring for why it was never folded into this same registry).
    # v1.8, Part F/O added the third: lineup_guess. The CFB data enrichment
    # operation added the fourth: cfb_heisman_guess (the first CFB mode).
    # The App-Wide Engine Migration operation added the fifth and sixth:
    # nfl_game_result_guess / cfb_game_result_guess. The Historical Engine
    # Enrichment operation added the seventh: nfl_game_boxscore_guess. The
    # public-readiness punch-list added the eighth: lineup_college_guess,
    # certified only after its real starvation defect was fixed.
    from gateway.services import public_game as public_game_service
    modes = {m["mode"] for m in public_game_service.list_public_modes()}
    assert modes == {
        "draft_guess", "championship_guess", "lineup_guess", "cfb_heisman_guess",
        "nfl_game_result_guess", "cfb_game_result_guess", "nfl_game_boxscore_guess",
        "lineup_college_guess",
    }


def test_player_from_clues_remains_internal_only(client):
    r = _get_game(client, mode="player_from_clues")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"
    assert "player_from_clues" not in {m["mode"] for m in client.get("/v1/public/modes").json()["modes"]}


# --- v1.3: certified-difficulty enforcement (Part 20/21) -----------------------

def test_draft_uncertified_easy_difficulty_rejected_immediately(client):
    r = _get_game(client, difficulty="easy")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_championship_uncertified_easy_difficulty_rejected_immediately(client):
    r = _get_champ_game(client, difficulty="easy")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_draft_certified_difficulties_actually_work(client):
    for diff in ("medium", "hard", "any"):
        r = _get_game(client, difficulty=diff, seed=f"test-draft-diff-{diff}")
        assert r.status_code == 200, f"difficulty={diff!r} should be certified and real"


def test_championship_certified_difficulties_actually_work(client):
    for diff in ("medium", "hard", "any"):
        r = _get_champ_game(client, difficulty=diff, seed=f"test-champ-diff-{diff}")
        assert r.status_code == 200, f"difficulty={diff!r} should be certified and real"


# --- v1.3: game ID / cross-mode tamper resistance (Part 7) ---------------------

def test_cross_mode_game_id_stays_scoped_to_its_own_mode(client):
    draft_game = _get_game(client, seed="test-tamper-draft").json()
    champ_game = _get_champ_game(client, seed="test-tamper-champ").json()
    assert draft_game["game_id"] != champ_game["game_id"]

    draft_stored = packages.load_package(draft_game["game_id"])
    champ_stored = packages.load_package(champ_game["game_id"])
    draft_answer = draft_stored["questions"][0]["answer"]
    champ_answer = champ_stored["questions"][0]["answer"]
    assert draft_answer != champ_answer  # a real team name vs. a real postseason outcome label

    # Submitting the DRAFT game's id with the CHAMPIONSHIP answer must be
    # judged against the draft game's own real answer, never the other
    # package's -- there is no "mode" field in the request for a client to
    # lie about (see public_game.py's validate_public_answer docstring).
    r = client.post("/v1/public/game/answer", json={"game_id": draft_game["game_id"], "answer": champ_answer})
    assert r.json()["correct"] is False
    assert r.json()["canonical_answer"] == draft_answer


# --- v1.3: contract versioning (Part 31) ----------------------------------------

def test_contract_version_present_and_stable(client):
    draft_game = _get_game(client).json()
    champ_game = _get_champ_game(client).json()
    assert draft_game["metadata"]["contract_version"] == 1
    assert champ_game["metadata"]["contract_version"] == 1


# --- v1.4: production rollout controls (Part 10/11) -----------------------

def test_master_switch_on_by_default(client):
    # Every other test in this file already implicitly proves this (they'd
    # all fail otherwise), but an explicit assertion documents the default.
    assert config.PUBLIC_GAME_ENABLED is True


def test_master_switch_off_blocks_game_fetch_safely(client, monkeypatch):
    from gateway.services import public_game
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    r = _get_game(client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_master_switch_off_blocks_answer_validation_safely(client, monkeypatch):
    from gateway.services import public_game
    game = _get_game(client).json()  # fetch BEFORE disabling
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": "x"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_master_switch_off_reflected_in_modes_list(client, monkeypatch):
    # v1.7: PUBLIC_GAME_ENABLED and PUBLIC_SIX_DEGREES_ENABLED are two
    # DELIBERATELY independent switches (see gateway/config.py's Six Degrees
    # section) -- turning off the guess-mode switch alone must not also
    # silently take Six Degrees down, and vice versa. This test now checks
    # exactly that independence rather than assuming one switch governs
    # every public mode.
    from gateway.services import public_game
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", False)
    modes = {m["mode"]: m for m in client.get("/v1/public/modes").json()["modes"]}
    assert modes["draft_guess"]["available"] is False
    assert modes["championship_guess"]["available"] is False
    assert modes["coach_connections"]["available"] is True
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", True)
    modes = client.get("/v1/public/modes").json()["modes"]
    assert all(m["available"] is True for m in modes)


def test_six_degrees_master_switch_independent_of_public_game_switch(client, monkeypatch):
    # Coach Connections v2 rebuild: shares the same PUBLIC_SIX_DEGREES_ENABLED
    # kill switch as the old six_degrees_guess mode did (it's a replacement
    # for that same product surface) -- see public_coach_connections.py's
    # module docstring.
    from gateway.services import public_coach_connections
    monkeypatch.setattr(public_coach_connections.config, "PUBLIC_SIX_DEGREES_ENABLED", False)
    modes = {m["mode"]: m for m in client.get("/v1/public/modes").json()["modes"]}
    assert modes["coach_connections"]["available"] is False
    assert modes["draft_guess"]["available"] is True
    assert modes["championship_guess"]["available"] is True
    monkeypatch.setattr(public_coach_connections.config, "PUBLIC_SIX_DEGREES_ENABLED", True)


def test_public_modes_env_var_narrows_but_cannot_expand(monkeypatch):
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess")
    assert config.public_modes_allowed() == frozenset({"draft_guess"})
    # Requesting a mode that isn't code-certified does NOT sneak it in.
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess,totally_made_up_mode")
    assert config.public_modes_allowed() == frozenset({"draft_guess"})
    monkeypatch.delenv("READS_PUBLIC_MODES", raising=False)
    assert config.public_modes_allowed() == config.PUBLIC_MODE_ALLOWLIST


def test_public_modes_env_var_temporarily_disables_one_mode(client, monkeypatch):
    monkeypatch.setenv("READS_PUBLIC_MODES", "draft_guess")
    r = _get_champ_game(client)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MODE_UNAVAILABLE"
    r2 = _get_game(client)
    assert r2.status_code == 200
    modes = client.get("/v1/public/modes").json()["modes"]
    by_id = {m["mode"]: m for m in modes}
    assert by_id["draft_guess"]["available"] is True
    assert by_id["championship_guess"]["available"] is False
    monkeypatch.delenv("READS_PUBLIC_MODES", raising=False)


# --- v1.4: readiness (Part 4/5/6) -------------------------------------------

def test_ready_route_exposes_no_filesystem_path(client):
    r = client.get("/v1/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert "db_path" not in body["engine_database"]
    assert "reason" not in body["engine_database"]
    assert body["mode_registry"]["loaded"] is True
    raw = r.text
    assert "/Users/" not in raw
    assert "nfl-trivia" not in raw


def test_health_route_is_minimal_and_safe(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"status", "service", "api_version"}


# --- v1.4: gameplay telemetry (Part 17/18) ----------------------------------

def test_answer_telemetry_correctly_identifies_mode(client, tmp_path, monkeypatch):
    # Real bug caught by actually inspecting a generated package's stored
    # `parsed_spec` (not assumed): it has no `domain` key at all (the
    # validator normalizes that away) -- an earlier version of the mode
    # lookup this test checks used `domain` and always logged `mode: None`
    # for every answer-submission telemetry event. Verified directly
    # against the real operational log file, not just that the endpoint
    # still returns 200 (which it did even with the bug, since the buggy
    # lookup never affected the client-facing response).
    from gateway import config as gw_config
    from gateway.services import public_game
    log_dir = tmp_path / "telemetry"
    monkeypatch.setattr(gw_config, "GATEWAY_AUDIT_LOG_DIR", log_dir)
    monkeypatch.setattr(gw_config, "OPERATIONAL_LOG_PATH", log_dir / "gateway_operational_log.jsonl")

    draft_game = _get_game(client, seed="telemetry-mode-draft").json()
    client.post("/v1/public/game/answer", json={"game_id": draft_game["game_id"], "answer": "x"})
    champ_game = _get_champ_game(client, seed="telemetry-mode-champ").json()
    client.post("/v1/public/game/answer", json={"game_id": champ_game["game_id"], "answer": "x"})

    lines = [json.loads(l) for l in gw_config.OPERATIONAL_LOG_PATH.read_text().splitlines() if l.strip()]
    answer_events = [l for l in lines if l.get("event") == "public_answer_submitted"]
    assert len(answer_events) == 2
    assert answer_events[0]["mode"] == "draft_guess"
    assert answer_events[1]["mode"] == "championship_guess"
    # Never the raw free-text answer (Part 17).
    assert all("answer" not in e for e in answer_events)


def test_game_served_telemetry_recorded(client, tmp_path, monkeypatch):
    from gateway import config as gw_config
    log_dir = tmp_path / "telemetry"
    monkeypatch.setattr(gw_config, "GATEWAY_AUDIT_LOG_DIR", log_dir)
    monkeypatch.setattr(gw_config, "OPERATIONAL_LOG_PATH", log_dir / "gateway_operational_log.jsonl")
    _get_game(client, seed="telemetry-served-check")
    lines = [json.loads(l) for l in gw_config.OPERATIONAL_LOG_PATH.read_text().splitlines() if l.strip()]
    served = [l for l in lines if l.get("event") == "public_game_served"]
    assert len(served) == 1
    assert served[0]["mode"] == "draft_guess"
    assert served[0]["generation_attempts"] >= 1
    assert served[0]["latency_ms"] > 0


# --- v1.6, Part A: public generation concurrency -----------------------------
# The old single-slot admin lock, once shared by the public path too, meant
# only 1 of N concurrent public fetches could ever succeed (v1.4/v1.5's own
# measured 1-success-out-of-15/6 results). generation.generate_public() now
# uses its own bounded pool (config.PUBLIC_GENERATION_MAX_CONCURRENCY) --
# these tests prove that fix at the code level, distinct from the real
# HTTP-level load test in the v1.6 report (which exercises an actual running
# Gateway process, not TestClient's in-process transport).

def test_public_generation_supports_real_concurrency(client):
    from concurrent.futures import ThreadPoolExecutor
    n = config.PUBLIC_GENERATION_MAX_CONCURRENCY
    with ThreadPoolExecutor(max_workers=n) as ex:
        responses = list(ex.map(lambda i: _get_game(client, seed=f"concurrency-{i}"), range(n)))
    statuses = [r.status_code for r in responses]
    # Old behavior (single shared lock): only 1 of these would have been
    # 200, the rest GENERATION_BUSY. New behavior: a batch sized exactly at
    # the pool's own capacity should all succeed.
    assert statuses.count(200) == n, f"expected all {n} concurrent public fetches to succeed, got {statuses}"


def test_public_generation_independent_from_admin_lock(client):
    # Directly proves Part A2's separation: an admin job holding the ADMIN
    # lock must not block a public fetch from succeeding, since they now use
    # two entirely separate gates.
    from gateway.services import generation
    acquired = generation._generation_lock.acquire(blocking=False)
    assert acquired, "test setup: admin lock should have been free"
    try:
        r = _get_game(client, seed="admin-lock-held-check")
        assert r.status_code == 200, (
            "public fetch was blocked by a busy ADMIN lock -- concurrency "
            "paths are not actually independent"
        )
    finally:
        generation._generation_lock.release()


def test_admin_generation_still_single_slot_after_public_change(client, auth_headers):
    # Confirms Part A2's other half: the admin path itself was NOT loosened.
    # Same assertion shape as test_staging_hardening.py's existing
    # test_rate_limit_does_not_bypass_generation_busy, repeated here so this
    # file's own concurrency section demonstrates both halves together.
    from concurrent.futures import ThreadPoolExecutor
    clues_request = "Identify the player from these three clues: drafted in the first round, plays quarterback, attended a school in the SEC."

    def call(i):
        return client.post("/v1/games/generate",
                            json={"request_text": clues_request, "puzzle_count": 2, "seed": f"admin-busy-{i}"},
                            headers=auth_headers)

    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(call, range(3)))
    codes = sorted(r.json().get("error", {}).get("code") or "OK" for r in results)
    assert codes.count("GENERATION_BUSY") == 2, f"expected admin path to remain single-slot, got {codes}"


def test_concurrent_answer_validation_no_cross_contamination(client):
    # Fetches two DIFFERENT real games (different prompts/options), submits
    # both answer requests concurrently, and confirms each response's
    # canonical_answer belongs to ITS OWN game -- not swapped/mixed up under
    # concurrent execution.
    from concurrent.futures import ThreadPoolExecutor
    game_a = _get_game(client, seed="contamination-check-a").json()
    game_b = _get_champ_game(client, seed="contamination-check-b").json()
    assert game_a["game_id"] != game_b["game_id"]

    def submit(game):
        return client.post("/v1/public/game/answer",
                            json={"game_id": game["game_id"], "answer": "not the real answer"}).json()

    with ThreadPoolExecutor(max_workers=2) as ex:
        result_a, result_b = list(ex.map(submit, [game_a, game_b]))

    assert result_a["canonical_answer"] in game_a["payload"]["options"], (
        "game A's answer response returned an option that isn't even one of game A's own choices "
        "-- possible cross-game contamination under concurrency"
    )
    assert result_b["canonical_answer"] in game_b["payload"]["options"], (
        "game B's answer response returned an option that isn't even one of game B's own choices "
        "-- possible cross-game contamination under concurrency"
    )


# --- nfl_game_result_guess / cfb_game_result_guess (App-Wide Engine Migration
# operation) -- the first modes built on tools/data_refresh/{nfl,cfb}_games_
# refresh.py's real, automatically-refreshed games tables, proving newly-
# ingested game data becomes real, generatable, certified content, not just
# rows sitting in a table. ------------------------------------------------

def test_nfl_game_result_no_auth_needed(client):
    r = _get_nfl_game_result_game(client)
    assert r.status_code == 200


def test_cfb_game_result_no_auth_needed(client):
    r = _get_cfb_game_result_game(client)
    assert r.status_code == 200


def test_nfl_game_result_payload_never_contains_answer(client):
    r = _get_nfl_game_result_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh nfl_game_result_guess response"
    body = r.json()
    assert body["mode"] == "nfl_game_result_guess"
    assert body["competition"] == "NFL"
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert len(body["payload"]["options"]) == 4


def test_cfb_game_result_payload_never_contains_answer(client):
    r = _get_cfb_game_result_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh cfb_game_result_guess response"
    body = r.json()
    assert body["mode"] == "cfb_game_result_guess"
    assert body["competition"] == "CFB"
    assert len(body["payload"]["options"]) == 4


def test_nfl_game_result_correct_answer_accepted(client):
    game = _get_nfl_game_result_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_nfl_game_result_incorrect_answer_rejected(client):
    game = _get_nfl_game_result_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_cfb_game_result_correct_answer_accepted(client):
    game = _get_cfb_game_result_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_nfl_game_result_easy_difficulty_is_certified_and_works(client):
    # Real survey (App-Wide Engine Migration operation): 2,219 of 6,484 real
    # accepted candidates graded Easy -- must NOT be rejected.
    r = _get_nfl_game_result_game(client, difficulty="easy")
    assert r.status_code == 200


def test_cfb_game_result_easy_difficulty_is_certified_and_works(client):
    # Real survey: 19,524 of 36,175 real accepted candidates graded Easy.
    r = _get_cfb_game_result_game(client, difficulty="easy")
    assert r.status_code == 200


def test_nfl_game_result_question_is_a_real_verifiable_fact(client):
    game = _get_nfl_game_result_game(client, seed="test-nfl-game-result-real-fact").json()
    assert game["payload"]["prompt"].startswith("Which team won when the ")
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    assert real_answer in game["payload"]["options"]


# --- nfl_game_boxscore_guess (Historical Engine Enrichment operation) --
# built on the newly-populated team_game_stats table, cross-verified
# against a real known final score before being trusted (2024 Week 1
# KC-BAL: both teams' box-score lines sum, via TDs*6+FG*3+PAT, to the
# real historical result on both sides). Genuinely distinct from
# nfl_game_result_guess -- asks which team gained more yards, not who
# won. -----------------------------------------------------------------

def test_boxscore_no_auth_needed(client):
    r = _get_boxscore_game(client)
    assert r.status_code == 200


def test_boxscore_payload_never_contains_answer(client):
    r = _get_boxscore_game(client)
    raw = r.text
    for forbidden in ("correctIndex", "answer\":", "source_ids", "provenance", "qa_checks_performed", "funnel"):
        assert forbidden not in raw, f"{forbidden!r} leaked in a fresh nfl_game_boxscore_guess response"
    body = r.json()
    assert body["mode"] == "nfl_game_boxscore_guess"
    assert body["competition"] == "NFL"
    assert set(body.keys()) == {"game_id", "mode", "competition", "difficulty", "title", "instructions", "payload", "metadata"}
    assert set(body["payload"].keys()) == {"prompt", "options", "visual_template", "visual_payload"}
    assert len(body["payload"]["options"]) == 4


def test_boxscore_correct_answer_accepted(client):
    game = _get_boxscore_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": real_answer})
    body = r.json()
    assert body["correct"] is True
    assert body["canonical_answer"] == real_answer


def test_boxscore_incorrect_answer_rejected(client):
    game = _get_boxscore_game(client).json()
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    wrong = next(o for o in game["payload"]["options"] if o != real_answer)
    r = client.post("/v1/public/game/answer", json={"game_id": game["game_id"], "answer": wrong})
    body = r.json()
    assert body["correct"] is False
    assert body["canonical_answer"] == real_answer


def test_boxscore_easy_difficulty_is_certified_and_works(client):
    # Real survey (Historical Engine Enrichment operation): 2,187 of 5,738
    # real accepted candidates graded Easy -- must NOT be rejected.
    r = _get_boxscore_game(client, difficulty="easy")
    assert r.status_code == 200


def test_boxscore_question_is_a_real_verifiable_fact(client):
    game = _get_boxscore_game(client, seed="test-boxscore-real-fact").json()
    assert "which team gained more total yards" in game["payload"]["prompt"]
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    assert real_answer in game["payload"]["options"]


def test_cfb_game_result_question_is_a_real_verifiable_fact(client):
    game = _get_cfb_game_result_game(client, seed="test-cfb-game-result-real-fact").json()
    assert game["payload"]["prompt"].startswith("Which team won when ")
    stored = packages.load_package(game["game_id"])
    real_answer = stored["questions"][0]["answer"]
    assert real_answer in game["payload"]["options"]
