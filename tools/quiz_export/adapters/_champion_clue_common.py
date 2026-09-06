"""Real, heterogeneous clue-fact generators for Three Clues One Champion /
Era Gauntlet.

Era Gauntlet rebuild (Pass 2.7): this module used to only ever describe the
60 real Super Bowl champions (`curated_nfl_offense_college_board`,
board_type='SB_CHAMPION') -- every board `fetch_ordered_candidates()`
could ever hand it was a champion, so Era Gauntlet was 100% Super Bowl
content by construction, not by choice. It now generalizes across the
SAME 3 pool_kinds from `_group_board_common.py` that already represent a
real (team, season) pair -- SB_CHAMPION, CURRENT_TEAM_2026,
NFL_TEAM_SEASON_ROSTER (DRAFT_CLASS/HONOR_GROUP are deliberately excluded
here: they represent a draft class or an All-Pro class, not a team's
season, so "guess the team AND season" has no coherent answer for them --
they stay exclusive to Odd College Out/One School Missing/Spot the Fake,
which don't make that same claim).

Real fact families, by pool_kind:
  - OPPONENT / SCORE / SB_MVP: SB_CHAMPION-only -- these are inherently
    championship facts (`nfl_championship_events`, `nfl_season_awards`
    award_type='SB_MVP'); a non-champion team-season has no real opponent/
    score/MVP to report, so these are never offered outside SB_CHAMPION.
  - COACH: real for ANY (team_code, season) -- `coach_team_seasons`
    (NFLVERSE_DATA, 1999+ coverage) is not restricted to championship
    seasons; resolved directly from the board's own `team_code` rather
    than through a championship-event lookup that only exists for
    champions.
  - RECORD: real for any (team_code, season) with real standings on file
    -- `season_standings` (NFLVERSE_DATA, 2002-2026), win-loss record and
    real playoff result where one exists. New this pass -- the concrete
    fix for non-champion boards (CURRENT_TEAM_2026, NFL_TEAM_SEASON_ROSTER)
    otherwise having only COACH as a real non-roster fact, which alone
    can't always clear the "2 of 3 non-roster clues" bar every board needs.
  - COLLEGE: one real position/college pair from the board itself -- works
    for every pool_kind, kept as one family among many, never the default.

Every clue is a REAL fact about a REAL person/team/season -- nothing here
is inferred or invented. A clue family with no real, resolvable data for a
given board (e.g. no coach on file, no championship event for a
non-champion board) is simply not offered for that board; the caller
selects only from families that actually returned a real clue.
"""
from __future__ import annotations

_TEAM_CODE_BY_DISPLAY_CACHE: dict | None = None


def _championship_event(c, team_display_name: str, season: int) -> dict | None:
    row = c.execute(
        "SELECT * FROM nfl_championship_events WHERE season=? AND winner_name_raw=?",
        (season, team_display_name),
    ).fetchone()
    return dict(row) if row else None


def opponent_clue(c, team_display_name: str, season: int) -> str | None:
    event = _championship_event(c, team_display_name, season)
    if not event or not event.get("loser_name_raw"):
        return None
    return f"This team's real Super Bowl opponent was the {event['loser_name_raw']}."


def score_clue(c, team_display_name: str, season: int) -> str | None:
    event = _championship_event(c, team_display_name, season)
    if not event or event.get("winner_score") is None or event.get("loser_score") is None:
        return None
    ot = " (in overtime)" if event.get("overtime") else ""
    return f"This team won the real Super Bowl by a score of {event['winner_score']}-{event['loser_score']}{ot}."


# Real perf fix caught by this pass's own test suite, not assumed: Era
# Gauntlet's pool grew from 60 to 502 real boards this pass, and
# coach_clue()/record_clue() used to run one SQL query EACH per board --
# ~1,000 extra individual queries per real generation call (every board is
# evaluate()'d regardless of target_count, same as every other adapter),
# enough to blow generation.py's 45s GENERATION_TIMEOUT_SECONDS (confirmed:
# gateway/tests/test_public_mode_wiring.py's cfb_three_clues_guess
# round-trip test consistently timed out at 45.4s before this fix). Both
# source tables are small, static reference data (936 / 800 rows) -- loaded
# ONCE, in full, into a plain dict, the first time either is needed, rather
# than re-queried per board. Never invalidated mid-process: these are
# real, rarely-refreshed reference tables (a scheduled data refresh job
# replaces them wholesale, not in place), and a brief staleness window
# after such a refresh is a correctness non-issue for trivia clue text.
_coach_cache: dict[tuple[str, int], str] | None = None
_record_cache: dict[tuple[str, int], tuple[int, int, int, str | None]] | None = None


def _load_coach_cache(c) -> dict[tuple[str, int], str]:
    global _coach_cache
    if _coach_cache is None:
        _coach_cache = {}
        for row in c.execute("SELECT team_code, season, coach_name FROM coach_team_seasons WHERE coach_name IS NOT NULL"):
            r = dict(row)
            _coach_cache[(r["team_code"], r["season"])] = r["coach_name"]
    return _coach_cache


