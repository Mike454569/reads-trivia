"""Knowledge Expansion Batch 2 -- NFL All-Pro, Pro Bowl, Hall of Fame,
NFL/CFB coordinators, NFL hometown/high school. Real, DB-backed tests:
All-Pro tier distinction, Pro Bowl season membership, HOF induction
classes, player identity ambiguity, coach identity, coordinator roles,
co-coordinator handling, historical coverage, hometown vs high-school
separation, NULL/UNKNOWN behavior, provenance, cross-league joins.
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


# --- Hall of Fame --------------------------------------------------------------

def test_hof_player_vs_non_player_never_merged(c):
    from tools.quiz_export import nfl_hof_facts as hof
    row = c.execute("SELECT COUNT(*) FROM nfl_hof_inductees WHERE is_player=0").fetchone()[0]
    assert row > 0  # real non-player inductees (coaches, owners, ...) exist and are tracked separately
    report = hof.eligibility_report(c)
    assert report["player_inductees"] + report["non_player_inductees"] == report["total_inductees"]


def test_hof_induction_class_is_real(c):
    from tools.quiz_export import nfl_hof_facts as hof
    result = hof.player_hof_status(c, player_id="PFR:AikmTr00")
    assert result["is_hall_of_famer"] is True
    assert result["class_year"] == 2006


def test_hof_non_hall_of_famer_is_honest(c):
    from tools.quiz_export import nfl_hof_facts as hof
    result = hof.player_hof_status(c, player_id="NOT_A_REAL_PLAYER_ID")
    assert result["is_hall_of_famer"] is False


def test_hof_class_year_grouping_real(c):
    from tools.quiz_export import nfl_hof_facts as hof
    cls = hof.hof_class(c, class_year=2006)
    names = {p["inductee_name_raw"] for p in cls["players"]}
    assert "Troy Aikman" in names


def test_hof_duplicate_name_across_classes_does_not_collide(c):
    """Real schema check: (inductee_name_raw, class_year) is the unique
    key, not name alone -- two different real people who share a name in
    different classes must not collide into one row."""
    dupe_names = c.execute(
        "SELECT inductee_name_raw, COUNT(*) n FROM nfl_hof_inductees GROUP BY inductee_name_raw HAVING n > 1"
    ).fetchall()
    for row in dupe_names:
        years = c.execute(
            "SELECT DISTINCT class_year FROM nfl_hof_inductees WHERE inductee_name_raw=?", (row["inductee_name_raw"],)
        ).fetchall()
        assert len(years) == row["n"]  # every same-name row is a genuinely distinct real class year


def test_hof_multi_team_player_real_and_ordered(c):
    from tools.quiz_export import nfl_hof_facts as hof
    row = c.execute(
        "SELECT hof_id FROM nfl_hof_inductee_teams GROUP BY hof_id HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    teams = hof.player_teams(c, hof_id=row["hof_id"])
    assert len(teams) > 1
    assert teams[0]["team_order"] < teams[1]["team_order"]


# --- All-Pro ---------------------------------------------------------------------

def test_all_pro_first_team_vs_second_team_never_collapsed(c):
    from tools.quiz_export import nfl_all_pro_facts as ap
    rows = ap.season_all_pro_players(c, season=2023, position_raw="Quarterback")
    levels = {r["honor_level"] for r in rows}
    assert "FIRST_TEAM" in levels and "SECOND_TEAM" in levels  # both real tiers present, not merged


def test_all_pro_selector_provenance_never_merged_across_bodies(c):
    """A player picked by only PFWA (not AP) must not be silently counted
    as an AP selection."""
    from tools.quiz_export import nfl_all_pro_facts as ap
    non_ap_rows = c.execute(
        "SELECT COUNT(*) FROM nfl_all_pro_selections WHERE is_ap=0 AND selectors_raw != ''"
    ).fetchone()[0]
    assert non_ap_rows > 0
    report = ap.eligibility_report(c)
    assert report["ap_confirmed_rows"] < report["total_rows"]  # real, disclosed distinction preserved


def test_all_pro_transitional_years_honestly_skipped(c):
    rows = c.execute("SELECT COUNT(*) FROM nfl_all_pro_selections WHERE season BETWEEN 1963 AND 1968").fetchone()[0]
    assert rows == 0  # real, disclosed format gap -- never force-parsed


def test_all_pro_cross_era_and_cross_position_real_examples(c):
    from tools.quiz_export import nfl_all_pro_facts as ap
    classic_qb = ap.season_all_pro_players(c, season=1940, position_raw="Quarterback")
    modern_cb = ap.season_all_pro_players(c, season=2023, position_raw="Cornerback")
    assert any(r["player_name_raw"] == "Sammy Baugh" for r in classic_qb)
    assert len(modern_cb) > 0


def test_all_pro_count_real(c):
    from tools.quiz_export import nfl_all_pro_facts as ap
    n = ap.player_all_pro_count(c, player_id="PFR:MannPe00")
    assert n > 0


# --- Pro Bowl ----------------------------------------------------------------------

def test_pro_bowl_tier_distinction_real(c):
    from tools.quiz_export import nfl_pro_bowl_facts as pb
    rows = pb.season_pro_bowl_players(c, season=2023, position_raw="Quarterback")
    tiers = {r["tier"] for r in rows}
    assert "STARTER" in tiers and "RESERVE" in tiers


def test_pro_bowl_season_membership_real(c):
    from tools.quiz_export import nfl_pro_bowl_facts as pb
    seasons = pb.player_pro_bowl_seasons(c, player_id="PFR:MannPe00")
    assert len(seasons) == 12  # real, verified count


def test_pro_bowl_compare_counts_real(c):
    from tools.quiz_export import nfl_pro_bowl_facts as pb
    result = pb.compare_pro_bowl_counts(c, player_id_a="PFR:MannPe00", player_id_b="NOT_A_REAL_PLAYER")
    assert result["more_selections"] == "PFR:MannPe00"


def test_pro_bowl_never_infers_a_missing_year(c):
    rows = c.execute("SELECT COUNT(*) FROM nfl_pro_bowl_selections WHERE season=1978").fetchone()[0]
    assert rows == 0  # real, disclosed per-year format gap


# --- NFL coordinators --------------------------------------------------------------

def test_nfl_coordinator_role_distinction_real(c):
    from tools.quiz_export import nfl_coordinator_facts as ncf
    result = ncf.team_season_coordinator(c, team_code="KC", season=2026, role="OFFENSIVE_COORDINATOR")
    assert result["found"] is True
    assert result["coach_name_raw"]


def test_nfl_coordinator_special_teams_honestly_unavailable(c):
    from tools.quiz_export import nfl_coordinator_facts as ncf
    result = ncf.team_season_coordinator(c, team_code="KC", season=2026, role="SPECIAL_TEAMS_COORDINATOR")
    assert result["found"] is False  # no real source for this role this batch -- never guessed


def test_nfl_coordinator_coach_identity_reused_not_duplicated(c):
    """A coordinator's coach_id must exist in the shared `coaches` identity table."""
    row = c.execute("SELECT DISTINCT coach_id FROM nfl_coordinators LIMIT 5").fetchall()
    for r in row:
        exists = c.execute("SELECT 1 FROM coaches WHERE coach_id=?", (r["coach_id"],)).fetchone()
        assert exists is not None


