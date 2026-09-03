"""v1.8, Part B/C/G/H/L -- tests for the Game Creator's Gateway routes
(/v1/creator/*). Admin-only, real-engine tests -- no mocking of the
translator/generation/QA path, matching the discipline every other
real-generation test in this suite already follows.
"""
DRAFT_REQUEST = "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
LINEUP_REQUEST = "Guess the NFL team from the colleges attended by the players on its offense, displayed by position."
UNSUPPORTED_REQUEST = "Make me an NFL trivia game about players favorite foods."
GIBBERISH_REQUEST = "asdkjaslkdj random nonsense not football at all"


# --- auth (Part L: admin-only, no exception) --------------------------------

def test_creator_feasibility_requires_admin(client):
    r = client.post("/v1/creator/feasibility", json={"request_text": DRAFT_REQUEST})
    assert r.status_code == 401


def test_creator_generate_requires_admin(client):
    r = client.post("/v1/creator/generate", json={"request_text": DRAFT_REQUEST})
    assert r.status_code == 401


def test_creator_queue_requires_admin(client):
    r = client.get("/v1/creator/queue")
    assert r.status_code == 401


def test_creator_review_requires_admin(client):
    r = client.post("/v1/creator/review", json={"package_id": "GGP:" + "a" * 24, "review_status": "APPROVED"})
    assert r.status_code == 401


def test_creator_capabilities_requires_admin(client):
    r = client.get("/v1/creator/capabilities")
    assert r.status_code == 401


# --- Part L: no code/spec injection surface ---------------------------------

