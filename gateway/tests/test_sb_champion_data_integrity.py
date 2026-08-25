"""P0 Accuracy + Reliability Hardening pass (Section 7): systematic
validation of the curated Super Bowl champion dataset
(curated_nfl_offense_college_board, board_type='SB_CHAMPION'), expanded
beyond a one-time spot check into a permanent, automated, full-dataset
cross-source consistency check.

Real bug this closes: every one of the 60 SB_CHAMPION rows had `season`
off by exactly +1 year (a real, systemic Gold Standard workbook labeling
error -- e.g. the curated row for the Denver Broncos' SB XXXIII win was
labeled season=1999 instead of the real 1998). Found by cross-checking
against nfl_championship_events, an INDEPENDENTLY Wikipedia-sourced table
already in this database (source_id='WIKIPEDIA_STRUCTURED', a genuinely
different pipeline than the curated workbook's 'READS_GOLD_STANDARD_
BLUEPRINT_V1'). Fixed via a direct, verified data correction (season = season
- 1 for all 60 rows); this file is what keeps it from silently drifting
back."""
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


def _curated_sb_rows(c):
    return c.execute(
        "SELECT board_id, season, team_display_name FROM curated_nfl_offense_college_board "
        "WHERE board_type='SB_CHAMPION' ORDER BY season ASC"
    ).fetchall()


def _wiki_rows(c):
    return c.execute(
        "SELECT sb_number, season, winner_name_raw FROM nfl_championship_events ORDER BY game_date ASC"
    ).fetchall()


def test_sb_champion_count_matches_second_source():
    c = engine_bootstrap.connect()
    try:
        curated = _curated_sb_rows(c)
        wiki = _wiki_rows(c)
    finally:
        c.close()
    assert len(curated) == 60, f"expected 60 real curated SB_CHAMPION rows, got {len(curated)}"
    assert len(wiki) == 60, f"expected 60 real nfl_championship_events rows, got {len(wiki)}"


def test_every_sb_champion_season_and_winner_matches_independent_source():
    """The real, full-dataset systematic check -- every one of the 60 real
    Super Bowls, paired positionally in chronological order (never by a
    fuzzy season/team-name match, which is ambiguous for repeat champions
    like the Steelers/49ers/Patriots/Cowboys), must agree on BOTH season
    and winner name with the independently-sourced nfl_championship_events
    table. A structurally valid join is not enough -- this checks the real
    facts."""
    c = engine_bootstrap.connect()
    try:
        curated = _curated_sb_rows(c)
        wiki = _wiki_rows(c)
    finally:
        c.close()

    mismatches = []
    for cur, wk in zip(curated, wiki):
        curated_name = cur["team_display_name"].strip().lower().replace("oakland/la raiders", "oakland raiders")
        wiki_name = wk["winner_name_raw"].strip().lower()
        if cur["season"] != wk["season"] or curated_name != wiki_name:
            mismatches.append({
                "board_id": cur["board_id"], "curated_season": cur["season"], "curated_team": cur["team_display_name"],
                "wiki_sb_number": wk["sb_number"], "wiki_season": wk["season"], "wiki_team": wk["winner_name_raw"],
            })
    assert not mismatches, f"{len(mismatches)} SB_CHAMPION rows disagree with the independent second source: {mismatches}"


def test_sb_champion_seasons_have_no_duplicates():
    c = engine_bootstrap.connect()
    try:
        seasons = [r["season"] for r in _curated_sb_rows(c)]
    finally:
        c.close()
    assert len(seasons) == len(set(seasons)), "duplicate season value(s) in SB_CHAMPION data -- two champions can't share one real season"


def test_sb_champion_offense_college_generates_the_corrected_season():
    """End-to-end: the real, live-generated question must show the
    corrected (real) season, not the pre-fix off-by-one value, for a
    specific, independently-verifiable real championship (SB XXIX, Jan
    1995, capped the 1994 season -- San Francisco 49ers)."""
    from tools.director_v02 import registry
    from tools import game_director_v01 as gd

    cap = registry.CAPABILITY_REGISTRY[
        ("guess", "NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE")
    ]
    spec = {
        "mechanic": "guess", "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
        "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
        "question_count": 60, "filters": {}, "exclusions": [],
    }
    pkg = gd.generate_package_from_spec(
        spec, cap["adapter"], request_text="integrity check", director_request_id="sb-season-check",
        seed="sb-season-integrity", target_count=60,
    )
    answers = {q["answer"] for q in pkg["questions"]}
    assert "1994 San Francisco 49ers" in answers, (
        f"expected the corrected '1994 San Francisco 49ers' answer to appear somewhere in a 60-question "
        f"pull; got answers like: {sorted(answers)[:5]}"
    )
    assert "1995 San Francisco 49ers" not in answers, "the pre-fix off-by-one season must never appear again"
