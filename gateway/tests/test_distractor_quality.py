"""Live-generated-game quality pass -- regression coverage for the real
distractor-quality bug found by actually playing CFB Heisman (real,
famous winners were surrounded by random Division-III/NAIA school names,
making the answer obvious without any football knowledge) and for the
shared `tools.quiz_export.distractors.sample_plausible()` mechanism the
fix is built on.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.director_v02 import pipeline  # noqa: E402
from tools.quiz_export import distractors  # noqa: E402
from tools.quiz_export.adapters import cfb_heisman  # noqa: E402


# --- tools.quiz_export.distractors.sample_plausible() -- unit coverage ------

def test_sample_plausible_prefers_the_curated_pool():
    rng = random.Random(42)
    plausible = {"a": "Alpha", "b": "Bravo", "c": "Charlie", "d": "Delta"}
    full = dict(plausible)
    full.update({"e": "Echo", "f": "Foxtrot"})
    result = distractors.sample_plausible(rng, "a", plausible, full, k=3)
    assert result is not None
    assert len(result) == 3
    # Every chosen id came from the plausible pool (it had enough real
    # options), never falling through to the wider "full" pool.
    assert set(result.keys()) <= set(plausible.keys()) - {"a"}


def test_sample_plausible_falls_back_to_full_pool_when_plausible_is_too_small():
    rng = random.Random(1)
    plausible = {"a": "Alpha", "b": "Bravo"}  # only 1 real option excluding "a"
    full = {"a": "Alpha", "b": "Bravo", "c": "Charlie", "d": "Delta", "e": "Echo"}
    result = distractors.sample_plausible(rng, "a", plausible, full, k=3)
    assert result is not None
    assert len(result) == 3
    # The one real plausible option ("b") is always kept -- never dropped in
    # favor of a less plausible one just because more options exist elsewhere.
    assert "b" in result


def test_sample_plausible_returns_none_when_truly_insufficient():
    rng = random.Random(1)
    plausible = {"a": "Alpha"}
    full = {"a": "Alpha", "b": "Bravo"}  # only 1 real option excluding "a" total
    assert distractors.sample_plausible(rng, "a", plausible, full, k=3) is None


def test_sample_plausible_never_includes_the_correct_id():
    rng = random.Random(7)
    plausible = {str(i): f"School {i}" for i in range(10)}
    for trial_seed in range(20):
        result = distractors.sample_plausible(random.Random(trial_seed), "3", plausible, plausible, k=3)
        assert "3" not in result


# --- CFB Heisman: the real bug, fixed --------------------------------------

def test_heisman_distractors_are_real_heisman_winning_schools_not_random():
    """The actual regression this fix targets: every distractor offered for
    a real Heisman question must itself be a real school that has produced a
    Heisman winner (the plausible pool has 41 real entries -- always enough
    to avoid the full-805-school fallback in practice), never an obscure
    school picked from the full, unscoped universe."""
    result = pipeline.run("Make me a CFB Heisman guessing game.", seed="pytest-heisman-distractor-quality", question_count_override=25)
    assert result.get("qa_status") == "PASSED"
    questions = result["questions"]
    assert len(questions) > 10  # real, non-trivial yield

    # _heisman_winning_schools needs a real connection -- pull the set once via the Engine directly.
    from tools.quiz_export import engine
    c = engine.connect()
    plausible = set(cfb_heisman._heisman_winning_schools(c).values())
    c.close()

    for q in questions:
        distractor_labels = [o for o in q["options"] if o != q["answer"]]
        assert len(distractor_labels) == 3
        for label in distractor_labels:
            assert label in plausible, (
                f"distractor {label!r} for {q['question']!r} is not a real Heisman-winning school -- "
                f"the plausible-pool fix regressed"
            )


def test_heisman_options_are_four_unique_real_schools():
    result = pipeline.run("Make me a CFB Heisman guessing game.", seed="pytest-heisman-uniqueness", question_count_override=15)
    assert result.get("qa_status") == "PASSED"
    for q in result["questions"]:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert q["options"][q["correctIndex"]] == q["answer"]