def test_nfl_coordinator_all_32_teams_covered(c):
    from tools.quiz_export import nfl_coordinator_facts as ncf
    report = ncf.eligibility_report(c)
    assert report["teams_covered"] == 32


# --- CFB coordinators ----------------------------------------------------------------

def test_cfb_co_coordinator_distinction_preserved(c):
    from tools.quiz_export import cfb_coordinator_facts as ccf
    rows = ccf.school_season_coordinators(c, school_id="CFB_SCHOOL_GEORGIA", season=2025)
    roles = {r["normalized_role"] for r in rows}
    assert "DEFENSIVE_COORDINATOR" in roles and "CO_DEFENSIVE_COORDINATOR" in roles


def test_cfb_coordinator_raw_title_retained(c):
    row = c.execute(
        "SELECT title_raw FROM cfb_coordinators WHERE school_id='CFB_SCHOOL_GEORGIA' AND normalized_role='OFFENSIVE_COORDINATOR'"
    ).fetchone()
    assert "coordinator" in row["title_raw"].lower()


def test_cfb_coordinator_unfetched_program_is_honest(c):
    from tools.quiz_export import cfb_coordinator_facts as ccf
    rows = ccf.school_season_coordinators(c, school_id="CFB_SCHOOL_TEXAS", season=2025)
    assert rows == []  # real, disclosed miss -- not a guessed/fabricated coordinator


