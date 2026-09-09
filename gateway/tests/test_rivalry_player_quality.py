"""Player Experience pass: real, confirmed-live Rivalries defects and their
permanent regression coverage.

The owner manually played the deployed application and found malformed
questions reaching production -- "Which school is Ole Miss's rival in the
game known as?" and "Which school is NC State's rival in the game known
as?" -- both real LSU-Ole Miss and North Carolina-NC State rows in
cfb_rivalries have a real "-" placeholder nickname (already correctly
normalized to "" by cfb_rivalry.py's own _real_nickname()), but the OLD
question template unconditionally appended the literal phrase "in the game
known as" regardless, leaving it dangling with nothing after it whenever
there was no real nickname. This file locks in the fix, the associated
generic-filler-explanation fix, and the within-game composition fix for
BOTH real Rivalries adapters (cfb_rivalry.py / cfb_rivalry_lookup_guess,
and cfb_rivalry_trivia.py / cfb_rivalry_guess).
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

_RIVALRY_SPEC = {
    "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_rivalry",
    "relationship_predicate": "RIVAL_OF", "object_type": "school",
    "answer_type": "school", "group_size": 4, "filters": {},
}
_TRIVIA_SPEC = {
    "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_trivia_question",
    "relationship_predicate": "CORRECT_TRIVIA_ANSWER", "object_type": "trivia_answer",
    "answer_type": "text", "group_size": 4, "filters": {},
}


def _generate_rivalry(seed: str, target_count: int = 96):
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_rivalry
    return v01.generate_package_from_spec(
        _RIVALRY_SPEC, cfb_rivalry, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


def _generate_trivia(seed: str, target_count: int = 10):
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_rivalry_trivia
    return v01.generate_package_from_spec(
        _TRIVIA_SPEC, cfb_rivalry_trivia, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


# --- Part 2A/3: no dangling/malformed question text ---------------------------

def test_no_rivalry_without_a_real_nickname_produces_a_dangling_question():
    """Direct reproduction of the exact reported bug: LSU-Ole Miss and
    North Carolina-NC State both have a real "-" placeholder nickname."""
    pkg = _generate_rivalry("pytest-dangling-check", target_count=96)
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        text = q["question"]
        assert not text.rstrip().endswith("as?"), text
        assert "known as?" not in text, text
        assert "known as \"\"" not in text, text
        # Every question must end in a real, complete sentence -- no
        # dangling connective word right before the final "?".
        for bad_ending in ("as?", "against?", "in the?", "called?", "known as ?"):
            assert not text.rstrip().endswith(bad_ending), text


def test_ole_miss_and_nc_state_specifically_now_resolve_to_a_complete_question():
    """Direct, deterministic reproduction of the exact two matchups the
    owner saw malformed in production -- calls evaluate() directly with a
    forced WHO_IS_RIVAL family (the exact family shown in both original
    screenshots) rather than relying on the adapter's own random per-seed
    family choice to happen to land on it."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    for matchup, ask_name in (("LSU vs. Ole Miss (SEC)", "Ole Miss"), ("North Carolina vs. NC State (ACC)", "NC State")):
        row = dict(c.execute(
            "SELECT rivalry_id, matchup, school_a_id, school_a, school_b_id, school_b, nickname, "
            "trophy, series_record, fun_fact FROM cfb_rivalries WHERE matchup = ?", (matchup,),
        ).fetchone())
        assert row["nickname"] == "-", (matchup, row["nickname"])  # confirms this is really the affected row
        if row["school_a"] == ask_name:
            candidate = {**row, "ask_id": row["school_a_id"], "ask_name": row["school_a"],
                         "answer_id": row["school_b_id"], "answer_name": row["school_b"]}
        else:
            candidate = {**row, "ask_id": row["school_b_id"], "ask_name": row["school_b"],
                         "answer_id": row["school_a_id"], "answer_name": row["school_a"]}
        import random
        rng = random.Random(f"pytest-force-who-is-rival-{matchup}")
        # Force WHO_IS_RIVAL by construction: patch _choose_family via a
        # monkeypatch-free trick isn't available at module scope here, so
        # instead call the real family-selection loop until it lands on
        # WHO_IS_RIVAL (guaranteed reachable since it's always in the
        # available list) rather than assume any specific rng draw.
        family = None
        for attempt in range(50):
            family = adapter._choose_family(candidate, random.Random(f"{matchup}-{attempt}"))
            if family == "WHO_IS_RIVAL":
                break
        assert family == "WHO_IS_RIVAL"
        guard = DuplicateGuard(track_entity=True)
        # Re-run evaluate() with rng seeds until WHO_IS_RIVAL is chosen inside it too.
        result = None
        for attempt in range(50):
            r = adapter.evaluate(c, candidate, random.Random(f"{matchup}-eval-{attempt}"), guard)
            if isinstance(r, dict) and r["question"].startswith("Which school is"):
                result = r
                break
        assert result is not None, f"WHO_IS_RIVAL form never reproduced for {matchup} across 50 attempts"
        assert result["question"] == f"Which school is {ask_name}’s real college football rival?"


