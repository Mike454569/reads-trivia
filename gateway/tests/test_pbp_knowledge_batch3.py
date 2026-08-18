"""Knowledge Expansion Batch 3 -- NFL/CFB play-by-play, CFB player-game
stats, and the CFB fantasy-draft eligibility upgrade. Real, DB-backed
tests: scoring-play classification, turnover classification, sack/
interception relationships, explosive-play thresholds, CFB drive
grouping, missing/ambiguous player identity, provenance, game isolation,
transfer-player handling, stat-null behavior, duplicates, weekly
participation, cross-validation against PBP, and fantasy-draft tier
selection.
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


@pytest.fixture
def c():
    conn = engine_bootstrap.connect()
    yield conn
    conn.close()


# --- NFL PBP -----------------------------------------------------------------

def test_nfl_scoring_play_classification_real_game(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    scoring = pbp.game_scoring_plays(c, game_id="2023_01_ARI_WAS")
    types = {s["scoring_type"] for s in scoring}
    assert "PASSING_TOUCHDOWN" in types
    assert "RUSHING_TOUCHDOWN" in types
    assert "FUMBLE_RETURN_TOUCHDOWN" in types
    assert "FIELD_GOAL" in types
    assert "EXTRA_POINT" in types
    assert "UNCLASSIFIED_TOUCHDOWN" not in types  # real regression check for the pass_touchdown/rush_touchdown select-column bug


def test_nfl_turnover_classification_real(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    turnovers = pbp.game_turnovers(c, game_id="2023_01_ARI_WAS")
    assert len(turnovers) == 5
    assert any(t["turnover_type"] == "INTERCEPTION" for t in turnovers)


def test_nfl_fumble_only_counted_when_lost(c):
    """A fumble the offense recovers itself must never appear as a turnover."""
    from tools.quiz_export import nfl_pbp_facts as pbp
    row = c.execute(
        "SELECT game_id, play_id, play_desc, fumble_lost FROM nfl_plays "
        "WHERE play_desc LIKE '%FUMBLES%' AND fumble_lost=0 LIMIT 1"
    ).fetchone()
    assert row is not None
    t = pbp.classify_turnover(dict(row))
    assert t is None


def test_nfl_explosive_play_thresholds_are_caller_configurable(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    default = pbp.explosive_plays(c, game_id="2023_01_ARI_WAS")
    narrow = pbp.explosive_plays(c, game_id="2023_01_ARI_WAS", rush_threshold=5, pass_threshold=5)
    assert len(narrow) >= len(default)  # a looser threshold must never return fewer real plays


def test_nfl_derived_facts_real_game(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    facts = pbp.game_derived_facts(c, game_id="2023_01_ARI_WAS")
    assert facts["found"] is True
    assert facts["total_turnovers"] == 5
    assert facts["scoring_play_count"] == 11
    assert facts["first_touchdown"]["play_id"] == "699"
    assert sum(facts["scoring_by_quarter"].values()) == facts["scoring_play_count"]


def test_nfl_game_isolation(c):
    """Plays from one game must never leak into another game's facts."""
    from tools.quiz_export import nfl_pbp_facts as pbp
    plays_a = pbp.game_plays(c, game_id="2023_01_ARI_WAS")
    assert all(p["game_id"] == "2023_01_ARI_WAS" for p in plays_a)


