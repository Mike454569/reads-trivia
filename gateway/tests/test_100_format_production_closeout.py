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
    assert snap["formats"]["distinct_format_count"] == 100
    assert snap["formats"]["target_gap"] == 0


def test_format_funnel_tracks_discovery_launch_completion_and_share():
    for token in (
        "trackFormatEvent('impression'",
        "trackFormatEvent('search'",
        "trackFormatEvent('filter'",
        "trackFormatEvent('launch'",
        "finishFormatAnalyticsRun(",
        "trackFormatEvent('abandon'",
        "trackFormatEvent('share'",
    ):
        assert token in APP
    assert "formatAnalyticsSummary()" in APP
    assert "rows.slice(-500)" in APP
    assert "durationMs" in APP
    assert "formatAnalyticsActiveRun" in APP


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
        "function dailyMechanicForFormatFamily",
        "_dailyFormatSourceId",
        "_dailyFormatSourceTitle",
        "formatSources:",
        "formatFamilies:",
    ):
        assert token in APP
    assert ".daily-format-five-grid" in CSS


def test_format_exploration_achievements_are_persistent_and_syncable():
    assert "formatPlayedIds: []" in APP
    assert "formatPlayedIds: formatPlayed" in APP
    for milestone in ("formatExplorer10","formatExplorer25","formatExplorer50","formatExplorer75","formatExplorer100"):
        assert milestone in APP
    for specialist in ("boardSpecialist","strategySpecialist","survivalSpecialist","identifySpecialist","rosterSpecialist","sequenceSpecialist"):
        assert specialist in APP
    assert "function completedFormatFamilyCount" in APP
    assert "rewardState.formatPlayedIds.push(mode)" in APP


def test_home_to_game_to_completion_to_share_smoke_wiring_exists():
    # Discovery card/quick play launches through the shared data-go path.
    assert 'data-go="' in APP and "esc(m.id)" in APP
    assert "function goToMode(mode)" in APP
    assert "startMechanicPilotRound(mechanicEntry.mechanicMode, mode);" in APP
    # Dynamic game completion and existing result/share affordances.
    assert "finishMechanicPilotSession(mechanicPilotModeConfig(s.modeKey), s);" in ENGINE
    assert 'data-share="daily"' in APP
    assert "shareResultCard(t.dataset.share)" in APP
    # Replay/next remains available in the mechanic shell.
    assert "data-mechanic-next" in ENGINE


def test_closeout_dedupes_discovery_impressions_and_syncs_format_badges_immediately():
    assert "function trackFormatHubImpression(modes)" in APP
    assert "formatHubLastImpressionSignature" in APP
    assert "trackFormatHubImpression(modes);" in APP
    completion=APP[APP.index("function recordPersonalizationCompletion"):APP.index("function personalizationMasteryRows")]
    assert "syncAchievementUnlocks();" in completion
    assert "playableMeta&&playableMeta.league" in completion


def test_real_db_ci_uses_isolated_volume_fork_and_dumb_helper():
    workflow=(ROOT/".github/workflows/gateway-tests.yml").read_text(encoding="utf-8")
    install=workflow[workflow.index("- name: Install flyctl"):workflow.index("- name: Fork real DB volume")]
    restore=workflow[workflow.index("- name: Fork real DB volume"):workflow.index("- name: Install dependencies", workflow.index("- name: Fork real DB volume"))]
    cleanup=workflow[workflow.index("- name: Clean up temporary Fly volume and machine"):]
    assert '"$HOME/.fly/bin/flyctl" version' in install
    assert '"$HOME/.fly/bin/flyctl" volumes fork "$SOURCE_VOLUME_ID"' in restore
    assert "alpine:3.20" in restore
    assert '--volume "${TEMP_VOL_ID}:/data"' in restore
    assert '--entrypoint "tail -f /dev/null"' in restore
    assert '"$HOME/.fly/bin/flyctl" ssh sftp get' in restore
    assert '"$HOME/.fly/bin/flyctl" machine destroy' in cleanup
    assert '"$HOME/.fly/bin/flyctl" volumes destroy' in cleanup

def test_gateway_workflow_cancels_stale_branch_runs():
    workflow=(ROOT/".github/workflows/gateway-tests.yml").read_text(encoding="utf-8")
    assert "concurrency:" in workflow
    assert "group: gateway-tests-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow
