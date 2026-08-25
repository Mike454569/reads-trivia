"""Final Technical Risk Cleanup pass: regression guard for the real
production drift incident -- `cfb_standings` silently held only the
current season (138 rows, all genuinely SOURCE_BACKED) after only the
routine "current season only" scheduled refresh had ever populated
production, while the real 2002-2025 historical backfill existed only in
this dev checkout and was never synced. No existing safety check caught
it because every row present WAS correctly provenanced -- the gap was
depth, not correctness.

These tests run against whatever database READS_ENGINE_DIR points at (the
local dev Engine DB in CI) -- they exist to catch this SAME regression
class reappearing here, and the identical check is also reachable live
against a deployed environment via GET /v1/admin/diagnostics/data-coverage
(see gateway/app.py) for a production-specific point-in-time check.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export import safety  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_cfb_standings_has_real_historical_depth_not_just_current_season():
    c = engine_bootstrap.connect()
    try:
        result = safety.check_season_coverage_safety(
            c, "cfb_standings", "season", 2002, where_extra="classification='fbs'"
        )
    finally:
        c.close()
    assert result["coverage_ok"], (
        f"cfb_standings (classification='fbs') only covers seasons "
        f"{result['min_season']}-{result['max_season']} ({result['distinct_seasons']} distinct season(s), "
        f"{result['row_count']} rows) -- expected real coverage back to {result['expected_min_season']}. "
        f"This is exactly the shape of the real production drift incident this test guards against."
    )
    assert result["distinct_seasons"] >= 20, (
        "cfb_standings has fewer than 20 distinct real seasons -- a suspiciously thin slice "
        "even if it technically reaches back to the expected minimum season."
    )


def test_season_standings_has_real_historical_depth():
    c = engine_bootstrap.connect()
    try:
        result = safety.check_season_coverage_safety(c, "season_standings", "season", 2002)
    finally:
        c.close()
    assert result["coverage_ok"], (
        f"season_standings only covers seasons {result['min_season']}-{result['max_season']} -- "
        f"expected real coverage back to {result['expected_min_season']}."
    )


def test_cfb_national_champion_survival_produces_a_real_nonzero_sequence():
    """The actual behavioral proof, not just a row-count proxy: with real
    historical depth present, the mechanic this coverage gap broke on
    production must generate a real, playable sequence."""
    from tools.director_v04 import elimination
    result = elimination.generate_sequence(
        seed="coverage-drift-regression-check", variant="CFB_NATIONAL_CHAMPION_SURVIVAL", sequence_length=10,
    )
    assert len(result["items"]) == 10, (
        f"only {len(result['items'])} of 10 CFB_NATIONAL_CHAMPION_SURVIVAL items were generated -- "
        f"shortfall_reason={result['shortfall_reason']!r}"
    )
    assert any(item["_private_membership"] for item in result["items"])
    assert any(not item["_private_membership"] for item in result["items"])
