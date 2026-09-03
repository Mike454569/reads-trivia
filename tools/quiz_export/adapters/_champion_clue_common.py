"""Real, heterogeneous clue-fact generators for Three Clues One Champion
(Gold Standard Modes + Creator Quality follow-up pass) -- replaces "reveal
3 of 11 roster colleges" as the ONLY clue family with 5 real, independently
verified fact types about the SAME 60 real Super Bowl champions
(`curated_nfl_offense_college_board`, board_type='SB_CHAMPION'):

  - OPPONENT: the real team it beat (`nfl_championship_events.loser_name_raw`)
  - SCORE: the real final score (`nfl_championship_events.winner_score`/`loser_score`)
  - COACH: the real head coach that season (`coach_team_seasons`, NFLVERSE_DATA,
    1999+ only -- a real, disclosed coverage floor, never fabricated for
    earlier seasons)
  - SB_MVP: the real Super Bowl MVP (`nfl_season_awards`, award_type='SB_MVP'
    -- note this table's own `season` is the REAL Super Bowl's calendar
    year, one greater than `nfl_championship_events.season`/the curated
    board's own season, which both use the NFL SEASON the team played;
    handled explicitly here, never silently misaligned)
  - COLLEGE: one real position/college pair from the existing curated board
    (kept as ONE possible family among five, not the default)

Every clue is a REAL fact about a REAL person/event/score for that exact
real champion -- nothing here is inferred or invented. A clue family that
has no real, resolvable data for a given champion (e.g. no real head coach
on file pre-1999) is simply not offered for that champion; the caller
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


def coach_clue(c, team_code: str | None, season: int) -> str | None:
    if not team_code:
        return None
    row = c.execute(
        "SELECT coach_name FROM coach_team_seasons WHERE season=? AND team_code=?",
        (season, team_code),
    ).fetchone()
    if not row or not row["coach_name"]:
        return None
    return f"This team's real head coach that season was {row['coach_name']}."


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


# (clue_family_id, generator) -- COLLEGE handled separately since it needs
# a `board`/`position`, not just (team_display_name, season).
_NON_ROSTER_CLUE_FAMILIES = (
    ("OPPONENT", opponent_clue),
    ("SCORE", score_clue),
    ("SB_MVP", sb_mvp_clue),
)


def real_available_clues(c, board: dict) -> list[tuple[str, str]]:
    """Returns every real, resolvable (family_id, clue_text) pair for this
    champion -- COACH included only when team_code is resolvable, COLLEGE
    included as one real fallback family so a champion with sparse
    non-roster data (pre-1999, no MVP resolved) still has enough real
    clues to build a real 3-clue puzzle."""
    team_display_name, season = board["team_display_name"], board["season"]
    clues: list[tuple[str, str]] = []
    for family_id, fn in _NON_ROSTER_CLUE_FAMILIES:
        text = fn(c, team_display_name, season)
        if text:
            clues.append((family_id, text))

    event = _championship_event(c, team_display_name, season)
    team_code = event.get("winner_team_code") if event else None
    coach_text = coach_clue(c, team_code, season)
    if coach_text:
        clues.append(("COACH", coach_text))

    # COLLEGE family: up to 3 real position/college pairs, offered as
    # individual candidate clues (never more than 1 actually used per
    # puzzle -- enforced by the caller, not here).
    for position in sorted(board["positions"].keys()):
        clues.append(("COLLEGE", college_clue(board, position)))

    return clues
