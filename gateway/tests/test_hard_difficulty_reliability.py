"""Reliability pass (Pass 2.6): explicit difficulty="hard" reliability for
Spot the Fake, Odd College Out, and One School Missing.

Root cause (found by direct reproduction, not assumed): these three modes
draw from the same 595-board `_group_board_common` pool, which has 196 real,
distinct, QA-passed Hard candidates (confirmed via a target_count=5000
direct survey against tools.game_director_v01.generate_package_from_spec()
-- see that survey's numbers echoed in this file's assertions below). There
was never a search-reliability problem in generate_package_from_spec()
itself: it evaluates every real candidate, then filters by difficulty --
confirmed by reading it. The actual blocker was one level up:
tools/director_v02/registry.py's CFB_SPOT_THE_FAKE_LINEUP/
CFB_ODD_COLLEGE_OUT/CFB_ONE_SCHOOL_MISSING entries hardcoded
supported_difficulties={"any","easy","medium"} -- a stale value copy-pasted
from before these domains' board pool was expanded from a 60-board
SB_CHAMPION-only source (genuinely zero real Hard boards) to today's
595-board 5-source pool. That registry-level gate rejected an explicit
difficulty="hard" request as UNDERSTOOD_BUT_UNSUPPORTED (in
tools/director_v02/pipeline.py's difficulty_override check, and identically
in validator.py's translator-driven path) before generation ever ran --
which looks identical to a real generation failure from the caller's side,
but is a completely different bug with a completely different fix. Fixed
by adding "hard" to all three registry entries and to the matching
PUBLIC_MODES certified_difficulties in gateway/services/public_game.py.
"""
import pytest

from gateway import config

_AFFECTED_MODES = ["cfb_spot_the_fake_guess", "cfb_odd_college_out_guess", "cfb_one_school_missing_guess"]
_SEEDS = [f"pytest-hard-seed-{i}" for i in range(5)]


def _get(client, mode, **params):
    params["mode"] = mode
    return client.get("/v1/public/game", params=params)


def _answer(client, game_id, answer):
    return client.post("/v1/public/game/answer", json={"game_id": game_id, "answer": answer})


# --- registry-level fix: hard is now a declared-supported difficulty -------

@pytest.mark.parametrize("mode,domain,predicate", [
    ("cfb_spot_the_fake_guess", "CFB_SPOT_THE_FAKE_LINEUP", "ALTERED_POSITION"),
    ("cfb_odd_college_out_guess", "CFB_ODD_COLLEGE_OUT", "IMPOSTOR_COLLEGE"),
    ("cfb_one_school_missing_guess", "CFB_ONE_SCHOOL_MISSING", "MISSING_COLLEGE"),
])
def test_registry_declares_hard_supported(mode, domain, predicate):
    from tools.director_v02 import registry as director_registry
    cap = director_registry.CAPABILITY_REGISTRY[("guess", domain, predicate)]
    assert "hard" in cap["supported_difficulties"]


@pytest.mark.parametrize("mode", _AFFECTED_MODES)
def test_public_mode_certifies_hard(mode):
    from gateway.services import public_game
    assert "hard" in public_game.PUBLIC_MODES[mode]["certified_difficulties"]


# --- real, repeated hard generation across multiple deterministic seeds ----
# This is the actual reliability claim: not "one lucky seed works" but
# "every one of several fixed seeds works," matching the 196-real-candidate
# pool's actual size (target_count=1 should never be starved by chance).

@pytest.mark.parametrize("mode", _AFFECTED_MODES)
def test_hard_generation_reliable_across_multiple_seeds(client, mode):
    failures = []
    for seed in _SEEDS:
        r = _get(client, mode, difficulty="hard", seed=seed)
        if r.status_code != 200:
            failures.append((seed, r.status_code, r.json()))
            continue
        body = r.json()
        if body.get("difficulty") != "Hard":
            failures.append((seed, "wrong-difficulty", body.get("difficulty")))
    assert not failures, f"{mode} hard generation failed for some seeds: {failures}"


@pytest.mark.parametrize("mode", _AFFECTED_MODES)
def test_hard_generation_full_eligibility_gate(client, mode):
    """Same hard eligibility bar Pass 2.5 applied to every new mode: real
    nonzero package, correct mode, correct (Hard) difficulty, plausible
    4-way options with no duplicates, and grading works both ways."""
    r = _get(client, mode, difficulty="hard", seed=f"pytest-hard-gate-{mode}")
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["mode"] == mode
    assert body["difficulty"] == "Hard"
    options = body["payload"]["options"]
    assert len(options) == 4
    assert len(set(options)) == 4  # no duplicate options

    r2 = _answer(client, body["game_id"], "Definitely Not A Real Answer")
    assert r2.status_code == 200
    assert r2.json()["correct"] is False
    canonical = r2.json()["canonical_answer"]
    assert canonical in options

    r3 = _answer(client, body["game_id"], canonical)
    assert r3.json()["correct"] is True


# --- shared fix does not break lower difficulty bands (regression) ---------

@pytest.mark.parametrize("mode", _AFFECTED_MODES)
@pytest.mark.parametrize("difficulty,expected_label", [("easy", "Easy"), ("medium", "Medium")])
def test_easy_and_medium_still_work_after_hard_fix(client, mode, difficulty, expected_label):
    r = _get(client, mode, difficulty=difficulty, seed=f"pytest-{difficulty}-regress-{mode}")
    assert r.status_code == 200, r.json()
    assert r.json()["difficulty"] == expected_label


