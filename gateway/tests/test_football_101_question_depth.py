"""Football 101 Encyclopedia question-depth and anti-repeat regressions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
FIELD = (ROOT / "football-field.js").read_text(encoding="utf-8")


def test_test_me_generator_has_multiple_question_families_per_diagram_category():
    expected = (
        "formation_widest",
        "formation_personnel",
        "formation_deepest",
        "formation_backfield_count",
        "front_db",
        "front_dl",
        "front_lb",
        "front_personnel",
        "coverage_type",
        "coverage_zone_count",
        "coverage_shell",
        "coverage_identify_by_zones",
        "pass_route_runner",
        "pass_runner_route",
        "pass_route_count",
        "pass_route_present",
        "run_block_count",
        "run_blocker_id",
        "run_identify_by_blocks",
    )
    dynamic_front = {"front_db", "front_dl", "front_lb"}
    for variant in expected:
        if variant in dynamic_front:
            assert f"key:'{variant}'" in FIELD
        else:
            assert f"variantKey: '{variant}'" in FIELD


def test_test_me_questions_are_derived_from_existing_diagram_data():
    assert "diagram.personnel" in FIELD
    assert "realPlayers(diagram)" in FIELD
    assert "(diagram.zones || []).length" in FIELD
    assert "(diagram.routes || [])" in FIELD
    assert "diagram.blocks || []" in FIELD


def test_recent_encyclopedia_questions_are_persisted_per_user_and_concept():
    assert "function f101QuestionHistoryKey(canonicalId)" in APP
    assert "readsF101QuestionHistory__" in APP
    assert "history.slice(-8)" in APP
    assert "function f101FreshTestQuestion(diagram, category, siblings)" in APP
    assert "for (var i = 0; i < 32; i++)" in APP
    assert "if (!seen[sig])" in APP


def test_test_me_click_uses_fresh_question_selector_not_raw_random_generator():
    click = APP[APP.index("if (t.dataset.f101TestMe !== undefined)"):APP.index("if (t.dataset.f101QuizAnswer !== undefined)")]
    assert "f101FreshTestQuestion(tmDiagram, tmCategory, tmSiblings)" in click
    assert "Math.random()" not in click
    assert "variantKey: tmQ.variantKey || null" in click
