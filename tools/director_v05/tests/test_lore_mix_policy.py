from tools.director_v05.lore_mix_policy import (
    enforce_mix_policy,
    question_mix_tags,
)


def _q(qid, relations):
    return {
        "question_id": qid,
        "clues": [{"relation": r, "text": r} for r in relations],
    }


def test_mix_tags_identify_draft_story_career_and_honors():
    q = _q("q1", ["DRAFTED_BY", "SUBJECT_OF_EVENT", "ALL_PRO"])
    tags = question_mix_tags(q)
    assert {"DRAFT", "STORY", "HONORS"} <= tags


def test_mixed_bank_caps_draft_heavy_questions():
    questions = [
        _q("d1", ["DRAFTED_BY", "ALL_PRO"]),
        _q("d2", ["DRAFTED_BY", "ROSTERED_BY"]),
        _q("d3", ["DRAFTED_BY", "PRO_BOWL"]),
        _q("d4", ["DRAFTED_BY", "SUBJECT_OF_EVENT"]),
        _q("s1", ["SUBJECT_OF_EVENT", "ROSTERED_BY"]),
        _q("s2", ["SUBJECT_OF_EVENT", "TRANSFERRED_TO"]),
        _q("s3", ["SUBJECT_OF_EVENT", "ALL_PRO"]),
        _q("c1", ["ROSTERED_BY", "ALL_PRO"]),
    ]
    out = enforce_mix_policy(
        questions,
        target=6,
        max_draft_fraction=0.25,
        min_story_fraction=0.40,
    )
    assert len(out["selected"]) == 6
    assert out["mix_counts"].get("DRAFT", 0) <= out["max_draft"]
    assert out["mix_counts"].get("STORY", 0) >= out["min_story"]


def test_policy_keeps_some_draft_when_available():
    questions = [
        _q("d1", ["DRAFTED_BY", "SUBJECT_OF_EVENT"]),
        _q("s1", ["SUBJECT_OF_EVENT", "ROSTERED_BY"]),
        _q("s2", ["SUBJECT_OF_EVENT", "ALL_PRO"]),
        _q("c1", ["ROSTERED_BY", "PRO_BOWL"]),
    ]
    out = enforce_mix_policy(questions, target=4)
    assert out["mix_counts"].get("DRAFT", 0) == 1


def test_story_floor_replaces_weaker_nonstory_items():
    questions = [
        _q("c1", ["ROSTERED_BY", "ALL_PRO"]),
        _q("c2", ["ROSTERED_BY", "PRO_BOWL"]),
        _q("c3", ["TRANSFERRED_TO", "RANKED"]),
        _q("s1", ["SUBJECT_OF_EVENT", "ALL_PRO"]),
        _q("s2", ["SUBJECT_OF_EVENT", "ROSTERED_BY"]),
    ]
    out = enforce_mix_policy(
        questions,
        target=4,
        max_draft_fraction=0.25,
        min_story_fraction=0.50,
    )
    assert out["mix_counts"].get("STORY", 0) >= 2
