from tools.director_v05.lore_question_writer import select_clues, writer_quality


def _clues():
    return [
        {"relation":"SUBJECT_OF_EVENT","text":"In 2022, I returned a broken-play touchdown after the ball changed hands twice.","source_kind":"LORE_EVENT"},
        {"relation":"DRAFTED_BY","text":"I was drafted by Green Bay in 2020.","source_kind":"STRUCTURED_FACT"},
        {"relation":"ROSTERED_BY","text":"I suited up for Detroit in 2021.","source_kind":"STRUCTURED_FACT"},
        {"relation":"ALL_PRO","text":"I earned First Team All-Pro honors in 2023.","source_kind":"STRUCTURED_FACT"},
        {"relation":"PRO_BOWL","text":"I made the Pro Bowl in 2023.","source_kind":"STRUCTURED_FACT"},
    ]


def test_casual_reveals_story_before_harder_bands():
    casual = select_clues(_clues(), "CASUAL")
    hard = select_clues(_clues(), "HARD")
    assert casual[0]["relation"] == "SUBJECT_OF_EVENT"
    assert hard[-1]["relation"] == "SUBJECT_OF_EVENT"


def test_writer_prefers_semantic_variety():
    chosen = select_clues(_clues(), "HARD")
    semantics = {c["relation"] for c in chosen}
    assert len(semantics) >= 2
    assert writer_quality(chosen)["status"] == "PASSED"


def test_variant_selection_is_deterministic():
    a = select_clues(_clues(), "SICKO", variant=1)
    b = select_clues(_clues(), "SICKO", variant=1)
    assert a == b


def test_writer_quality_rejects_robotic_copy():
    clues = [
        {"relation":"DRAFTED_BY","text":"Structured fact: GB.","source_kind":"STRUCTURED_FACT"},
        {"relation":"ROSTERED_BY","text":"Subject of event: x.","source_kind":"LORE_EVENT"},
        {"relation":"ALL_PRO","text":"Verified chain step.","source_kind":"STRUCTURED_FACT"},
    ]
    result = writer_quality(clues)
    assert result["status"] == "FAILED"
    assert "ROBOTIC_WRITER_COPY" in result["errors"]