def test_a_real_nickname_still_renders_correctly():
    """Regression guard the other direction -- fixing the no-nickname case
    must not break the common case where a real nickname exists. Calls the
    real evaluate() directly (retrying rng seeds until it lands on
    WHO_IS_RIVAL, since Iron Bowl also has a real trophy/series leader and
    a random draw could legitimately land on a different family)."""
    import random

    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    row = dict(c.execute(
        "SELECT rivalry_id, matchup, school_a_id, school_a, school_b_id, school_b, nickname, "
        "trophy, series_record, fun_fact FROM cfb_rivalries WHERE matchup = 'Alabama vs. Auburn'"
    ).fetchone())
    assert row["nickname"] == "Iron Bowl"
    candidate = {**row, "ask_id": row["school_a_id"], "ask_name": row["school_a"],
                 "answer_id": row["school_b_id"], "answer_name": row["school_b"]}
    guard = DuplicateGuard(track_entity=True)
    result = None
    for attempt in range(50):
        r = adapter.evaluate(c, candidate, random.Random(f"iron-bowl-eval-{attempt}"), guard)
        if isinstance(r, dict) and r["question"].startswith("Which school is"):
            result = r
            break
    assert result is not None, "WHO_IS_RIVAL form never reproduced for Iron Bowl across 50 attempts"
    assert result["question"].endswith('known as "Iron Bowl"?')


# --- Part 2B: trophy provenance ------------------------------------------------

