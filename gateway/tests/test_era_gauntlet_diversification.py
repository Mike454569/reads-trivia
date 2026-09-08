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
    """Real user-reported bug (screenshot): a '1960s'-labeled stage showed a
    real 1974 Pittsburgh Steelers question with distractor options from
    1969/1983/1985 -- spanning 3 different decades. Root cause was a
    'near in years' (_DISTRACTOR_ERA_WINDOW_YEARS=12) distractor window
    that fell back to a fully-unscoped 502-board pool whenever fewer than
    3 same-window candidates existed. Fixed with a strict same-decade-
    first pool (every real decade 1960s-2020s has >=4 real boards, so the
    strict pool is always achievable -- verified directly against the live
    Engine DB before writing this fix). This test enforces the ACTUAL
    user complaint: every option (correct + all distractors) must share
    the same real decade, not just be 'within 30 years' of each other."""
    pkg = _generate("pytest-era-leak-seed", target_count=10, filters={"era_gauntlet": True})
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        decades = set()
        for opt in q["options"]:
            year = int(opt.split(" ", 1)[0])
            decades.add((year // 10) * 10)
        assert len(decades) == 1, f"options span multiple decades {decades}: {q['options']}"


def test_era_gauntlet_distractors_never_fall_back_to_the_unscoped_pool():
    """Swept regression: across many real seeds, the strict same-decade
    pool must always have >=3 candidates (real per-decade board counts
    measured directly: 1960s=4, 1970s=10, 1980s=10, 1990s=10, 2000s=137,
    2010s=293, 2020s=38 -- every decade clears the bar), so the old
    unscoped-fallback path should never actually trigger in practice."""
    for i in range(40):
        pkg = _generate(f"pytest-era-no-fallback-{i}", target_count=10, filters={"era_gauntlet": True})
        assert pkg["qa_status"] == "PASSED"
        for q in pkg["questions"]:
            decades = {(int(opt.split(" ", 1)[0]) // 10) * 10 for opt in q["options"]}
            assert len(decades) == 1, f"seed {i}: options span multiple decades {decades}: {q['options']}"


def test_era_gauntlet_visual_payload_reports_the_real_decade_label():
    """The frontend used to hardcode a fixed ['1960s', ..., '2020s'] array
    indexed by stage number, which silently broke once the SB-cap redesign
    let a run skip a decade or repeat one. The adapter now exposes the
    real decade for each stage (and the real, full per-run sequence) via
    the existing visual_payload channel so the frontend never has to
    guess the stage-to-decade mapping."""
    pkg = _generate("pytest-era-visual-payload", target_count=10, filters={"era_gauntlet": True})
    assert pkg["qa_status"] == "PASSED"
    questions = pkg["questions"]
    assert questions, "expected a real, non-empty gauntlet"
    for q in questions:
        vp = q.get("visual_payload")
        assert vp and "era_decade_label" in vp, f"missing visual_payload.era_decade_label: {q}"
        answer_year = int(q["answer"].split(" ", 1)[0])
        expected = f"{(answer_year // 10) * 10}s"
        assert vp["era_decade_label"] == expected, (vp["era_decade_label"], expected)


def test_era_gauntlet_sequence_labels_match_the_real_stage_order():
    """era_sequence_labels (when present) must be the exact real, full
    7-stage decade sequence for this run -- the frontend's replacement for
    the old hardcoded array."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    try:
        for seed in ("pytest-era-seq-a", "pytest-era-seq-b", "pytest-era-seq-c"):
            candidates = adapter.fetch_ordered_candidates(c, seed, {"era_gauntlet": True})
            assert candidates, "expected a real, non-empty gauntlet candidate list"
            expected_sequence = [f"{(b['season'] // 10) * 10}s" for b in candidates]
            rng = engine.seeded(seed)
            guard = DuplicateGuard()
            for board in candidates:
                result = adapter.evaluate(c, board, rng, guard)
                assert isinstance(result, dict), result
                vp = result["visual_payload"]
                assert vp.get("era_sequence_labels") == expected_sequence
                guard.record(result["question"], result.get("_audit", {}).get("entity_key"))
    finally:
        c.close()


def test_era_gauntlet_board_mutation_does_not_leak_across_unrelated_requests():
    """Safety guard for the in-place board mutation _era_gauntlet_candidates()
    uses to attach _era_sequence_labels: fetch_all_boards() clears and
    rebuilds its own module-level cache on every call (verified directly in
    _group_board_common.py), so every call returns fresh dict objects --
    mutating them must never bleed into a later, unrelated (e.g. plain
    Three Clues, non-gauntlet) request."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter

    c = engine.connect()
    try:
        adapter.fetch_ordered_candidates(c, "pytest-mutation-a", {"era_gauntlet": True})
        plain_boards = adapter.fetch_ordered_candidates(c, "pytest-mutation-b", {})
        assert not any("_era_sequence_labels" in b for b in plain_boards), (
            "a plain (non-gauntlet) request picked up stale _era_sequence_labels from an earlier gauntlet run"
        )
    finally:
        c.close()


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


# --- Absolute Final Closeout: hard SB-stage cap (real data-shape fix) ------

def test_era_gauntlet_never_exceeds_the_hard_sb_stage_cap():
    """The real regression this fix closes: 1960s-1990s are each 100% real
    SB_CHAMPION-only (zero non-champion alternative exists in this Engine
    for those decades), so the OLD one-stage-per-decade algorithm forced
    4 of 7 stages to be Super Bowl content on every single run regardless
    of randomness -- measured directly at 71.4% SB share in one real
    playthrough. The fix caps chosen SB-only decades at 2, filling the
    rest from the real, deep 2000s/2010s/2020s non-champion pools. Swept
    across 500 real seeds -- the count-based cap must never break."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter

    factory_spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES", "object_type": "team_season",
        "answer_type": "team_season", "group_size": 4, "filters": {"era_gauntlet": True},
    }
    violations = []
    zero_stage_runs = 0
    for i in range(500):
        pkg = v01.generate_package_from_spec(
            factory_spec, adapter, request_text="pytest", director_request_id="pytest",
            seed=f"pytest-sb-cap-sweep-{i}", target_count=10, id_start=1,
        )
        n = len(pkg["questions"])
        if n == 0:
            zero_stage_runs += 1
            continue
        sb_count = sum(1 for q in pkg["questions"] if "won the Super Bowl" in q["notes"])
        if sb_count > 2:
            violations.append((i, sb_count, n))
    assert zero_stage_runs == 0, "every real seed must produce a real, non-empty gauntlet"
    assert violations == [], f"runs exceeding the hard 2-SB-stage cap: {violations}"


def test_era_gauntlet_sb_only_decades_are_spread_not_always_the_same_two():
    """The stratified-sample fix: which 2 of the 4 real SB-only decades
    (1960s/1970s/1980s/1990s) get chosen must genuinely vary across seeds,
    not silently collapse to the same pair every time."""
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as adapter

    factory_spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES", "object_type": "team_season",
        "answer_type": "team_season", "group_size": 4, "filters": {"era_gauntlet": True},
    }
    seen_decade_pairs = set()
    for i in range(60):
        pkg = v01.generate_package_from_spec(
            factory_spec, adapter, request_text="pytest", director_request_id="pytest",
            seed=f"pytest-sb-spread-{i}", target_count=10, id_start=1,
        )
        sb_seasons = tuple(sorted(
            int(q["notes"].split()[1]) for q in pkg["questions"] if "won the Super Bowl" in q["notes"]
        ))
        decades = tuple(sorted({(s // 10) * 10 for s in sb_seasons}))
        seen_decade_pairs.add(decades)
    assert len(seen_decade_pairs) >= 3, (
        f"expected the chosen SB-only decade pair to vary meaningfully across seeds, only saw {seen_decade_pairs}"
    )


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


# --- Closeout pass (Part 5): STATISTICAL_LEADER / NOTABLE_GAME clue families --

def test_statistical_leader_clue_family_appears_in_the_real_pool():
    """New real, non-roster clue family: a team-season's real passing/
    rushing/receiving yardage leader (player_season_stats), added alongside
    OPPONENT/SCORE/COACH/SB_MVP/RECORD/COLLEGE."""
    pkg = _generate("pytest-stat-leader-seed", target_count=800)
    assert any("leader that season gained" in q["question"] and "yards" in q["question"]
               for q in pkg["questions"])


def test_notable_game_clue_family_appears_in_the_real_pool():
    """New real, non-roster, deterministic clue family: a team-season's
    real biggest margin-of-victory game (games table home/away scores) --
    never a subjective 'craziest game' label."""
    pkg = _generate("pytest-notable-game-seed", target_count=800)
    assert any("margin of victory" in q["question"] for q in pkg["questions"])


def test_statistical_leader_clue_never_fabricates_a_zero_stat():
    """A team-season with no real passing/rushing/receiving production on
    file must simply not offer this clue -- never a fabricated 0-yard
    'leader'."""
    from tools.quiz_export.adapters import _champion_clue_common as clue_common
    from tools.quiz_export import engine

    c = engine.connect()
    try:
        cache = clue_common._load_stat_cache(c)
        for key, entries in list(cache.items())[:200]:
            for label, name, yards in entries:
                assert yards > 0, f"{key} {label} clue would report a non-positive yardage: {yards}"
    finally:
        c.close()


def test_notable_game_margin_is_always_a_real_positive_number():
    from tools.quiz_export.adapters import _champion_clue_common as clue_common
    from tools.quiz_export import engine

    c = engine.connect()
    try:
        cache = clue_common._load_game_margin_cache(c)
        for key, (margin, opponent) in list(cache.items())[:200]:
            assert margin > 0
            assert opponent
    finally:
        c.close()


def test_ranking_family_deliberately_not_offered_for_this_nfl_only_domain():
    """Explicit, documented scope decision (Part 5): this adapter's whole
    domain is NFL team-seasons, which have no real weekly/final poll
    ranking the way CFB does -- RANKING must never be fabricated here."""
    pkg = _generate("pytest-no-fake-ranking-seed", target_count=800)
    for q in pkg["questions"]:
        assert "ranked" not in q["question"].lower() and "ranking" not in q["question"].lower()
