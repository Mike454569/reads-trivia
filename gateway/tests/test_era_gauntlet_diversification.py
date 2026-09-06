"""Era Gauntlet rebuild (Pass 2.7): permanent regression coverage for the
CFB_THREE_CLUES_ONE_CHAMPION domain's diversification away from 100% Super
Bowl content, and for the real N+1 performance bug this pass found and
fixed while building it (evaluate() re-calling group_common.fetch_all_boards()
once per candidate -- ~73s for a 502-board pool, enough to blow
generation.py's 45s timeout on every public request).

Root cause audited directly: cfb_three_clues_one_champion.py (which backs
BOTH cfb_three_clues_guess and era_gauntlet_guess) used to import only
_college_offense_curated_common's 60-board SB_CHAMPION table -- 100% Super
Bowl content by construction, not by design choice, since
_group_board_common.py's wider 595-board pool already existed and was
already used by 3 sibling adapters (Spot the Fake, Odd College Out, One
School Missing) in the same directory.
"""
import time

import pytest


def _real_available_clues(board):
    from tools.quiz_export.adapters import _champion_clue_common as clue_common
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        return clue_common.real_available_clues(c, board)
    finally:
        c.close()


def _generate(seed, target_count=500, filters=None):
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter
    factory_spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES", "object_type": "team_season",
        "answer_type": "team_season", "group_size": 4, "filters": filters or {},
    }
    return v01.generate_package_from_spec(
        factory_spec, adapter, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


# --- the core diversification claim -----------------------------------------

def test_pool_is_no_longer_only_super_bowl_champions():
    from tools.quiz_export.adapters import _group_board_common as group_common
    from tools.quiz_export import engine
    c = engine.connect()
    boards = group_common.fetch_all_boards(c, pool_kinds=("SB_CHAMPION", "CURRENT_TEAM_2026", "NFL_TEAM_SEASON_ROSTER"))
    c.close()
    by_kind = {}
    for b in boards:
        by_kind[b["pool_kind"]] = by_kind.get(b["pool_kind"], 0) + 1
    assert by_kind.get("SB_CHAMPION", 0) > 0
    assert by_kind.get("NFL_TEAM_SEASON_ROSTER", 0) > 0
    assert by_kind.get("CURRENT_TEAM_2026", 0) > 0
    # The real point: Super Bowl content is a real minority of the pool,
    # not the foundation -- matches the ~12% measured this pass.
    total = sum(by_kind.values())
    sb_share = by_kind.get("SB_CHAMPION", 0) / total
    assert sb_share < 0.25, f"SB_CHAMPION share is {sb_share:.1%}, expected a real minority"


def test_generated_questions_are_mostly_non_super_bowl():
    pkg = _generate("pytest-diversify-seed", target_count=500)
    assert pkg["qa_status"] == "PASSED"
    questions = pkg["questions"]
    assert len(questions) >= 100
    sb_count = sum(1 for q in questions if "won the Super Bowl" in q["notes"])
    sb_share = sb_count / len(questions)
    assert sb_share < 0.25, f"{sb_share:.1%} of generated questions are Super Bowl-sourced, expected a real minority"
    # And genuinely non-trivial non-roster family variety, not just COLLEGE.
    families_seen = set()
    for q in questions:
        inside = q["notes"].split("(")[1].split(")")[0]
        families_seen.update(f.strip() for f in inside.split(","))
    assert {"COACH", "RECORD"} <= families_seen, f"expected real non-championship families, saw {families_seen}"


def test_non_champion_boards_never_claim_they_won_the_super_bowl():
    """Real bug this pass fixed before it could ship: the old hardcoded
    question/notes wording always said "Guess the Super Bowl-winning team"
    and "won the Super Bowl" -- which would be FALSE for a real
    non-champion team-season now that the pool includes them."""
    pkg = _generate("pytest-wording-seed", target_count=300)
    for q in pkg["questions"]:
        if "won the Super Bowl" not in q["notes"]:
            assert "Super Bowl-winning" not in q["question"], (
                f"non-champion question falsely claims Super Bowl-winning: {q['question']!r}"
            )


# --- the real N+1 performance bug -------------------------------------------

def test_generation_does_not_regress_into_the_n_plus_one_bug():
    """Real bug found by this pass's own test suite: evaluate() used to
    re-call group_common.fetch_all_boards() once per candidate (502 real
    calls for a 502-board pool), which clears and rebuilds that function's
    own internal cache every time -- ~73s total, enough to blow
    generation.py's real 45s GENERATION_TIMEOUT_SECONDS on every public
    request. Fixed by caching fetch_ordered_candidates()'s own board list
    and having evaluate() reuse it. A generous 10s budget here (vs. the
    ~0.4s actually measured) leaves real headroom for this machine's own
    documented ambient CPU variance while still catching a real regression
    back into O(n^2) territory."""
    t0 = time.perf_counter()
    pkg = _generate("pytest-perf-seed", target_count=500)
    elapsed = time.perf_counter() - t0
    assert pkg["qa_status"] == "PASSED"
    assert elapsed < 10.0, f"generation took {elapsed:.1f}s -- likely regressed back into the N+1 bug"


def test_public_route_hard_difficulty_completes_well_within_timeout(client):
    """The exact real-world symptom this pass's own regression test caught:
    a real HTTP request through the public route, not just a direct
    generate_package_from_spec() call."""
    t0 = time.perf_counter()
    r = client.get("/v1/public/game", params={"mode": "cfb_three_clues_guess", "difficulty": "hard", "seed": "pytest-route-perf"})
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200, r.json()
    assert elapsed < 15.0, f"request took {elapsed:.1f}s -- likely regressed back into the N+1 bug"


# --- era anti-leak rule -------------------------------------------------

def test_era_gauntlet_distractors_are_era_plausible():
    """Section 12's anti-leak rule: distractors must be plausible teams
    from roughly the same period, not an unscoped mix across 60 years."""
    pkg = _generate("pytest-era-leak-seed", target_count=10, filters={"era_gauntlet": True})
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        seasons = []
        for opt in q["options"]:
            year_str = opt.split(" ", 1)[0]
            seasons.append(int(year_str))
        # The correct answer's season and every distractor's season should
        # fall within a real, plausible window of each other -- not one
        # option from the 1960s next to another from the 2020s.
        assert max(seasons) - min(seasons) <= 30, f"options span too wide an era: {q['options']}"


def test_era_gauntlet_still_progresses_through_seven_real_eras(client):
    seen_prompts = set()
    for stage in range(7):
        r = client.get("/v1/public/game", params={"mode": "era_gauntlet_guess", "seed": "pytest-era-fixed-2", "stage": stage})
        assert r.status_code == 200, r.json()
        seen_prompts.add(r.json()["payload"]["prompt"])
    assert len(seen_prompts) == 7, "each of the 7 real eras must still be a distinct real question"


def test_era_gauntlet_seven_stages_are_not_all_super_bowl_boards():
    """The exact complaint this pass fixes: 'A seven-stage Era Gauntlet
    should not contain seven roster/Super Bowl questions.'"""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter
    factory_spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES", "object_type": "team_season",
        "answer_type": "team_season", "group_size": 4, "filters": {"era_gauntlet": True},
    }
    non_sb_seen = 0
    for seed in ["era-mix-a", "era-mix-b", "era-mix-c"]:
        pkg = v01.generate_package_from_spec(
            factory_spec, adapter, request_text="pytest", director_request_id="pytest",
            seed=seed, target_count=10, id_start=1,
        )
        non_sb_seen += sum(1 for q in pkg["questions"] if "won the Super Bowl" not in q["notes"])
    assert non_sb_seen > 0, "expected at least one non-Super-Bowl stage across 3 real 7-stage runs"


# --- DRAFT_CLASS/HONOR_GROUP correctly excluded (no coherent team+season) --

def test_draft_class_and_honor_group_never_appear_as_answers():
    """These pool_kinds represent a draft class or an All-Pro class, not a
    team's season -- "guess the team AND season" has no coherent answer for
    them, so they must never surface here (they stay exclusive to Odd
    College Out / One School Missing / Spot the Fake)."""
    pkg = _generate("pytest-no-draft-class-seed", target_count=300)
    for q in pkg["questions"]:
        assert "NFL Draft, Round 1" not in q["question"] and "NFL Draft" not in q["answer"]
        assert "All-Pro" not in q["answer"]
