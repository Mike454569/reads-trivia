"""P0/P1 Accuracy + Reliability Hardening passes: current-season
roster-fact drift detection AND (P1) real enforcement of it. See
tools/director_v02/roster_freshness.py's own module docstring for why
historical and current-season data need different freshness treatment,
and why STALE actually blocks generation while WARN does not."""
from __future__ import annotations

import datetime as dt
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02 import roster_freshness  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402


@contextmanager
def _snapshot_date_shifted(days_ago: int):
    """Simulates an old snapshot by temporarily moving
    CURRENT_TEAM_SNAPSHOT_DATE back -- the only way to exercise the real
    STALE/WARN code paths in fetch_ordered_candidates() (which always calls
    freshness_report() with the real, unfixed today) without waiting for
    real calendar time to pass. Always restored, even on failure."""
    original = roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE
    roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE = dt.date.today() - dt.timedelta(days=days_ago)
    try:
        yield
    finally:
        roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE = original


def test_freshness_report_is_fresh_right_at_snapshot_date():
    report = roster_freshness.freshness_report(today=roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE)
    assert report["age_days"] == 0
    assert report["status"] == "FRESH"


def test_freshness_report_warns_after_threshold():
    warn_date = roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE + dt.timedelta(days=roster_freshness.WARN_AFTER_DAYS)
    report = roster_freshness.freshness_report(today=warn_date)
    assert report["status"] == "WARN"


def test_freshness_report_stale_after_threshold():
    stale_date = roster_freshness.CURRENT_TEAM_SNAPSHOT_DATE + dt.timedelta(days=roster_freshness.STALE_AFTER_DAYS)
    report = roster_freshness.freshness_report(today=stale_date)
    assert report["status"] == "STALE"


def test_freshness_thresholds_are_ordered_sensibly():
    assert 0 < roster_freshness.WARN_AFTER_DAYS < roster_freshness.STALE_AFTER_DAYS


@pytest.mark.skipif(not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database")
def test_offense_college_curated_safety_check_reports_real_freshness():
    from tools.quiz_export.adapters import nfl_offense_college_curated

    c = engine_bootstrap.connect()
    try:
        result = nfl_offense_college_curated.safety_check(c)
    finally:
        c.close()
    assert "roster_freshness" in result
    assert result["roster_freshness"]["status"] in ("FRESH", "WARN", "STALE")
    assert result["roster_freshness"]["age_days"] >= 0


# --- P1: real enforcement -- STALE actually blocks, WARN does not --------

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _generate_offense_college(seed: str):
    from tools.director_v02 import registry
    from tools import game_director_v01 as gd

    cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_OFFENSE_COLLEGE_CURATED", "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE")]
    spec = {
        "mechanic": "guess", "domain": "NFL_OFFENSE_COLLEGE_CURATED",
        "relationship_predicate": "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE",
        "question_count": 5, "filters": {}, "exclusions": [],
    }
    return gd.generate_package_from_spec(
        spec, cap["adapter"], request_text="freshness enforcement test", director_request_id=f"freshness-{seed}",
        seed=seed, target_count=5,
    )


def test_fresh_generates_normally():
    with _snapshot_date_shifted(days_ago=0):
        pkg = _generate_offense_college("freshness-fresh")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0


def test_warn_does_not_block_generation():
    """Explicit requirement: WARN is a soft signal, never auto-blocking."""
    with _snapshot_date_shifted(days_ago=roster_freshness.WARN_AFTER_DAYS + 5):
        pkg = _generate_offense_college("freshness-warn")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
    assert pkg["production_safety"]["roster_freshness"]["status"] == "WARN"


def test_stale_quarantines_the_capability():
    with _snapshot_date_shifted(days_ago=roster_freshness.STALE_AFTER_DAYS + 5):
        pkg = _generate_offense_college("freshness-stale")
    assert pkg["qa_status"] == "FAILED"
    assert len(pkg["questions"]) == 0
    assert pkg["production_safety"]["roster_freshness"]["status"] == "STALE"
    # A clear, specific limitation -- not the generic "0 candidates passed
    # validation" message that reads like a data bug.
    assert "STALE" in pkg["funnel"]["shortfall_reason"]
    assert "quarantin" in pkg["funnel"]["shortfall_reason"].lower()


def test_stale_package_never_passes_the_shared_contract_guard():
    """The P0 shared guard (package_contract.validate_package_contract())
    must independently agree this package isn't playable -- belt and
    suspenders, not just the qa_status field."""
    from tools.director_v02.package_contract import validate_package_contract

    with _snapshot_date_shifted(days_ago=roster_freshness.STALE_AFTER_DAYS + 5):
        pkg = _generate_offense_college("freshness-stale-contract")
    violations = validate_package_contract(pkg)
    assert violations, "a STALE-quarantined (0-question) package must fail the shared contract guard"


def test_stale_raises_a_clean_no_eligible_game_error_from_the_public_api():
    from gateway.services import public_game
    from gateway.errors import GatewayError

    with _snapshot_date_shifted(days_ago=roster_freshness.STALE_AFTER_DAYS + 5):
        with pytest.raises(GatewayError) as exc_info:
            public_game.get_public_game(mode="offense_college_guess", difficulty=None, seed=None, exclude_game_ids=None)
    assert exc_info.value.code == "NO_ELIGIBLE_GAME"


def test_stale_does_not_affect_historical_sb_champion_capability():
    """Explicit requirement: historical capabilities must remain
    unaffected. NFL_SB_CHAMPION_OFFENSE_COLLEGE reads a DIFFERENT
    board_type (SB_CHAMPION, not CURRENT_TEAM_2026) from the same table --
    a permanently-fixed historical fact that should never be quarantined
    for staleness."""
    from tools.director_v02 import registry
    from tools import game_director_v01 as gd

    cap = registry.CAPABILITY_REGISTRY[
        ("guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE")
    ]
    spec = {
        "mechanic": "guess", "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
        "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
        "question_count": 5, "filters": {}, "exclusions": [],
    }
    with _snapshot_date_shifted(days_ago=roster_freshness.STALE_AFTER_DAYS + 5):
        pkg = gd.generate_package_from_spec(
            spec, cap["adapter"], request_text="historical unaffected check",
            director_request_id="freshness-historical-unaffected", seed="freshness-historical", target_count=5,
        )
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 0
