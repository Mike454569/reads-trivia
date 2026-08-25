"""P0 Accuracy + Reliability Hardening pass (Section 5): current-season
roster-fact drift detection. See tools/director_v02/roster_freshness.py's
own module docstring for why historical and current-season data need
different freshness treatment."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02 import roster_freshness  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402


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
