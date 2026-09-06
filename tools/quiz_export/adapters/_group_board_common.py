"""Shared multi-source "board" layer (Gold Standard Modes + Creator Quality
follow-up pass) -- the single reusable pool underneath Odd College Out,
Spot the Fake Lineup, One School Missing, and Three Clues One Champion.

A "board" is `{board_id, title, season, difficulty, positions: {slot:
college}, pool_kind}` -- the EXACT shape `_college_offense_curated_common.
fetch_boards()` already produces for the curated SB_CHAMPION/CURRENT_TEAM_2026
tables (60 + 32 real boards). This module generalizes that same shape to
three MORE real, independently-verified sources, so the four modes above
stop depending on one single 92-board dataset:

  - `sb_champion_boards()` / `current_team_boards()`: thin wrappers around
    the existing curated tables (no new data).
  - `nfl_team_season_roster_boards()`: real (season, team_code) starting
    skill-position groups from `canonical_roster_seasons` (starts>0, same
    real "starter = highest real games-started" signal lineup.py already
    established) joined to `nfl_players_draft.college` BY player_id -- never
    a name join. 416 real team-seasons measured directly (>=4 college-
    resolved starters), 2006-2018.
  - `draft_class_boards()`: real Round 1 draft classes from
    `nfl_players_draft`, grouped by `draft_season`. 47 real classes
    measured directly (>=4 college-resolved picks), 1980-2026.
  - `honor_group_boards()`: real NFL First-Team All-Pro classes from
    `nfl_all_pro_selections`, joined to `nfl_players_draft.college` by
    player_id. 46 real season groups measured directly (>=4 college-
    resolved honorees), 1980-2025.

Every source's `positions` dict values are real colleges attributed to a
real person for a real (season, team/draft-class/honor-class) -- nothing
here is invented, inferred, or guessed. `pool_kind` is carried through to
every board so a caller can log/audit which real source produced a given
generated question (provenance preserved end to end).
"""
from __future__ import annotations

from . import _college_offense_curated_common as curated_common
from .draft import resolve_franchise

# Same real, measured range lineup.py's own docstring establishes for this
# exact "starts>0, college-resolved" shape -- not re-derived here, reused.
TEAM_SEASON_MIN_SEASON, TEAM_SEASON_MAX_SEASON = 2006, 2018
DRAFT_CLASS_MIN_SEASON, DRAFT_CLASS_MAX_SEASON = 1980, 2026
HONOR_GROUP_MIN_SEASON, HONOR_GROUP_MAX_SEASON = 1980, 2025

ALL_POOL_KINDS = (
    "SB_CHAMPION", "CURRENT_TEAM_2026", "NFL_TEAM_SEASON_ROSTER",
    "DRAFT_CLASS", "HONOR_GROUP",
)


def sb_champion_boards(c) -> list[dict]:
    boards = curated_common.fetch_boards(c, "SB_CHAMPION")
    out = []
    for b in boards:
        b = dict(b)
        b["pool_kind"] = "SB_CHAMPION"
        b["title"] = f"{b['season']} {b['team_display_name']} (Super Bowl champion)"
        out.append(b)
    return out


def current_team_boards(c) -> list[dict]:
    boards = curated_common.fetch_boards(c, "CURRENT_TEAM_2026")
    out = []
    for b in boards:
        b = dict(b)
        b["pool_kind"] = "CURRENT_TEAM_2026"
        b["title"] = f"{b['season']} {b['team_display_name']}"
        out.append(b)
    return out