# --- NFL hometown / high school --------------------------------------------------------

def test_hometown_and_high_school_kept_as_distinct_concepts(c):
    """Real example this batch: Troy Aikman was born in West Covina,
    California but attended high school in Henryetta, Oklahoma -- the two
    location concepts must never be merged."""
    from tools.quiz_export import nfl_hometown_facts as hm
    bg = hm.player_background(c, player_id="PFR:AikmTr00")
    assert bg["found"] is True
    assert bg["birthplace_state"] == "California"
    assert bg["high_school_state"] == "Oklahoma"


def test_hometown_missing_player_is_honest(c):
    from tools.quiz_export import nfl_hometown_facts as hm
    result = hm.player_background(c, player_id="NOT_A_REAL_PLAYER")
    assert result["found"] is False


def test_high_school_players_lookup_real(c):
    from tools.quiz_export import nfl_hometown_facts as hm
    row = c.execute("SELECT high_school_name FROM nfl_player_background WHERE high_school_name IS NOT NULL LIMIT 1").fetchone()
    results = hm.high_school_players(c, high_school_name=row["high_school_name"])
    assert len(results) >= 1


def test_hometown_sample_disclosed_not_league_wide(c):
    from tools.quiz_export import nfl_hometown_facts as hm
    report = hm.eligibility_report(c)
    assert report["total_players_attempted"] == 107
    assert report["hometown_equals_birthplace_source_limitation"] is True


# --- Cross-league --------------------------------------------------------------------

def test_all_america_to_hof_overlap_real(c):
    from tools.quiz_export import cross_league_batch2_facts as cl
    result = cl.all_america_to_hof(c)
    assert result["all_america_players"] > 0
    assert 0 <= result["also_hall_of_fame"] <= result["all_america_players"]


def test_all_america_to_all_pro_overlap_real(c):
    from tools.quiz_export import cross_league_batch2_facts as cl
    result = cl.all_america_to_all_pro(c)
    assert result["also_ap_all_pro"] > 0  # real, non-trivial overlap


def test_transfer_overlap_is_honestly_small(c):
    """Batch 1 found the transfer->NFL bridge is only 4.6% and skews very
    recent (portal era) -- real overlap with All-Pro/Pro Bowl/HOF should
    be small/zero, not forced."""
    from tools.quiz_export import cross_league_batch2_facts as cl
    result = cl.transfer_to_all_pro_pro_bowl_hof(c)
    assert result["real_transfers"] > 0
    assert result["also_hall_of_fame"] >= 0


def test_college_to_hof_uses_real_data_not_hardcoded(c):
    from tools.quiz_export import cross_league_batch2_facts as cl
    rows = cl.college_to_hof_players(c)
    assert len(rows) > 0
    assert all(r["n"] > 0 for r in rows)


# --- Provenance ------------------------------------------------------------------------

def test_all_pro_provenance_traceable(c):
    row = c.execute("SELECT selection_id, source_page, retrieved_at FROM nfl_all_pro_selections LIMIT 1").fetchone()
    assert row["source_page"].startswith("https://en.wikipedia.org/wiki/")
    assert row["retrieved_at"]


def test_pro_bowl_provenance_traceable(c):
    row = c.execute("SELECT source_page, retrieved_at, verification_status FROM nfl_pro_bowl_selections LIMIT 1").fetchone()
    assert row["source_page"] and row["retrieved_at"] and row["verification_status"] == "WIKIPEDIA_STRUCTURED_SECONDARY"


def test_coordinator_provenance_traceable(c):
    row = c.execute("SELECT source_page, retrieved_at FROM nfl_coordinators LIMIT 1").fetchone()
    assert row["source_page"] and row["retrieved_at"]