def test_trophy_family_never_selected_without_real_trophy_data():
    """Confirmed already-safe by direct code audit (_choose_family only
    ever adds "TROPHY" to the option list when _real_trophy(row) is
    truthy) -- locked in here so it can't silently regress. A rivalry
    being named after something (e.g. a real nickname) does NOT by itself
    prove a trophy exists; this must always come from the real, separate
    `trophy` column, never inferred from the nickname."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry as adapter

    c = engine.connect()
    rows = [dict(r) for r in c.execute(
        "SELECT rivalry_id, matchup, school_a_id, school_a, school_b_id, school_b, nickname, "
        "trophy, series_record, fun_fact FROM cfb_rivalries "
        "WHERE school_a_id IS NOT NULL AND school_b_id IS NOT NULL"
    ).fetchall()]
    no_trophy_rows = [r for r in rows if adapter._real_trophy(r) == ""]
    assert len(no_trophy_rows) >= 10, "expected a real, measured population of no-trophy rivalries to test against"
    import random
    rng = random.Random("pytest-trophy-provenance")
    for row in no_trophy_rows:
        candidate = {"rivalry_id": row["rivalry_id"], "nickname": row["nickname"], "trophy": row["trophy"],
                     "series_record": row["series_record"], "fun_fact": row["fun_fact"],
                     "ask_id": row["school_a_id"], "ask_name": row["school_a"],
                     "answer_id": row["school_b_id"], "answer_name": row["school_b"]}
        for _ in range(20):
            assert adapter._choose_family(candidate, rng) != "TROPHY"


def test_every_real_trophy_question_answers_with_the_real_trophy_column():
    pkg = _generate_rivalry("pytest-trophy-answer-check", target_count=96)
    trophy_questions = [q for q in pkg["questions"] if q["question"].startswith("What real trophy")]
    assert len(trophy_questions) >= 1
    from tools.quiz_export import engine
    c = engine.connect()
    real_trophies = {r[0] for r in c.execute(
        "SELECT trophy FROM cfb_rivalries WHERE trophy IS NOT NULL AND trophy != '' AND trophy != '-'"
    ).fetchall()}
    for q in trophy_questions:
        assert q["answer"] in real_trophies, q["answer"]


# --- Part 2D: explanations must teach something, not restate the premise ------

def test_explanations_are_never_the_generic_filler_pattern():
    """Real, confirmed-live bug: notes used to read exactly
    "X and Y play in a rivalry game." for any rivalry with no real
    nickname -- that just restates the question's own premise and teaches
    the player nothing (Part 2D's bad example, reproduced verbatim by the
    old code). Every one of the 48 real rivalries has at least one real
    extra fact on file (measured directly), so this should never recur."""
    pkg = _generate_rivalry("pytest-filler-check", target_count=96)
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        notes = q["notes"]
        assert notes, "every question must have a real explanation"
        assert not notes.rstrip().endswith("play in a rivalry game."), notes
        assert "play in a rivalry game." not in notes or len(notes) > len("X and Y play in a rivalry game.") + 5


def test_explanations_include_real_fun_facts_when_available():
    """The dataset's fun_fact column is genuinely informative real content
    (measured: rich, specific historical facts) that the old notes only
    used as a last resort -- confirm it's actually surfaced now."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry as adapter

    c = engine.connect()
    row = dict(c.execute(
        "SELECT * FROM cfb_rivalries WHERE matchup = 'Alabama vs. Auburn'"
    ).fetchone())
    assert row is not None
    real_fun_fact = adapter._real_fun_fact(row)
    assert real_fun_fact, "Iron Bowl must have a real fun_fact on file for this test to mean anything"
    candidate = {**row, "ask_name": row["school_a"], "answer_name": row["school_b"]}
    notes = adapter._compose_notes(candidate, "WHO_IS_RIVAL", adapter._real_nickname(row), row["school_b"])
    assert real_fun_fact in notes


# --- Part 3/5: within-game composition -----------------------------------------

def test_no_rivalry_game_lets_one_family_exceed_half_the_questions():
    def classify(q):
        if q["question"].startswith("What real trophy"):
            return "TROPHY"
        if q["question"].startswith("Which school leads"):
            return "SERIES_LEADER"
        return "WHO_IS_RIVAL"
    checked = 0
    for i in range(60):
        pkg = _generate_rivalry(f"pytest-composition-{i}", target_count=10)
        qs = pkg["questions"]
        if len(qs) < 10:
            continue
        checked += 1
        fams = Counter(classify(q) for q in qs)
        assert max(fams.values()) <= 5, (i, fams)  # no more than half of 10
    assert checked >= 30, "too few full 10-question games sampled to trust this"


def test_no_rivalry_game_repeats_the_same_family_consecutively():
    def classify(q):
        if q["question"].startswith("What real trophy"):
            return "TROPHY"
        if q["question"].startswith("Which school leads"):
            return "SERIES_LEADER"
        return "WHO_IS_RIVAL"
    for i in range(60):
        pkg = _generate_rivalry(f"pytest-consec-{i}", target_count=10)
        qs = pkg["questions"]
        if len(qs) < 10:
            continue
        fams = [classify(q) for q in qs]
        for a, b in zip(fams, fams[1:]):
            assert a != b, (i, fams)


def test_no_rivalry_game_repeats_a_correct_answer():
    for i in range(60):
        pkg = _generate_rivalry(f"pytest-answer-repeat-{i}", target_count=10)
        qs = pkg["questions"]
        if len(qs) < 10:
            continue
        answers = [q["answer"] for q in qs]
        assert len(set(answers)) == len(answers), (i, answers)