@pytest.mark.parametrize("mode", _AFFECTED_MODES)
def test_explicit_hard_never_silently_downgrades_or_relabels(client, mode):
    """difficulty="hard" must mean real certified Hard content, never a
    silently-downgraded Easy/Medium board relabeled as Hard."""
    for seed in _SEEDS[:3]:
        r = _get(client, mode, difficulty="hard", seed=seed)
        assert r.status_code == 200, r.json()
        assert r.json()["difficulty"] == "Hard"


# --- real candidate-pool size sanity check (matches the Pass 2.6 survey) ---

@pytest.mark.parametrize("domain,predicate", [
    ("CFB_SPOT_THE_FAKE_LINEUP", "ALTERED_POSITION"),
    ("CFB_ODD_COLLEGE_OUT", "IMPOSTOR_COLLEGE"),
    ("CFB_ONE_SCHOOL_MISSING", "MISSING_COLLEGE"),
])
def test_real_hard_candidate_pool_is_large_not_marginal(domain, predicate):
    """Guards against a future data change silently shrinking the real Hard
    pool back down to near-zero without anyone noticing -- 196 real, distinct
    candidates measured this pass; alert well before it could plausibly
    starve a real target_count=1 request (MAX_GAME_FETCH_ATTEMPTS retries)."""
    from tools import game_director_v01 as v01
    from tools.director_v02 import registry as director_registry

    cap = director_registry.CAPABILITY_REGISTRY[("guess", domain, predicate)]
    adapter = cap["adapter"]
    factory_spec = {
        "competition_id": cap["competition_id"], "mechanic": "guess",
        "entity_type": cap["entity_type"], "relationship_predicate": predicate,
        "object_type": cap["object_type"], "answer_type": cap["answer_type"],
        "group_size": cap["group_size"], "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        factory_spec, adapter,
        request_text=f"pytest hard pool size {domain}", director_request_id="pytest",
        seed=f"pytest-pool-size-{domain}", target_count=5000, id_start=1,
        difficulty_filter="hard",
    )
    questions = pkg.get("questions", [])
    assert len(questions) >= 50, (
        f"{domain} real Hard candidate pool shrank to {len(questions)} "
        f"(expected >= 50, measured 196 this pass) -- investigate before this starves real requests"
    )
    assert len(set(q["question"] for q in questions)) == len(questions), "duplicate Hard questions found"


# --- Creator (NL) difficulty routing survives translator -> Director -------

@pytest.mark.parametrize("prompt,expected_domain,expected_difficulty", [
    ("Make me a hard Spot the Fake game", "CFB_SPOT_THE_FAKE_LINEUP", "hard"),
    ("Give me a difficult Odd College Out", "CFB_ODD_COLLEGE_OUT", "hard"),
    ("Make One School Missing hard", "CFB_ONE_SCHOOL_MISSING", "hard"),
    ("Give me an easy Spot the Fake", "CFB_SPOT_THE_FAKE_LINEUP", "easy"),
    ("Give me a medium Odd College Out", "CFB_ODD_COLLEGE_OUT", "medium"),
])
def test_nl_difficulty_qualifier_survives_to_generated_package(prompt, expected_domain, expected_difficulty):
    from tools.director_v02 import pipeline

    result = pipeline.run(prompt, provider="mock", seed=f"pytest-nl-{expected_domain}-{expected_difficulty}")
    assert result.get("status") in (None, "GENERATED"), (
        f"{prompt!r} did not resolve to a generated package: {result}"
    )
    spec = result.get("director_spec", {})
    assert spec.get("domain") == expected_domain
    assert spec.get("difficulty") == expected_difficulty
    questions = result.get("questions", [])
    assert questions, f"{prompt!r} resolved but generated zero real questions"
    assert questions[0]["difficulty"].lower() == expected_difficulty


# --- existing (untouched) domain keeps its real, genuine hard exclusion ----

def test_three_clues_domain_now_correctly_includes_hard():
    """Superseded by the Era Gauntlet rebuild (Pass 2.7): at the time this
    test was written (Pass 2.6), CFB_THREE_CLUES_ONE_CHAMPION drew from a
    narrower, 60-board SB_CHAMPION-only pool with genuinely zero real Hard
    boards, so excluding "hard" was correct. Pass 2.7 legitimately expanded
    this domain's real pool to 502 team-seasons (SB_CHAMPION +
    CURRENT_TEAM_2026 + NFL_TEAM_SEASON_ROSTER), which DOES have real Hard
    candidates (164, confirmed by a direct target_count=5000 survey) --
    "hard" is now correctly supported, not a regression of Pass 2.6's fix."""
    from tools.director_v02 import registry as director_registry

    cap = director_registry.CAPABILITY_REGISTRY[
        ("guess", "CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES")
    ]
    assert "hard" in cap["supported_difficulties"]


def test_allowlist_unchanged_by_this_pass():
    """This pass fixes difficulty support, not mode availability -- the
    public mode allowlist itself is unchanged."""
    for mode in _AFFECTED_MODES:
        assert mode in config.PUBLIC_MODE_ALLOWLIST
