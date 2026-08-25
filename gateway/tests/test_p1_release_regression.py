"""P1 Release Readiness pass: the explicit regression list from this pass's
own instructions, re-verified end-to-end after the STALE-enforcement,
OL-cell-verification, and stale-comment fixes. Every capability here shares
code paths touched by this pass (game_director_v01.py's shortfall_reason,
nfl_offense_college_curated.py's fetch_ordered_candidates(), the SB season
data fix) -- this file exists so none of those changes can silently break
a real, previously-working capability."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v02 import registry  # noqa: E402
from tools.director_v02.providers.mock import MockDeterministicTranslator  # noqa: E402
from tools.director_v02.package_contract import validate_package_contract  # noqa: E402
from tools import game_director_v01 as gd  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _gen(domain, predicate, seed, n=5):
    cap = registry.CAPABILITY_REGISTRY[("guess", domain, predicate)]
    spec = {
        "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
        "question_count": n, "filters": {}, "exclusions": [],
    }
    return gd.generate_package_from_spec(
        spec, cap["adapter"], request_text="p1 regression", director_request_id=f"p1-regression-{seed}",
        seed=seed, target_count=n,
    )


def test_nfl_offense_by_college():
    pkg = _gen("NFL_OFFENSE_COLLEGE_CURATED", "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE", "p1-reg-1")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    assert validate_package_contract(pkg) == []


def test_super_bowl_offense_by_college():
    pkg = _gen("NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE", "p1-reg-2")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    assert validate_package_contract(pkg) == []


def test_nfl_who_am_i():
    from tools.director_v04 import player_from_clues
    pkg = player_from_clues.build_package(seed="p1-reg-3", target_count=10)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["puzzle_count"] > 0


def test_cfb_who_am_i():
    from tools.director_v04 import cfb_player_from_clues
    pkg = cfb_player_from_clues.build_package(seed="p1-reg-4", target_count=10)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["puzzle_count"] > 0


def test_cfb_ranking_upset():
    pkg = _gen("CFB_UPSET", "RANKING_UPSET", "p1-reg-5")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    assert validate_package_contract(pkg) == []


def test_same_week_cfb_rb_comparison_routes_correctly():
    translator = MockDeterministicTranslator()
    r = translator.translate("give me two rbs from the same cfb week and make me choose who had the bigger day")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "CFB_STAT_COMPARISON"


def test_nfl_first_td_slang_prompt_routes_correctly():
    translator = MockDeterministicTranslator()
    r = translator.translate("who got the first tuddy")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "NFL_SCORING_PLAY"
    assert r["spec"]["relationship_predicate"] == "FIRST_TOUCHDOWN_SCORER"


def test_team_to_offensive_coordinator_direction():
    translator = MockDeterministicTranslator()
    r = translator.translate("give me an nfl team offense and season and make me guess the coordinator")
    assert r["translation_status"] == "TRANSLATED"
    assert r["spec"]["domain"] == "NFL_OFFENSIVE_COORDINATOR"
    pkg = _gen("NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE", "p1-reg-8")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0


def test_shared_empty_package_guard_still_rejects_empty_packages():
    pkg = _gen("NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE", "p1-reg-guard")
    broken = dict(pkg)
    broken["questions"] = []
    violations = validate_package_contract(broken)
    assert violations
    assert any("empty" in v for v in violations)
