"""P0 Accuracy + Reliability Hardening pass: permanent regression coverage
for the real false-join bug found during an earlier production validation
pass -- CFB Ranking Upset previously claimed Ole Miss upset AP No. 5
Georgia in Week 1 of the 2025 season. Root cause: cfb_rankings carries a
SEPARATE real row for the same (school, season, week, poll) whenever a
regular-season week number collides with a postseason week number (both
tagged "week 1") -- the adapter's LEFT JOIN fanned out into multiple
candidate rows for ONE real game, mixing regular-season and postseason
ranks into a self-contradictory pair. Fixed in
tools/quiz_export/adapters/cfb_upset_ranking.py by also matching
season_type on the join. This file exists so that fix can never silently
regress.

The real game this bug was about: game_id 401769073, the actual 2025 CFP
game where Georgia (home) lost to Ole Miss (away) 34-39 -- Georgia was
ranked #5 (regular season) / #6 (postseason poll) at kickoff, Ole Miss was
#21 (regular season) / #3 (postseason poll). Using SELF-CONSISTENT
postseason ranks (the correct season_type for a postseason game), Ole Miss
(#3) was ranked BETTER than Georgia (#6) -- so this specific game is not a
real "upset" under RANKING_UPSET's own definition and must never be
generated as one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters import cfb_upset_ranking  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

OLE_MISS_GEORGIA_CFP_2025_GAME_ID = "401769073"


def test_ole_miss_georgia_2025_cfp_game_never_generated_as_false_upset():
    """The exact regression case: this real game must either be entirely
    absent from candidates, or (if present) have fully self-consistent
    ranks for its own season_type -- never a mismatched regular/postseason
    rank pair, and never accepted by evaluate() as a real upset (Ole Miss
    was the better-ranked team using the correct postseason poll)."""
    c = engine_bootstrap.connect()
    try:
        candidates = cfb_upset_ranking.fetch_ordered_candidates(c, seed="regression-ole-miss-georgia")
        matches = [row for row in candidates if row["game_id"] == OLE_MISS_GEORGIA_CFP_2025_GAME_ID]
        # The season_type join fix must collapse this to at most one
        # self-consistent row -- never the pre-fix fan-out of up to 4 rows
        # mixing regular/postseason ranks.
        assert len(matches) <= 1, (
            f"expected at most 1 self-consistent candidate row for game "
            f"{OLE_MISS_GEORGIA_CFP_2025_GAME_ID}, got {len(matches)}: {matches}"
        )
        for row in matches:
            # Real, correct postseason ranks for this exact game (verified
            # directly against cfb_rankings): Georgia #6, Ole Miss #3.
            assert row["home_rank"] == 6, f"Georgia's postseason rank should be 6, got {row['home_rank']}"
            assert row["away_rank"] == 3, f"Ole Miss's postseason rank should be 3, got {row['away_rank']}"

        rng = engine_bootstrap.seeded("regression-ole-miss-georgia-evaluate")
        from tools.quiz_export import duplicates as duplicates_mod

        class _Guard:
            def __init__(self):
                self._q, self._e = set(), set()

            def question_seen(self, q):
                return q in self._q

            def entity_seen(self, e):
                return e in self._e

        for row in matches:
            result = cfb_upset_ranking.evaluate(c, row, rng, _Guard())
            # Ole Miss (#3 postseason) was ranked BETTER than Georgia (#6
            # postseason) -- this is never a real upset by RANKING_UPSET's
            # own definition, and evaluate() must reject it, not accept it
            # as a playable question.
            assert result == "WINNER_RANKED_BETTER_NOT_AN_UPSET", (
                f"the real Ole Miss/Georgia 2025 CFP game must never be accepted as a valid upset "
                f"question -- got {result!r}"
            )
    finally:
        c.close()


def test_no_ranking_upset_candidate_has_a_mismatched_season_type_rank():
    """Broader integrity check, not just the one named regression case:
    for every real candidate row, both ranks (when present) must come from
    the SAME season_type as the game itself -- the general form of the bug
    the season_type join fix closes. Verified directly against the raw
    cfb_rankings table, independent of the adapter's own join logic, so a
    future accidental removal of the join condition would be caught here
    even if it didn't happen to reintroduce the exact Ole Miss/Georgia case."""
    c = engine_bootstrap.connect()
    try:
        candidates = cfb_upset_ranking.fetch_ordered_candidates(c, seed="regression-season-type-integrity")
        checked = 0
        for row in candidates[:500]:  # a real, representative sample -- not every row, for test speed
            game = c.execute(
                "SELECT season_type FROM cfb_games_canonical WHERE game_id=?", (row["game_id"],)
            ).fetchone()
            assert game is not None, f"candidate game_id {row['game_id']} not found in cfb_games_canonical"
            game_season_type = game["season_type"]
            for school_id, rank in ((row["home_school_id"], row["home_rank"]), (row["away_school_id"], row["away_rank"])):
                if rank is None:
                    continue
                real_row = c.execute(
                    "SELECT 1 FROM cfb_rankings WHERE school_id=? AND season=? AND week=? "
                    "AND poll='AP Top 25' AND season_type=? AND rank=?",
                    (school_id, row["season"], row["week"], game_season_type, rank),
                ).fetchone()
                assert real_row is not None, (
                    f"candidate row for game {row['game_id']} cites rank {rank} for {school_id} but no real "
                    f"cfb_rankings row exists for that exact (school, season, week, poll, season_type) -- a "
                    f"mismatched-season_type rank leaked through"
                )
            checked += 1
        assert checked > 0, "no real candidates were available to check -- audit is not exercising real data"
    finally:
        c.close()
