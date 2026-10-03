from tools.director_v05.lore_mix_policy import enforce_mix_policy

def _q(qid, relations):
    return {
        "question_id": qid,
        "clues": [{"relation": r, "text": r} for r in relations],
        "answer": {"id": qid, "label": qid, "type": "NFL_PLAYER"},
    }

def test_small_package_draft_cap_is_mathematically_exact():
    questions = [
        _q("draft", ["DRAFTED_BY"]),
        _q("story1", ["SUBJECT_OF_EVENT"]),
        _q("story2", ["SUBJECT_OF_EVENT"]),
        _q("career", ["ROSTERED_BY"]),
    ]
    out = enforce_mix_policy(
        questions,
        target=3,
        max_draft_fraction=0.25,
        min_story_fraction=0.40,
    )
    assert out["max_draft"] == 0
    assert out["mix_counts"].get("DRAFT", 0) == 0
    assert out["draft_fraction"] <= 0.25
    assert out["mix_counts"].get("STORY", 0) >= 2
    assert out["story_fraction"] >= 0.40

def test_four_question_package_allows_one_draft():
    questions = [
        _q("draft", ["DRAFTED_BY"]),
        _q("story1", ["SUBJECT_OF_EVENT"]),
        _q("story2", ["SUBJECT_OF_EVENT"]),
        _q("career", ["ROSTERED_BY"]),
    ]
    out = enforce_mix_policy(questions, target=4)
    assert out["max_draft"] == 1
    assert out["mix_counts"].get("DRAFT", 0) == 1
    assert out["draft_fraction"] == 0.25