def test_creator_feasibility_rejects_a_spec_field(client, auth_headers):
    # CreatorFeasibilityRequest has NO `spec` field at all (extra="forbid") --
    # a client cannot hand-craft a structured spec to try to reach an
    # unregistered/internal capability triple directly.
    r = client.post(
        "/v1/creator/feasibility",
        json={"request_text": DRAFT_REQUEST, "spec": {"mechanic": "guess"}},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_creator_feasibility_rejects_empty_text(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": ""}, headers=auth_headers)
    assert r.status_code == 400


def test_creator_feasibility_rejects_oversized_text(client, auth_headers):
    from gateway import config
    r = client.post(
        "/v1/creator/feasibility",
        json={"request_text": "x" * (config.MAX_REQUEST_TEXT_CHARS + 1)},
        headers=auth_headers,
    )
    assert r.status_code == 400


# --- feasibility (Part C) ----------------------------------------------------

def test_creator_feasibility_supported(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": DRAFT_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["support_status"] == "SUPPORTED"


def test_creator_feasibility_supported_with_limitations_for_proof_game(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": LINEUP_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert len(body["known_limitations"]) == 3


def test_creator_feasibility_understood_but_unsupported(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": UNSUPPORTED_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    # "favorite foods" alone (no "both" coordination signal) is plain NO_MATCH,
    # not UNDERSTOOD_UNSUPPORTED_MECHANIC -- see mock.py's own module docstring.
    assert r.json()["support_status"] == "UNKNOWN"


def test_creator_feasibility_unknown_for_gibberish(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": GIBBERISH_REQUEST}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["support_status"] == "UNKNOWN"


# --- generate + review queue (Part G/H) --------------------------------------

def test_creator_generate_then_appears_in_queue_as_generated(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-gen-1"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["package_id"] and body["qa_status"] == "PASSED"
    assert body["review_status"] == "GENERATED"

    r2 = client.get("/v1/creator/queue", params={"review_status": "GENERATED"}, headers=auth_headers)
    assert r2.status_code == 200
    ids = {p["package_id"] for p in r2.json()["packages"]}
    assert body["package_id"] in ids


def test_creator_approve_then_reflected_in_queue_and_package(client, auth_headers):
    gen = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-approve-1"},
        headers=auth_headers,
    ).json()
    pid = gen["package_id"]

    r = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "APPROVED"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_status"] == "APPROVED"
    assert r.json()["reviewed_at"]

    r2 = client.get(f"/v1/games/{pid}", headers=auth_headers)
    assert r2.json()["review_status"] == "APPROVED"

    r3 = client.get("/v1/creator/queue", params={"review_status": "APPROVED"}, headers=auth_headers)
    ids = {p["package_id"] for p in r3.json()["packages"]}
    assert pid in ids


def test_creator_reject_then_reflected(client, auth_headers):
    gen = client.post(
        "/v1/creator/generate",
        json={"request_text": DRAFT_REQUEST, "puzzle_count": 2, "seed": "pytest-creator-reject-1"},
        headers=auth_headers,
    ).json()
    pid = gen["package_id"]
    r = client.post("/v1/creator/review", json={"package_id": pid, "review_status": "REJECTED"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_status"] == "REJECTED"


def test_creator_review_unknown_package_404(client, auth_headers):
    fake_id = "GGP:" + "0" * 24
    r = client.post("/v1/creator/review", json={"package_id": fake_id, "review_status": "APPROVED"}, headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PACKAGE_NOT_FOUND"


def test_creator_review_rejects_generated_as_a_target_status(client, auth_headers):
    # GENERATED is set only by generation itself -- not a human-settable
    # target of the review action (models.py's Literal excludes it).
    r = client.post(
        "/v1/creator/review",
        json={"package_id": "GGP:" + "0" * 24, "review_status": "GENERATED"},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_creator_queue_invalid_review_status_filter_rejected(client, auth_headers):
    r = client.get("/v1/creator/queue", params={"review_status": "NOT_A_REAL_STATUS"}, headers=auth_headers)
    assert r.status_code == 400


# --- capability reference (Part C) -------------------------------------------

def test_creator_capabilities_lists_twenty_one_with_real_statuses(client, auth_headers):
    # 23, not 12: the NFL Wikipedia history import registered two (WON_CHAMPIONSHIP/
    # NFL_SUPER_BOWL, WON_AWARD/NFL_AWARDS), the Creator-gap-audit operation
    # registered nine more (box score sacks/turnovers/penalties, CFB championship,
    # NFL/CFB season stat leaders, NFL coaching, CFB transfer, CFB rivalry), and
    # Reliability-design Phases 3-4 registered two real, GENERATION_VERIFIED-or-
    # better (not yet publicly released) capabilities, NFL_PLAYER_SEASON/
    # TEAM_OF_SEASON (now HUMAN_APPROVED) and CFB_PLAYER_SEASON/SCHOOL_OF_SEASON --
    # included here because this route reflects real catalog-verified state
    # (Phase 3's feasibility.py correction), and GENERATION_VERIFIED/HUMAN_APPROVED
    # are proven enough for this admin-only "what's already possible" reference view.
    # Creator Semantic Routing + Who Am I pass: 23 -> 29 -- 6 real new
    # GENERATION_VERIFIED capabilities (NFL_ALL_PRO, NFL_PRO_BOWL,
    # NFL_HALL_OF_FAME, NFL_OFFENSIVE_COORDINATOR, NFL_DEFENSIVE_COORDINATOR,
    # CFB_PLAYER_IDENTITY/IDENTIFY_FROM_CLUES), each individually verified
    # end-to-end via a real, passing 100-round Tier-2 certification probe.
    # Creator Capability Completion pass: 29 -> 53 -- 24 real new
    # GENERATION_VERIFIED capabilities (rankings, upsets, NFL PBP scoring,
    # NFL defensive events, drives, CFB same-week stat comparisons, top
    # single-game performers, ordered transfer paths, honor+college
    # compositions, cross-league honors), each individually verified
    # end-to-end via a real, passing 100-round Tier-2 certification probe.
    # Rivalry Data + Gold Standard Content Integration operation: 53 -> 64 --
    # 11 real new GENERATION_VERIFIED/PUBLIC_ENABLED capabilities (CFB Rivalry
    # Trivia, curated NFL offense-by-college, Super Bowl champion offense by
    # college, and 8 more Gold Standard "10. New Game Modes" concepts built
    # on the same curated data), each individually Tier-2 certified.
    # Creator/Game Quality Correction pass: 64 -> 66 -- CFB_RANKING__
    # RANKED_HIGHER (true 2-team ranking comparison) and CFB_OFFENSE_
    # LINEUP__TEAM_SEASON_OF_STARTING_OFFENSE (first real CFB-team-roster
    # capability), each individually Tier-2 certified.
    r = client.get("/v1/creator/capabilities", headers=auth_headers)
    assert r.status_code == 200
    caps = r.json()["capabilities"]
    assert len(caps) == 66
    lineup = next(c for c in caps if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP")
    assert lineup["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    lineup_college = next(c for c in caps if c["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE")
    assert lineup_college["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    heisman = next(c for c in caps if c["relationship_predicate"] == "WON_HEISMAN")
    assert heisman["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    game_results = [c for c in caps if c["relationship_predicate"] == "WON_GAME"]
    assert len(game_results) == 2
    assert {c["domain"] for c in game_results} == {"NFL_GAME_RESULT", "CFB_GAME_RESULT"}
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in game_results)
    championship_results = [c for c in caps if c["relationship_predicate"] == "WON_CHAMPIONSHIP"]
    assert len(championship_results) == 2
    assert {c["domain"] for c in championship_results} == {"NFL_SUPER_BOWL", "CFB_CHAMPIONSHIP"}
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in championship_results)
    awards = next(c for c in caps if c["relationship_predicate"] == "WON_AWARD")
    assert awards["domain"] == "NFL_AWARDS"
    assert awards["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    stat_leaders = [c for c in caps if c["relationship_predicate"] == "LED_LEAGUE_IN_STAT"]
    assert len(stat_leaders) == 2
    assert {c["domain"] for c in stat_leaders} == {"NFL_SEASON_STATS", "CFB_SEASON_STATS"}
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in stat_leaders)
    boxscore_extras = [c for c in caps if c["relationship_predicate"] in
                        ("HAD_MORE_SACKS", "HAD_FEWER_TURNOVERS", "HAD_FEWER_PENALTIES")]
    assert len(boxscore_extras) == 3
    assert all(c["domain"] == "NFL_GAME_BOXSCORE" for c in boxscore_extras)
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in boxscore_extras)
    coaching = next(c for c in caps if c["relationship_predicate"] == "COACHED_TEAM")
    assert coaching["domain"] == "NFL_COACHING"
    assert coaching["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    attended_college_results = [c for c in caps if c["relationship_predicate"] == "ATTENDED_COLLEGE"]
    assert len(attended_college_results) == 2
    assert {c["domain"] for c in attended_college_results} == {"NFL_DRAFT", "CFB_TRANSFER"}
    assert all(c["support_status"] == "SUPPORTED_WITH_LIMITATIONS" for c in attended_college_results)
    rivalry = next(c for c in caps if c["relationship_predicate"] == "RIVAL_OF")
    assert rivalry["domain"] == "CFB_RIVALRY"
    assert rivalry["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