def _load_record_cache(c) -> dict[tuple[str, int], tuple[int, int, int, str | None]]:
    global _record_cache
    if _record_cache is None:
        _record_cache = {}
        for row in c.execute(
            "SELECT team_code, season, wins, losses, ties, playoff_result FROM season_standings "
            "WHERE wins IS NOT NULL AND losses IS NOT NULL"
        ):
            r = dict(row)
            _record_cache[(r["team_code"], r["season"])] = (r["wins"], r["losses"], r["ties"] or 0, r["playoff_result"])
    return _record_cache


def coach_clue(c, team_code: str | None, season: int) -> str | None:
    if not team_code:
        return None
    coach_name = _load_coach_cache(c).get((team_code, season))
    if not coach_name:
        return None
    return f"This team's real head coach that season was {coach_name}."


def record_clue(c, team_code: str | None, season: int) -> str | None:
    """Real win-loss record (and real playoff result where one exists) for
    ANY (team_code, season) -- unlike opponent/score/sb_mvp, this is not
    restricted to championship seasons, which is exactly what makes it
    usable for the CURRENT_TEAM_2026/NFL_TEAM_SEASON_ROSTER boards those
    three families can't describe."""
    if not team_code:
        return None
    entry = _load_record_cache(c).get((team_code, season))
    if not entry:
        return None
    wins, losses, ties, playoff_result = entry
    record = f"{wins}-{losses}" + (f"-{ties}" if ties else "")
    playoff = _PLAYOFF_RESULT_TEXT.get(playoff_result)
    suffix = f", {playoff}" if playoff else ""
    return f"This team finished that real season {record}{suffix}."


# Real, distinct values confirmed directly against season_standings.playoff_result
# (2002-2026): WonSB 22, LostSB 22, LostCC 48, LostDV 96, LostWC 108, NULL 504
# (missed the playoffs entirely -- no clue text added for that real case).
_PLAYOFF_RESULT_TEXT = {
    "WonSB": "and won the Super Bowl",
    "LostSB": "and lost the Super Bowl",
    "LostCC": "and lost in the Conference Championship",
    "LostDV": "and lost in the Divisional round",
    "LostWC": "and lost in the Wild Card round",
}


def sb_mvp_clue(c, team_display_name: str, season: int) -> str | None:
    # Real, deliberate offset: nfl_season_awards.SB_MVP.season is the real
    # calendar year the Super Bowl was PLAYED (January of the following
    # year), one greater than the NFL season the champion actually played
    # -- confirmed directly (SB I: championship season=1966, SB_MVP
    # season=1967). Never silently queried with the un-adjusted season.
    row = c.execute(
        "SELECT player_name_raw FROM nfl_season_awards "
        "WHERE award_type='SB_MVP' AND season=? AND team_name_raw=?",
        (season + 1, team_display_name),
    ).fetchone()
    if not row or not row["player_name_raw"]:
        return None
    return f"This team's real Super Bowl MVP was {row['player_name_raw']}."


def college_clue(board: dict, position: str) -> str:
    return f"{position} from {board['positions'][position]}"


# (clue_family_id, generator) -- SB_CHAMPION-only real facts. COACH/RECORD
# are handled separately below since they resolve for any pool_kind via the
# board's own team_code, never through a championship-event lookup that
# only exists for real champions. COLLEGE also handled separately since it
# needs a `board`/`position`, not just (team_display_name, season).
_CHAMPION_ONLY_CLUE_FAMILIES = (
    ("OPPONENT", opponent_clue),
    ("SCORE", score_clue),
    ("SB_MVP", sb_mvp_clue),
)


def real_available_clues(c, board: dict) -> list[tuple[str, str]]:
    """Returns every real, resolvable (family_id, clue_text) pair for this
    board. OPPONENT/SCORE/SB_MVP only for real SB_CHAMPION boards (they are
    inherently championship facts); COACH/RECORD attempted for every
    pool_kind directly from the board's own real team_code (Era Gauntlet
    rebuild, Pass 2.7 -- see module docstring); COLLEGE included as a real
    fallback family for every pool_kind so a board with sparse non-roster
    data still has enough real clues to build a real puzzle."""
    team_display_name, season = board["team_display_name"], board["season"]
    clues: list[tuple[str, str]] = []

    if board.get("pool_kind") == "SB_CHAMPION":
        for family_id, fn in _CHAMPION_ONLY_CLUE_FAMILIES:
            text = fn(c, team_display_name, season)
            if text:
                clues.append((family_id, text))

    team_code = board.get("team_code")
    coach_text = coach_clue(c, team_code, season)
    if coach_text:
        clues.append(("COACH", coach_text))
    record_text = record_clue(c, team_code, season)
    if record_text:
        clues.append(("RECORD", record_text))

    # COLLEGE family: up to 3 real position/college pairs, offered as
    # individual candidate clues (never more than 1 actually used per
    # puzzle -- enforced by the caller, not here).
    for position in sorted(board["positions"].keys()):
        clues.append(("COLLEGE", college_clue(board, position)))

    return clues
