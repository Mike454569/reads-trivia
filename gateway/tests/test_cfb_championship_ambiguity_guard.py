from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_1957_static_question_names_selector_and_explains_split():
    text = (ROOT / "data" / "cfb.js").read_text(encoding="utf-8")
    assert "Which school did the UPI coaches poll and FWAA recognize as national champion in 1957 under Woody Hayes?" in text
    assert "Auburn finished No. 1 in the AP poll." in text
    assert "Which school won the 1957 national championship under Woody Hayes?" not in text


def test_daily_reads_blocks_bare_title_winner_questions():
    text = (ROOT / "app.js").read_text(encoding="utf-8")
    assert "function dailyBareTitleWinnerQuestion(q)" in text
    assert "if (dailyBareTitleWinnerQuestion(q)) return false;" in text
    assert "function cfbChampionshipQuestionNeedsSelector(q)" in text


def test_pre_bcs_generic_title_questions_are_filtered_from_cfb_pool():
    text = (ROOT / "app.js").read_text(encoding="utf-8")
    assert ".filter(function (q) { return !cfbChampionshipQuestionNeedsSelector(q); });" in text
