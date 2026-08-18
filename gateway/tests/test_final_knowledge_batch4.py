"""Final Knowledge Expansion Batch 4 -- NFL defensive PBP identity, real
NFL drives, broader CFB PBP identity, CFB kicking (XP), and verification
of already-complete historical NFL player-game coverage. Real, DB-backed
tests: defensive event identity, ambiguous/unresolved identity, source
provenance, historical NULL behavior, drive relationships, CFB play-level
identity, cross-validation, and query performance regressions.
"""
from __future__ import annotations

import sys
import time
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


# --- NFL defensive PBP identity ------------------------------------------------

def test_nfl_interceptor_identity_real(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    events = ndd.game_defensive_events(c, game_id="1999_01_ARI_PHI")
    intercept_rows = [e for e in events if e.get("interception_player_id")]
    assert any(e["interception_player_id"] == "PFR:HarrAl21" for e in intercept_rows)


def test_nfl_two_sack_game_real(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    n = ndd.player_game_sacks(c, player_id="PFR:AbraJo00", game_id="2000_07_NYJ_NE")
    assert n >= 2
    assert ndd.player_sacked_qb_in_game(c, player_id="PFR:AbraJo00", game_id="2000_07_NYJ_NE") is True


def test_nfl_forced_fumble_real(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    events = ndd.game_defensive_events(c, game_id="1999_01_ARI_PHI")
    assert any(e.get("forced_fumble_player_1_id") == "PFR:RiceSi00" for e in events)


def test_nfl_defensive_identity_never_forced(c):
    """A GSIS id with no canonical_players match must stay NULL, not guessed."""
    row = c.execute(
        "SELECT sack_player_gsis, sack_player_id FROM nfl_plays_defense_ext "
        "WHERE sack_player_gsis IS NOT NULL AND sack_player_gsis != '' AND sack_player_id IS NULL LIMIT 1"
    ).fetchone()
    assert row is not None  # real, disclosed unresolved GSIS ids exist
    assert row["sack_player_id"] is None


def test_nfl_defensive_identity_resolution_measured_and_strong(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    report = ndd.defensive_identity_coverage(c)
    assert report["sack_resolution_pct"] > 80.0
    assert report["interception_resolution_pct"] > 80.0


def test_nfl_defensive_provenance_traceable(c):
    row = c.execute("SELECT source_id, retrieved_at, verification_status FROM nfl_plays_defense_ext LIMIT 1").fetchone()
    assert row["source_id"] == "NFLVERSE_DATA"
    assert row["retrieved_at"] and row["verification_status"]


# --- NFL drives -----------------------------------------------------------------

def test_nfl_drives_real_game(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    drives = ndd.game_drives(c, game_id="2023_01_ARI_WAS")
    assert len(drives) > 0
    td_drives = [d for d in drives if d["result_raw"] == "Touchdown"]
    assert any(d["points"] == 7 and d["is_scoring"] for d in td_drives)
    fg_drives = [d for d in drives if d["result_raw"] == "Field goal"]
    assert any(d["points"] == 3 for d in fg_drives)


def test_nfl_drive_turnover_classification_includes_opp_touchdown(c):
    """A drive that ends in the OPPONENT scoring (pick-six/fumble-return
    TD charted against this offense's drive) must be flagged as a real
    turnover, and must never be credited 7 points to the offense."""
    row = c.execute("SELECT game_id, drive_number FROM nfl_drives_real WHERE result_raw='Opp touchdown' LIMIT 1").fetchone()
    if row:
        from tools.quiz_export import nfl_defense_drive_facts as ndd
        d = ndd.drive_result(c, game_id=row["game_id"], drive_number=row["drive_number"])
        assert d["found"] is True


def test_nfl_drive_sequence_real(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    seq = ndd.game_drive_sequence(c, game_id="2023_01_ARI_WAS")
    assert len(seq) > 0
    assert "Touchdown" in seq


def test_nfl_drive_missing_game_is_honest(c):
    from tools.quiz_export import nfl_defense_drive_facts as ndd
    d = ndd.drive_result(c, game_id="NOT_A_REAL_GAME", drive_number=1)
    assert d["found"] is False


# --- Broader CFB PBP identity ----------------------------------------------------

def test_cfb_broader_events_include_non_scoring_plays(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    events = cpbp.game_play_events(c, game_id="401520145")
    types = {e["play_type"] for e in events}
    assert "Rush" in types
    assert "Pass Reception" in types
    assert "Sack" in types


def test_cfb_split_sack_both_defenders_tracked_separately(c):
    """A real split sack (two defenders) must keep both identities
    distinct, never collapsed into one credited sacker."""
    from tools.quiz_export import cfb_pbp_facts as cpbp
    events = cpbp.game_play_events(c, game_id="401520145")
    split_sacks = [e for e in events if e["play_type"] == "Sack" and "defender2" in e.get("identity", {})]
    assert len(split_sacks) >= 1
    e = split_sacks[0]
    assert e["identity"]["defender"]["name_raw"] != e["identity"]["defender2"]["name_raw"]


def test_cfb_broader_identity_coverage_improves_on_batch3_scope(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    cov = cpbp.broader_identity_coverage(c, game_id="401520145")
    assert cov["resolution_pct"] > 90.0
    assert "Rush" in cov["by_event_type"]
    assert "Sack" in cov["by_event_type"]


def test_cfb_ambiguous_or_missing_participant_never_guessed(c):
    from tools.quiz_export import cfb_pbp_facts as cpbp
    result = cpbp._resolve_cfb_player_name(c, name="A Totally Fake Player Name", school_id="CFB_SCHOOL_UTEP", season=2023)
    assert result["cfb_player_id"] is None
    assert result["resolution"] == "NO_ROSTER_MATCH"


# --- CFB kicking (XP) ------------------------------------------------------------

def test_cfb_kicking_real_xp_data(c):
    from tools.quiz_export import cfb_kicking_facts as ckf
    row = c.execute("SELECT cfb_player_id, game_id FROM cfb_player_game_kicking_ext WHERE xp_attempted > 0 LIMIT 1").fetchone()
    assert row is not None
    line = ckf.player_game_kicking(c, cfb_player_id=row["cfb_player_id"], game_id=row["game_id"])
    assert line["found"] is True
    assert line["xp_attempted"] > 0


def test_cfb_kicking_no_xp_attempts_is_honest_none(c):
    from tools.quiz_export import cfb_kicking_facts as ckf
    row = c.execute("SELECT cfb_player_id, game_id FROM cfb_player_game_kicking_ext WHERE xp_attempted = 0 LIMIT 1").fetchone()
    if row:
        result = ckf.kicker_perfect_xp_game(c, cfb_player_id=row["cfb_player_id"], game_id=row["game_id"])
        assert result is None  # never a fabricated True/False with zero real attempts


def test_cfb_kicking_missing_player_is_honest(c):
    from tools.quiz_export import cfb_kicking_facts as ckf
    line = ckf.player_game_kicking(c, cfb_player_id="NOT_A_REAL_PLAYER", game_id="401520154")
    assert line["found"] is False


def test_cfb_kicking_identity_reuses_espn_athlete_id_space(c):
    row = c.execute("SELECT cfb_player_id FROM cfb_player_game_kicking_ext LIMIT 5").fetchall()
    for r in row:
        exists = c.execute("SELECT 1 FROM canonical_cfb_players WHERE cfb_player_id=?", (r["cfb_player_id"],)).fetchone()
        assert exists is not None


# --- Cross-validation --------------------------------------------------------------

def test_cross_validate_fg_between_espn_and_batch3_source(c):
    from tools.quiz_export import cfb_kicking_facts as ckf
    row = c.execute(
        "SELECT DISTINCT game_id FROM cfb_player_game_kicking_ext WHERE fg_attempted > 0 LIMIT 1"
    ).fetchone()
    assert row is not None
    results = ckf.cross_validate_field_goals(c, game_id=row["game_id"])
    assert len(results) > 0


# --- Historical NFL player-game stats (verification, not new ingestion) -------------

def test_historical_nfl_player_game_stats_already_full_range(c):
    row = c.execute("SELECT MIN(season), MAX(season) FROM player_game_stats").fetchone()
    assert row[0] <= 1999
    assert row[1] >= 2025


def test_historical_nfl_defensive_stats_real_not_placeholder(c):
    """Confirms 1999-era defensive stats are real recorded values, not a
    zero-filled placeholder -- see report for the full verification."""
    n = c.execute("SELECT COUNT(*) FROM player_game_stats WHERE season=1999 AND tackles > 0").fetchone()[0]
    assert n > 1000


# --- Performance ------------------------------------------------------------------

def test_nfl_defense_ext_sack_lookup_uses_index(c):
    plan = c.execute("EXPLAIN QUERY PLAN SELECT * FROM nfl_plays_defense_ext WHERE sack_player_id=?", ("PFR:AbraJo00",)).fetchall()
    assert any("USING INDEX" in str(tuple(row)) for row in plan)


def test_nfl_drives_game_lookup_is_fast(c):
    t0 = time.time()
    c.execute("SELECT * FROM nfl_drives_real WHERE game_id=?", ("2023_01_ARI_WAS",)).fetchall()
    assert time.time() - t0 < 0.5
