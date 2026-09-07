"""Creator/Game Quality Correction pass -- Franchise Marathon (#12) and
College Offense -> real CFB rosters (#8) regression tests.

Franchise Marathon was real (a working filters=... call) but completely
unreachable from natural language before this pass -- a user typing
"Franchise Marathon" got NO_MATCH every time. "College Offense" always
silently routed to the Gold Standard workbook's NFL-Super-Bowl-champion
concept, even for a plain, unqualified request -- never a real college
football team.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_franchise_marathon_phrase_now_reachable_from_natural_language():
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate("Give me a Cowboys franchise marathon.")
    assert r["translation_status"] == "TRANSLATED"
    spec = r["spec"]
    # Closeout pass (Part 3 rebuild): moved off NFL_SB_CHAMPION_OFFENSE_COLLEGE
    # onto franchise_marathon.py's own real 8-stage-progression domain.
    assert spec["domain"] == "NFL_FRANCHISE_MARATHON"
    assert spec["relationship_predicate"] == "FRANCHISE_MARATHON_STAGE"
    assert spec["filters"] == {"franchise_name": "cowboys"}


def test_franchise_marathon_generates_a_real_eight_stage_dynasty_history():
    """Closeout pass (Part 3 rebuild): the old assumption that every real
    answer is a "<season> <team>" string embedding the franchise name no
    longer holds -- only the deep-cut (Super Bowl) stage's answer is a
    season; the other 7 real stages answer with a division, a W-L record, a
    coach, a drafted player, an award honoree, a playoff-result phrase, and
    a roster member. What must still hold: every question NAMES the real
    franchise (see franchise_marathon.py's wording-quality fix), and no two
    stages repeat a question or an answer."""
    from tools.director_v02 import pipeline

    pkg = pipeline.run(
        "Give me a Cowboys franchise marathon.", provider="mock",
        seed="test-franchise-marathon-cowboys", question_count_override=20,
    )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) >= 6
    for q in pkg["questions"]:
        assert "Dallas Cowboys" in q["question"] or "Final boss" in q["question"]
    texts = [q["question"] for q in pkg["questions"]]
    answers = [q["options"][q["correctIndex"]] for q in pkg["questions"]]
    assert len(set(texts)) == len(texts)
    assert len(set(answers)) == len(answers)
    assert sum(1 for q in pkg["questions"] if q["question"].startswith("Final boss:")) <= 1


def test_franchise_marathon_reunites_relocated_franchise_across_display_names():
    """Raiders real history spans 2 different real team_seasons full_name
    strings (Oakland Raiders / Las Vegas Raiders) -- every family must be
    queried across the franchise's FULL real team_code history, not just
    its current one, and the identity stage should surface the real
    relocation directly."""
    from tools.director_v02 import pipeline

    pkg = pipeline.run(
        "Give me a Raiders dynasty game.", provider="mock",
        seed="test-franchise-marathon-raiders", question_count_override=20,
    )
    assert pkg["qa_status"] == "PASSED"
    assert any("Oakland Raiders" in q["question"] or "Las Vegas Raiders" in q["question"]
               for q in pkg["questions"])


def test_college_offense_bare_phrase_routes_to_real_cfb_capability_not_nfl():
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate("Give me a college offense game.")
    assert r["translation_status"] == "TRANSLATED"
    spec = r["spec"]
    assert spec["domain"] == "CFB_OFFENSE_LINEUP"
    assert spec["relationship_predicate"] == "TEAM_SEASON_OF_STARTING_OFFENSE"


def test_college_offense_with_super_bowl_qualifier_still_reaches_gold_standard_nfl_concept():
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate("Make me guess a Super Bowl champion college offense game.")
    assert r["translation_status"] == "TRANSLATED"
    spec = r["spec"]
    assert spec["domain"] == "NFL_SB_CHAMPION_OFFENSE_COLLEGE"


def test_college_offense_generates_real_cfb_team_and_real_players():
    from tools.director_v02 import pipeline

    pkg = pipeline.run(
        "Give me a college offense game.", provider="mock",
        seed="test-college-offense-cfb", question_count_override=5,
    )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) >= 1
    for q in pkg["questions"]:
        assert len(q["options"]) == 4
        assert q["visual_payload"]["positions"]
        positions_seen = {p["position"] for p in q["visual_payload"]["positions"]}
        assert positions_seen == {"QB", "RB", "WR", "TE"}