def nfl_team_season_roster_boards(c) -> list[dict]:
    rows = c.execute(
        "SELECT crs.season, crs.team_code, crs.player_id, crs.position, crs.starts, d.college "
        "FROM canonical_roster_seasons crs "
        "JOIN nfl_players_draft d ON d.player_key = crs.player_id "
        "WHERE crs.starts > 0 AND crs.position IS NOT NULL "
        "AND d.college IS NOT NULL AND d.college != '' "
        "AND crs.verification_status = 'SOURCE_BACKED' "
        "ORDER BY crs.season, crs.team_code, crs.starts DESC, crs.player_id"
    ).fetchall()

    groups: dict[tuple[int, str], list] = {}
    for r in rows:
        groups.setdefault((r["season"], r["team_code"]), []).append(r)

    boards = []
    for (season, team_code), players in groups.items():
        if not (TEAM_SEASON_MIN_SEASON <= season <= TEAM_SEASON_MAX_SEASON):
            continue
        qbs = [p for p in players if p["position"] == "QB"]
        rbs = [p for p in players if p["position"] == "RB"]
        wrs = [p for p in players if p["position"] == "WR"]
        tes = [p for p in players if p["position"] == "TE"]
        slots = {}
        if qbs:
            slots["QB"] = qbs[0]["college"]
        if rbs:
            slots["RB"] = rbs[0]["college"]
        if len(wrs) >= 1:
            slots["WR1"] = wrs[0]["college"]
        if len(wrs) >= 2:
            slots["WR2"] = wrs[1]["college"]
        if tes:
            slots["TE"] = tes[0]["college"]
        if len(slots) < 4:
            continue  # not enough real, distinct slots to build a fair board

        franchise, err = resolve_franchise(c, team_code, season)
        if err:
            continue  # a real, disclosed identity gap -- skipped, never guessed
        diff_score = (TEAM_SEASON_MAX_SEASON - season) / max(TEAM_SEASON_MAX_SEASON - TEAM_SEASON_MIN_SEASON, 1)
        boards.append({
            "board_id": f"NFL_TEAM_SEASON:{season}:{team_code}",
            "team_display_name": franchise["full_name"], "season": season,
            # Era Gauntlet / Three Clues diversification (Pass 2.7): real
            # team_code carried through so a caller can look up REAL
            # non-championship facts (coach, season record) for this
            # team-season directly -- these boards are not champions, so
            # nfl_championship_events has no row for them; team_code lets
            # coach_team_seasons/season_standings be queried without one.
            "team_code": team_code,
            "difficulty": _score_to_label(diff_score),
            "positions": slots, "pool_kind": "NFL_TEAM_SEASON_ROSTER",
            "title": f"{season} {franchise['full_name']} starting offense",
        })
    return boards


def draft_class_boards(c) -> list[dict]:
    rows = c.execute(
        "SELECT draft_season, draft_pick_overall, position, college FROM nfl_players_draft "
        "WHERE draft_round = 1 AND college IS NOT NULL AND college != '' "
        "ORDER BY draft_season, draft_pick_overall"
    ).fetchall()

    groups: dict[int, list] = {}
    for r in rows:
        if not (DRAFT_CLASS_MIN_SEASON <= r["draft_season"] <= DRAFT_CLASS_MAX_SEASON):
            continue
        groups.setdefault(r["draft_season"], []).append(r)

    boards = []
    for season, picks in groups.items():
        if len(picks) < 4:
            continue
        picks = picks[:8]  # cap at the top 8 real round-1 picks -- comparable size to an 11-slot lineup board
        slots = {}
        for p in picks:
            label = f"Pick {p['draft_pick_overall']}"
            slots[label] = p["college"]
        diff_score = (DRAFT_CLASS_MAX_SEASON - season) / max(DRAFT_CLASS_MAX_SEASON - DRAFT_CLASS_MIN_SEASON, 1)
        boards.append({
            "board_id": f"DRAFT_CLASS:{season}",
            "team_display_name": f"{season} NFL Draft's real Round 1 class",
            "season": season, "difficulty": _score_to_label(diff_score),
            "positions": slots, "pool_kind": "DRAFT_CLASS",
            "title": f"{season} NFL Draft, Round 1",
        })
    return boards