def test_rivalry_lookup_game_maximizes_unique_rivalries():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    for seed in ("pytest-unique-riv-1", "pytest-unique-riv-2", "pytest-unique-riv-3"):
        candidates = adapter.fetch_ordered_candidates(c, seed)
        guard = DuplicateGuard(track_entity=True)
        rng = engine.seeded(f"{seed}:distractors")
        accepted = []
        for row in candidates:
            result = adapter.evaluate(c, row, rng, guard)
            if isinstance(result, str):
                continue
            accepted.append(result)
            guard.record(result["question"], result["_audit"]["entity_key"])
        composed = adapter.compose_export_order(accepted, 10)[:10]
        rivalry_ids = [q["_audit"]["rivalry_id"] for q in composed]
        assert len(set(rivalry_ids)) == len(rivalry_ids), (seed, rivalry_ids)


def test_trivia_bank_game_never_lets_one_pack_or_category_exceed_half():
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry_trivia as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    for i in range(40):
        seed = f"pytest-trivia-composition-{i}"
        candidates = adapter.fetch_ordered_candidates(c, seed)
        guard = DuplicateGuard(track_entity=True)
        rng = engine.seeded(f"{seed}:distractors")
        accepted = []
        for row in candidates:
            result = adapter.evaluate(c, row, rng, guard)
            if isinstance(result, str):
                continue
            accepted.append(result)
            guard.record(result["question"], result["_audit"]["entity_key"])
        composed = adapter.compose_export_order(accepted, 10)[:10]
        if len(composed) < 10:
            continue
        groups = Counter(adapter._diversity_group(q) for q in composed)
        assert max(groups.values()) <= 5, (seed, groups)


def test_trivia_bank_game_never_repeats_a_correct_answer():
    for i in range(60):
        pkg = _generate_trivia(f"pytest-trivia-answer-repeat-{i}", target_count=10)
        qs = pkg["questions"]
        if len(qs) < 10:
            continue
        answers = [q["answer"] for q in qs]
        assert len(set(answers)) == len(answers), (i, answers)


# --- Real fix: cfb_rivalry_guess must be strictly rivalry-based ---------------

def test_public_cfb_rivalry_guess_mode_is_scoped_to_rivalry_only(client):
    """Real, confirmed-live bug: this mode's own instructions promise "a
    real question from a real, named CFB rivalry", but the spec had no
    rivalry_only filter -- a real "Who won the 1985 Heisman?" (a general-
    category row, nothing to do with any specific rivalry) could surface
    in a mode advertised as rivalry-specific. Every one of many real
    samples must come from a real, named rivalry pack."""
    from tools.quiz_export import engine
    from gateway.services import packages as packages_mod

    c = engine.connect()
    # game_director_v01.py's final question-rebuild loop only allow-lists a
    # hand-picked set of _audit fields onto the persisted question (entity_key,
    # source_ids, provenance) -- is_rivalry/rivalry_pack_name aren't among
    # them, so _audit itself is empty on the saved package. entity_key
    # ("cfbtrivia:<trivia_id>") IS in that allow-list, so it's the real,
    # already-surviving field to verify against the source of truth with.
    seen_any_pack = False
    for i in range(15):
        r = client.get("/v1/public/game", params={"mode": "cfb_rivalry_guess", "seed": f"pytest-rivalry-only-{i}"})
        assert r.status_code == 200
        saved = packages_mod.load_package(r.json()["game_id"])
        question = saved["questions"][0]
        entity_key = question.get("entity_key", "")
        assert entity_key.startswith("cfbtrivia:"), question
        trivia_id = entity_key.split(":", 1)[1]
        row = c.execute(
            "SELECT is_rivalry, rivalry_pack_name FROM cfb_trivia_bank WHERE trivia_id = ?", (trivia_id,)
        ).fetchone()
        assert row is not None, trivia_id
        assert row[0] == 1, question["question"]
        assert row[1], f"rivalry row {trivia_id} has no rivalry_pack_name"
        seen_any_pack = True
    assert seen_any_pack


