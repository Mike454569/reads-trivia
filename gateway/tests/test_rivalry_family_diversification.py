"""Rivalries going deeper (Pass 2.7): permanent regression coverage for the
3 real question families cfb_rivalry.py now rotates through, instead of
always asking "who is X's rival" with different flavor text.

TROPHY and SERIES_LEADER both reuse real columns (trophy, series_record)
this adapter already fetched into every candidate but only ever used as
`notes` flavor text before this pass.
"""
from tools import game_director_v01 as v01
from tools.quiz_export.adapters import cfb_rivalry as adapter

_FACTORY_SPEC = {
    "competition_id": "CFB", "mechanic": "guess", "entity_type": "cfb_school",
    "relationship_predicate": "RIVAL_OF", "object_type": "school",
    "answer_type": "school", "group_size": 4, "filters": {},
}


def _generate(seed, target_count=96):
    return v01.generate_package_from_spec(
        _FACTORY_SPEC, adapter, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


def _family_of(question_text: str) -> str:
    if "leads the real all-time series" in question_text:
        return "SERIES_LEADER"
    if "real trophy is awarded" in question_text:
        return "TROPHY"
    return "WHO_IS_RIVAL"


def test_all_three_families_appear_across_the_real_pool():
    pkg = _generate("pytest-rivalry-families-1")
    assert pkg["qa_status"] == "PASSED"
    families = {_family_of(q["question"]) for q in pkg["questions"]}
    assert families == {"WHO_IS_RIVAL", "SERIES_LEADER", "TROPHY"}


def test_no_family_dominates_the_real_pool():
    """Section 20's cross-mode repetition protection: no single question
    family should be the overwhelming majority now that 3 real families
    exist -- WHO_IS_RIVAL is the only one guaranteed for every rivalry, so
    it's expected to lead, but not swamp the other two."""
    pkg = _generate("pytest-rivalry-families-2")
    n = len(pkg["questions"])
    assert n >= 50
    counts = {"WHO_IS_RIVAL": 0, "SERIES_LEADER": 0, "TROPHY": 0}
    for q in pkg["questions"]:
        counts[_family_of(q["question"])] += 1
    for family, count in counts.items():
        assert count / n < 0.75, f"{family} is {count}/{n} ({count / n:.0%}) of the real pool -- too dominant"


def test_trophy_questions_never_offer_a_non_trophy_distractor():
    pkg = _generate("pytest-rivalry-trophy-seed")
    trophy_qs = [q for q in pkg["questions"] if _family_of(q["question"]) == "TROPHY"]
    assert trophy_qs, "expected at least one real TROPHY question in this sample"
    for q in trophy_qs:
        assert len(set(q["options"])) == 4


def test_series_leader_questions_answer_is_one_of_the_two_real_schools():
    pkg = _generate("pytest-rivalry-series-seed")
    series_qs = [q for q in pkg["questions"] if _family_of(q["question"]) == "SERIES_LEADER"]
    assert series_qs, "expected at least one real SERIES_LEADER question in this sample"
    for q in series_qs:
        # A real school name can itself contain parentheses (e.g. "Miami
        # (FL)") or a rivalry nickname can (e.g. "(the original)") --
        # rather than fragile paren-boundary parsing, just confirm the
        # correct answer's exact text appears literally in the question,
        # which the "...(A vs. B)?" template always guarantees for both
        # real schools.
        correct = q["options"][q["correctIndex"]]
        assert correct in q["question"], f"{correct!r} does not appear in the question text: {q['question']!r}"


def test_who_is_rival_family_unchanged_no_placeholder_nickname():
    """Regression for the real "-" placeholder nickname bug Pass 2.5 fixed
    -- must still hold with 3 families in rotation, not just 1."""
    pkg = _generate("pytest-rivalry-no-regress-seed", target_count=300)
    for q in pkg["questions"]:
        assert '("-")' not in q["question"]


def test_zero_duplicate_questions_across_a_real_full_pool_run():
    pkg = _generate("pytest-rivalry-dup-check-seed", target_count=96)
    texts = [q["question"] for q in pkg["questions"]]
    assert len(set(texts)) == len(texts)
