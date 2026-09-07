"""Absolute Final Closeout (Item 13): final 500+-run content-depth stress
test across the named modes -- Franchise Marathon, Era Gauntlet, Three
Clues One Champion, NFL Draft History, CFB Rivalry Trivia, NFL Super Bowl
History, One School Missing, and NFL Who Am I (Player From Clues).

Each mode is driven directly through its real adapter/pipeline (the same
generation path the public API uses under the hood -- see each mode's own
diversification test file for the narrower, mode-specific regression
coverage this file does not duplicate). This file's job is the CONSOLIDATED
proof: run enough real generations across ALL of them in one pass (500+
total) and report duplicate rate, top-entity concentration, and difficulty
spread per mode, so the final report can cite one consistent, reproducible
measurement rather than stitching together numbers from separate ad hoc
investigations.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_TOTAL_GENERATED = {}  # populated by each test, checked by the final summary test


def _guess_pipeline_answers(domain, predicate, adapter, *, entity_type, object_type, answer_type,
                             filters=None, runs=6, target_count=100, seed_prefix="stress"):
    from tools import game_director_v01 as v01

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": entity_type,
        "relationship_predicate": predicate, "object_type": object_type,
        "answer_type": answer_type, "group_size": 4, "filters": filters or {},
    }
    all_questions = []
    for i in range(runs):
        pkg = v01.generate_package_from_spec(
            spec, adapter, request_text="pytest", director_request_id="pytest",
            seed=f"{seed_prefix}-{domain}-{i}", target_count=target_count, id_start=1,
        )
        all_questions.extend(pkg["questions"])
    return all_questions


def _report(name, questions, *, min_expected=1):
    assert len(questions) >= min_expected, f"{name}: only {len(questions)} real questions generated"
    _TOTAL_GENERATED[name] = len(questions)
    answers = Counter(q["answer"] for q in questions)
    texts = Counter(q["question"] for q in questions)
    top_entity, top_count = answers.most_common(1)[0]
    difficulty = Counter(q["difficulty"] for q in questions)
    dup_question_rate = 1 - (len(texts) / len(questions))
    print(f"\n[stress:{name}] n={len(questions)} distinct_answers={len(answers)} "
          f"top={top_entity!r}({top_count/len(questions):.1%}) "
          f"dup_question_rate={dup_question_rate:.1%} difficulty={dict(difficulty)}")
    return {
        "n": len(questions), "distinct_answers": len(answers),
        "top_entity": top_entity, "top_share": top_count / len(questions),
        "dup_question_rate": dup_question_rate, "difficulty": dict(difficulty),
    }


def test_franchise_marathon_stress():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import franchise_marathon as fm

    franchises = ["Cowboys", "Patriots", "Packers", "Steelers", "49ers", "Chiefs", "Eagles", "Ravens"]
    all_q = []
    for fr in franchises:
        spec = {
            "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_franchise_marathon_stage",
            "relationship_predicate": "FRANCHISE_MARATHON_STAGE", "object_type": "mixed",
            "answer_type": "mixed", "group_size": 4, "filters": {"franchise_name": fr},
        }
        pkg = v01.generate_package_from_spec(
            spec, fm, request_text="pytest", director_request_id="pytest",
            seed=f"stress-fm-{fr}", target_count=8, id_start=1,
        )
        all_q.extend(pkg["questions"])
    r = _report("franchise_marathon", all_q, min_expected=40)
    assert r["top_share"] <= 0.20  # 8 franchises x ~8 stages -- no single answer should dominate


def test_era_gauntlet_stress():
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as tcoc

    q = _guess_pipeline_answers(
        "era_gauntlet", "TEAM_SEASON_FROM_THREE_CLUES", tcoc,
        entity_type="nfl_sb_champion_offense_board_college", object_type="team_season", answer_type="team_season",
        filters={"era_gauntlet": True}, runs=15, target_count=7, seed_prefix="stress-era",
    )
    _report("era_gauntlet", q, min_expected=60)


def test_three_clues_one_champion_stress():
    from tools.quiz_export.adapters import cfb_three_clues_one_champion as tcoc

    q = _guess_pipeline_answers(
        "three_clues", "TEAM_SEASON_FROM_THREE_CLUES", tcoc,
        entity_type="nfl_sb_champion_offense_board_college", object_type="team_season", answer_type="team_season",
        runs=6, target_count=100, seed_prefix="stress-3c",
    )
    r = _report("three_clues_one_champion", q, min_expected=200)
    assert r["top_share"] <= 0.10


def test_nfl_draft_history_stress():
    from tools.quiz_export.adapters import draft as draft_adapter

    q = _guess_pipeline_answers(
        "nfl_draft", "DRAFTED_BY", draft_adapter,
        entity_type="nfl_player", object_type="team", answer_type="team",
        runs=6, target_count=100, seed_prefix="stress-draft",
    )
    r = _report("nfl_draft_history", q, min_expected=200)
    assert r["top_share"] <= 0.10  # 32 real teams -- no team should dominate the answer key


def test_cfb_rivalry_trivia_stress():
    from tools.quiz_export.adapters import cfb_rivalry_trivia

    q = _guess_pipeline_answers(
        "cfb_rivalry_trivia", "CORRECT_TRIVIA_ANSWER", cfb_rivalry_trivia,
        entity_type="cfb_trivia_question", object_type="trivia_answer", answer_type="text",
        runs=6, target_count=100, seed_prefix="stress-rivalry",
    )
    _report("cfb_rivalry_trivia", q, min_expected=200)


def test_nfl_super_bowl_history_stress():
    from tools.quiz_export.adapters import nfl_super_bowl

    q = _guess_pipeline_answers(
        "nfl_super_bowl", "WON_CHAMPIONSHIP", nfl_super_bowl,
        entity_type="nfl_super_bowl_result", object_type="team", answer_type="team",
        runs=6, target_count=100, seed_prefix="stress-sb",
    )
    r = _report("nfl_super_bowl_history", q, min_expected=60)
    assert r["top_share"] <= 0.15


def test_one_school_missing_stress():
    from tools.quiz_export.adapters import cfb_one_school_missing

    q = _guess_pipeline_answers(
        "one_school_missing", "MISSING_COLLEGE", cfb_one_school_missing,
        entity_type="nfl_sb_champion_offense_board_college", object_type="college", answer_type="college",
        runs=6, target_count=100, seed_prefix="stress-osm",
    )
    r = _report("one_school_missing", q, min_expected=200)
    assert r["top_share"] <= 0.10


def test_nfl_who_am_i_stress():
    from tools.director_v04 import player_from_clues

    all_puzzles = []
    for i in range(20):
        pkg = player_from_clues.build_package(seed=f"stress-whoami-{i}", target_count=25)
        within_batch = Counter("|".join(f"{c['clue_type']}={c['value']}" for c in p["clues"]) for p in pkg["puzzles"])
        assert all(n == 1 for n in within_batch.values()), "a duplicate clue sequence appeared within one batch"
        all_puzzles.extend(pkg["puzzles"])
    assert len(all_puzzles) >= 100, f"only {len(all_puzzles)} real Who Am I puzzles generated"
    _TOTAL_GENERATED["nfl_who_am_i"] = len(all_puzzles)
    targets = Counter(p["answer"]["player_id"] for p in all_puzzles)
    top_pid, top_count = targets.most_common(1)[0]
    clue_seqs = Counter("|".join(f"{c['clue_type']}={c['value']}" for c in p["clues"]) for p in all_puzzles)
    dup_rate = 1 - (len(clue_seqs) / len(all_puzzles))
    print(f"\n[stress:nfl_who_am_i] n={len(all_puzzles)} distinct_targets={len(targets)} "
          f"top_target_share={top_count/len(all_puzzles):.1%} dup_clue_sequence_rate={dup_rate:.1%}")
    assert top_count / len(all_puzzles) <= 0.10
    # Clue selection is deterministic PER PLAYER (broadest-still-narrowing
    # first, alphabetical tie-break, no RNG -- see build_puzzle()'s own
    # docstring) -- only WHICH players get selected into a given 25-puzzle
    # batch varies by seed. So the same player recurring across different
    # seeds' batches (and therefore an identical clue sequence, dup_rate
    # printed above) is real, expected behavior, not a duplicate-content
    # bug -- the actual guarantee this project makes is zero duplicates
    # WITHIN one batch, already checked per-seed in the loop above.


def test_final_summary_exceeds_five_hundred_total_real_generations():
    """The consolidated Item 13 requirement: 500+ real generations across
    the named modes in one reproducible pass. Depends on every test above
    having already populated _TOTAL_GENERATED -- pytest runs a module's
    tests in definition order by default, so this stays last."""
    total = sum(_TOTAL_GENERATED.values())
    print(f"\n[stress:TOTAL] {dict(_TOTAL_GENERATED)} => {total} real generations across "
          f"{len(_TOTAL_GENERATED)} modes")
    assert total >= 500, f"only {total} total real generations across {list(_TOTAL_GENERATED)}"
    assert len(_TOTAL_GENERATED) >= 8, "expected all 8 named modes to have run"
