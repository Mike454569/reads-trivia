"""Final 100-format production closeout smoke coverage.

Static contract tests deliberately protect the cross-file wiring that is easy
to regress in a large single-page frontend: discovery, analytics, dynamic
completion hooks, Daily Format Five, achievements, replay/share surfaces and
the honest 100-format audit.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
ENGINE=(ROOT/"engine-game-ui.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_closeout_keeps_honest_100_format_audit_green():
    from tools.director_v02.format_audit import audit_snapshot
    snap=audit_snapshot()
    assert snap["passes_integrity_gate"] is True
    assert snap["reached_100_distinct_formats"] is True
    assert snap["registry"]["distinct_format_count"] == 100
    assert snap["registry"]["target_gap"] == 0


def test_format_funnel_tracks_discovery_launch_completion_and_share():
    for token in (
        "trackFormatEvent('impression'",
        "trackFormatEvent('search'",
        "trackFormatEvent('filter'",
        "trackFormatEvent('launch'",
        "trackFormatEvent('complete'",
        "trackFormatEvent('share'",
    ):
        assert token in APP
    assert "formatAnalyticsSummary()" in APP
    assert "rows.slice(-500)" in APP


def test_dynamic_formats_feed_same_completion_pipeline_as_legacy_games():
    assert "sourceModeId: sourceModeId || null" in ENGINE
    assert "typeof pushLeaderboard === 'function'" in ENGINE
    assert "completionMode = s.sourceModeId || cfg.publicMode || s.modeKey" in ENGINE
    # pushLeaderboard is the centralized legacy path for these downstream hooks.
    for token in (
        "recordPersonalizationCompletion(mode, fields);",
        "recordSeasonGame(mode, fields);",
        "awardProgressForCompletion(mode, fields);",
        "syncAchievementUnlocks();",
    ):
        assert token in APP


def test_daily_reads_has_deterministic_full_catalog_format_five():
    for token in (
        "function dailyFormatRotation()",
        "formatHubRecommendationRows(40)",
        "modeIds:chosen.slice(0,5)",
        "function markDailyFormatCompleted(mode)",
        "dailyFormatRotationHtml(false)",
        "dailyFormatRotationHtml(true)",
    ):
        assert token in APP
    assert ".daily-format-five-grid" in CSS


def test_format_exploration_achievements_are_persistent_and_syncable():
    assert "formatPlayedIds: []" in APP
    assert "formatPlayedIds: formatPlayed" in APP
    for milestone in ("formatExplorer10","formatExplorer25","formatExplorer50","formatExplorer75","formatExplorer100"):
        assert milestone in APP
    assert "rewardState.formatPlayedIds.push(mode)" in APP


def test_home_to_game_to_completion_to_share_smoke_wiring_exists():
    # Discovery card/quick play launches through the shared data-go path.
    assert 'data-go="'+esc(m.id)+'"' in APP
    assert "function goToMode(mode)" in APP
    assert "startMechanicPilotRound(mechanicEntry.mechanicMode, mode);" in APP
    # Dynamic game completion and existing result/share affordances.
    assert "finishMechanicPilotSession(mechanicPilotModeConfig(s.modeKey), s);" in ENGINE
    assert 'data-share="daily"' in APP
    assert "shareResultCard(t.dataset.share)" in APP
    # Replay/next remains available in the mechanic shell.
    assert "data-mechanic-next" in ENGINE
