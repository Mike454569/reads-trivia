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
    assert spec["domain"] == "NFL_SB_CHAMPION_OFFENSE_COLLEGE"
    assert spec["filters"] == {"franchise_name": "cowboys"}


def test_franchise_marathon_generates_real_chronological_dynasty_history():
    from tools.director_v02 import pipeline

    pkg = pipeline.run(
        "Give me a Cowboys franchise marathon.", provider="mock",
        seed="test-franchise-marathon-cowboys", question_count_override=20,
    )
    assert pkg["qa_status"] == "PASSED"
    # The real season is embedded in the answer text itself ("<season> <team>").
    answers = [q["options"][q["correctIndex"]] for q in pkg["questions"]]
    assert len(answers) >= 1
    for a in answers:
        assert "Cowboys" in a
    real_seasons = [int(a.split()[0]) for a in answers]
    assert real_seasons == sorted(real_seasons), "Franchise Marathon must be real chronological order, not shuffled"


def test_franchise_marathon_reunites_relocated_franchise_across_display_names():
    """Raiders real championship history spans 3 different real
    team_display_name strings (Oakland/LA/"Oakland-LA") -- all 3 must be
    reachable from one nickname, not just the exact-match display string."""
    from tools.director_v02 import pipeline

    pkg = pipeline.run(
        "Give me a Raiders dynasty game.", provider="mock",
        seed="test-franchise-marathon-raiders", question_count_override=20,
    )
    assert pkg["qa_status"] == "PASSED"
    answers = [q["options"][q["correctIndex"]] for q in pkg["questions"]]
    assert any("Oakland" in a for a in answers) or any("Los Angeles" in a for a in answers)
    for a in answers:
        assert "Raiders" in a


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