def test_public_cfb_rivalry_guess_no_longer_certifies_medium():
    """Real, measured: the rivalry-only pool has 0 real Medium-labeled
    rows (the source bank's own Medium-and-named-rivalry rows are already
    promoted to Easy elsewhere in this same pipeline) -- "medium" must be
    removed from certified difficulties, not silently return empty."""
    from gateway.services import public_game
    entry = public_game.PUBLIC_MODES["cfb_rivalry_guess"]
    assert entry["certified_difficulties"] == frozenset({"easy", "hard"})
    assert entry["spec"]["filters"] == {"rivalry_only": True}


def test_public_cfb_rivalry_guess_medium_is_cleanly_rejected(client):
    r = client.get("/v1/public/game", params={"mode": "cfb_rivalry_guess", "difficulty": "medium"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


# --- Real, player-reported bugs: name the matchup + no BS team facts ----------

def test_every_rivalry_trivia_question_names_the_real_matchup_up_front():
    """Real, confirmed-live bug: a question like "Both programs claim a
    combined total of well over a dozen national championships -- true or
    false?" never told the player which two schools it was about until the
    post-answer reveal note. Every rivalry-bank question must now open
    with the real matchup (or the pack's real nickname) before the
    question text itself."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry_trivia as adapter

    c = engine.connect()
    pkg = _generate_trivia("pytest-matchup-prefix-check", target_count=40)
    assert pkg["qa_status"] == "PASSED"
    for q in pkg["questions"]:
        row = c.execute(
            "SELECT is_rivalry, school_a_id, school_b_id, rivalry_pack_name FROM cfb_trivia_bank "
            "WHERE trivia_id = ?", (q["entity_key"].split(":", 1)[1],),
        ).fetchone()
        if not row["is_rivalry"]:
            continue
        a_name = adapter._school_name(c, row["school_a_id"])
        b_name = adapter._school_name(c, row["school_b_id"])
        expected_prefix = f"{a_name} vs. {b_name}" if a_name and b_name else row["rivalry_pack_name"]
        assert q["question"].startswith(f"{expected_prefix}: "), q["question"]


def test_rivalry_trivia_never_serves_a_non_rivalry_specific_row():
    """Real, player-reported bug: a majority of every curated rivalry
    pack is generic single-school trivia (colors/mascot/fight song/stadium
    name/individual awards/NFL Draft/national championships/coach hires)
    that never tests any actual head-to-head rivalry knowledge -- e.g.
    "What are Auburn's school colors?" inside the Iron Bowl pack. See
    _cfb_rivalry_trivia_exclude_ids.py for the full three-pass audit. None
    of those 693 known-bad rows may ever reach a real game."""
    from tools.quiz_export.adapters._cfb_rivalry_trivia_exclude_ids import (
        NON_RIVALRY_SPECIFIC_TRIVIA_IDS,
    )

    for i in range(20):
        pkg = _generate_trivia(f"pytest-no-bs-facts-{i}", target_count=20)
        for q in pkg["questions"]:
            entity_key = q.get("entity_key") or ""
            assert entity_key.startswith("cfbtrivia:"), q
            trivia_id = entity_key.split(":", 1)[1]
            assert trivia_id not in NON_RIVALRY_SPECIFIC_TRIVIA_IDS, q["question"]


def test_evaluate_rejects_a_known_non_rivalry_specific_row_directly():
    """Direct unit check on the exact reported row (Nebraska vs Oklahoma's
    "combined national championships" question, which never named either
    school) -- confirms it's now excluded rather than merely untested."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import cfb_rivalry_trivia as adapter
    from tools.quiz_export.duplicates import DuplicateGuard

    c = engine.connect()
    row = c.execute("SELECT * FROM cfb_trivia_bank WHERE trivia_id = 'CFBTRIV_732'").fetchone()
    assert row is not None
    result = adapter.evaluate(c, row, engine.seeded("pytest-732"), DuplicateGuard(track_entity=True))
    assert result == "NOT_RIVALRY_SPECIFIC"