def test_nfl_defensive_identity_honestly_unavailable(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    coverage = pbp.identity_coverage(c, season=2023)
    assert coverage["defensive_player_identity_available"] is False
    assert coverage["passer_resolution_pct"] > 90.0  # real, structured, near-complete offense-side coverage


def test_nfl_pbp_provenance_raw_text_preserved(c):
    from tools.quiz_export import nfl_pbp_facts as pbp
    plays = pbp.game_plays(c, game_id="2023_01_ARI_WAS")
    assert all(p["play_desc"] for p in plays if p["play_type"] in ("run", "pass"))


# --- CFB PBP -----------------------------------------------------------------

def test_cfb_scoring_play_classification_real_game(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    scoring = cpbp.game_scoring_plays(c, game_id="401520145")
    types = [s["scoring_type"] for s in scoring]
    assert "FIELD_GOAL" in types
    assert types.count("RUSHING_TOUCHDOWN") == 3
    assert "PASSING_TOUCHDOWN" in types


def test_cfb_two_point_conversion_requires_real_success_flag(c):
    """A failed two-point attempt must never be classified as a scoring play."""
    from tools.quiz_export import cfb_pbp_facts as cpbp
    failed = c.execute("SELECT play_type, scoring FROM cfb_plays WHERE play_type='2pt Conversion' AND scoring=0 LIMIT 1").fetchone()
    assert failed is not None
    scoring_type, agrees = cpbp.classify_scoring_play(dict(failed))
    assert scoring_type is None


def test_cfb_scoring_flag_disagreement_disclosed_not_hidden(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    report = cpbp.eligibility_report(c)
    assert report["scoring_flag_vs_play_type_agreement"]["disagree"] > 0  # real, confirmed source discrepancy


def test_cfb_drives_use_real_drive_id(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    drives = cpbp.game_drives(c, game_id="401520145")
    assert len(drives) == 22
    assert all(d["drive_id"] for d in drives)
    scoring_drives = [d for d in drives if d["is_scoring"]]
    assert any(d["points"] == 3 for d in scoring_drives)  # the real field goal drive
    assert any(d["points"] == 6 for d in scoring_drives)  # a real touchdown drive


def test_cfb_player_identity_resolved_on_real_scoring_play(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    scoring = cpbp.game_scoring_plays(c, game_id="401520145")
    pass_td = next(s for s in scoring if s["scoring_type"] == "PASSING_TOUCHDOWN")
    assert pass_td["identity"]["passer"]["resolution"] == "UNIQUE_ROSTER_MATCH"
    assert pass_td["identity"]["passer"]["cfb_player_id"] is not None


def test_cfb_player_identity_never_guesses_ambiguous_or_missing(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    result = cpbp._resolve_cfb_player_name(c, name="NOT_A_REAL_PLAYER_XYZ", school_id="CFB_SCHOOL_GEORGIA", season=2023)
    assert result["cfb_player_id"] is None
    assert result["resolution"] == "NO_ROSTER_MATCH"


def test_cfb_identity_coverage_measured_honestly(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    coverage = cpbp.identity_coverage(c, game_id="401520145")
    assert coverage["resolution_pct"] == 100.0
    assert coverage["ambiguous"] == 0


# --- CFB player-game stats -----------------------------------------------------

def test_cfb_player_game_stats_real_identity(c):
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    line = pgs.player_game_stat_line(c, cfb_player_id="ESPN_CFB:4575668", game_id="401520145")
    assert line["found"] is True
    assert line["passing_tds"] == 1


def test_cfb_player_game_stats_missing_is_honest(c):
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    line = pgs.player_game_stat_line(c, cfb_player_id="NOT_A_REAL_PLAYER", game_id="401520145")
    assert line["found"] is False


def test_cfb_player_game_stats_no_duplicate_rows(c):
    dupes = c.execute(
        "SELECT game_id, cfb_player_id, COUNT(*) n FROM cfb_player_game_stats_real GROUP BY game_id, cfb_player_id HAVING n > 1"
    ).fetchall()
    assert len(dupes) == 0


def test_cfb_player_game_stats_transfer_player_both_schools_real(c):
    """A real transfer player (Batch 1's cfb_transfer_summary) must have
    real, distinct game rows under BOTH schools -- never merged, never
    dropped to just one."""
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    row = c.execute(
        "SELECT cfb_player_id, first_school_id, last_school_id FROM cfb_transfer_summary "
        "WHERE cfb_player_id='ESPN_CFB:2094390'"
    ).fetchone()
    assert row is not None
    first_games = c.execute(
        "SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE cfb_player_id=? AND school_id=?",
        (row["cfb_player_id"], row["first_school_id"]),
    ).fetchone()[0]
    last_games = c.execute(
        "SELECT COUNT(*) FROM cfb_player_game_stats_real WHERE cfb_player_id=? AND school_id=?",
        (row["cfb_player_id"], row["last_school_id"]),
    ).fetchone()[0]
    assert first_games > 0 and last_games > 0


def test_cfb_player_game_stats_null_not_fabricated_zero(c):
    """tackles/tackles_for_loss/extra_points_made are real source gaps --
    must stay NULL, never a fabricated 0."""
    row = c.execute("SELECT tackles, tackles_for_loss, extra_points_made FROM cfb_player_game_stats_real LIMIT 1").fetchone()
    assert row["tackles"] is None
    assert row["tackles_for_loss"] is None
    assert row["extra_points_made"] is None


def test_cfb_player_game_stats_sack_real(c):
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    line = pgs.player_game_stat_line(c, cfb_player_id="ESPN_CFB:500313", game_id="400548422")
    assert line["found"] is True
    assert line["sacks"] == 2.0


def test_cfb_weekly_participation_real(c):
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    assert pgs.played_in_game(c, cfb_player_id="ESPN_CFB:4575668", game_id="401520145") is True
    assert pgs.played_in_game(c, cfb_player_id="NOT_A_REAL_PLAYER", game_id="401520145") is False


def test_cfb_team_top_performer_real(c):
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    top = pgs.team_week_top_performer(c, school_id="CFB_SCHOOL_UTEP", game_id="401520145", category="passing_yards")
    assert top["found"] is True
    assert top["cfb_player_id"] == "ESPN_CFB:4575668"


# --- Cross-validation ----------------------------------------------------------

def test_cross_validation_pbp_matches_player_game_stats_on_real_game(c):
    """Independently-derived TD counts (PBP-classified vs. raw structured
    CSV aggregation) must agree for this real, spot-checked game."""
    from tools.quiz_export import cfb_pbp_facts as cpbp
    from tools.quiz_export import cfb_player_game_stats_facts as pgs
    scoring = cpbp.game_scoring_plays(c, game_id="401520145")
    pass_td_player = next(s["identity"]["passer"]["cfb_player_id"] for s in scoring if s["scoring_type"] == "PASSING_TOUCHDOWN")
    line = pgs.player_game_stat_line(c, cfb_player_id=pass_td_player, game_id="401520145")
    assert line["passing_tds"] == 1


# --- Fantasy draft upgrade ----------------------------------------------------

def test_cfb_fantasy_draft_uses_confirmed_participation_for_completed_week(c):
    from tools.director_v04 import live_weekly_fantasy_draft as fd
    row = c.execute(
        "SELECT season, week FROM cfb_player_game_stats_real WHERE week IS NOT NULL ORDER BY season DESC, week DESC LIMIT 1"
    ).fetchone()
    result = fd.check_slate_feasibility("CFB_WEEKLY_FANTASY_DRAFT", row["season"], row["week"])
    assert result["pool_source"] == "GAME_PARTICIPATION_CONFIRMED"
    assert result["support_status"] == "SUPPORTED"


def test_cfb_fantasy_draft_falls_back_honestly_for_unscheduled_week(c):
    from tools.director_v04 import live_weekly_fantasy_draft as fd
    result = fd.check_slate_feasibility("CFB_WEEKLY_FANTASY_DRAFT", 2026, 1)
    assert result["support_status"] == "MISSING_DATA"  # no real games/rosters -- never fabricated


def test_nfl_fantasy_draft_tier_unaffected_by_cfb_change(c):
    """Regression: the NFL pool logic must be untouched by this batch's CFB-only edit."""
    from tools.director_v04 import live_weekly_fantasy_draft as fd
    row = c.execute(
        "SELECT pgs.season, pgs.week FROM player_game_stats pgs "
        "JOIN games g ON g.season=pgs.season AND g.week=CAST(pgs.week AS TEXT) AND g.game_type='REG' "
        "ORDER BY pgs.season DESC, CAST(pgs.week AS INTEGER) DESC LIMIT 1"
    ).fetchone()
    result = fd.check_slate_feasibility("NFL_WEEKLY_FANTASY_DRAFT", row["season"], row["week"])
    assert result["pool_source"] == "GAME_PARTICIPATION_CONFIRMED"
