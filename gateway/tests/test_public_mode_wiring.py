"""Public Mode Wiring pass (Pass 2.5): the 7 real backend capabilities
(Rivalries, Spot the Fake, Three Clues One Champion, Era Gauntlet, Odd
College Out, One School Missing, Franchise Marathon) wired into the public
API this pass. Runs against the real Engine database via the real public
route -- not mocked.

The core real bug this pass found and fixed: package_id is a hash of
(request_text, seed, relationship_predicate, package_version) ONLY (see
tools/game_director_v01.py) -- it does not depend on target_count/
puzzle_count or filters. The old hardcoded puzzle_count=1 in
generation.generate_public() meant a "sequential" mode (franchise_name /
era_gauntlet filters, whose real candidate order is deliberately NOT
seed-shuffled -- see sb_champion_offense_college.py's
fetch_ordered_candidates()) could only ever return its real FIRST stage,
forever, regardless of seed. Fixed via a real `stage_index` parameter
threaded through get_public_game() -> generate_public(puzzle_count=...).
"""
import pytest

from gateway import config


def _get(client, mode, **params):
    params["mode"] = mode
    return client.get("/v1/public/game", params=params)


def _answer(client, game_id, answer):
    return client.post("/v1/public/game/answer", json={"game_id": game_id, "answer": answer})


# --- registry shape ---------------------------------------------------------

def test_eight_new_modes_on_the_allowlist():
    new_modes = {
        "cfb_rivalry_guess", "cfb_rivalry_lookup_guess", "cfb_spot_the_fake_guess", "cfb_three_clues_guess",
        "era_gauntlet_guess", "cfb_odd_college_out_guess", "cfb_one_school_missing_guess",
        "franchise_marathon_guess",
    }
    assert new_modes <= config.PUBLIC_MODE_ALLOWLIST


# --- one real fetch + real answer round-trip per non-sequential new mode ----

@pytest.mark.parametrize("mode", [
    "cfb_rivalry_guess", "cfb_rivalry_lookup_guess", "cfb_spot_the_fake_guess", "cfb_three_clues_guess",
    "cfb_odd_college_out_guess", "cfb_one_school_missing_guess",
])
def test_new_mode_real_fetch_and_answer_roundtrip(client, mode):
    r = _get(client, mode, seed=f"pytest-{mode}-1")
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == mode
    assert len(body["payload"]["options"]) == 4
    assert len(set(body["payload"]["options"])) == 4  # no duplicate options (no multi-valid-answer trap)

    r2 = _answer(client, body["game_id"], "Definitely Not A Real Answer")
    assert r2.status_code == 200
    assert r2.json()["correct"] is False
    canonical = r2.json()["canonical_answer"]
    assert canonical in body["payload"]["options"]

    r3 = _answer(client, body["game_id"], canonical)
    assert r3.json()["correct"] is True


# --- sequential modes: real stage progression -------------------------------

def test_era_gauntlet_progresses_through_seven_real_distinct_stages(client):
    seen_prompts = set()
    for stage in range(7):
        r = _get(client, "era_gauntlet_guess", seed="pytest-era-fixed", stage=stage)
        assert r.status_code == 200, r.json()
        seen_prompts.add(r.json()["payload"]["prompt"])
    assert len(seen_prompts) == 7, "each of the 7 real eras must be a distinct real question"


def test_era_gauntlet_stage_seven_is_sequence_complete(client):
    r = _get(client, "era_gauntlet_guess", seed="pytest-era-fixed", stage=7)
    assert r.status_code == 200  # SEQUENCE_COMPLETE is a well-defined 200, not a 5xx
    body = r.json()
    assert body["error"]["code"] == "SEQUENCE_COMPLETE"
    assert body["error"]["stage_count"] == 7


def test_franchise_marathon_real_chronological_progression(client):
    seasons = []
    for stage in range(3):  # Steelers has >=3 real distinct stages (measured this pass)
        r = _get(client, "franchise_marathon_guess", seed="pytest-marathon-fixed", stage=stage, franchise="steelers")
        assert r.status_code == 200, r.json()
        game_id = r.json()["game_id"]
        canonical = _answer(client, game_id, "x").json()["canonical_answer"]
        assert "Steelers" in canonical
        seasons.append(int(canonical.split()[0]))
    assert seasons == sorted(seasons), "Franchise Marathon must progress in real chronological order"
    assert len(set(seasons)) == len(seasons), "each stage must be a distinct real season"


def test_franchise_marathon_eventually_sequence_completes(client):
    # Dolphins has 2 real raw boards (1972, 1973) but only 1 real SURVIVING
    # stage after the standard duplicate-question guard -- measured
    # directly this pass, not assumed (the two back-to-back dynasty
    # seasons collide on question text, same documented behavior as
    # Cowboys' 1990s three-peat above).
    r = _get(client, "franchise_marathon_guess", seed="pytest-marathon-dolphins", stage=0, franchise="dolphins")
    assert r.status_code == 200, r.json()
    r2 = _get(client, "franchise_marathon_guess", seed="pytest-marathon-dolphins", stage=1, franchise="dolphins")
    assert r2.status_code == 200
    body = r2.json()
    assert body["error"]["code"] == "SEQUENCE_COMPLETE"
    assert body["error"]["stage_count"] == 1


# --- hard eligibility gate: caller cannot misuse sequential/filter params ---

def test_stage_index_rejected_for_non_sequential_mode(client):
    r = _get(client, "cfb_ranking_guess", seed="x", stage=0)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_franchise_filter_rejected_for_mode_without_caller_filter_key(client):
    r = _get(client, "cfb_ranking_guess", seed="x", franchise="cowboys")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


# --- telemetry mode disambiguation (two real domain/predicate collisions) --

def test_franchise_marathon_and_sb_champion_offense_share_predicate_but_resolve_distinctly():
    from gateway.services import public_game as pg
    fm = pg.PUBLIC_MODES["franchise_marathon_guess"]
    sb = pg.PUBLIC_MODES["sb_champion_offense_college_guess"]
    assert fm["spec"]["relationship_predicate"] == sb["spec"]["relationship_predicate"]
    assert pg._mode_for_package({"parsed_spec": {"relationship_predicate": fm["spec"]["relationship_predicate"],
                                                   "filters": {"franchise_name": "cowboys"}}}) == "franchise_marathon_guess"
    assert pg._mode_for_package({"parsed_spec": {"relationship_predicate": sb["spec"]["relationship_predicate"],
                                                   "filters": {}}}) == "sb_champion_offense_college_guess"


def test_era_gauntlet_and_three_clues_share_predicate_but_resolve_distinctly():
    from gateway.services import public_game as pg
    eg = pg.PUBLIC_MODES["era_gauntlet_guess"]
    tc = pg.PUBLIC_MODES["cfb_three_clues_guess"]
    assert eg["spec"]["relationship_predicate"] == tc["spec"]["relationship_predicate"]
    assert pg._mode_for_package({"parsed_spec": {"relationship_predicate": eg["spec"]["relationship_predicate"],
                                                   "filters": {"era_gauntlet": True}}}) == "era_gauntlet_guess"
    assert pg._mode_for_package({"parsed_spec": {"relationship_predicate": tc["spec"]["relationship_predicate"],
                                                   "filters": {}}}) == "cfb_three_clues_guess"


# --- Section 11: natural-language Creator reachability ---------------------

