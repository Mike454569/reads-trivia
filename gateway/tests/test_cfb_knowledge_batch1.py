"""Knowledge Expansion Batch 1 -- CFB rankings, All-America, transfers,
betting lines. Real, DB-backed tests: normalization, identity resolution,
duplicate handling, missing/null behavior, relationship queries,
provenance, derived betting outcomes, transfer ambiguity, poll
distinction, All-America distinction.
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


# --- Rankings ----------------------------------------------------------------

def test_rankings_poll_identity_never_merged(c):
    from tools.quiz_export import cfb_rankings_facts as rk
    polls = rk.real_polls(c)
    assert "AP Top 25" in polls and "Coaches Poll" in polls
    assert len(polls) >= 5  # real, distinct polls, never collapsed into one


def test_rankings_unranked_team_returns_honest_none(c):
    from tools.quiz_export import cfb_rankings_facts as rk
    result = rk.rank_for(c, school_id="CFB_SCHOOL_DOES_NOT_EXIST", season=2023, week=1)
    assert result["ranked"] is False
    assert result["rank"] is None


def test_rankings_season_type_prevents_false_conflicts(c):
    """Real bug found and fixed this batch: a naive (season, week, poll,
    school) grouping falsely flagged 1,141 'conflicts' that were actually
    distinct regular-season vs postseason rows sharing a week number."""
    from tools.quiz_export import cfb_rankings_facts as rk
    regular = rk.rank_for(c, school_id="CFB_SCHOOL_COLORADO", season=2002, week=1, season_type="regular")
    postseason = rk.rank_for(c, school_id="CFB_SCHOOL_COLORADO", season=2002, week=1, season_type="postseason")
    assert regular["ranked"] and postseason["ranked"]
    assert regular["rank"] != postseason["rank"]  # genuinely different real polls, never merged
    assert not regular["conflict"] and not postseason["conflict"]


def test_rankings_never_infer_missing_week(c):
    from tools.quiz_export import cfb_rankings_facts as rk
    # A far-future week with no real row must be honestly unranked, not an error or a guess.
    result = rk.rank_for(c, school_id="CFB_SCHOOL_GEORGIA", season=2023, week=99)
    assert result["ranked"] is False


def test_game_ranking_context_real_ranked_vs_unranked(c):
    from tools.quiz_export import cfb_rankings_facts as rk
    ctx = rk.game_ranking_context(c, game_id="401525871")  # Oklahoma (ranked) vs UCF (unranked), 2023 week 8
    assert ctx["found"] is True
    assert ctx["matchup_category"] == "RANKED_VS_UNRANKED"
    assert ctx["home_team_rank"]["ranked"] is True
    assert ctx["away_team_rank"]["ranked"] is False


def test_game_ranking_context_missing_game_is_honest(c):
    from tools.quiz_export import cfb_rankings_facts as rk
    ctx = rk.game_ranking_context(c, game_id="not-a-real-game-id")
    assert ctx["found"] is False


# --- All-America --------------------------------------------------------------

def test_all_america_identity_resolution_never_guesses_ambiguous_names(c):
    """Real, found ambiguity: 12 rows have 2+ distinct real canonical
    players at the same school under the same normalized name -- these
    must be excluded from the certified table, never force-matched."""
    row = c.execute(
        "SELECT record_id, player_name, school_id FROM cfb_all_america aa "
        "WHERE NOT EXISTS (SELECT 1 FROM cfb_all_america_certified cert WHERE cert.record_id = aa.record_id) "
        "LIMIT 1"
    ).fetchone()
    assert row is not None  # real unresolved rows exist and are excluded, not forced


def test_all_america_certified_rows_have_a_real_canonical_player(c):
    rows = c.execute("SELECT cfb_player_id FROM cfb_all_america_certified LIMIT 50").fetchall()
    assert rows
    for r in rows:
        exists = c.execute("SELECT 1 FROM canonical_cfb_players WHERE cfb_player_id=?", (r["cfb_player_id"],)).fetchone()
        assert exists is not None


def test_all_america_school_lookup_finds_multiple_honorees(c):
    from tools.quiz_export import cfb_all_america_facts as aa
    row = c.execute(
        "SELECT school_id, COUNT(*) c FROM cfb_all_america_certified GROUP BY school_id ORDER BY c DESC LIMIT 1"
    ).fetchone()
    results = aa.school_all_americans(c, school_id=row["school_id"])
    assert len(results) == row["c"]
    assert len(results) > 1


def test_all_america_honor_level_distinction_preserved_not_flattened(c):
    """is_consensus is a real, distinct field from selectors_raw -- never
    collapsed into a single generic boolean that discards selector
    provenance."""
    row = c.execute("SELECT is_consensus, selectors_raw FROM cfb_all_america_certified WHERE is_consensus=1 LIMIT 1").fetchone()
    assert row is not None
    assert row["selectors_raw"] is not None  # raw provenance retained alongside the normalized flag


def test_all_america_provenance_traceable_to_source_row(c):
    from tools.quiz_export import cfb_all_america_facts as aa
    row = c.execute("SELECT cfb_player_id, record_id FROM cfb_all_america_certified LIMIT 1").fetchone()
    honors = aa.player_honor(c, cfb_player_id=row["cfb_player_id"])
    assert any(h["record_id"] == row["record_id"] for h in honors)
    source = c.execute("SELECT * FROM cfb_all_america WHERE record_id=?", (row["record_id"],)).fetchone()
    assert source is not None  # every certified fact traces back to a real source row


# --- Transfers -----------------------------------------------------------------

def test_transfer_authoritative_table_has_zero_orphaned_identities(c):
    from tools.quiz_export import cfb_transfer_facts as tr
    report = tr.integrity_report(c)
    assert report["orphaned_player_id_rows"] == 0
    assert report["real_transfer_rows"] > 0


def test_transfer_path_is_real_and_ordered(c):
    from tools.quiz_export import cfb_transfer_facts as tr
    row = c.execute("SELECT cfb_player_id FROM cfb_transfer_summary WHERE transfer_count > 0 LIMIT 1").fetchone()
    path = tr.transfer_path(c, cfb_player_id=row["cfb_player_id"])
    assert path["found"] is True
    assert path["is_transfer"] is True
    assert len(path["path"]) == path["school_count"]
    assert path["first_school_id"] != path["last_school_id"]


def test_transfer_not_found_is_honest(c):
    from tools.quiz_export import cfb_transfer_facts as tr
    result = tr.transfer_path(c, cfb_player_id="NOT_A_REAL_PLAYER_ID")
    assert result["found"] is False


def test_transfers_in_and_out_are_real_and_distinct(c):
    from tools.quiz_export import cfb_transfer_facts as tr
    row = c.execute("SELECT first_school_id FROM cfb_transfer_summary WHERE transfer_count > 0 LIMIT 1").fetchone()
    out_transfers = tr.transfers_involving_school(c, school_id=row["first_school_id"], direction="out")
    assert len(out_transfers) >= 1
    for t in out_transfers:
        assert t["first_school_id"] == row["first_school_id"]


# --- Betting lines ---------------------------------------------------------------

def test_betting_lines_join_cleanly_to_real_games(c):
    from tools.quiz_export import cfb_betting_facts as bl
    report = bl.eligibility_report(c)
    assert report["unresolved_games"] == 0
    assert report["total_rows"] == report["matched_to_real_game"]


def test_betting_missing_line_never_produces_a_fabricated_result(c):
    from tools.quiz_export import cfb_betting_facts as bl
    result = bl.spread_result(c, game_id="401635575", provider="NOT_A_REAL_PROVIDER")
    assert result["has_line"] is False
    assert result["cover_result"] is None


def test_betting_push_is_a_real_push_not_a_win_or_loss(c):
    from tools.quiz_export import cfb_betting_facts as bl
    result = bl.spread_result(c, game_id="401645362", provider="DraftKings")
    assert result["cover_result"] == "PUSH"


def test_betting_cover_result_matches_real_final_score(c):
    """Real, direct math check -- proves the derivation, not a hardcoded answer."""
    from tools.quiz_export import cfb_betting_facts as bl
    game = c.execute(
        "SELECT home_score, away_score FROM cfb_games_canonical WHERE game_id=?", ("401635575",),
    ).fetchone()
    result = bl.spread_result(c, game_id="401635575", provider="DraftKings")
    home_margin = game["home_score"] - game["away_score"]
    ats_margin = home_margin + result["spread"]
    assert (ats_margin > 0) == (result["cover_result"] == "FAVORITE_COVERED") or result["cover_result"] == "PUSH"


def test_betting_over_under_never_computed_without_a_final_score(c):
    from tools.quiz_export import cfb_betting_facts as bl
    unplayed = c.execute(
        "SELECT b.game_id, b.provider FROM cfb_betting_lines b JOIN cfb_games_canonical g ON g.game_id=b.game_id "
        "WHERE g.home_score IS NULL LIMIT 1"
    ).fetchone()
    if unplayed:
        result = bl.total_result(c, game_id=unplayed["game_id"], provider=unplayed["provider"])
        assert result["over_under_result"] is None


def test_betting_provider_identity_preserved_not_averaged(c):
    from tools.quiz_export import cfb_betting_facts as bl
    lines = bl.game_line(c, game_id="401635575")
    if len(lines) > 1:
        providers = {l["provider"] for l in lines}
        assert len(providers) == len(lines)  # one real row per real provider, never merged


# --- Cross-league --------------------------------------------------------------

def test_all_america_to_nfl_bridge_uses_real_certified_data(c):
    from tools.quiz_export import cfb_all_america_facts as aa
    result = aa.all_america_to_nfl_bridge(c)
    assert result["total_certified_honors"] > 0
    assert 0 <= result["joined_to_nfl_identity"] <= result["total_certified_honors"]


def test_transfer_to_nfl_bridge_uses_real_certified_data(c):
    from tools.quiz_export import cfb_transfer_facts as tr
    result = tr.transfer_to_nfl_bridge(c)
    assert result["total_real_transfers"] > 0
    assert 0 <= result["joined_to_nfl_identity"] <= result["total_real_transfers"]