def honor_group_boards(c) -> list[dict]:
    rows = c.execute(
        "SELECT a.season, a.position_raw, a.player_id, d.college FROM nfl_all_pro_selections a "
        "JOIN nfl_players_draft d ON d.player_key = a.player_id "
        "WHERE a.is_ap = 1 AND a.honor_level = 'FIRST_TEAM' "
        "AND d.college IS NOT NULL AND d.college != '' "
        "ORDER BY a.season, a.position_raw, a.player_id"
    ).fetchall()

    groups: dict[int, list] = {}
    for r in rows:
        if not (HONOR_GROUP_MIN_SEASON <= r["season"] <= HONOR_GROUP_MAX_SEASON):
            continue
        groups.setdefault(r["season"], []).append(r)

    boards = []
    for season, honorees in groups.items():
        if len(honorees) < 4:
            continue
        honorees = honorees[:11]  # cap, comparable size to an 11-slot lineup board
        slots = {}
        seen_labels: dict[str, int] = {}
        for h in honorees:
            base = (h["position_raw"] or "Honoree").strip()
            n = seen_labels.get(base, 0) + 1
            seen_labels[base] = n
            label = base if n == 1 else f"{base} {n}"
            slots[label] = h["college"]
        diff_score = (HONOR_GROUP_MAX_SEASON - season) / max(HONOR_GROUP_MAX_SEASON - HONOR_GROUP_MIN_SEASON, 1)
        boards.append({
            "board_id": f"HONOR_GROUP:AP_FIRST_TEAM:{season}",
            "team_display_name": f"{season} AP NFL First-Team All-Pro roster",
            "season": season, "difficulty": _score_to_label(diff_score),
            "positions": slots, "pool_kind": "HONOR_GROUP",
            "title": f"{season} AP First-Team All-Pro",
        })
    return boards


def _score_to_label(diff_score: float) -> str:
    # The curated SB_CHAMPION/CURRENT_TEAM_2026 boards' own `difficulty`
    # field is a plain 3-band {"EASY","MEDIUM","HARD"} string (this is what
    # every caller of fetch_boards()/these new sources maps through its own
    # _DIFF_MAP) -- engine.band()/game_factory.band() is a DIFFERENT,
    # 4-tier vocabulary (adds "EXPERT") used elsewhere in this codebase for
    # question-level difficulty, not board-level. Bucketed directly here to
    # match the real, existing board contract instead of introducing a
    # vocabulary mismatch.
    if diff_score <= 0.33:
        return "EASY"
    if diff_score <= 0.66:
        return "MEDIUM"
    return "HARD"


_SOURCE_FUNCS = {
    "SB_CHAMPION": sb_champion_boards,
    "CURRENT_TEAM_2026": current_team_boards,
    "NFL_TEAM_SEASON_ROSTER": nfl_team_season_roster_boards,
    "DRAFT_CLASS": draft_class_boards,
    "HONOR_GROUP": honor_group_boards,
}

# Real, measured N+1 fix (same class of defect this pass already fixed in
# cfb_ranking.py/cfb_upset_ranking.py): NFL_TEAM_SEASON_ROSTER/DRAFT_CLASS/
# HONOR_GROUP each re-scan a real, non-trivial table (canonical_roster_
# seasons JOIN nfl_players_draft, etc.) -- cheap once, expensive re-run once
# per candidate if all_colleges_for_kind() recomputed it on every evaluate()
# call. Cached per pool_kind for the duration of one generation call only,
# reset at the top of fetch_all_boards() (called exactly once per real
# request, before any evaluate() calls).
_boards_cache: dict[str, list[dict]] = {}


def _boards_for_kind(c, pool_kind: str) -> list[dict]:
    cached = _boards_cache.get(pool_kind)
    if cached is None:
        cached = _SOURCE_FUNCS[pool_kind](c)
        _boards_cache[pool_kind] = cached
    return cached


def fetch_all_boards(c, pool_kinds: tuple[str, ...] | None = None) -> list[dict]:
    """The single entry point every Gold Standard mode adapter calls. Merges
    real boards from every requested source (default: all 5) into one flat
    list, each still carrying its own real `pool_kind` for provenance."""
    _boards_cache.clear()
    kinds = pool_kinds or ALL_POOL_KINDS
    boards = []
    for kind in kinds:
        if kind not in _SOURCE_FUNCS:
            continue
        boards.extend(_boards_for_kind(c, kind))
    return boards


def all_colleges_for_kind(c, pool_kind: str) -> list[str]:
    """Real distractor-college universe SCOPED to one source's own real
    colleges -- never mixed across sources (a draft-class impostor drawn
    from the curated Gold Standard workbook's own 183-college universe
    would be a real college, but from a totally different real dataset than
    the board being shown, which is a real but arbitrary scope mismatch,
    not a provenance error -- kept clean by never mixing)."""
    if pool_kind in ("SB_CHAMPION", "CURRENT_TEAM_2026"):
        return curated_common.all_colleges(c)
    boards = _boards_for_kind(c, pool_kind)
    colleges = sorted({v for b in boards for v in b["positions"].values()})
    return colleges