@pytest.mark.parametrize("prompt,expected_domain,expected_predicate,filter_check", [
    ("Make me an Iron Bowl rivalry game", "CFB_RIVALRY_TRIVIA", "CORRECT_TRIVIA_ANSWER", lambda f: f.get("rivalry_pack_number") == 1),
    ("Make me play Spot the Fake", "CFB_SPOT_THE_FAKE_LINEUP", "ALTERED_POSITION", lambda f: f == {}),
    ("Give me Three Clues One Champion", "CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES", lambda f: f == {}),
    ("Make me an Era Gauntlet", "CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES", lambda f: f.get("era_gauntlet") is True),
    ("Give me Odd College Out", "CFB_ODD_COLLEGE_OUT", "IMPOSTOR_COLLEGE", lambda f: f == {}),
    ("Make me play One School Missing", "CFB_ONE_SCHOOL_MISSING", "MISSING_COLLEGE", lambda f: f == {}),
    ("Give me a Packers Franchise Marathon", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE", lambda f: f.get("franchise_name") == "packers"),
    # Two real gaps found and fixed this pass:
    ("Make me something about rivalries", "CFB_RIVALRY", "RIVAL_OF", lambda f: f == {}),
    ("Give me a historical football challenge", "CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES", lambda f: f.get("era_gauntlet") is True),
])
def test_nl_prompt_resolves_to_a_real_public_mode(prompt, expected_domain, expected_predicate, filter_check):
    from tools.director_v02.providers.mock import MockDeterministicTranslator
    from gateway.services import public_game as pg

    r = MockDeterministicTranslator().translate(prompt)
    assert r["translation_status"] == "TRANSLATED", r
    spec = r["spec"]
    assert spec["domain"] == expected_domain
    assert spec["relationship_predicate"] == expected_predicate
    assert filter_check(spec.get("filters") or {})
    # And the resolved (domain, predicate) must match at least one real
    # public mode -- "translates" is not the same as "can actually launch
    # publicly" (Section 11's own explicit standard).
    matches = [m for m, e in pg.PUBLIC_MODES.items()
               if e["spec"]["domain"] == expected_domain and e["spec"]["relationship_predicate"] == expected_predicate]
    assert matches, f"{prompt!r} resolved to a real spec with no matching public mode"


def test_bare_franchise_marathon_request_needs_clarification_not_failure():
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate("Give me a Franchise Marathon")
    # A bare request genuinely can't launch (which franchise?) -- this
    # must be the well-defined NEEDS_CLARIFICATION outcome, never NO_MATCH.
    assert r["translation_status"] == "NEEDS_CLARIFICATION"


# --- real bug found and fixed while making cfb_rivalry_lookup_guess public -

def test_rivalry_lookup_never_shows_placeholder_nickname_text():
    """Real bug found via actual generation, not assumed: 32 of 96 real
    rivalry rows have a literal "-" placeholder nickname (no real nickname
    exists for that rivalry) -- the adapter's original `if row["nickname"]`
    check didn't catch this (a non-empty "-" string is truthy), producing
    'in the game known as ("-")' for a full third of all real questions."""
    from tools.quiz_export import engine as engine_bootstrap
    from tools.quiz_export.adapters import cfb_rivalry as adapter

    c = engine_bootstrap.connect()
    rows = adapter.fetch_ordered_candidates(c, "pytest-nickname-fix-check")
    saw_placeholder_rows = 0
    for row in rows:
        if (row["nickname"] or "").strip() == "-":
            saw_placeholder_rows += 1
    assert saw_placeholder_rows > 0, "fixture assumption changed -- no placeholder rows left to test against"

    import random as _random
    rng = _random.Random(1)
    from tools.quiz_export import duplicates as duplicates_mod
    guard = duplicates_mod.DuplicateGuard()
    bad_questions = []
    for row in rows:
        result = adapter.evaluate(c, row, rng, guard)
        if isinstance(result, dict) and '("-")' in result["question"]:
            bad_questions.append(result["question"])
    assert not bad_questions, f"placeholder nickname leaked into real question text: {bad_questions[:3]}"


# --- regression: existing modes untouched by this pass still work ----------

@pytest.mark.parametrize("mode", ["draft_guess", "nfl_game_result_guess", "cfb_ranking_guess", "cfb_upset_guess"])
def test_existing_mode_regression(client, mode):
    r = _get(client, mode, seed=f"pytest-regress-{mode}")
    assert r.status_code == 200, r.json()
    assert len(r.json()["payload"]["options"]) >= 2
